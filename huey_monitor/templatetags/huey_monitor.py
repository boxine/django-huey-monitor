from django import template
from django.template.loader import render_to_string
from huey.contrib.djhuey import HUEY


register = template.Library()


@register.simple_tag
def huey_counts_info():
    context = dict(
        huey_pending_count=HUEY.pending_count(),
        huey_scheduled_count=HUEY.scheduled_count(),
        huey_result_count=HUEY.result_count(),
    )
    return render_to_string('admin/huey_monitor/huey_counts_info.html', context)
