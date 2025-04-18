import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from django.conf import settings


DeviceCategory = Literal["auto", "computer", "mobile", "smart_speaker", "smart_tv", "watch"]
ReferrerCategory = Literal["app", "host"]
UserAgentType = Literal["app", "bot", "browser", "library"]


@dataclass
class UserAgentData:
    user_agent: str
    type: UserAgentType
    name: str
    is_bot: bool
    device_name: str | None = None
    device_category: DeviceCategory | None = None
    referrer_name: str | None = None
    referrer_category: ReferrerCategory | None = None

    @classmethod
    # pylint: disable=redefined-builtin
    def from_dicts(
        cls,
        user_agent: str,
        type: UserAgentType,
        ua_dict: "UserAgentDict",
        device: "DeviceDict | None",
        referrer: "ReferrerDict | None",
    ):
        return cls(
            user_agent=user_agent,
            type=type,
            name=ua_dict["name"],
            is_bot=type == "bot" or ua_dict.get("category") == "bot",
            device_name=device["name"] if device else None,
            device_category=device["category"] if device else None,
            referrer_name=referrer["name"] if referrer else None,
            referrer_category=referrer["category"] if referrer else None,
        )


class BaseUserAgentDict(TypedDict):
    name: str
    pattern: str
    comments: str | None
    description: str | None
    examples: list[str] | None
    svg: str | None
    urls: list[str] | None


class UserAgentDict(BaseUserAgentDict):
    category: Literal["bot"] | None


class DeviceDict(BaseUserAgentDict):
    category: DeviceCategory


class ReferrerDict(BaseUserAgentDict):
    category: ReferrerCategory


user_agent_dict_cache: dict[str, list] = {}


def get_useragent_data(user_agent: str) -> UserAgentData | None:
    basenames: list[tuple[UserAgentType, str]] = [
        ("bot", "bots"),
        ("app", "apps"),
        ("library", "libraries"),
        ("browser", "browsers"),
    ]

    for key, basename in basenames:
        ua_dict: UserAgentDict | None = get_useragent_dict_from_file(basename, user_agent)
        if ua_dict:
            device: DeviceDict | None = get_useragent_dict_from_file("devices", user_agent) if key != "bot" else None
            referrer: ReferrerDict | None = (
                get_useragent_dict_from_file("referrers", user_agent)
                if key == "browser" else None
            )

            return UserAgentData.from_dicts(
                user_agent=user_agent,
                type=key,
                ua_dict=ua_dict,
                device=device,
                referrer=referrer,
            )

    return None


def get_useragent_dict_from_file(basename: str, user_agent: str):
    for ua_dict in get_useragent_dicts(basename):
        if re.search(ua_dict["pattern"], user_agent):
            return ua_dict
    return None


def get_useragent_dicts(basename: str):
    from podcasts import user_agent

    cached = user_agent.user_agent_dict_cache.get(basename, None)
    if cached is not None:
        return cached

    dicts = []
    json_path = Path(settings.BASE_DIR).resolve() / f"user-agents-v2/src/{basename}.json"

    if json_path.is_file():
        with json_path.open("rt") as f:
            dicts = json.loads(f.read()).get("entries", [])

    user_agent.user_agent_dict_cache[basename] = dicts

    return dicts
