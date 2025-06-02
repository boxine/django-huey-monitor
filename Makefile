SHELL := /bin/bash

help: ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -_]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## install huey monitor package
	./manage.py install

update:  ## Update the dependencies as according to the pyproject.toml file
	./manage.py update_req

run-dev-server:  ## Run Django's developer server

test:  ## Run unittests
	./manage.py test

nox:  ## Run unittests via nox
	./manage.py nox

makemessages:  ## Make and compile locales message files
	./manage.py makemessages --all --no-location --no-obsolete --ignore=htmlcov --ignore=".nox*" --ignore=volumes
	./manage.py compilemessages --ignore=htmlcov --ignore=".nox*" --ignore=volumes

clean: ## Remove created files from the test project (e.g.: SQlite, static files)
	git clean -dfX huey_monitor_project/

###################################################################################################
# docker

build: ## Update/Build docker services
	./compose.sh pull --parallel
	./compose.sh build --pull --parallel

up: build ## Start docker containers
	./compose.sh up -d
	$(MAKE) logs

down: ## Stop all containers
	./compose.sh down

shell-django: ## go into a interactive bash shell in Django container
	./compose.sh exec django /bin/bash

run-shell-django: ## Build and start the Django container and go into shell
	./compose.sh build --pull --parallel django
	./compose.sh run --entrypoint '/bin/bash' django

shell-huey1: ## go into a interactive bash shell in Huey worker container 1
	./compose.sh exec huey1 /bin/bash

shell-huey2:  ## go into a interactive bash shell in Huey worker container 2
	./compose.sh exec huey2 /bin/bash

shell-huey3:  ## go into a interactive bash shell in Huey worker container 3
	./compose.sh exec huey3 /bin/bash

shell-redis:  ## go into a interactive bash shell in Redis container
	./compose.sh exec redis /bin/ash

logs: ## Display and follow docker logs
	./compose.sh logs --tail=500 --follow

logs-django: ## Display and follow docker logs only from "django" container
	./compose.sh logs --tail=500 --follow django

reload-django: ## Reload the Django dev server
	./compose.sh exec django /django/docker/utils/kill_python.sh
	./compose.sh logs --tail=500 --follow django

reload-huey: ## Reload the Huey worker
	./compose.sh exec huey1 /django/docker/utils/kill_python.sh
	./compose.sh exec huey2 /django/docker/utils/kill_python.sh
	./compose.sh exec huey3 /django/docker/utils/kill_python.sh
	./compose.sh logs --tail=500 --follow huey1 huey2 huey3

restart: down up  ## Restart the containers

fire-test-tasks:  ## Call "fire-test-tasks" manage command to create some Huey Tasks
	./compose.sh exec django /django/manage.py fire_test_tasks

fire-many-test-tasks:  ## Call "fire-test-tasks" with --count 10000 to create many task entries ;)
	./compose.sh exec django /django/manage.py fire_test_tasks --count 10000

fire-parallel-processing-task:  ## Just fire "parallel processing" Huey Task
	./compose.sh exec django /django/manage.py fire_parallel_processing_task

delete-all-tasks-data:  ## Delete all Task/Signal database enties
	./compose.sh exec django /django/manage.py delete_all_tasks_data

.PHONY: help install update run-dev-server test nox  makemessages clean build up down shell-django shell-huey1 shell-huey2 shell-huey3 logs reload-django reload-huey restart fire-test-tasks fire-parallel-processing-task delete-all-tasks-data
