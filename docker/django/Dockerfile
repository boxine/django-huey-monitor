# https://hub.docker.com/_/python
FROM python:3.11-slim-bookworm

# for pip cache:
ENV XDG_CACHE_HOME=/pipcache/.cache

ENV PYTHONUNBUFFERED=1

# Install deps
RUN set -x \
    && apt-get update \
    && apt-get install -y postgresql-client python3-pip \
    && rm -rf /var/lib/apt \
    && python3 -m pip install -U pip \
    && pip3 install -U setuptools psycopg2-binary watchfiles

WORKDIR /django

COPY . ./

# Bootstrap: The first manage.py call will create the .venv
RUN ./manage.py version
