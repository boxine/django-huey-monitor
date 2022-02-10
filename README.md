# django-huey-monitor

Django based tool for monitoring [huey task queue](https://github.com/coleifer/huey)

Current implementation will just store all Huey task signals into the database
and display them in the Django admin.


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
~/django-huey-monitor$ make
help                 List all commands
install-poetry       install or update poetry via pip
install              install via poetry
update               Update the dependencies as according to the pyproject.toml file
lint                 Run code formatters and linter
fix-code-style       Fix code formatting
tox-listenvs         List all tox test environments
tox                  Run pytest via tox with all environments
pytest               Run pytest
pytest-ci            Run pytest with CI settings
publish              Release new version to PyPi
makemessages         Make and compile locales message files
clean                Remove created files from the test project (e.g.: SQlite, static files)
build                Update/Build docker services
up                   Start docker containers
down                 Stop all containers
shell_django         go into a interactive bash shell in Django container
shell_huey           go into a interactive bash shell in Huey worker container
logs                 Display and follow docker logs
reload_django        Reload the Django dev server
reload_huey          Reload the Huey worker
restart              Restart the containers
fire_test_tasks      Call "fire_test_tasks" manage command to create some Huey Tasks

~/django-huey-monitor$ make install-poetry
~/django-huey-monitor$ make install
~/django-huey-monitor$ make up
```


It's also possible to run the test setup with SQLite and Huey immediate setup
without docker:

```bash
~$ git clone https://github.com/boxine/django-huey-monitor.git
~$ cd django-huey-monitor
~/django-huey-monitor$ ./manage.sh run_testserver
```


## Backwards-incompatible changes


### Version compatibility

| huey-monitor    | Django           | Python
|-----------------|------------------|------------------
| >v0.5.0         | v2.2, v3.1, v3.2 | v3.7, v3.8, v3.9
| <=v0.4.0        | v2.2, v3.0, v3.1 | v3.7, v3.8, v3.9


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

* [dev](https://github.com/boxine/django-huey-monitor/compare/v0.5.0...master)
  * _tbc_
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
