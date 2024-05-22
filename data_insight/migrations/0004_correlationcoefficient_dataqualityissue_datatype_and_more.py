# Generated by Django 5.0.3 on 2024-04-08 04:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_insight', '0003_project_pipeline'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrelationCoefficient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column1_name', models.CharField(max_length=100)),
                ('column2_name', models.CharField(max_length=100)),
                ('coefficient', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='DataQualityIssue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='DataType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=100)),
                ('data_type', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='DescriptiveStatistic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=100)),
                ('mean', models.FloatField()),
                ('std_dev', models.FloatField()),
                ('min_val', models.FloatField()),
                ('max_val', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='MissingValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TestResults',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('table_name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.project')),
            ],
        ),
        migrations.CreateModel(
            name='UniqueValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column_name', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
                ('test_result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.testresults')),
            ],
        ),
        migrations.DeleteModel(
            name='Product',
        ),
        migrations.AddField(
            model_name='missingvalue',
            name='test_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.testresults'),
        ),
        migrations.AddField(
            model_name='descriptivestatistic',
            name='test_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.testresults'),
        ),
        migrations.AddField(
            model_name='datatype',
            name='test_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.testresults'),
        ),
        migrations.AddField(
            model_name='dataqualityissue',
            name='test_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.testresults'),
        ),
        migrations.AddField(
            model_name='correlationcoefficient',
            name='test_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_insight.testresults'),
        ),
    ]