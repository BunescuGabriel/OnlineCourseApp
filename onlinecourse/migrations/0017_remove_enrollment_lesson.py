# Generated by Django 4.2.1 on 2023-07-21 19:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('onlinecourse', '0016_alter_enrollment_lesson'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='enrollment',
            name='lesson',
        ),
    ]
