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

        diff = end_dt - obj.create_dt
        total_seconds = diff.total_seconds()
        if total_seconds > 60:
            return f'{total_seconds/60:.2f} Min.'
        else:
            return f'{total_seconds:.2f} Sec.'

    list_display = ('create_dt', 'update_dt', 'name', 'state', 'duration')
    readonly_fields = ('task_id', 'signals', 'create_dt')
    ordering = ('-update_dt',)
    list_display_links = ('name',)
    date_hierarchy = 'create_dt'
    list_filter = ('name', 'state__signal_name')
    search_fields = ('name', 'state__exception_line', 'state__exception')


@admin.register(SignalInfoModel)
class SignalInfoModelAdmin(admin.ModelAdmin):
    def task_name(self, obj):
        return obj.task.name

    list_display = ('create_dt', 'task_name', '__str__', 'task_id')
    readonly_fields = ('create_dt',)
    list_display_links = ('task_name',)
    ordering = ('-create_dt',)
    date_hierarchy = 'create_dt'
    list_filter = ('task__name', 'signal_name')
    search_fields = ('task__name', 'exception_line', 'exception')

    def has_change_permission(self, request, obj=None):
        return False
