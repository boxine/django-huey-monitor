from huey_monitor import __version__


def huey_monitor_version_string(request):
    return {"version_string": f"v{__version__}"}
