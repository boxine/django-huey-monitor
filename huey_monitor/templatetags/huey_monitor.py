import logging

from django import template
from django.template.loader import render_to_string
from huey.contrib.djhuey import HUEY


logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def huey_counts_info():
    try:
        context = dict(
            huey_pending_count=HUEY.pending_count(),
            huey_scheduled_count=HUEY.scheduled_count(),
            huey_result_count=HUEY.result_count(),
        )
    except OSError as err:
        # e.g.: Redis down or other setup used see #127
        logger.exception('Failed to get counts from HUEY: %s', err)

        return f'<p>Huey counts: ({type(err).__name__}: {err})</p>'
    else:
        return render_to_string('admin/huey_monitor/huey_counts_info.html', context)
