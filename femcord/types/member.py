"""
Copyright 2022-2026 czubix

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

from ..enums import StatusTypes
from ..utils import ID_PATTERN, parse_time
from ..permissions import Permissions

from .channel import Channel
from .presence import Presence, ClientStatus
from .voice import VoiceState

from datetime import datetime

from typing import Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client
    from ..commands import Context
    from .user import User
    from .role import Role

@dataclass
class Member:
    __client: "Client"
    user: "User"
    roles: Sequence["Role"]
    permissions: Permissions
    joined_at: datetime
    presence: Presence
    voice_state: VoiceState
    guild_id: str
    deaf: bool = None
    mute: bool = None
    nick: str = None
    avatar: str = None
    premium_since: datetime = None
    pending: bool = None
    is_pending: bool = None
    hoisted_role: "Role" = None
    communication_disabled_until: datetime = None

    def __str__(self):
        return "<Member user={!r} roles={!r} presence={!r}>".format(self.user, self.roles, self.presence)

    def __repr__(self):
        return "<Member user={!r} roles={!r} presence={!r}>".format(self.user, self.roles, self.presence)

    @classmethod
    async def from_raw(cls, client, guild, member, user):
        member["user"] = user
        member["guild_id"] = guild.id

        if member is not None:
            member["roles"] = [guild.roles[0]] + sorted((guild.get_role(role) for role in member["roles"]), key=lambda role: role.position if role else 0)
            member["permissions"] = Permissions(*set(permission for permissions in [role.permissions.permissions for role in member["roles"] if role] for permission in permissions))
            member["joined_at"] = parse_time(member["joined_at"])

            if "premium_since" in member:
                member["premium_since"] = parse_time(member["premium_since"])
            if "communication_disabled_until" in member:
                member["communication_disabled_until"] = parse_time(member["communication_disabled_until"])

            for role in member["roles"][::-1]:
                if role and role.hoist is True:
                    member["hoisted_role"] = role
                    break

        member["presence"] = Presence(client, StatusTypes.OFFLINE, [], ClientStatus(client))
        member["voice_state"] = VoiceState(client, *[None] * 7)

        return cls(client, **member)

    @staticmethod
    def from_arg(ctx: "Context", argument) -> "Member":
        result = ID_PATTERN.search(argument)

        if result is not None:
            argument = result.group()

        return ctx.guild.get_member(argument)

    async def kick(self, reason: Optional[str] = None) -> dict | str:
        return await self.__client.http.kick_member(self.guild_id, self.user.id, reason=reason)

    async def ban(self, reason: Optional[str] = None, delete_message_seconds: Optional[int] = 0) -> dict | str:
        return await self.__client.http.ban_member(self.guild_id, self.user.id, reason=reason, delete_message_seconds=delete_message_seconds)

    async def modify(self, *, nick: Optional[str] = None, roles: Optional[list["Role"]] = None, mute: Optional[bool] = None, deaf: Optional[bool] = None, channel: Optional[Channel] = None, communication_disabled_until: Optional[datetime] = None) -> dict | str:
        if roles:
            roles = [role.id for role in roles]
        if channel:
            channel = channel.id
        if communication_disabled_until:
            communication_disabled_until = communication_disabled_until.isoformat()

        return await self.__client.http.modify_member(self.guild_id, self.user.id, nick=nick, roles=roles, mute=mute, deaf=deaf, channel_id=channel, communication_disabled_until=communication_disabled_until)

    async def add_role(self, role: "Role") -> dict | str:
        return await self.__client.http.add_role(self.guild_id, self.user.id, role.id)

    async def remove_role(self, role: "Role") -> dict | str:
        return await self.__client.http.remove_role(self.guild_id, self.user.id, role.id)