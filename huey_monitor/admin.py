from bx_django_utils.templatetags.humanize_time import human_duration
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from huey_monitor.models import SignalInfoModel, TaskModel


class TaskModelChangeList(ChangeList):
    def get_queryset(self, request):
        """
        List only the main-tasks (sub-tasks will be inlined)
        """
        qs = super().get_queryset(request)
        qs = qs.filter(parent_task__isnull=True)
        return qs


@admin.register(TaskModel)
class TaskModelAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return TaskModelChangeList

    def column_name(self, obj):
        qs = TaskModel.objects.filter(parent_task_id=obj.pk)
        context = {
            'main_task': obj,
            'sub_tasks': qs
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
                'main_task': TaskModel.objects.get(pk=obj.parent_task_id)
            }
        else:
            # This is a main Task
            qs = TaskModel.objects.filter(parent_task_id=obj.pk)
            context = {
                'sub_tasks': qs
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

    list_display = (
        'human_update_dt',
        'column_name',
        'state',
        'total',
        'human_unit',
        'human_percentage',
        'human_progress',
        'human_throughput',
        'duration'
    )
    readonly_fields = (
        'task_id', 'signals', 'create_dt', 'update_dt',
        'human_percentage',
        'human_progress',
        'human_throughput',
    )
    ordering = ('-update_dt',)
    list_display_links = None
    date_hierarchy = 'create_dt'
    list_filter = ('state__hostname', 'name', 'state__signal_name')
    search_fields = ('name', 'state__exception_line', 'state__exception')
    fieldsets = (
        (_('Meta'), {
            'fields': (
                'task_id',
                'create_dt', 'update_dt'
            )
        }),
        (_('Task Information'), {
            'fields': (
                'name',
                'state',
                'human_progress_string',
                'signals'
            )
        }),
        (_('Hierarchy'), {
            'fields': (
                'task_hierarchy_info',
            )
        }),
    )

    class Media:
        css = {
            'all': ('huey_monitor.css',)
        }


@admin.register(SignalInfoModel)
class SignalInfoModelAdmin(admin.ModelAdmin):
    def task_name(self, obj):
        return obj.task.name

    list_display = ('create_dt', 'task_name', '__str__', 'hostname', 'pid', 'thread')
    readonly_fields = ('create_dt',)
    list_display_links = ('task_name',)
    ordering = ('-create_dt',)
    date_hierarchy = 'create_dt'
    list_filter = ('hostname', 'task__name', 'signal_name')
    search_fields = ('task__name', 'exception_line', 'exception')

    def has_change_permission(self, request, obj=None):
        return False
