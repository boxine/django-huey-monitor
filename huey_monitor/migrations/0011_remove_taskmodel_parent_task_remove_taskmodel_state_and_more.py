# Generated by Django 4.2 on 2023-04-12 14:08

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('huey_monitor', '0010_alter_taskmodel_parent_task'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskmodel',
            name='parent_task',
        ),
        migrations.RemoveField(
            model_name='taskmodel',
            name='state',
        ),
        migrations.DeleteModel(
            name='SignalInfoModel',
        ),
        migrations.DeleteModel(
            name='TaskModel',
        ),
    ]
