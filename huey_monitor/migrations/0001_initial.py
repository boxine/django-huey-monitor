# Generated by Django 2.2.17 on 2020-12-14 15:30

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SignalInfoModel',
            fields=[
                ('id',
                 models.UUIDField(
                     default=uuid.uuid4,
                     editable=False,
                     primary_key=True,
                     serialize=False)),
                ('signal_name',
                 models.CharField(
                     help_text='Name of the signal',
                     max_length=128,
                     verbose_name='Signal Name')),
                ('exception_line',
                 models.TextField(
                     max_length=128,
                     verbose_name='Exception Line')),
                ('exception',
                 models.TextField(
                     blank=True,
                     help_text='Full information of a exception',
                     null=True,
                     verbose_name='Exception')),
                ('create_dt',
                 models.DateTimeField(
                     auto_now_add=True,
                     help_text='(will be set automatically)',
                     verbose_name='Create date')),
            ],
            options={
                'verbose_name': 'Task Signal',
                'verbose_name_plural': 'Task Signals',
            },
        ),
        migrations.CreateModel(
            name='TaskModel',
            fields=[
                ('create_dt',
                 models.DateTimeField(
                     blank=True,
                     editable=False,
                     help_text='ModelTimetrackingMixin.create_dt.help_text',
                     null=True,
                     verbose_name='ModelTimetrackingMixin.create_dt.verbose_name')),
                ('update_dt',
                 models.DateTimeField(
                     blank=True,
                     editable=False,
                     help_text='ModelTimetrackingMixin.update_dt.help_text',
                     null=True,
                     verbose_name='ModelTimetrackingMixin.update_dt.verbose_name')),
                ('task_id',
                 models.UUIDField(
                     help_text='The UUID of the Huey-Task',
                     primary_key=True,
                     serialize=False,
                     verbose_name='Task UUID')),
                ('name',
                 models.CharField(
                     max_length=128,
                     verbose_name='Task name')),
                ('state',
                 models.ForeignKey(
                     blank=True,
                     help_text='Last Signal information',
                     null=True,
                     on_delete=django.db.models.deletion.PROTECT,
                     related_name='+',
                     to='huey_monitor.SignalInfoModel',
                     verbose_name='State')),
            ],
            options={
                'verbose_name': 'Task',
                'verbose_name_plural': 'Tasks',
            },
        ),
        migrations.AddField(
            model_name='signalinfomodel',
            name='task',
            field=models.ForeignKey(
                help_text='The Task instance for this Signal Info entry.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='signals',
                to='huey_monitor.TaskModel',
                verbose_name='Task'),
        ),
    ]
