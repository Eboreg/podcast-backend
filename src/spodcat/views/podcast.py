import logging
from datetime import date, timedelta
from typing import cast
from urllib.parse import urljoin

import rest_framework.renderers
from django.apps import apps
from django.db.models import Max, Prefetch
from django.http import HttpResponse
from django.template.response import TemplateResponse
from feedgen.entry import FeedEntry
from feedgen.ext.podcast import PodcastExtension
from feedgen.ext.podcast_entry import PodcastEntryExtension
from feedgen.feed import FeedGenerator
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_json_api import views

from spodcat import serializers
from spodcat.logs.chart_data import ChartData
from spodcat.models import Episode, Podcast, PodcastContent
from spodcat.podcasting2 import Podcast2EntryExtension, Podcast2Extension
from spodcat.settings import spodcat_settings
from spodcat.utils import date_to_datetime


logger = logging.getLogger(__name__)


class PodcastFeedGenerator(FeedGenerator):
    podcast: PodcastExtension
    podcast2: Podcast2Extension


class PodcastFeedEntry(FeedEntry):
    podcast: PodcastEntryExtension
    podcast2: Podcast2EntryExtension


class PodcastViewSet(views.ReadOnlyModelViewSet):
    prefetch_for_includes = {
        "authors": ["authors"],
        "categories": ["categories"],
        "contents": [
            Prefetch("contents", queryset=PodcastContent.objects.partial().listed().with_has_songs()),
        ],
        "links": ["links"],
    }
    select_for_includes = {
        "__all__": ["name_font_face"],
    }
    queryset = Podcast.objects.order_by_last_content(reverse=True)
    serializer_class = serializers.PodcastSerializer

    @action(
        methods=["get"],
        detail=False,
        serializer_class=serializers.ChartSerializer,
        renderer_classes=[rest_framework.renderers.JSONRenderer, rest_framework.renderers.BrowsableAPIRenderer],
        authentication_classes=[SessionAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def chart(self, request: Request):
        from spodcat.logs.models import (
            PodcastEpisodeAudioRequestLog,
            PodcastRssRequestLog,
        )

        chart_type = request.query_params["type"]
        chart_qs = PodcastEpisodeAudioRequestLog.objects.filter(is_bot=False).filter_by_user(request.user)
        chart_data: ChartData | None = None
        start_date = self.get_chart_start_date(request)
        end_date = self.get_chart_end_date(request)

        if chart_type == "play-time":
            chart_data = chart_qs.get_podcast_play_count_chart_data(start_date, end_date).fill_empty_points()
        elif chart_type == "unique-ips":
            chart_data = chart_qs.get_unique_ips_chart_data(start_date, end_date).fill_empty_points()
        elif chart_type == "rss-unique-ips":
            chart_js = (
                PodcastRssRequestLog.objects
                .filter(is_bot=False)
                .exclude(user_agent="")
                .filter_by_user(request.user)
            )
            chart_data = chart_js.get_unique_ips_chart_data(start_date, end_date).fill_empty_points()

        if chart_data:
            serializer = self.get_serializer(chart_data)
            return Response(serializer.data)

        raise ValidationError({"type": "Not a valid chart type."})

    @action(
        methods=["get"],
        url_path="chart",
        detail=True,
        serializer_class=serializers.ChartSerializer,
        renderer_classes=[rest_framework.renderers.JSONRenderer, rest_framework.renderers.BrowsableAPIRenderer],
        authentication_classes=[SessionAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def detail_chart(self, request: Request, pk: str):
        from spodcat.logs.models import PodcastEpisodeAudioRequestLog

        chart_type = request.query_params["type"]
        chart_qs = (
            PodcastEpisodeAudioRequestLog.objects
            .filter(is_bot=False, episode__podcast=pk)
            .filter_by_user(request.user)
        )
        chart_data: ChartData | None = None

        if chart_type == "play-time":
            start_date = self.get_chart_start_date(request)
            end_date = self.get_chart_end_date(request)
            chart_data = chart_qs.get_episode_play_count_chart_data(start_date, end_date)

        if chart_data:
            serializer = self.get_serializer(chart_data)
            return Response(serializer.data)

        raise ValidationError({"type": "Not a valid chart type."})

    def get_chart_end_date(self, request: Request):
        return (
            date.fromisoformat(request.query_params["end"])
            if "end" in request.query_params
            else date.today()
        )

    def get_chart_start_date(self, request: Request):
        return (
            date.fromisoformat(request.query_params["start"])
            if "start" in request.query_params
            else date.today() - timedelta(days=30)
        )

    @action(methods=["post"], detail=True)
    def ping(self, request: Request, pk: str):
        instance = self.get_object()

        if apps.is_installed("spodcat.logs"):
            from spodcat.logs.models import PodcastRequestLog

            PodcastRequestLog.create_from_request(request=request, podcast=instance)

        return Response()

    @action(methods=["get"], detail=True)
    # pylint: disable=no-member
    def rss(self, request: Request, pk: str):
        queryset = self.get_queryset().prefetch_related("authors", "categories").select_related("owner")
        podcast: Podcast = get_object_or_404(queryset, slug=pk)
        authors = [{"name": o.get_full_name(), "email": o.email} for o in podcast.authors.all()]
        categories = [c.to_dict() for c in podcast.categories.all()]
        episode_qs = Episode.objects.filter(podcast=podcast).listed().with_has_chapters()
        last_published = episode_qs.aggregate(last_published=Max("published"))["last_published"]
        author_string = ", ".join([a["name"] for a in authors if a["name"]])

        if apps.is_installed("spodcat.logs"):
            from spodcat.logs.models import PodcastRssRequestLog

            PodcastRssRequestLog.create_from_request(request=request, podcast=podcast)

        fg = FeedGenerator()
        fg.load_extension("podcast")
        fg.register_extension("podcast2", Podcast2Extension, Podcast2EntryExtension)
        fg = cast(PodcastFeedGenerator, fg)
        fg.title(podcast.name)
        fg.link([
            {"href": podcast.rss_url, "rel": "self", "type": "application/rss+xml"},
            {"href": podcast.frontend_url, "rel": "alternate"},
        ])
        fg.description(podcast.tagline or podcast.name)
        fg.podcast.itunes_type("episodic")
        if last_published:
            fg.lastBuildDate(date_to_datetime(last_published))
        if podcast.cover:
            fg.podcast.itunes_image(podcast.cover.url)
            if podcast.cover_height and podcast.cover_width:
                fg.image(url=podcast.cover.url, width=str(podcast.cover_width), height=str(podcast.cover_height))
            if podcast.cover_width:
                fg.podcast2.podcast_image(podcast.cover.url, podcast.cover_width)
        if podcast.cover_thumbnail and podcast.cover_thumbnail_width:
            fg.podcast2.podcast_image(podcast.cover_thumbnail.url, podcast.cover_thumbnail_width)
        if podcast.owner.email and podcast.owner.get_full_name():
            fg.podcast.itunes_owner(name=podcast.owner.get_full_name(), email=podcast.owner.email)
        if authors:
            fg.author(authors)
        if author_string:
            fg.podcast.itunes_author(author_string)
        if podcast.language:
            fg.language(podcast.language)
        if categories:
            fg.podcast.itunes_category(categories)
        fg.podcast2.podcast_guid(str(podcast.guid))

        for episode in episode_qs:
            fe = cast(PodcastFeedEntry, fg.add_entry(order="append"))
            if episode.has_chapters:
                fe.podcast2.podcast_chapters(
                    spodcat_settings.get_absolute_backend_url("spodcat:episode-chapters", args=(episode.id,))
                )
            fe.title(episode.name)
            fe.content(episode.description_html, type="CDATA")
            fe.description(episode.description_text)
            fe.podcast.itunes_summary(episode.description_text)
            fe.published(date_to_datetime(episode.published))
            fe.podcast.itunes_season(episode.season)
            fe.podcast2.podcast_season(episode.season)
            if episode.number is not None and episode.number % 1 == 0:
                fe.podcast.itunes_episode(episode.number)
            fe.podcast2.podcast_episode(episode.number)
            fe.podcast.itunes_episode_type("full")
            fe.link(href=urljoin(spodcat_settings.FRONTEND_ROOT_URL, f"{podcast.slug}/episode/{episode.slug}"))
            fe.podcast.itunes_duration(round(episode.duration_seconds))
            if episode.image:
                fe.podcast.itunes_image(episode.image.url)
                fe.podcast2.podcast_image(episode.image.url, episode.image_width)
            if episode.audio_file:
                fe.enclosure(
                    url=episode.audio_file.url,
                    type=episode.audio_content_type,
                    length=episode.audio_file_length,
                )
            fe.guid(guid=str(episode.id), permalink=False)
            if authors:
                fe.author(authors)
            if author_string:
                fe.podcast.itunes_author(author_string)

        rss = fg.rss_str(pretty=True)

        if request.query_params.get("html"):
            return TemplateResponse(
                request=request,
                template="spodcat/rss.html",
                context={"rss": rss.decode()},
            )

        return HttpResponse(
            content=rss,
            content_type="application/xml; charset=utf-8",
            headers={"Content-Disposition": f"inline; filename=\"{podcast.slug}.rss.xml\""},
        )
