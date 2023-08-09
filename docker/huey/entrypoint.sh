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

    # install/update venv and wait for services:
    /django/docker/utils/init.sh "${1}"

    ./manage.py --help
    ./manage.py run_huey --worker-type process --workers 2
    echo "Huey terminated with exit code: $?"
    sleep 3
    exit 1
)

exit 2
