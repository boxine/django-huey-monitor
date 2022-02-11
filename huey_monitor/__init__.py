"""
    Huey Monitor Django reuseable App
"""

from django import VERSION as DJANGO_VERSION


if DJANGO_VERSION < (3, 2):
    default_app_config = 'huey_monitor.apps.HueyMonitorConfig'


__version__ = '0.5.0'
