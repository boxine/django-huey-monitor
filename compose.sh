#!/bin/bash

source docker/common.env

set -ex

exec poetry run docker-compose "$@"
