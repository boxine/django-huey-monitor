# Generated by Django 3.2.10 on 2022-01-03 17:39

from django.db import migrations, models


def forward_code(apps, schema_editor):
    # Assume that all old, existing task are finished ;)
    TaskModel = apps.get_model('huey_monitor', 'taskmodel')
    TaskModel.objects.update(finished=True)


class Migration(migrations.Migration):

    dependencies = [
        ('huey_monitor', '0005_progress_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskmodel',
            name='desc',
            field=models.CharField(blank=True, default='', help_text='Prefix for progress information', max_length=64, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='signalinfomodel',
            name='exception_line',
            field=models.TextField(blank=True, max_length=128, verbose_name='Exception Line'),
        ),
        migrations.AddField(
            model_name='signalinfomodel',
            name='progress_count',
            field=models.PositiveIntegerField(blank=True, help_text='Number of units processed (At the time of this signal creation)', null=True, verbose_name='Progress Count'),
        ),
        migrations.AddField(
            model_name='taskmodel',
            name='finished',
            field=models.BooleanField(default=False, help_text='Indicates that this Task no longer waits or run. (It does not mean that execution was successfully completed.)', verbose_name='Finished'),
        ),
        migrations.AddField(
            model_name='taskmodel',
            name='progress_count',
            field=models.PositiveIntegerField(blank=True, help_text='Number of units processed (Up-to-date only if task finished)', null=True, verbose_name='Progress Count'),
        ),
        migrations.DeleteModel(
            name='TaskProgressModel',
        ),
        migrations.RunPython(forward_code, reverse_code=migrations.RunPython.noop),
    ]
