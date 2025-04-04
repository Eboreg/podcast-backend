# Generated by Django 5.1.6 on 2025-03-08 16:13

import django.db.models.deletion
import klaatu_django.db
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PodcastContentRequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('remote_host', klaatu_django.db.TruncatedCharField(blank=True, max_length=100)),
                ('remote_addr', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', klaatu_django.db.TruncatedCharField(blank=True, max_length=200)),
                ('referer', klaatu_django.db.TruncatedCharField(blank=True, max_length=100)),
                ('path_info', klaatu_django.db.TruncatedCharField(blank=True, max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PodcastRequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('remote_host', klaatu_django.db.TruncatedCharField(blank=True, max_length=100)),
                ('remote_addr', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', klaatu_django.db.TruncatedCharField(blank=True, max_length=200)),
                ('referer', klaatu_django.db.TruncatedCharField(blank=True, max_length=100)),
                ('path_info', klaatu_django.db.TruncatedCharField(blank=True, max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EpisodeAudioRequestLog',
            fields=[
                ('podcastcontentrequestlog_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='logs.podcastcontentrequestlog')),
            ],
            options={
                'abstract': False,
            },
            bases=('logs.podcastcontentrequestlog',),
        ),
    ]
