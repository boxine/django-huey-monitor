#!/bin/sh

set -e

restart_error_handler() {
    echo "Restart ${0} in 3 sec..."
    sleep 3
    (
        set -x
        exec ${0} reload
    )
}
trap restart_error_handler 0

echo "_______________________________________________________________________"
echo "$(date +%c) - ${0} $*"

(
    set -x

    cat huey_monitor_project/settings/docker.py

    # install/update venv and wait for services:
    /django/docker/utils/init.sh "${1}"

    ./manage.py --help

    # Needed for AlwaysLoggedInAsSuperUserMiddleware:
    export RUN_MAIN=true

    watchfiles --filter python "python manage.py run_dev_server --noreload django:8000" /django/
    echo "runserver terminated with exit code: $?"
    sleep 3
    exit 1
)

exit 2
