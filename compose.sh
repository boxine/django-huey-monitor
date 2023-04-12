#!/bin/bash

source docker/common.env

set -ex

exec .venv/bin/docker-compose "$@"
