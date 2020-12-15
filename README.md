# django-huey-monitor

Django based tool for monitoring huey task queue: https://github.com/coleifer/huey


Project state: planing/pre-alpha ;)


## developing

To start developing e.g.:

```bash
~$ git clone https://github.com/boxine/django-huey-monitor.git
~$ cd django-huey-monitor
~/django-huey-monitor$ make
help                 List all commands
install-poetry       install or update poetry via pip
install              install via poetry
update               Update the dependencies as according to the pyproject.toml file
lint                 Run code formatters and linter
fix-code-style       Fix code formatting
tox-listenvs         List all tox test environments
tox                  Run pytest via tox with all environments
tox-py36             Run pytest via tox with *python v3.6*
tox-py37             Run pytest via tox with *python v3.7*
tox-py38             Run pytest via tox with *python v3.8*
tox-py39             Run pytest via tox with *python v3.9*
pytest               Run pytest
pytest-ci            Run pytest with CI settings
publish              Release new version to PyPi
makemessages         Make and compile locales message files
start-dev-server     Start Django dev. server with the test project
clean                Remove created files from the test project (e.g.: SQlite, static files)
build                Update/Build docker services
up                   Start docker containers
down                 Stop all containers
logs                 Display and follow docker logs
```


## License

[GPL](LICENSE). Patches welcome!


## Links

* https://pypi.org/project/django-huey-monitor/
