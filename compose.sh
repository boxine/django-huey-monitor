#!/bin/bash

source docker/common.env

set -ex

exec docker compose "$@"
