"""
Copyright 2022-2025 czubix

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from .dataclass import dataclass

from ..utils import parse_time

from datetime import datetime

from typing import Sequence, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client

@dataclass
class EmbedFooter:
    text: str
    icon_url: str = None
    proxy_icon_url: str = None

@dataclass
class EmbedImage:
    url: str
    height: int
    width: int
    proxy_url: str = None
    placeholder_version: Any = None
    placeholder: Any = None
    flags: int = None
    description: str = None

@dataclass
class EmbedThumbnail:
    url: str
    height: int
    width: int
    proxy_url: str = None
    placeholder_version: Any = None
    placeholder: Any = None
    flags: int = None
    description: str = None

@dataclass
class EmbedVideo:
    url: str
    height: int
    width: int
    proxy_url: str = None
    placeholder_version: Any = None
    placeholder: Any = None
    flags: int = None
    description: str = None

@dataclass
class EmbedProvider:
    name: str
    url: str = None

@dataclass
class EmbedAuthor:
    name: str
    icon_url: str = None
    proxy_icon_url: str = None
    url: str = None

@dataclass
class EmbedField:
    name: str
    value: str
    inline: bool

@dataclass
class Embed:
    __client: "Client"
    type: str
    title: str = None
    description: str = None
    url: str = None
    timestamp: datetime = None
    color: int = None
    footer: EmbedFooter = None
    image: EmbedImage = None
    thumbnail: EmbedThumbnail = None
    video: EmbedVideo = None
    provider: EmbedProvider = None
    author: EmbedAuthor = None
    fields: Sequence[EmbedField] = None
    reference_id: str = None
    placeholder_version: Any = None

    @classmethod
    async def from_raw(cls, client, embed):
        if "timestamp" in embed:
            embed["timestamp"] = parse_time(embed["timestamp"])
        if "footer" in embed:
            embed["footer"] = EmbedFooter(**embed["footer"])
        if "image" in embed:
            embed["image"] = EmbedImage(**embed["image"])
        if "thumbnail" in embed:
            embed["thumbnail"] = EmbedThumbnail(**embed["thumbnail"])
        if "video" in embed:
            embed["video"] = EmbedVideo(**embed["video"])
        if "provider" in embed:
            embed["provider"] = EmbedProvider(**embed["provider"])
        if "author" in embed:
            embed["author"] = EmbedAuthor(**embed["author"])
        if "fields" in embed:
            embed["fields"] = [EmbedField(**field) for field in embed["fields"]]

        return cls(client, **embed)