import math
import os
from io import BytesIO
from typing import BinaryIO, Generator

from django.core.files.images import ImageFile
from django.db.models.fields.files import FieldFile, ImageFieldFile
from PIL import Image
from pydub import AudioSegment


def delete_storage_file(file: FieldFile):
    if file:
        file.storage.delete(name=file.name)


def downscale_image(image: ImageFieldFile, max_width: int, max_height: int, save: bool = False):
    if image and image.width > max_width and image.height > max_height:
        buf = BytesIO()

        with Image.open(image) as im:
            ratio = max(max_width / im.width, max_height / im.height)
            im.thumbnail((int(im.width * ratio), int(im.height * ratio)))
            im.save(buf, format=im.format)

        image.save(name=image.name, content=ImageFile(file=buf), save=save)


def generate_thumbnail(from_field: ImageFieldFile, to_field: ImageFieldFile, size: int, save: bool = False):
    stem, suffix = os.path.splitext(os.path.basename(from_field.name))
    thumbnail_filename = f"{stem}-thumbnail{suffix}"
    buf = BytesIO()

    with Image.open(from_field) as im:
        ratio = size / max(im.width, im.height)
        im.thumbnail((int(im.width * ratio), int(im.height * ratio)))
        im.save(buf, format=im.format)
        mimetype = im.get_format_mimetype()

    to_field.save(name=thumbnail_filename, content=ImageFile(file=buf), save=save)
    return mimetype


def get_audio_file_dbfs_array(file: BinaryIO, format_name: str) -> list[float]:
    audio = AudioSegment.from_file(file, format_name)
    return get_audio_segment_dbfs_array(audio)


def get_audio_segment_dbfs_array(audio: AudioSegment) -> list[float]:
    dbfs_values = [-100.0 if s.dBFS < -100 else s.dBFS for s in split_audio_segment(audio, 200)]
    min_dbfs = min(dbfs_values)
    dbfs_values = [dbfs - min_dbfs for dbfs in dbfs_values]
    max_dbfs = max(dbfs_values)
    multiplier = 100 / max_dbfs

    return [dbfs * multiplier for dbfs in dbfs_values]


def seconds_to_timestamp(value: int):
    hours = int(value / 60 / 60)
    minutes = int(value / 60 % 60)
    seconds = int(value % 60 % 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def split_audio_segment(whole: AudioSegment, parts: int) -> "Generator[AudioSegment]":
    i = 0
    n = math.ceil(len(whole) / parts)

    while i < len(whole):
        yield whole[i:i + n]
        i += n
