# django-huey-monitor

Django based tool for monitoring [huey task queue](https://github.com/coleifer/huey)

Current implementation will just store all Huey task signals into the database
and display them in the Django admin.

[![tests](https://github.com/boxine/django-huey-monitor//actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/boxine/django-huey-monitor//actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/huey_monitor/branch/main/graph/badge.svg)](https://app.codecov.io/github/jedie/huey_monitor)
[![django-huey-monitor @ PyPi](https://img.shields.io/pypi/v/django-huey-monitor?label=django-huey-monitor%20%40%20PyPi)](https://pypi.org/project/django-huey-monitor/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-huey-monitor)](https://github.com/boxine/django-huey-monitor//blob/main/pyproject.toml)
[![License GPL-3.0-or-later](https://img.shields.io/pypi/l/django-huey-monitor)](https://github.com/boxine/django-huey-monitor//blob/main/LICENSE)


## Quickstart

```bash
pip install django-huey-monitor
```

```python
INSTALLED_APPS = [
    #...
    'bx_django_utils', # https://github.com/boxine/bx_django_utils
    'huey_monitor',
    #...
]
```

Note: You must normally not change your Huey tasks.

### Collect main-/sub-tasks

Huey monitor model can store information about task hierarchy. But this information can't be collected automatically.
You have to store these information in your Task code.

e.g.:

```python
@task(context=True)
def sub_task(task, parent_task_id, chunk_data):
    # Save the task hierarchy by:
    TaskModel.objects.set_parent_task(
        main_task_id=parent_task_id,
        sub_task_id=task.id,
    )
    # ... do something with e.g.: chunk_data ...


@task(context=True)
def main_task(task):
    for chunk_data in something:
        sub_task(parent_task_id=task.id, chunk_data=chunk_data)
```

Working example can be found in the test app here: [huey_monitor_tests/test_app/tasks.py](https://github.com/boxine/django-huey-monitor/blob/master/huey_monitor_tests/test_app/tasks.py)


### Collect progress information

Running task can store progress information in a similar way as [tqdm](https://pypi.org/project/tqdm/).
So it's possible to see the progress in admin.

Minimal example:

```python
@task(context=True)
def foobar_task(task, list_to_process):
    process_info = ProcessInfo(
        task,
        desc='A description of this Job',
        total=len(list_to_process)
    )

    for item in list_to_process:
        # ...to something with the {item}...
        process_info.update(n=1) # add the information that one item was processed
```

It is also possible to divide the work to several tasks and collect information about the processing of main-/sub-tasks.

Working example can be found in the test app here: [huey_monitor_tests/test_app/tasks.py](https://github.com/boxine/django-huey-monitor/blob/master/huey_monitor_tests/test_app/tasks.py)


## settings

### override list filter (optional)

It is possible to override `list_filter` of `SignalInfoModelAdmin` and `TaskModelAdmin` via settings.
e.g.:

```python
HUEY_MONITOR_SIGNAL_INFO_MODEL_LIST_FILTER = ('task__name', 'signal_name')
HUEY_MONITOR_TASK_MODEL_LIST_FILTER = ('name', 'state__signal_name')
```

Note: This both settings are optional.
In this example is the "hostname" filter not present ;)


## run test project

Note: You can quickly test Huey Monitor with the test project, e.g:

```bash
~/django-huey-monitor$ ./manage.sh run_testserver
```
or in an isolated Docker container:
```bash
~/django-huey-monitor$ make up
```
More info see below.

# Screenshots

(More Screenshots here: [boxine.github.io/django-huey-monitor/](https://boxine.github.io/django-huey-monitor/))

### 2021-02-22-v030-task-details.png

![2021-02-22-v030-task-details.png](https://raw.githubusercontent.com/boxine/django-huey-monitor/gh-pages/2021-02-22-v030-task-details.png)

### 2021-02-22-v030-progress-info1.png

![2021-02-22-v030-progress-info1.png](https://raw.githubusercontent.com/boxine/django-huey-monitor/gh-pages/2021-02-22-v030-progress-info1.png)


## developing

* install docker
* clone the project
* start the container

To start developing e.g.:

```bash
~$ git clone https://github.com/boxine/django-huey-monitor.git
~$ cd django-huey-monitor
~/django-huey-monitor$ ./manage.py
~/django-huey-monitor$ make help
~/django-huey-monitor$ make up
```

Point our browser to: `http://localhost:8000/`

Our Makefile contains the following targets:

[comment]: <> (✂✂✂ auto generated make help start ✂✂✂)
```
help                           List all commands
install                        install huey monitor package
update                         Update the dependencies as according to the pyproject.toml file
run-dev-server                 Run Django's developer server
test                           Run unittests
nox                            Run unittests via nox
makemessages                   Make and compile locales message files
clean                          Remove created files from the test project (e.g.: SQlite, static files)
build                          Update/Build docker services
up                             Start docker containers
down                           Stop all containers
shell-django                   go into a interactive bash shell in Django container
run-shell-django               Build and start the Django container and go into shell
shell-huey1                    go into a interactive bash shell in Huey worker container 1
shell-huey2                    go into a interactive bash shell in Huey worker container 2
shell-huey3                    go into a interactive bash shell in Huey worker container 3
shell-redis                    go into a interactive bash shell in Redis container
logs                           Display and follow docker logs
logs-django                    Display and follow docker logs only from "django" container
reload-django                  Reload the Django dev server
reload-huey                    Reload the Huey worker
restart                        Restart the containers
fire-test-tasks                Call "fire-test-tasks" manage command to create some Huey Tasks
fire-many-test-tasks           Call "fire-test-tasks" with --count 10000 to create many task entries ;)
fire-parallel-processing-task  Just fire "parallel processing" Huey Task
delete-all-tasks-data          Delete all Task/Signal database enties
```
[comment]: <> (✂✂✂ auto generated make help end ✂✂✂)


It's also possible to run the test setup with SQLite and Huey immediate setup
without docker:

```bash
~$ git clone https://github.com/boxine/django-huey-monitor.git
~$ cd django-huey-monitor
~/django-huey-monitor$ ./manage.py run_dev_server
```


## Backwards-incompatible changes


### Version compatibility

| Huey Monitor | Django           | Python             |
|--------------|------------------|--------------------|
| >0.10.0      | v4.2, v5.0, v5.1 | v3.11, v3.12       |
| >v0.7.0      | v3.2, v4.1, v4.2 | v3.9, v3.10, v3.11 |
| >v0.6.0      | v3.2, v4.0, v4.1 | v3.9, v3.10, v3.11 |
| >v0.5.0      | v2.2, v3.1, v3.2 | v3.7, v3.8, v3.9   |
| <=v0.4.0     | v2.2, v3.0, v3.1 | v3.7, v3.8, v3.9   |


### v0.10.0

Set min. Python to v3.11.
Remove Django 3.2.x and add Django v5.1.x to text matrix.


### v0.6.0

We refactor the project setup: Developer must reinit the repository.

### v0.5.0

Change CI and remove tests against Django 3.0, but add test run with Django v3.2

### v0.3.0 -> v0.4.0 - Outsourcing Django stuff

[bx_py_utils](https://github.com/boxine/bx_py_utils) was split and Django related stuff moved into: [bx_django_utils](https://github.com/boxine/bx_django_utils)

You must change your Django settings and replace the app name:
```diff
 INSTALLED_APPS = [
     #...
-     'bx_py_utils',
+     'bx_django_utils',
     'huey_monitor',
     #...
 ]
```


## History

* [dev](https://github.com/boxine/django-huey-monitor/compare/v0.9.1...main)
  * _tbc_
* [v0.9.1 - 26.01.2024](https://github.com/boxine/django-huey-monitor/compare/v0.9.0...v0.9.1)
  * Fix `DisallowedModelAdminLookup` in `SignalInfoModelAdmin`, too.
* [v0.9.0 - 22.12.2023](https://github.com/boxine/django-huey-monitor/compare/v0.8.1...v0.9.0)
  * Fix #135 `DisallowedModelAdminLookup` in `TaskModelAdmin`
  * Add "thread" name as change list filter.
  * Enhance test project setup
  * Apply manageprojects updates
  * Remove Python v3.9 support
  * Add Django v5.0 to test matrix and remove Django 4.1
  * Enable local AUTOLOGIN as default
  * Use unittest "load_tests Protocol" and deny any requests in tests
  * Add https://github.com/PyCQA/flake8-bugbear
  * Update requirements
* [v0.8.1 - 20.11.2023](https://github.com/boxine/django-huey-monitor/compare/v0.8.0...v0.8.1)
  * Bugfix `ZeroDivisionError` in admin
* [v0.8.0 - 20.11.2023](https://github.com/boxine/django-huey-monitor/compare/v0.7.1...v0.8.0)
  * Make is possible to override `list_filter` of `SignalInfoModelAdmin` and `TaskModelAdmin` via settings
  * Update local docker dev setup
* [v0.7.1 - 18.08.2023](https://github.com/boxine/django-huey-monitor/compare/v0.7.0...v0.7.1)
  * Fix #127: Catch error getting HUEY counts
* [v0.7.0 - 09.08.2023](https://github.com/boxine/django-huey-monitor/compare/v0.6.0...v0.7.0)
  * New: Display Huey pending/scheduled/result task counts in admin
  * Switch to git `main` branch
  * Switch from `pytest` to normal `unittests`
  * Switch from `poetry` to `pip-tools`
  * Use https://github.com/jedie/manage_django_project for developing
  * Expand test matrix by remove Django 4.0 and add 4.2
  * Enhance tox config
* [v0.6.0 - 09.01.2023](https://github.com/boxine/django-huey-monitor/compare/v0.5.0...v0.6.0)
  * Test against Django v3.2, v4.0, v4.1 and Python v3.9 - v3.11
  * Optimize Admin change list ([contributed by henribru](https://github.com/boxine/django-huey-monitor/pull/110))
  * Order sub-tasks chronologically in admin ([contributed by Skrattoune](https://github.com/boxine/django-huey-monitor/pull/90))
  * displaying progression for parent_tasks ([contributed by Skrattoune](https://github.com/boxine/django-huey-monitor/pull/91))
  * Delegating set_parent_task to `ProcessInfo.__init__` ([contributed by Skrattoune](https://github.com/boxine/django-huey-monitor/pull/111))
  * Fix #27 auto crop overlong process info description
  * NEW #102 Unlock all tasks via change list object tool link
  * Fix #81 Expand `TaskModel.desc` max. length and make `SignalInfoModel.exception_line` optional
  * Update docker test setup
* [v0.5.0 - 10.02.2022](https://github.com/boxine/django-huey-monitor/compare/v0.4.6...v0.5.0)
  * Refactor models: Remove `TaskProgressModel` and store progress information into `TaskModel`
* [v0.4.6 - 03.02.2022](https://github.com/boxine/django-huey-monitor/compare/v0.4.5...v0.4.6)
  * [Display task desc or name in TaskAdmin](https://github.com/boxine/django-huey-monitor/pull/72) (contributed by [Skrattoune](https://github.com/Skrattoune))
  * update requirements
  * use [Darker](https://github.com/akaihola/darker) as code formatter
  * Check linting via PyTest plugins
* [v0.4.5 - 28.01.2022](https://github.com/boxine/django-huey-monitor/compare/v0.4.4...v0.4.5)
  * Fix [#46](https://github.com/boxine/django-huey-monitor/issues/46) by increment existing TaskProgressModel instances (based on [contribution](https://github.com/boxine/django-huey-monitor/pull/67) by [Skrattoune](https://github.com/Skrattoune))
* [v0.4.4 - 07.01.2022](https://github.com/boxine/django-huey-monitor/compare/v0.4.3...v0.4.4)
  * Add missing `huey_monitor.css` file
* [v0.4.3 - 07.01.2022](https://github.com/boxine/django-huey-monitor/compare/v0.4.2...v0.4.3)
  * Add temporary `cumulate2parents` flag to `ProcessInfo` ([contributed by formacube](https://github.com/boxine/django-huey-monitor/pull/44))
* [v0.4.2 - 25.08.2020](https://github.com/boxine/django-huey-monitor/compare/v0.4.1...v0.4.2)
  * suppress the default_app_config attribute in Django 3.2+ (contributed by [Jonas Svarvaa](https://github.com/xolan))
* [v0.4.1 - 02.06.2020](https://github.com/boxine/django-huey-monitor/compare/v0.4.0...v0.4.1)
  * Bugfix `ProcessInfo.__str__()`
  * [#27](https://github.com/boxine/django-huey-monitor/issues/27) Check 'desc' length in `ProcessInfo`
  * Remove test against Django 3.0 and add tests with Django 3.2
  * Bugfix local `tox` runs and use different Python versions
* [v0.4.0 - 21.05.2020](https://github.com/boxine/django-huey-monitor/compare/v0.3.0...v0.4.0)
  * bx_py_utils was split and Django related stuff moved into: https://github.com/boxine/bx_django_utils
* [v0.3.0 - 22.02.2020](https://github.com/boxine/django-huey-monitor/compare/v0.2.0...v0.3.0)
  * Store and display running task progress information a little bit as [tqdm](https://pypi.org/project/tqdm/) [#17](https://github.com/boxine/django-huey-monitor/issues/17)
* [v0.2.0 - 17.02.2020](https://github.com/boxine/django-huey-monitor/compare/v0.1.0...v0.2.0)
  * Store "parent_task" information for main-/sub-tasks
* [v0.1.0 - 21.12.2020](https://github.com/boxine/django-huey-monitor/compare/v0.0.1...v0.1.0)
  * Work-a-round if a Huey worker died
  * Fix missing translations from bx_py_utils in test project
  * Simulate a cluster of Huey worker via docker and the test project
* v0.0.1 - 15.12.2021
  * initial release

## License

[GPL](LICENSE). Patches welcome!


## Links

* https://pypi.org/project/django-huey-monitor/
