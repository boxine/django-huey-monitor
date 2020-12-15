#!/bin/sh

set -ex

psql -U postgres -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\""
