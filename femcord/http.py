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

import asyncio

from aiohttp import ClientSession, FormData, ContentTypeError

from .embed import Embed
from .components import Components

from .enums import *
from .errors import *

import json, logging

from typing import Optional, List, Sequence, Union, Coroutine

class Route:
    def __init__(self, method: str, *endpoint: str) -> None:
        self.method = method
        self.endpoint = "/" + "/".join(endpoint)

    def __eq__(self, route) -> bool:
        return self.method == route.method and self.endpoint == route.endpoint

    def __ne__(self, route) -> bool:
        return self.method != route.method and self.endpoint != route.endpoint

class HTTP:
    URL = "https://discord.com/api/v10"
    CDN_URL = "https://cdn.discordapp.com"

    async def __new__(cls, *args) -> "HTTP":
        instance = super().__new__(cls)
        await instance.__init__(*args)
        return instance

    async def __init__(self, client) -> None:
        client.http = self
        self.loop = asyncio.get_event_loop()
        self.session: ClientSession = ClientSession(loop=self.loop)
        self.token: str = client.token
        self.bot: bool = client.bot

    async def request(self, route: Route, *, headers: Optional[dict] = {}, data: Optional[dict] = None, params: Optional[dict] = None, files: Optional[List[Union[str, bytes]]] = None) -> Union[dict, str]:
        headers.update({"authorization": ("Bot " if self.bot is True else "") + self.token, "user-agent": "femcord"})

        kwargs = dict(json=data)

        if params is not None:
            kwargs["params"] = params

        if files is not None:
            form = FormData()
            form.add_field("payload_json", json.dumps(data))

            for index, file in enumerate(files):
                form.add_field("file[%s]" % index, file[1], content_type="application/octet-stream", filename=file[0])

            kwargs = dict(data=form)

        async with self.session.request(route.method, HTTP.URL + route.endpoint, headers=headers, **kwargs) as response:
            logging.debug(f"{route.method} {route.endpoint}, data: {data}, params: {params}, files: {[file[0] for file in files] if files is not None else None}; status: {response.status}, text: {await response.text()}")

            try:
                response_data = await response.json()
            except ContentTypeError:
                response_data = await response.text()

            if 300 > response.status >= 200:
                return response_data

            if response.status in (400, 401, 403, 404, 405):
                message = response_data

                if isinstance(response_data, dict):
                    message = response_data["message"]

                raise HTTPException(message, response.status, response_data)

            elif response.status == 429:
                await asyncio.sleep(response_data["retry_after"])
                return await self.request(route, headers=headers, data=data, params=params, files=files)

    def start_typing(self, channel_id: str) -> Coroutine:
        return self.request(Route("POST", "channels", channel_id, "typing"))

    def send_message(self, channel_id: str, content: Optional[str] = None, *, embed: Optional[Embed] = None, embeds: Optional[Sequence[Embed]] = None, components: Optional[Components] = None, files: Optional[List[Union[str, bytes]]] = [], mentions: Optional[list] = [], stickers: Optional[list] = None, other: Optional[dict] = {}) -> Coroutine:
        data = {**other, "allowed_mentions": {"parse": mentions, "users": [], "replied_user": False}}

        if content is not None:
            data["content"] = str(content)

        if embed is not None and isinstance(embed, Embed):
            data["embeds"] = []

            if embed.__dict__:
                data["embeds"].append(embed.__dict__)

        if embeds is not None:
            data["embeds"] = []

            for embed in embeds:
                if embed.__dict__:
                    data["embeds"].append(embed.__dict__)

        if components is not None:
            data["components"] = getattr(components, "components", components)

        if stickers is not None:
            data["sticker_ids"] = [sticker.id for sticker in stickers]

        return self.request(Route("POST", "channels", channel_id, "messages"), data=data, files=files)

    def edit_message(self, channel_id: str, message_id: str, content: Optional[str] = None, *, embed: Optional[Embed] = None, embeds: Optional[Sequence[Embed]] = None, components: Optional[Components] = None, files: Optional[List[Union[str, bytes]]] = [], mentions: Optional[list] = [], stickers: Optional[list] = None, other: Optional[dict] = {}) -> Coroutine:
        data = {**other, "allowed_mentions": {"parse": mentions, "users": [], "replied_user": False}}

        if content is not None:
            data["content"] = str(content)

        if embed is not None and isinstance(embed, Embed):
            data["embeds"] = []

            if embed.__dict__:
                data["embeds"].append(embed.__dict__)

        if embeds is not None:
            data["embeds"] = []

            for embed in embeds:
                if embed.__dict__:
                    data["embeds"].append(embed.__dict__)

        if components is not None:
            data["components"] = getattr(components, "components", components)

        if stickers is not None:
            data["sticker_ids"] = [sticker.id for sticker in stickers]

        return self.request(Route("PATCH", "channels", channel_id, "messages", message_id), data=data, files=files)

    def delete_message(self, channel_id: str, message_id: str) -> Coroutine:
        return self.request(Route("DELETE", "channels", channel_id, "messages", message_id))

    def interaction_callback(self, interaction_id: str, interaction_token: str, interaction_type: InteractionCallbackTypes, content: Optional[str] = None, *, title: Optional[str] = None, custom_id: str = None, embed: Embed = None, embeds: Sequence[Embed] = None, components: Optional[Components] = None, files: Optional[List[Union[str, bytes]]] = [], mentions: Optional[list] = [], stickers: Optional[list] = None, other: Optional[dict] = {}) -> Coroutine:
        data = {"type": interaction_type.value, "data": {**other, "allowed_mentions": {"parse": mentions, "users": [], "replied_user": False}}}

        if content is not None:
            data["data"]["content"] = str(content)

        if title is not None:
            data["data"]["title"] = title

        if custom_id is not None:
            data["data"]["custom_id"] = custom_id

        if embed is not None and isinstance(embed, Embed):
            data["data"]["embeds"] = []

            if embed.__dict__:
                data["data"]["embeds"].append(embed.__dict__)

        if embeds is not None:
            data["data"]["embeds"] = []

            for embed in embeds:
                if embed.__dict__:
                    data["data"]["embeds"].append(embed.__dict__)

        if components is not None:
            data["data"]["components"] = getattr(components, "components", components)

        if stickers is not None:
            data["sticker_ids"] = [sticker.id for sticker in stickers]

        return self.request(Route("POST", "interactions", interaction_id, interaction_token, "callback"), data=data, files=files)

    def kick_member(self, guild_id: str, member_id: str, reason: Optional[str] = None) -> Coroutine:
        headers = {}

        if reason is not None:
            headers["X-Audit-Log-Reason"] = reason

        return self.request(Route("DELETE", "guilds", guild_id, "members", member_id), headers=headers)

    def ban_member(self, guild_id: str, member_id: str, reason: Optional[str] = None, delete_message_seconds: Optional[int] = 0) -> Coroutine:
        headers = {}

        if reason is not None:
            headers["X-Audit-Log-Reason"] = reason

        return self.request(Route("PUT", "guilds", guild_id, "bans", member_id), headers=headers, data={"delete_message_seconds": delete_message_seconds})

    def unban_member(self, guild_id: str, member_id: str, reason: Optional[str] = None) -> Coroutine:
        headers = {}

        if reason is not None:
            headers["X-Audit-Log-Reason"] = reason

        return self.request(Route("DELETE", "guilds", guild_id, "bans", member_id), headers=headers)

    def modify_member(self, guild_id: str, member_id: str, *, nick: Optional[str] = None, roles: Optional[List[str]] = None, mute: Optional[bool] = None, deaf: Optional[bool] = None, channel_id: Optional[str] = None, communication_disabled_until: Optional[int] = None) -> Coroutine:
        data = {"nick": nick}

        if roles:
            data["roles"] = roles
        if mute:
            data["mute"] = mute
        if deaf:
            data["deaf"] = deaf
        if channel_id:
            data["channel_id"] = channel_id
        if communication_disabled_until:
            data["communication_disabled_until"] = communication_disabled_until

        return self.request(Route("PATCH", "guilds", guild_id, "members", member_id), data=data)

    def add_role(self, guild_id: str, member_id: str, role_id: str) -> Coroutine:
        return self.request(Route("PUT", "guilds", guild_id, "members", member_id, "roles", role_id))

    def remove_role(self, guild_id: str, member_id: str, role_id: str) -> Coroutine:
        return self.request(Route("DELETE", "guilds", guild_id, "members", member_id, "roles", role_id))

    def get_messages(self, channel_id: str, *, around: Optional[str] = None, before: Optional[str] = None, after: Optional[str] = None, limit: Optional[str] = None) -> Coroutine:
        params = {}

        if around is not None:
            params["around"] = around
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit

        return self.request(Route("GET", "channels", channel_id, "messages"), params=params)

    def purge_channel(self, channel_id: str, messages: str) -> Coroutine:
        return self.request(Route("POST", "channels", channel_id, "messages", "bulk-delete"), data={"messages": messages})

    def open_dm(self, user_id: str) -> Coroutine:
        return self.request(Route("POST", "users", "@me", "channels"), data={"recipient_id": user_id})