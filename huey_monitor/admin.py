from bx_py_utils.templatetags.humanize_time import human_duration
from django.contrib import admin
from django.template.loader import render_to_string
from django.utils import timezone

from huey_monitor.models import SignalInfoModel, TaskModel


@admin.register(TaskModel)
class TaskModelAdmin(admin.ModelAdmin):
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

    list_display = ('human_create_dt', 'human_update_dt', 'name', 'state', 'duration')
    readonly_fields = ('task_id', 'signals', 'create_dt', 'update_dt')
    ordering = ('-update_dt',)
    list_display_links = ('name',)
    date_hierarchy = 'create_dt'
    list_filter = ('state__hostname', 'name', 'state__signal_name')
    search_fields = ('name', 'state__exception_line', 'state__exception')


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
