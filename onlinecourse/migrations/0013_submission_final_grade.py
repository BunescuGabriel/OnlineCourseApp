# Generated by Django 4.2.1 on 2023-07-21 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinecourse', '0012_remove_submission_lesson'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='final_grade',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
    ]
