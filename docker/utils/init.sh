#!/bin/sh

# init script for all python based containers

set -e

if [ "${1}" = "reload" ]
then
    echo "\n\nReload: Skip init...\n\n"
    exit 0
fi

(
    set -x
    # Wait if redis and postgres available:
    /django/docker/utils/wait_for_services.py
)

if [ "$(which psql)" != "" ]; then
    echo -n "\nTest if Postgres is available...\n"
    until psql -h "${DB_HOST}" -U "${DB_USER}" -c '\l'; do
        echo "Postgres is unavailable, yet..."
        sleep 1
    done
fi

