"""
Copyright 2022-2024 czubix

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

from ..utils import time_from_snowflake

from datetime import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client

@dataclass
class Emoji:
    __client: "Client"
    name: str
    id: str = None
    created_at: datetime = None
    animated: bool = None
    require_colons: bool = None
    managed: bool = None
    available: bool = None

    def __str__(self):
        return f"<{"a" if self.animated else ""}:{self.name}:{self.id}>"

    def __repr__(self):
        return "<Emoji id={!r} name={!r} animated={!r}>".format(self.id, self.name, self.animated)

    @property
    def url(self) -> str:
        extension = ".gif" if self.animated else ".png"
        return "https://cdn.discordapp.com/emojis/" + self.id + extension

    @classmethod
    async def from_raw(cls, client, emoji):
        if emoji.get("id", None) is not None:
            emoji["created_at"] = time_from_snowflake(emoji["id"])

        return cls(client, **emoji)