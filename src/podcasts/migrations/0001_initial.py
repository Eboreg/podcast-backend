# Generated by Django 5.1.6 on 2025-04-08 15:36

import uuid

import django.db.models.deletion
import django.db.models.functions.text
import django.utils.timezone
import martor.models
from django.db import migrations, models

import podcasts.models.episode
import podcasts.models.podcast
import podcasts.models.podcast_link
import podcasts.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PodcastContent',
            fields=[
                ('slug', models.SlugField(max_length=100)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', martor.models.MartorField(blank=True, default=None, null=True)),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_draft', models.BooleanField(default=False, verbose_name='Draft')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
            ],
            options={
                'ordering': ['-published'],
            },
        ),
        migrations.CreateModel(
            name='Podcast',
            fields=[
                ('slug', models.SlugField(help_text='Will be used in URLs.', primary_key=True, serialize=False, validators=[podcasts.validators.podcast_slug_validator])),
                ('name', models.CharField(max_length=100)),
                ('tagline', models.CharField(blank=True, default=None, max_length=500, null=True)),
                ('description', martor.models.MartorField(blank=True, default=None, null=True)),
                ('cover', models.ImageField(blank=True, default=None, help_text="This is the round 'avatar' image.", null=True, upload_to=podcasts.models.podcast.podcast_image_path, validators=[podcasts.validators.podcast_cover_validator])),
                ('cover_height', models.PositiveIntegerField(default=None, null=True)),
                ('cover_width', models.PositiveIntegerField(default=None, null=True)),
                ('cover_mimetype', models.CharField(default=None, max_length=50, null=True)),
                ('cover_thumbnail', models.ImageField(blank=True, default=None, null=True, upload_to=podcasts.models.podcast.podcast_image_path)),
                ('cover_thumbnail_height', models.PositiveIntegerField(default=None, null=True)),
                ('cover_thumbnail_width', models.PositiveIntegerField(default=None, null=True)),
                ('cover_thumbnail_mimetype', models.CharField(default=None, max_length=50, null=True)),
                ('banner', models.ImageField(blank=True, default=None, help_text='Should be >= 960px wide and have aspect ratio 3:1.', null=True, upload_to=podcasts.models.podcast.podcast_image_path, verbose_name='Banner image')),
                ('banner_height', models.PositiveIntegerField(default=None, null=True)),
                ('banner_width', models.PositiveIntegerField(default=None, null=True)),
                ('favicon', models.ImageField(blank=True, default=None, null=True, upload_to=podcasts.models.podcast.podcast_image_path)),
                ('favicon_content_type', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('language', models.CharField(blank=True, choices=podcasts.models.podcast.get_language_choices, default=None, max_length=5, null=True)),
                ('name_font_family', models.CharField(choices=[('Anton', 'Anton'), ('Deutsche Uncialis', 'Deutsche Uncialis'), ('Fascinate Inline', 'Fascinate Inline'), ('Futura Display BQ', 'Futura Display BQ'), ('Limelight', 'Limelight'), ('Lobster', 'Lobster'), ('Roboto Black', 'Roboto Black'), ('Roboto Serif Bold', 'Roboto Serif Bold'), ('Unifraktur Cook', 'Unifraktur Cook')], default='Unifraktur Cook', max_length=50)),
                ('name_font_size', models.CharField(choices=[('small', 'small'), ('normal', 'normal'), ('large', 'large')], default='normal', max_length=10)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PodcastLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('icon', models.CharField(choices=[('facebook', 'Facebook'), ('patreon', 'Patreon'), ('discord', 'Discord'), ('apple', 'Apple'), ('android', 'Android'), ('spotify', 'Spotify'), ('itunes', 'Itunes')], default=None, max_length=10, null=True)),
                ('custom_icon', models.ImageField(blank=True, default=None, null=True, upload_to=podcasts.models.podcast_link.podcast_link_icon_path)),
                ('url', models.URLField()),
                ('label', models.CharField(max_length=100)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('theme', models.CharField(choices=[('primary', 'Primary'), ('secondary', 'Secondary'), ('tertiary', 'Tertiary')], default='primary', max_length=10)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': [django.db.models.functions.text.Lower('name')],
                'indexes': [models.Index(fields=['name'], name='podcasts_ar_name_0f4045_idx')],
                'constraints': [models.UniqueConstraint(fields=('name',), name='podcasts__artist__name__uq')],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cat', models.CharField(max_length=50)),
                ('sub', models.CharField(default=None, max_length=50, null=True)),
            ],
            options={
                'ordering': ['cat', 'sub'],
                'indexes': [models.Index(fields=['cat', 'sub'], name='podcasts_ca_cat_aaa27d_idx')],
            },
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('podcastcontent_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='podcasts.podcastcontent')),
                ('season', models.PositiveSmallIntegerField(blank=True, default=None, null=True)),
                ('number', models.PositiveSmallIntegerField(blank=True, default=None, null=True)),
                ('audio_file', models.FileField(blank=True, default=None, null=True, upload_to=podcasts.models.episode.episode_audio_file_path)),
                ('duration_seconds', models.FloatField(blank=True, default=0.0, verbose_name='duration')),
                ('dbfs_array', models.JSONField(blank=True, default=list)),
                ('audio_content_type', models.CharField(blank=True, max_length=100)),
                ('audio_file_length', models.PositiveIntegerField(blank=True, default=0)),
                ('image', models.ImageField(blank=True, default=None, null=True, upload_to=podcasts.models.episode.episode_image_path)),
                ('image_height', models.PositiveIntegerField(default=None, null=True)),
                ('image_width', models.PositiveIntegerField(default=None, null=True)),
                ('image_mimetype', models.CharField(default=None, max_length=50, null=True)),
                ('image_thumbnail', models.ImageField(blank=True, default=None, null=True, upload_to=podcasts.models.episode.episode_image_path)),
                ('image_thumbnail_height', models.PositiveIntegerField(default=None, null=True)),
                ('image_thumbnail_width', models.PositiveIntegerField(default=None, null=True)),
                ('image_thumbnail_mimetype', models.CharField(default=None, max_length=50, null=True)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('podcasts.podcastcontent',),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('podcastcontent_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='podcasts.podcastcontent')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('podcasts.podcastcontent',),
        ),
        migrations.CreateModel(
            name='EpisodeSong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('comment', models.CharField(blank=True, default=None, max_length=100, null=True)),
                ('timestamp', models.PositiveIntegerField()),
                ('artists', models.ManyToManyField(blank=True, related_name='songs', to='podcasts.artist')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.AddField(
            model_name='podcastcontent',
            name='podcast',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='contents', to='podcasts.podcast'),
        ),
    ]
