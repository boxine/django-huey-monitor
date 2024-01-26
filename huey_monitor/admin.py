from bx_django_utils.templatetags.humanize_time import human_duration
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.views.main import ChangeList
from django.db.models import OuterRef, Prefetch
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import HUEY
from huey.signals import SIGNAL_EXECUTING

from huey_monitor.models import SignalInfoModel, TaskModel


class FixLookupAllowedMixin:
    """
    Work-a-round for: https://code.djangoproject.com/ticket/35020
    # FIXME: Remove after release into all supported Django versions.
    """

    def lookup_allowed(self, lookup, value):
        list_filter = self._get_list_filter()
        if lookup in list_filter:
            return True
        return super().lookup_allowed(lookup, value)

    def _get_list_filter(self):
        """return list_filter without `request` object."""
        raise NotImplementedError()

    def get_list_filter(self, request):
        return self._get_list_filter()


class TaskModelChangeList(ChangeList):
    def get_queryset(self, request):
        """
        List only the main-tasks (sub-tasks will be inlined)
        """
        qs = super().get_queryset(request)
        executing_dt = SignalInfoModel.objects.filter(
            task_id=OuterRef('task_id'), signal_name=SIGNAL_EXECUTING
        ).values('create_dt')[:1]
        qs = (
            qs.filter(parent_task__isnull=True)
            .prefetch_related(
                Prefetch(
                    'sub_tasks',
                    queryset=TaskModel.objects.select_related('state')
                    .annotate(executing_dt=executing_dt)
                    .order_by('-create_dt'),
                )
            )
            .annotate(executing_dt=executing_dt)
        )
        return qs


@admin.register(TaskModel)
class TaskModelAdmin(FixLookupAllowedMixin, admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return TaskModelChangeList

    def column_name(self, obj):
        qs = obj.sub_tasks.all()
        context = {
            'main_task': obj,
            'sub_tasks': qs,
        }
        return render_to_string(
            template_name='admin/huey_monitor/taskmodel/column_name.html',
            context=context,
        )

    column_name.short_description = _('Task name')

    def task_hierarchy_info(self, obj):
        if obj.parent_task_id is not None:
            # This is a sub task
            context = {
                'main_task': TaskModel.objects.get(pk=obj.parent_task_id),
            }
        else:
            # This is a main Task
            qs = TaskModel.objects.filter(parent_task_id=obj.pk)
            context = {
                'sub_tasks': qs,
            }

        return render_to_string(
            template_name='admin/huey_monitor/taskmodel/task_hierarchy_info.html',
            context=context,
        )

    task_hierarchy_info.short_description = _('Task hierarchy')

    def has_change_permission(self, request, obj=None):
        return False

    def signals(self, obj):
        signals = SignalInfoModel.objects.filter(task_id=obj.pk).order_by('-create_dt')
        context = {
            'task': obj,
            'signals': signals,
        }
        return render_to_string('admin/huey_monitor/taskmodel/field_signals.html', context)

    def duration(self, obj):
        if not obj.state:
            return '-'

        if obj.state.signal_name == 'executing':
            end_dt = timezone.now()
        else:
            end_dt = obj.state.create_dt

        return human_duration(obj.create_dt, end_dt)

    def changelist_url(self):
        info = (self.admin_site.name, self.model._meta.app_label, self.model._meta.model_name)
        url_name = '%s:%s_%s_changelist' % info
        return reverse(url_name, current_app=self.admin_site.name)

    def flush_locks_view(self, request):
        flushed = HUEY.flush_locks()
        if not flushed:
            messages.info(request, 'No tasks locks exists, nothing to flush, ok.')
        else:
            messages.success(request, f'Flush task locks: {", ".join(sorted(flushed))}')
        return redirect(self.changelist_url())

    def get_urls(self):
        urls = [
            path(
                'flush_locks/',
                self.admin_site.admin_view(self.flush_locks_view),
                name='flush_locks',
            ),
        ] + super().get_urls()
        return urls

    list_display = (
        'human_update_dt',
        'column_name',
        'state',
        'total',
        'human_unit',
        'human_percentage',
        'human_progress',
        'human_throughput',
        'duration',
    )
    readonly_fields = (
        'task_id',
        'signals',
        'create_dt',
        'update_dt',
        'human_percentage',
        'human_progress',
        'human_throughput',
    )
    ordering = ('-update_dt',)
    list_display_links = None
    list_select_related = ('state',)
    date_hierarchy = 'create_dt'
    search_fields = ('name', 'state__exception_line', 'state__exception')
    fieldsets = (
        (_('Meta'), {'fields': ('task_id', 'create_dt', 'update_dt')}),
        (
            _('Task Information'),
            {
                'fields': (
                    'name',
                    'desc',
                    'state',
                    'progress_count',
                    'cumulate_progress',
                    'human_progress_string',
                    'signals',
                )
            },
        ),
        (_('Hierarchy'), {'fields': ('task_hierarchy_info',)}),
    )

    def _get_list_filter(self):
        """return list_filter without `request` object."""
        return getattr(settings, 'HUEY_MONITOR_TASK_MODEL_LIST_FILTER', None) or (
            'name',
            'state__signal_name',
            'state__thread',
            'state__hostname',
        )

    def get_list_filter(self, request):
        return self._get_list_filter()

    class Media:
        css = {
            'all': ('huey_monitor.css',),
        }


@admin.register(SignalInfoModel)
class SignalInfoModelAdmin(FixLookupAllowedMixin, admin.ModelAdmin):
    def task_name(self, obj):
        return obj.task.name

    list_display = (
        'create_dt',
        'task_name',
        '__str__',
        'progress_count',
        'hostname',
        'pid',
        'thread',
    )
    readonly_fields = ('create_dt',)
    list_display_links = ('task_name',)
    ordering = ('-create_dt',)
    date_hierarchy = 'create_dt'
    search_fields = ('task__name', 'exception_line', 'exception')

    def _get_list_filter(self):
        """return list_filter without `request` object."""
        return getattr(settings, 'HUEY_MONITOR_SIGNAL_INFO_MODEL_LIST_FILTER', None) or (
            'task__name',
            'signal_name',
            'thread',
            'hostname',
        )

    def get_list_filter(self, request):
        return self._get_list_filter()

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('task')
