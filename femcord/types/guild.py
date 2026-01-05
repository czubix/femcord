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

from ..http import Route
from ..enums import VerificationLevel, DefaultMessageNotification, ExplicitContentFilter, NSFWLevel, MfaLevel, AuditLogEvents
from ..utils import get_index, parse_time, time_from_snowflake
from ..errors import InvalidArgument

from .channel import Channel
from .user import User
from .role import Role
from .emoji import Emoji
from .sticker import Sticker
from .member import Member

from datetime import datetime

from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import Client

CDN_URL = "https://cdn.discordapp.com"
EXTENSIONS = ("png", "jpg", "jpeg", "webp", "gif")

@dataclass
class WelcomeScreenChannel:
    __client: "Client"
    channel: Channel
    description: str
    emoji_id: str
    emoji_name: str

    @classmethod
    async def from_raw(cls, client, channels: list[Channel], channel: dict):
        channel["channel"] = [_channel := [_channel for _channel in channels if _channel.id == channel["channel_id"]], _channel if len(_channel) >= 1 else None][1]
        return cls(client, **channel)

@dataclass
class WelcomeScreen:
    __client: "Client"
    description: str
    welcome_channels: list[WelcomeScreenChannel]

    @classmethod
    async def from_raw(cls, client, channels: list[Channel], welcomescreen: dict):
        welcomescreen["welcome_channels"] = [await WelcomeScreenChannel.from_raw(client, channels, channel) for channel in welcomescreen["welcome_channels"]]

        return cls(client, **welcomescreen)

@dataclass
class AuditLogChange:
    """Represents a change in an audit log entry."""
    __client: "Client"
    key: str
    new_value: Optional[Any] = None
    old_value: Optional[Any] = None

    @classmethod
    def from_raw(cls, client, change: dict) -> "AuditLogChange":
        change_data = change.copy()
        return cls(client, **change_data)

    @property
    def is_reset(self) -> bool:
        """Returns True if the property was reset or set to null."""
        return "new_value" not in self.__dict__ and "old_value" in self.__dict__

    @property
    def was_previously_null(self) -> bool:
        """Returns True if the property was previously null."""
        return "old_value" not in self.__dict__ and "new_value" in self.__dict__

    @property
    def is_role_change(self) -> bool:
        """Returns True if this is a partial role change ($add or $remove)."""
        return self.key in ("$add", "$remove")

    @property
    def is_command_permission_change(self) -> bool:
        """Returns True if this is a command permission change (snowflake as key)."""
        return self.key.isdigit() and len(self.key) >= 17  # Discord snowflake length

    def get_role_changes(self) -> list[dict] | None:
        """For partial role changes, returns the array of role objects."""
        if self.is_role_change and self.new_value:
            return self.new_value
        return None

    def get_command_permission_entity_id(self) -> str | None:
        """For command permission changes, returns the entity ID (role, channel, or user)."""
        if self.is_command_permission_change:
            return self.key
        return None

@dataclass
class AuditLogEntry:
    __client: "Client"
    id: str
    target_id: str
    changes: list[AuditLogChange]
    user_id: str
    action_type: AuditLogEvents
    options: Optional[dict] = None
    reason: Optional[str] = None

    @classmethod
    async def from_raw(cls, client, entry: dict) -> "AuditLogEntry":
        entry["action_type"] = AuditLogEvents(entry["action_type"])

        if "changes" in entry:
            entry["changes"] = [AuditLogChange.from_raw(client, change) for change in entry["changes"]]
        else:
            entry["changes"] = []

        if "options" not in entry:
            entry["options"] = None

        return cls(client, **entry)

    @property
    def application_id(self) -> str | None:
        """ID of the app whose permissions were targeted (APPLICATION_COMMAND_PERMISSION_UPDATE)"""
        return self.options.get("application_id") if self.options else None

    @property
    def auto_moderation_rule_name(self) -> str | None:
        """Name of the Auto Moderation rule that was triggered"""
        return self.options.get("auto_moderation_rule_name") if self.options else None

    @property
    def auto_moderation_rule_trigger_type(self) -> str | None:
        """Trigger type of the Auto Moderation rule that was triggered"""
        return self.options.get("auto_moderation_rule_trigger_type") if self.options else None

    @property
    def channel_id(self) -> str | None:
        """Channel in which the entities were targeted"""
        return self.options.get("channel_id") if self.options else None

    @property
    def count(self) -> str | None:
        """Number of entities that were targeted"""
        return self.options.get("count") if self.options else None

    @property
    def delete_member_days(self) -> str | None:
        """Number of days after which inactive members were kicked"""
        return self.options.get("delete_member_days") if self.options else None

    @property
    def option_id(self) -> str | None:
        """ID of the overwritten entity (using option_id to avoid conflict with class id)"""
        return self.options.get("id") if self.options else None

    @property
    def members_removed(self) -> str | None:
        """Number of members removed by the prune"""
        return self.options.get("members_removed") if self.options else None

    @property
    def message_id(self) -> str | None:
        """ID of the message that was targeted"""
        return self.options.get("message_id") if self.options else None

    @property
    def role_name(self) -> str | None:
        """Name of the role if type is "0" (not present if type is "1")"""
        return self.options.get("role_name") if self.options else None

    @property
    def overwrite_type(self) -> str | None:
        """Type of overwritten entity - role ("0") or member ("1")"""
        return self.options.get("type") if self.options else None

    @property
    def integration_type(self) -> str | None:
        """The type of integration which performed the action"""
        return self.options.get("integration_type") if self.options else None

    def get_change(self, key: str) -> AuditLogChange | None:
        """Get a specific change by its key."""
        for change in self.changes:
            if change.key == key:
                return change
        return None

    def get_changes_by_type(self, change_type: str) -> list[AuditLogChange]:
        """Get all changes of a specific type (e.g., '$add', '$remove')."""
        return [change for change in self.changes if change.key == change_type]

    def get_role_additions(self) -> list[dict]:
        """Get all role additions from partial role changes."""
        add_change = self.get_change("$add")
        role_changes = add_change.get_role_changes() if add_change else None
        return role_changes if role_changes is not None else []

    def get_role_removals(self) -> list[dict]:
        """Get all role removals from partial role changes."""
        remove_change = self.get_change("$remove")
        role_changes = remove_change.get_role_changes() if remove_change else None
        return role_changes if role_changes is not None else []

    def get_command_permission_changes(self) -> list[AuditLogChange]:
        """Get all command permission changes (where key is a snowflake)."""
        return [change for change in self.changes if change.is_command_permission_change]

    def has_field_change(self, field_name: str) -> bool:
        """Check if a specific field was changed."""
        return any(change.key == field_name for change in self.changes)

    def get_field_change_value(self, field_name: str, get_new: bool = True) -> Any | None:
        """Get the new or old value for a specific field change."""
        change = self.get_change(field_name)
        if change:
            return change.new_value if get_new else change.old_value
        return None

@dataclass
class Guild:
    __client: "Client"
    id: str
    name: str
    icon: str
    icon_url: str
    splash: str
    discovery_splash: str
    afk_timeout: int
    verification_level: VerificationLevel
    default_message_notifications: DefaultMessageNotification
    explicit_content_filter: ExplicitContentFilter
    roles: list[Role]
    features: list[str]
    mfa_level: MfaLevel
    joined_at: datetime
    large: bool
    member_count: int
    members: dict[str, Member]
    channels: list[Channel]
    threads: list[Channel]
    description: str
    banner: str
    banner_url: str
    premium_tier: int
    premium_subscription_count: int
    preferred_locale: str
    nsfw_level: NSFWLevel
    stickers: list[Sticker]
    premium_progress_bar_enabled: bool
    created_at: datetime
    owner: Optional[Member] = None
    afk_channel: Optional[Channel] = None
    system_channel: Optional[Channel] = None
    rules_channel: Optional[Channel] = None
    vanity_url: Optional[str] = None
    public_updates_channel: Optional[Channel] = None
    emojis: Optional[list[Emoji]] = None
    icon_hash: Optional[str] = None
    widget_enabled: Optional[bool] = None
    widget_channel: Optional[Channel] = None
    approximate_member_count: Optional[int] = None
    welcome_screen: Optional[WelcomeScreen] = None
    me: Optional[Member] = None

    __CHANGE_KEYS__ = (
        (
            "rules_channel_id",
            "rules_channel"
        ),
        (
            "system_channel_id",
            "system_channel"
        ),
        (
            "vanity_url_code",
            "vanity_url"
        ),
        (
            "public_updates_channel_id",
            "public_updates_channel"
        ),
        (
            "afk_channel_id",
            "afk_channel"
        ),
        (
            "owner_id",
            "owner"
        )
    )

    def __str__(self) -> str:
        return "<Guild id={!r} name={!r} owner={!r}>".format(self.id, self.name, self.owner)

    def __repr__(self) -> str:
        return "<Guild id={!r} name={!r} owner={!r}>".format(self.id, self.name, self.owner)

    @classmethod
    async def from_raw(cls, client, guild: dict) -> "Guild":
        icon_url = CDN_URL + "/icons/%s/%s.%s" % (guild["id"], guild["icon"], "gif" if guild["icon"] and guild["icon"][:2] == "a_" else "png")
        banner_url = CDN_URL + "/banners/%s/%s.%s" % (guild["id"], guild["banner"], "gif" if guild["banner"] and guild["banner"][:2] == "a_" else "png")

        if guild["icon"] is None:
            icon_url = CDN_URL + "/embed/avatars/%s.png" % (int(guild["id"]) % 6)

        if guild["banner"] is None:
            banner_url = None

        channels = [await Channel.from_raw(client, channel) for channel in guild["channels"]]

        guild["verification_level"] = VerificationLevel(guild["verification_level"])
        guild["default_message_notifications"] = DefaultMessageNotification(guild["default_message_notifications"])
        guild["explicit_content_filter"] = ExplicitContentFilter(guild["explicit_content_filter"])
        guild["roles"] = sorted([await Role.from_raw(client, role) for role in guild["roles"]], key=lambda role: role.position)
        guild["emojis"] = [await Emoji.from_raw(client, emoji) for emoji in guild["emojis"]]
        guild["mfa_level"] = MfaLevel(guild["mfa_level"])
        guild["joined_at"] = parse_time(guild["joined_at"])
        guild["channels"] = channels
        guild["threads"] = [await Channel.from_raw(client, thread) for thread in guild["threads"]]
        guild["nsfw_level"] = NSFWLevel(guild["nsfw_level"])
        guild["stickers"] = [await Sticker.from_raw(client, sticker) for sticker in guild["stickers"]]
        guild["created_at"] = time_from_snowflake(guild["id"])
        guild["icon_url"] = icon_url
        guild["banner_url"] = banner_url

        if "public_updates_channel" in guild:
            index = get_index(guild["channels"], guild["public_updates_channel"], key=lambda channel: channel.id)
            guild["public_updates_channel"] = guild["channels"][index] if index is not None else None
        if "afk_channel" in guild:
            index = get_index(guild["channels"], guild["afk_channel"], key=lambda channel: channel.id)
            guild["afk_channel"] = guild["channels"][index] if index is not None else None
        if "system_channel" in guild:
            index = get_index(guild["channels"], guild["system_channel"], key=lambda channel: channel.id)
            guild["system_channel"] = guild["channels"][index] if index is not None else None
        if "rules_channel" in guild:
            index = get_index(guild["channels"], guild["rules_channel"], key=lambda channel: channel.id)
            guild["rules_channel"] = guild["channels"][index] if index is not None else None
        if "widget_channel" in guild:
            index = get_index(guild["channels"], guild["widget_channel"], key=lambda channel: channel.id)
            guild["widget_channel"] = guild["channels"][index] if index is not None else None
        if "welcome_screen" in guild:
            guild["welcome_screen"] = await WelcomeScreen.from_raw(client, channels, guild["welcome_screen"])
        
        g = cls(client, **guild)
        g.members = {}

        for member in guild["members"]:
            if member["user"]["id"] == guild["owner"]:
                if member["user"]["id"] in client.gateway.users:
                    user = client.gateway.users[member["user"]["id"]]
                else:
                    user = await User.from_raw(client, member["user"])
                    client.gateway.users[user.id] = user
                owner = await Member.from_raw(client, g, member, user)
                g.owner = owner
                g.members[user.id] = owner
                break

        return g

    @property
    def default_role(self) -> Role:
        return [role for role in self.roles if role.id == self.id][0]

    def get_channel(self, channel_id_or_name: str) -> Channel | None:
        if not channel_id_or_name:
            return

        for channel in self.channels + self.threads:
            if channel.name.lower() == channel_id_or_name.lower() or channel.id == channel_id_or_name:
                return channel

    def get_role(self, role_id_or_name: str) -> Role | None:
        if not role_id_or_name:
            return

        for role in self.roles:
            if role.name.lower() == role_id_or_name.lower() or role.id == role_id_or_name:
                return role

    def get_emoji(self, emoji_name_or_id: str) -> Emoji | None:
        if not emoji_name_or_id:
            return

        if self.emojis is None:
            return

        for emoji in self.emojis:
            if emoji.name.lower() == emoji_name_or_id.lower() or emoji.id == emoji_name_or_id:
                return emoji

    def get_sticker(self, sticker_name_or_id: str) -> Sticker | None:
        if not sticker_name_or_id:
            return

        for sticker in self.stickers:
            if sticker.name.lower() == sticker_name_or_id.lower() or sticker.id == sticker_name_or_id:
                return sticker

    def icon_as(self, extension: str) -> str:
        if extension not in EXTENSIONS:
            raise InvalidArgument("Invalid extension")

        return CDN_URL + "/icons/%s/%s.%s" % (self.id, self.icon, extension)

    def banner_as(self, extension: str) -> str:
        if extension not in EXTENSIONS:
            raise InvalidArgument("Invalid extension")

        return CDN_URL + "/banners/%s/%s.%s" % (self.id, self.banner, extension)

    async def fetch_member(self, member_id: str) -> dict[str, str]:
        return await self.__client.http.request(Route("GET", "guilds", self.id, "members", member_id))

    async def get_member(self, member: dict | str, user: Optional[User | dict] = None) -> Member:
        if isinstance(member, str) and member in self.members:
            return self.members[member]

        for cached_member in self.members.values():
            if isinstance(member, str):
                if member.lower() in (cached_member.user.username.lower(), cached_member.user.id) + \
                                     ((cached_member.user.global_name.lower(),) if cached_member.user.global_name else ()) + \
                                     ((cached_member.nick.lower(),) if cached_member.nick else ()):
                    return cached_member
            elif isinstance(member, dict):
                if user is not None:
                    if isinstance(user, User):
                        if user.id == cached_member.user.id:
                            return cached_member
                    elif isinstance(user, dict):
                        if user["id"] == cached_member.user.id:
                            return cached_member
                elif "user" in member:
                    if member["user"]["id"] == cached_member.user.id:
                        return cached_member

        if isinstance(member, str):
            member = await self.fetch_member(member)

        if isinstance(user, dict):
            user = await self.__client.gateway.get_user(user)

        if not user and "user" in member:
            user = await self.__client.gateway.get_user(member["user"])

        member = await Member.from_raw(self.__client, self, member, user)
        self.members[member.user.id] = member

        return member

    async def ban(self, user: User, reason: Optional[str] = None, delete_message_seconds: Optional[int] = 0) -> dict | str:
        return await self.__client.http.ban_member(self.id, user.id, reason=reason, delete_message_seconds=delete_message_seconds)

    async def unban(self, member_id: str, reason: Optional[str] = None) -> dict | str:
        return await self.__client.http.unban_member(self.id, member_id, reason=reason)

    async def audit_log(self, limit: int = 100, before: Optional[str] = None, after: Optional[str] = None) -> list[AuditLogEntry]:
        response = await self.__client.http.audit_log(self.id, limit=limit, before=before, after=after)
        return [await AuditLogEntry.from_raw(self.__client, entry) for entry in response["audit_log_entries"]]