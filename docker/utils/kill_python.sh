#!/bin/sh

PIDS="$(pidof python) $(pidof python3)"

set -ex

for pid in ${PIDS}; do kill $pid; done
