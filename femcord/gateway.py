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

import asyncio

import sys
import base64
import traceback
import time
import copy

from .websocket import WebSocket
from .http import HTTP, Route, HTTPException
from .utils import get_index, get_mime, parse_time, MISSING

from .types import (
    Guild, Channel, Role,
    User, Member,
    Message, MessageComponents, Attachment, Embed,
    Interaction,
    Emoji, Sticker,
    Presence,
    VoiceState)
from .enums import (
    Opcodes, Intents as IntentsEnum,
    MfaLevel, ExplicitContentFilter, VerificationLevel, NSFWLevel,
    DefaultMessageNotification)

from types import CoroutineType

from typing import Callable, Optional, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client

class EventHandler:
    def __init__(self) -> None:
        self.gateway: Gateway = None
        self.handlers: dict[str, Callable[[dict], Optional[tuple]]] = {}

    async def __call__(self, name: str, *args) -> Callable[[str, ...], Awaitable[Optional[tuple]]]:
        handler = self.handlers.get(name)

        if not handler:
            return

        return handler(self.gateway, *args)

    def bind_gateway(self, gateway: "Gateway") -> None:
        self.gateway = gateway

    def event(self, callable: Callable) -> None:
        self.handlers[callable.__name__] = callable

        return callable

handler = EventHandler()

class Heartbeat:
    def __init__(self, gateway: "Gateway", heartbeat_interval: float) -> None:
        self.loop = asyncio.get_event_loop()
        self.gateway: Gateway = gateway
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_task: asyncio.Task = None
        self.time: float = None

    def send(self) -> Awaitable[None]:
        return self.gateway.ws.send(Opcodes.HEARTBEAT, self.gateway.sequence_number)

    async def heartbeat_loop(self) -> None:
        await self.send()

        while True:
            self.time = time.time()
            await asyncio.sleep(self.heartbeat_interval / 1000)
            await self.send()

    def start(self) -> None:
        self.heartbeat_task = self.loop.create_task(self.heartbeat_loop())

    def stop(self) -> None:
        self.heartbeat_task.cancel()

class Gateway:
    async def __new__(cls, *args) -> "Gateway":
        instance = super().__new__(cls)
        await instance.__init__(*args)
        return instance

    async def __init__(self, client: "Client") -> None:
        handler.bind_gateway(self)
        client.gateway = self
        self.loop = asyncio.get_event_loop()
        self.__client = client
        self.__http = client.http
        self.ws: "WebSocket" = MISSING
        self.ready = False
        self.heartbeat: Heartbeat = MISSING
        self.latency: int = MISSING
        self.last_latencies: list[int] = []
        self.last_latencies_limit = client.last_latencies_limit
        self.session_id: str = MISSING
        self.sequence_number: int = MISSING

        self.resuming: bool = False
        self.last_sequence_number: int = MISSING

        self.bot_user: User = MISSING
        self.emojis: list[Emoji] = MISSING

        self.guilds: list[Guild] = []
        self.unavailable_guilds: list[dict] = []
        self.users: dict[str, User] = {}

        self.messages_limit = client.messages_limit
        self.messages: list[Message] = []

        self.dispatched_ready = False
        self.presence: Optional[Presence] = None

        self.copied_objects: list[object] = []

        await WebSocket(self, client)

    async def dispatch(self, event: str, *args, **kwargs) -> None:
        for listener in self.__client.waiting_for:
            if listener[0] == event:
                try:
                    if listener[2](*args) is True:
                        listener[1].set_result(args)
                        return self.__client.waiting_for.remove(listener)
                except Exception:
                    pass

        for listener in self.__client.listeners:
            if listener.__name__ == "on_" + event:
                try:
                    self.loop.create_task(listener(*args, **kwargs))
                except Exception:
                    traceback.print_exc()

    def reset(self) -> None:
        self.guilds = []
        self.unavailable_guilds = []
        self.users = {}

    async def identify(self) -> None:
        self.reset()

        identify_data = {
            "token": self.__client.token,
            "properties": {
                "os": "Android" if self.__client.mobile else sys.platform,
                "browser": "Discord Android" if self.__client.mobile else "femcord"
            },
            "large_threshold": 250
        }

        if self.__client.bot is True:
            identify_data["intents"] = self.__client.intents.get_int()

        if self.presence is not None:
            identify_data["presence"] = self.presence.to_dict()

        await self.ws.send(Opcodes.IDENTIFY, identify_data)

    async def resume(self) -> None:
        await self.ws.send(Opcodes.RESUME, {
            "token": self.__client.token,
            "session_id": self.session_id,
            "seq": self.last_sequence_number
        })

        self.resuming = False
        self.last_sequence_number = None

    async def on_message(self, op: Opcodes, data: dict, sequence_number: int, event_name: str) -> None:
        self.sequence_number = sequence_number

        if op is Opcodes.HELLO:
            self.heartbeat = Heartbeat(self, data["heartbeat_interval"])
            self.heartbeat.start()

            if self.resuming is True:
                while (index := len(self.copied_objects)) > 0:
                    del self.copied_objects[index - 1]
                    index -= 1

                await self.dispatch("reconnect")
                return await self.resume()

            await self.identify()

        elif op is Opcodes.INVALID_SESSION:
            while (index := len(self.copied_objects)) > 0:
                del self.copied_objects[index - 1]
                index -= 1

            await asyncio.sleep(5)
            await self.identify()
            await asyncio.sleep(1)
            await self.dispatch("reconnect")

        elif op is Opcodes.HEARTBEAT_ACK:
            if len(self.last_latencies) > self.last_latencies_limit:
                self.last_latencies.pop(0)

            if self.latency is not MISSING:
                self.last_latencies.append(self.latency)

            self.latency = round((time.time() - self.heartbeat.time) * 1000)

        if event_name == "READY":
            self.session_id = data["session_id"]
            self.bot_user = await User.from_raw(self.__client, data["user"])
            self.emojis = await self.get_application_emojis() if self.__client.bot else []
            self.unavailable_guilds = data["guilds"]

            self.ready = True

            if self.__client.bot is False:
                self.unavailable_guilds = []
                self.guilds = [await Guild.from_raw(self.__client, guild) for guild in data["guilds"]]

                if not self.dispatched_ready:
                    self.dispatched_ready = True
                    await self.dispatch("ready")

        elif event_name == "RESUMED":
            self.ready = True

        elif isinstance(event_name, str) and isinstance(data, dict):
            if self.dispatched_ready:
                await self.dispatch("raw_" + event_name.lower(), copied_data := copy.copy(data))
                del copied_data

            if not self.dispatched_ready and event_name == "GUILD_CREATE":
                await self.guild_create(data)

                if len(self.unavailable_guilds) <= len(self.guilds):
                    self.dispatched_ready = True

                    return await self.dispatch("ready")

            if not self.dispatched_ready:
                return

            parsed_data = await handler(event_name.lower(), data)

            if isinstance(parsed_data, CoroutineType):
                parsed_data = await parsed_data
            else:
                parsed_data = data,

            if parsed_data is None:
                return

            if parsed_data == (None,):
                parsed_data = ()

            if self.dispatched_ready:
                await self.dispatch(event_name.lower(), *parsed_data)

    async def set_presence(self, presence: Presence) -> None:
        self.presence = presence
        if not self.ready:
            return
        await self.ws.send(Opcodes.PRESENCE_UPDATE, self.presence.to_dict())

    def get_guild(self, guild_id: str) -> Guild:
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild

    def get_channel(self, channel_id: str) -> Channel:
        for guild in self.guilds:
            for channel in guild.channels + guild.threads:
                if channel.id == channel_id:
                    return channel

    def get_guild_by_channel_id(self, channel_id: str) -> Guild:
        for guild in self.guilds:
            for channel in guild.channels:
                if channel.id == channel_id:
                    return guild

    def cache_message(self, message: Message) -> None:
        self.messages.append(message)

        if len(self.messages) > self.messages_limit:
            del self.messages[0]

    def get_emoji(self, *, emoji_id: str = None, name: str = None) -> Emoji:
        if emoji_id is not None:
            kwargs = dict(value=emoji_id, key=lambda e: e.id)
        if name is not None:
            kwargs = dict(value=name, key=lambda e: e.name)

        index = get_index(self.emojis, **kwargs)

        if index is None:
            raise Exception("Emoji not found")

        return self.emojis[index]

    async def get_application_emojis(self) -> list[Emoji]:
        return [await Emoji.from_raw(self.__client, emoji) for emoji in (await self.__http.get_application_emojis(self.bot_user.id))["items"]]

    async def create_application_emoji(self, name: str, image: bytes) -> Emoji:
        image = f"data:{get_mime(image)};base64," + base64.b64encode(image).decode()
        emoji = await Emoji.from_raw(self.__client, await self.__http.create_application_emoji(name, image))
        self.emojis.append(emoji)
        return emoji

    async def edit_application_emoji(self, emoji_id: str, *, name: Optional[str] = None, image: Optional[bytes] = None) -> Emoji:
        if image is not None:
            image = f"data:{get_mime(image)};base64," + base64.b64encode(image).decode()

        index = get_index(self.emojis, emoji_id, key=lambda e: e.id)

        if index is None:
            raise Exception("Emoji not found")

        del self.emojis[index]

        emoji = await Emoji.from_raw(self.__client, await self.__http.edit_application_emoji(self.bot_user.id, emoji_id, name=name, image=image))

        self.emojis.insert(index, emoji)

        return emoji

    async def delete_application_emoji(self, emoji_id: str) -> None:
        index = get_index(self.emojis, emoji_id, key=lambda e: e.id)

        if index is None:
            raise Exception("Emoji not found")

        await self.__http.delete_application_emoji(emoji_id)

        del self.emojis[index]

    async def fetch_user(self, user_id: str) -> dict | str:
        return await self.__http.request(Route("GET", "users", user_id))

    async def get_user(self, user: dict | str) -> User:
        for cached_user in self.users.values():
            if isinstance(user, str):
                if user.lower() in (cached_user.username.lower(), (cached_user.global_name or "").lower(), cached_user.id):
                    return cached_user
            elif isinstance(user, dict):
                if user["id"] == cached_user.id:
                    return cached_user

        if isinstance(user, str):
            user = await self.fetch_user(user)

        user = await User.from_raw(self.__client, user)
        self.users[user.id] = user

        return user

    def copy[T](self, _object: T, deep: bool = False) -> T:
        if deep is True:
            copied_object = copy.deepcopy(_object)
        elif deep is False:
            copied_object = copy.copy(_object)

        self.copied_objects.append(copied_object)

        return copied_object

    @handler.event
    async def channel_create(self, channel):
        if "guild_id" not in channel:
            return

        guild = self.get_guild(channel["guild_id"])
        channel = await Channel.from_raw(self.__client, channel)

        guild.channels.append(channel)

        return channel,

    @handler.event
    async def channel_update(self, channel):
        if "guild_id" not in channel:
            return

        guild = self.get_guild(channel["guild_id"])
        channel = await Channel.from_raw(self.__client, channel)

        index = get_index(guild.channels, channel.id, key=lambda c: c.id)

        old_channel = self.copy(guild.channels[index])
        guild.channels[index] = channel

        return old_channel, channel

    @handler.event
    async def channel_delete(self, channel):
        if "guild_id" not in channel:
            return

        guild = self.get_guild(channel["guild_id"])

        index = get_index(guild.channels, channel["id"], key=lambda c: c.id)

        channel = guild.channels[index]
        del guild.channels[index]

        return channel,

    @handler.event
    async def thread_create(self, thread):
        guild = self.get_guild(thread["guild_id"])
        thread = await Channel.from_raw(self.__client, thread)

        guild.threads.append(thread)

        return thread,

    @handler.event
    async def thread_update(self, thread):
        guild = self.get_guild(thread["guild_id"])
        thread = await Channel.from_raw(self.__client, thread)

        index = get_index(guild.threads, thread.id, key=lambda t: t.id)

        if index is None:
            return

        old_thread = self.copy(guild.threads[index])
        guild.threads[index] = thread

        return old_thread, thread

    @handler.event
    async def thread_delete(self, thread):
        guild = self.get_guild(thread["guild_id"])

        index = get_index(guild.threads, thread["id"], key=lambda t: t.id)

        thread = guild.threads[index]
        del guild.threads[index]

        return thread,

    async def add_members(self, guild: Guild, members: list[dict], presences: list[dict]) -> None:
        for member in members:
            if member["user"]["id"] in self.users:
                user = self.users[member["user"]["id"]]
            else:
                user = await User.from_raw(self.__client, member["user"])
                self.users[user.id] = user

            await asyncio.sleep(0)

            member = await Member.from_raw(self.__client, guild, member, user)

            if member.user.id == guild.owner:
                guild.owner = member
            elif member.user.id == self.bot_user.id:
                guild.me = member

            guild.members.append(member)

            if presences:
                for presence in presences:
                    if "user" in presence and presence["user"]["id"] == member.user.id:
                        member.presence = await Presence.from_raw(self.__client, presence)
                    await asyncio.sleep(0)

    @handler.event
    async def guild_create(self, guild):
        members = guild["members"]
        presences = guild["presences"]

        guild = await Guild.from_raw(self.__client, guild)
        self.guilds.append(guild)

        if guild.member_count != len(members):
            await self.ws.send(Opcodes.REQUEST_GUILD_MEMBERS, {"guild_id": guild.id, "query": "", "limit": 0, "presences": self.__client.intents.has(IntentsEnum.GUILD_PRESENCES)})
        else:
            self.loop.create_task(self.add_members(guild, members, presences))

        return guild,

    @handler.event
    async def guild_members_chunk(self, chunk):
        self.loop.create_task(self.add_members(self.get_guild(chunk["guild_id"]), chunk["members"], chunk["presences"]))

        return chunk,

    @handler.event
    async def presence_update(self, presence):
        guild = self.get_guild(presence["guild_id"])

        if not guild:
            return

        index = get_index(guild.members, presence["user"]["id"], key=lambda m: m.user.id)

        if not index:
            return

        member = guild.members[index]

        member.presence = await Presence.from_raw(self.__client, presence)

        return member,

    @handler.event
    async def guild_update(self, guild):
        index = get_index(self.guilds, guild["id"], key=lambda g: g.id)

        old_guild = self.copy(self.guilds[index])

        guild_object = self.guilds[index]

        guild_object.premium_tier = guild["premium_tier"]
        guild_object.discovery_splash = guild["discovery_splash"]
        guild_object.owner = await guild_object.get_member(guild["owner_id"])
        guild_object.banner = guild["banner"]
        guild_object.features = guild["features"]
        guild_object.premium_progress_bar_enabled = guild["premium_progress_bar_enabled"]
        guild_object.nsfw_level = NSFWLevel(guild["nsfw_level"])
        guild_object.verification_level = VerificationLevel(guild["verification_level"])
        guild_object.splash = guild["splash"]
        guild_object.afk_timeout = guild["afk_timeout"]
        guild_object.icon = guild["icon"]
        guild_object.preferred_locale = guild["preferred_locale"]
        guild_object.explicit_content_filter = ExplicitContentFilter(guild["explicit_content_filter"])
        guild_object.default_message_notifications = DefaultMessageNotification(guild["default_message_notifications"])
        guild_object.name = guild["name"]
        guild_object.widget_enabled = guild["widget_enabled"]
        guild_object.description = guild["description"]
        guild_object.premium_subscription_count = guild["premium_subscription_count"]
        guild_object.mfa_level = MfaLevel(guild["mfa_level"])

        if guild["public_updates_channel_id"] is not None:
            guild_object.public_updates_channel = guild_object.get_channel(guild["public_updates_channel_id"])

        if guild["rules_channel_id"] is not None:
            guild_object.rules_channel = guild_object.get_channel(guild["rules_channel_id"])

        if guild["afk_channel_id"] is not None:
            guild_object.afk_channel = guild_object.get_channel(guild["afk_channel_id"])

        if "vanity_url" in guild and guild["vanity_url"] is not None:
            guild_object.vanity_url = guild["vanity_url"]

        if guild["icon"] is None:
            icon_url = HTTP.CDN_URL + "/embed/avatars/%s.png" % (int(guild["id"]) % 5)
        else:
            icon_format = "gif" if guild["icon"][0:2] == "a_" else "png"
            icon_url = HTTP.CDN_URL + "/icons/%s/%s.%s" % (guild["id"], guild["icon"], icon_format)

        guild_object.icon_url = icon_url

        return old_guild, guild_object

    @handler.event
    async def guild_delete(self, guild):
        guild = self.get_guild(guild["id"])

        if guild is None:
            return

        index = get_index(self.guilds, guild.id, key=lambda g: g.id)
        del self.guilds[index]

        return guild,

    @handler.event
    async def guild_ban_add(self, ban):
        guild = self.get_guild(ban["guild_id"])
        user = await self.get_user(ban["user"])

        return guild, user

    @handler.event
    async def guild_ban_remove(self, ban):
        guild = self.get_guild(ban["guild_id"])
        user = await self.get_user(ban["user"])

        return guild, user

    @handler.event
    async def guild_emojis_update(self, emojis):
        guild = self.get_guild(emojis["guild_id"])

        old_emojis = self.copy(guild.emojis)
        guild.emojis = [await Emoji.from_raw(self.__client, emoji) for emoji in emojis["emojis"]]

        return old_emojis, guild.emojis

    @handler.event
    async def guild_stickers_update(self, stickers):
        guild = self.get_guild(stickers["guild_id"])

        old_stickers = self.copy(guild.stickers)
        guild.stickers = [await Sticker.from_raw(self.__client, sticker) for sticker in stickers["stickers"]]

        return old_stickers, guild.stickers

    @handler.event
    async def guild_member_add(self, member):
        guild = self.get_guild(member["guild_id"])
        del member["guild_id"]

        member = await guild.get_member(member)

        return guild, member

    @handler.event
    async def guild_member_update(self, member):
        if not self.guilds:
            return

        guild = self.get_guild(member["guild_id"])

        if guild is None:
            return None, None, member

        try:
            old_member = self.copy(await guild.get_member(member["user"]["id"]))
        except HTTPException:
            return

        del member["guild_id"]

        user = await User.from_raw(self.__client, member["user"])
        del member["user"]

        self.users[user.id] = user

        member = await Member.from_raw(self.__client, guild, member, user)
        member_index = get_index(guild.members, member.user.id, key=lambda m: m.user.id)

        if member_index is None:
            guild.members.append(member)
        else:
            guild.members[member_index] = member

        return guild, old_member, member

    @handler.event
    async def guild_member_remove(self, user):
        guild = self.get_guild(user["guild_id"])

        if not guild:
            return

        user = await self.get_user(user["user"])

        index = get_index(guild.members, user.id, key=lambda m: m.user.id)

        if index is not None:
            del guild.members[index]

        return guild, user

    @handler.event
    async def guild_role_create(self, role):
        guild = self.get_guild(role["guild_id"])

        role = await Role.from_raw(self.__client, role["role"])
        guild.roles.append(role)

        return guild, role

    @handler.event
    async def guild_role_update(self, role):
        guild = self.get_guild(role["guild_id"])
        role = await Role.from_raw(self.__client, role["role"])

        index = get_index(guild.roles, role.id, key=lambda r: r.id)

        old_role = self.copy(guild.roles[index])
        guild.roles[index] = role

        return guild, old_role, role

    @handler.event
    async def guild_role_delete(self, role):
        guild = self.get_guild(role["guild_id"])

        role = guild.get_role(role["role_id"])

        if not role:
            return

        index = get_index(guild.roles, role.id, key=lambda r: r.id)
        del guild.roles[index]

        return guild, role

    @handler.event
    async def interaction_create(self, interaction):
        return await Interaction.from_raw(self.__client, interaction),

    @handler.event
    async def message_create(self, message):
        message = await Message.from_raw(self.__client, message)

        self.cache_message(message)

        return message,

    @handler.event
    async def message_update(self, message):
        index = get_index(self.messages, message["id"], key=lambda m: m.id)

        if index is None:
            return None, None

        old_message = self.messages[index]
        new_message = self.copy(old_message)

        if "content" in message:
            new_message.content = message["content"]
        if "edited_timestamp" in message:
            new_message.edited_timestamp = parse_time(message["edited_timestamp"])
        if "attachments" in message:
            new_message.attachments = [Attachment(**attachment) for attachment in message["attachments"]]
        if "embeds" in message:
            new_message.embeds = [await Embed.from_raw(self.__client, embed) for embed in message["embeds"]]
        if "components" in message:
            new_message.components = [await MessageComponents.from_raw(self.__client, component) for component in message["components"]]

        self.messages[index] = new_message

        return old_message, new_message

    @handler.event
    async def message_delete(self, message):
        index = get_index(self.messages, message["id"], key=lambda m: m.id)

        if index is None:
            return message["id"],

        message = self.messages[index]
        del self.messages[index]

        return message,

    @handler.event
    async def message_delete_bulk(self, message):
        messages = []

        for message_id in message["ids"]:
            index = get_index(self.messages, message_id, key=lambda m: m.id)

            if index is None:
                messages.append(message_id)
            else:
                messages.append(self.messages[index])

        return messages,

    @handler.event
    async def message_reaction_add(self, reaction):
        guild = self.get_guild(reaction["guild_id"])
        channel = guild.get_channel(reaction["channel_id"])
        user = await self.get_user(reaction["user_id"])

        if user is None:
            return

        emoji = await Emoji.from_raw(self.__client, reaction["emoji"])

        index = get_index(self.messages, reaction["message_id"], key=lambda m: m.id)

        if index is None:
            message = reaction["message_id"]
        else:
            message = self.messages[index]

        if "member" in reaction:
            member = await guild.get_member(reaction["member"])

            return guild, channel, member, message, emoji

        return guild, channel, user, message, emoji

    @handler.event
    async def message_reaction_remove(self, reaction):
        guild = self.get_guild(reaction["guild_id"])
        channel = guild.get_channel(reaction["channel_id"])
        user = await self.get_user(reaction["user_id"])

        if user is None:
            return

        emoji = await Emoji.from_raw(self.__client, reaction["emoji"])

        index = get_index(self.messages, reaction["message_id"], key=lambda m: m.id)

        if index is None:
            message = reaction["message_id"]
        else:
            message = self.messages[index]

        if "member" in reaction:
            member = await guild.get_member(reaction["member"])

            return guild, channel, member, message, emoji

        return guild, channel, user, message, emoji

    @handler.event
    async def message_reaction_remove_all(self, reaction):
        guild = self.get_guild(reaction["guild_id"])
        channel = guild.get_channel(reaction["channel_id"])

        index = get_index(self.messages, reaction["message_id"], key=lambda m: m.id)

        if index is None:
            message = reaction["message_id"]
        else:
            message = self.messages[index]

        return guild, channel, message

    @handler.event
    async def message_reaction_remove_emoji(self, reaction):
        guild = self.get_guild(reaction["guild_id"])
        channel = guild.get_channel(reaction["channel_id"])
        emoji = await Emoji.from_raw(self.__client, reaction["emoji"])

        index = get_index(self.messages, reaction["message_id"], key=lambda m: m.id)

        if index is None:
            message = reaction["message_id"]
        else:
            message = self.messages[index]

        return guild, channel, message, emoji

    @handler.event
    async def voice_state_update(self, voice_state):
        guild = None
        channel = None
        member = None

        if voice_state["channel_id"] is not None:
            guild = self.get_guild_by_channel_id(voice_state["channel_id"])
            channel = guild.get_channel(voice_state["channel_id"])

        if voice_state["guild_id"] is not None:
            guild = self.get_guild(voice_state["guild_id"])

        member = await guild.get_member(voice_state["user_id"])

        old_voice_state = self.copy(member.voice_state)

        _voice_state = await VoiceState.from_raw(self.__client, voice_state)
        _voice_state.guild = guild
        _voice_state.channel = channel
        member.voice_state = _voice_state

        return member, old_voice_state, _voice_state