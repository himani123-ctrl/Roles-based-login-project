# Generated by Django 5.0.7 on 2024-09-21 05:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_expensereport_expensedetail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensereport',
            name='company_address',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='expensereport',
            name='report_from',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='expensereport',
            name='report_to',
            field=models.CharField(max_length=100),
        ),
    ]
