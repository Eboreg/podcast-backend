from django import forms
from django.conf import settings
from django.contrib.admin.widgets import (
    AdminTextareaWidget,
    AutocompleteSelectMultiple,
)
from django.core.validators import EMPTY_VALUES
from martor.widgets import MartorWidget as BaseMartorWidget


def seconds_to_timestamp(value: int):
    hours = int(value / 60 / 60)
    minutes = int(value / 60 % 60)
    seconds = int(value % 60 % 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


class ArtistAutocompleteWidget(AutocompleteSelectMultiple):
    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"

        return forms.Media(
            js=(
                f"admin/js/vendor/jquery/jquery{extra}.js",
                f"admin/js/vendor/select2/select2.full{extra}.js",
                "admin/js/jquery.init.js",
                "assets/js/artist_autocomplete.js",
            ),
            css={
                "screen": (
                    f"admin/css/vendor/select2/select2{extra}.css",
                    "admin/css/autocomplete.css",
                ),
            },
        )

    def optgroups(self, name, value, attr=None):
        selected_choices = {str(v) for v in value if str(v) not in EMPTY_VALUES}
        subgroup = []
        for idx, artist in enumerate([a for a in self.choices if str(a.id) in value]):
            subgroup.append(self.create_option(name, artist.id, artist.name, selected_choices, idx))
        return [(None, subgroup, 0)]


class ArtistMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset, **kwargs):
        super().__init__(queryset, **kwargs)
        self._choices = list(queryset)

    def clean(self, value):
        value = self.prepare_value(value)
        new_value = []
        for pk in value:
            if isinstance(pk, str) and pk.startswith("NEW--"):
                name = pk[5:]
                artist = self.queryset.filter(name__iexact=name).first()
                if not artist:
                    artist = self.queryset.create(name=name)
                new_value.append(artist.pk)
            else:
                new_value.append(pk)
        return super().clean(new_value)


class TimestampField(forms.Field):
    widget = forms.TimeInput

    def prepare_value(self, value):
        if isinstance(value, int):
            return seconds_to_timestamp(value)
        return super().prepare_value(value)

    def to_python(self, value):
        if isinstance(value, str) and value:
            value = value.replace(".", ":")
            parts = value.split(":")
            seconds = int(parts[-1]) if len(parts) > 0 else 0
            minutes = int(parts[-2]) if len(parts) > 1 else 0
            hours = int(parts[-3]) if len(parts) > 2 else 0
            return seconds + (minutes * 60) + (hours * 60 * 60)
        return super().to_python(value)


class EpisodeSongForm(forms.ModelForm):
    timestamp = TimestampField()


class MartorWidget(BaseMartorWidget):
    class Media:
        extend = False
        css = {
            "all": (
                "plugins/css/bootstrap.min.css",
                "martor/css/martor-admin.min.css",
                "plugins/css/ace.min.css",
                "plugins/css/resizable.min.css",
                "assets/css/martor.css",
            )
        }

        js = (
            "plugins/js/jquery.min.js",
            "plugins/js/bootstrap.min.js",
            "plugins/js/ace.js",
            "plugins/js/mode-markdown.js",
            "plugins/js/ext-language_tools.js",
            "plugins/js/theme-github.js",
            "plugins/js/highlight.min.js",
            "plugins/js/resizable.min.js",
            "plugins/js/emojis.min.js",
            "martor/js/martor.bootstrap.min.js",
        )


class AdminMartorWidget(MartorWidget, AdminTextareaWidget):
    pass
