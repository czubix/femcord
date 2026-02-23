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

from ..enums import CommandOptionTypes, ApplicationCommandTypes, ComponentTypes, InteractionTypes, ChannelTypes, InteractionCallbackTypes, MessageFlags, InteractionContextTypes
from ..utils import get_index
from ..permissions import Permissions

from .channel import Channel
from .entitlement import Entitlement
from .role import Role

from typing import Generic, Literal, Optional, Sequence, TypeVar, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client
    from ..embed import Embed
    from ..components import Components
    from .guild import Guild
    from .role import Role
    from .message import Message, MessageComponents
    from .member import Member
    from .user import User

# InteractionData = TypeVar("InteractionData", bound=Union["None", "PingInteraction", "ApplicationCommandData", "MessageComponentData", "ModalSubmitData"])
# T = TypeVar("T", bound="InteractionTypes")

@dataclass
class InteractionDataOption:
    __client: "Client" # type: ignore
    name: str
    type: CommandOptionTypes
    value: Optional["User | Channel | Role | str | float | int | bool"] = None
    options: Optional[Sequence["InteractionDataOption"]] = None
    focused: Optional[bool] = None

    @classmethod
    async def from_raw(cls, client: "Client", guild: "Guild | None", dataoption: dict, resolved: dict | None):
        dataoption["type"] = CommandOptionTypes(dataoption["type"])

        match dataoption["type"]:
            case CommandOptionTypes.USER:
                dataoption["value"] = await client.gateway.get_user(dataoption["value"])
            case CommandOptionTypes.CHANNEL:
                if guild is not None:
                    dataoption["value"] = guild.get_channel(dataoption["value"])
                elif resolved is None:
                    dataoption["value"] = Channel(client, dataoption["value"], ChannelTypes.NONE)
                else:
                    resolved_channel = resolved["channels"][dataoption["value"]]
                    dataoption["value"] = await Channel.from_raw(client, resolved_channel)

            case CommandOptionTypes.ROLE:
                if guild is not None:
                    dataoption["value"] = guild.get_role(dataoption["value"])
                elif resolved is not None:
                    resolved_role = resolved["roles"][dataoption["value"]]
                    dataoption["value"] = await Role.from_raw(client, resolved_role)

        if "options" in dataoption:
            dataoption["options"] = [await cls.from_raw(client, guild, dataoption, resolved) for dataoption in dataoption["options"]]

        return cls(client, **dataoption)

@dataclass
class InteractionData:
    __client: "Client" # type: ignore
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[ApplicationCommandTypes] = None
    options: Optional[Sequence[InteractionDataOption]] = None
    custom_id: Optional[str] = None
    component_type: Optional[ComponentTypes] = None
    values: Optional[list] = None
    target: Optional["User | Message"] = None
    components: Optional[Sequence["MessageComponents"]] = None
    resolved: Optional[dict] = None

    __CHANGE_KEYS__ = (
        (
            "target_id",
            "target"
        ),
    )

    @classmethod
    async def from_raw(cls, client: "Client", ids: tuple[str | None, str | None], data: dict):
        guild_id, channel_id = ids

        if "type" in data:
            data["type"] = ApplicationCommandTypes(data["type"])
        if "options" in data:
            guild = client.gateway.get_guild(guild_id) if guild_id else None
            data["options"] = [await InteractionDataOption.from_raw(client, guild, dataoption, data.get("resolved")) for dataoption in data["options"]]
        if "component_type" in data:
            data["component_type"] = ComponentTypes(data["component_type"])
        if "target" in data:
            if data["type"] == ApplicationCommandTypes.USER:
                data["target"] = await client.gateway.get_user(data["resolved"]["users"][data["target"]])
            elif data["type"] == ApplicationCommandTypes.MESSAGE:
                data["target"] = await Message.from_raw(client, data["resolved"]["messages"][data["target"]])
        if "components" in data:
            data["components"] = [await MessageComponents.from_raw(client, component) for component in data["components"]]

        return cls(client, **data)

# @dataclass
# class ApplicationCommandData:
#     __client: "Client" # type: ignore
#     id: str
#     name: str
#     type: ApplicationCommandTypes
#     resolved: Optional[dict] = None
#     options: Optional[Sequence[InteractionDataOption]] = None
#     target: Optional["User | Message"] = None

#     __CHANGE_KEYS__ = (
#         (
#             "target_id",
#             "target"
#         ),
#     )

#     @classmethod
#     async def from_raw(cls, client: "Client", ids: tuple[str | None, str | None], data: dict) -> "ApplicationCommandData":
#         guild_id, channel_id = ids

#         data["type"] = ApplicationCommandTypes(data["type"])

#         if "options" in data:
#             guild = client.gateway.get_guild(guild_id) if guild_id else None
#             data["options"] = [await InteractionDataOption.from_raw(client, guild, dataoption, data.get("resolved")) for dataoption in data["options"]]
#         if "guild" in data:
#             data["guild"] = client.gateway.get_guild(data["guild"])
#         if "target" in data:
#             if data["type"] == ApplicationCommandTypes.USER:
#                 data["target"] = await client.gateway.get_user(data["resolved"]["users"][data["target"]])
#             elif data["type"] == ApplicationCommandTypes.MESSAGE:
#                 data["target"] = await Message.from_raw(client, data["resolved"]["messages"][data["target"]])

#         return cls(client, **data)

# @dataclass
# class MessageComponentData:
#     __client: "Client" # type: ignore
#     custom_id: str
#     component_type: ComponentTypes
#     values: Optional[list] = None
#     resolved: Optional[dict] = None

#     @classmethod
#     async def from_raw(cls, client: "Client", data: dict) -> "MessageComponentData":
#         data["component_type"] = ComponentTypes(data["component_type"])
#         return cls(client, **data)

# @dataclass
# class ModalSubmitData:
#     __client: "Client" # type: ignore
#     custom_id: str
#     components: Sequence["MessageComponents"]
#     resolved: Optional[dict] = None

#     @classmethod
#     async def from_raw(cls, client: "Client", data: dict) -> "ModalSubmitData":
#         data["components"] = [await MessageComponents.from_raw(client, component) for component in data["components"]]
#         return cls(client, **data)

@dataclass
class Interaction:
    __client: "Client" # type: ignore
    id: str
    application_id: str
    type: InteractionTypes
    token: str
    version: int
    entitlements: Sequence[Entitlement]
    authorizing_integration_owners: dict[str, str]
    attachment_size_limit: int
    data: InteractionData = None # type: ignore
    guild: Optional["Guild"] = None
    channel: Optional[Channel] = None
    member: Optional["Member"] = None
    name: Optional[str] = None
    user: Optional["User"] = None
    message: Optional["Message"] = None
    app_permissions: Optional[Permissions] = None
    locale: Optional[str] = None
    guild_locale: Optional[str] = None
    context: Optional[InteractionContextTypes] = None

    __CHANGE_KEYS__ = (
        (
            "channel_id",
            "channel"
        ),
        (
            "guild_id",
            "guild"
        )
    )

    def __str__(self):
        return "<Interaction id={!r} type={!r}>".format(self.id, self.type)

    def __repr__(self):
        return "<Interaction id={!r} type={!r}>".format(self.id, self.type)

    @classmethod
    async def from_raw(cls, client: "Client", interaction: dict):
        if "type" in interaction:
            interaction["type"] = InteractionTypes(interaction["type"])
        if "data" in interaction:
            interaction["data"] = await InteractionData.from_raw(client, (interaction.get("guild_id"), interaction.get("channel_id")), interaction["data"])
            # match interaction["type"]:
            #     case InteractionTypes.APPLICATION_COMMAND:
            #         interaction["data"] = await ApplicationCommandData.from_raw(client, (interaction.get("guild_id"), interaction.get("channel_id")), interaction["data"])
            #     case InteractionTypes.MESSAGE_COMPONENT:
            #         interaction["data"] = await MessageComponentData.from_raw(client, interaction["data"])
            #     case InteractionTypes.MODAL_SUBMIT:
            #         interaction["data"] = await ModalSubmitData.from_raw(client, interaction["data"])
        if "guild" in interaction:
            interaction["guild"] = client.gateway.get_guild(interaction["guild"])
            if interaction["guild"]:
                if "channel" in interaction:
                    interaction["channel"] = interaction["guild"].get_channel(interaction["channel"])
                if "member" in interaction:
                    interaction["user"] = interaction["member"]["user"]
                    interaction["member"] = await interaction["guild"].get_member(interaction["member"])
            else:
                if "member" in interaction:
                    interaction["user"] = interaction["member"]["user"]
        if "user" in interaction:
            interaction["user"] = await client.gateway.get_user(interaction["user"])
        if "message" in interaction:
            index = get_index(client.gateway.messages, interaction["message"]["id"], key=lambda m: m.id)

            if index is None:
                interaction["message"] = await Message.from_raw(client, interaction["message"])
                client.gateway.cache_message(interaction["message"])
            else:
                interaction["message"] = client.gateway.messages[index]
        if "channel" in interaction and isinstance(interaction["channel"], str):
            interaction["channel"] = Channel(client, interaction["channel"], ChannelTypes.DM)
        if "app_permissions" in interaction:
            interaction["app_permissions"] = Permissions.from_int(int(interaction["app_permissions"]))
        if "locale" in interaction:
            interaction["locale"] = interaction["locale"]
        if "guild_locale" in interaction:
            interaction["guild_locale"] = interaction["guild_locale"]
        if "entitlements" in interaction:
            interaction["entitlements"] = [Entitlement.from_raw(client, entitlement) for entitlement in interaction["entitlements"]]

        return cls(client, **interaction)

    async def callback(
            self,
            interaction_type: InteractionCallbackTypes,
            content: Optional[str] = None,
            *,
            title: Optional[str] = None,
            custom_id: Optional[str] = None,
            embed: Optional["Embed"] = None,
            embeds: Optional[Sequence["Embed"]] = None,
            components: Optional["Components"] = None,
            files: Optional[list[tuple[str, str | bytes]]] = None,
            mentions: Optional[list] = [],
            flags: Optional[list[MessageFlags]] = None,
            other: Optional[dict] = None
    ) -> dict:
        return await self.__client.http.interaction_callback(self.id, self.token, interaction_type, content, title=title, custom_id=custom_id, embed=embed, embeds=embeds, components=components, files=files, mentions=mentions, flags=flags, other=other)

    async def edit(
            self,
            content: Optional[str] = None,
            *,
            title: Optional[str] = None,
            custom_id: Optional[str] = None,
            embed: Optional["Embed"] = None,
            embeds: Optional[Sequence["Embed"]] = None,
            components: Optional["Components"] = None,
            files: Optional[list[tuple[str, str | bytes]]] = None,
            mentions: Optional[list] = [],
            flags: Optional[list[MessageFlags]] = None,
            other: Optional[dict] = None
        ) -> None:
        await self.__client.http.interaction_edit(self.__client.gateway.bot_user.id, self.token, content, title=title, custom_id=custom_id, embed=embed, embeds=embeds, components=components, files=files, mentions=mentions, flags=flags, other=other)

    async def send(
            self,
            content: Optional[str] = None,
            *,
            title: Optional[str] = None,
            custom_id: Optional[str] = None,
            embed: Optional["Embed"] = None,
            embeds: Optional[Sequence["Embed"]] = None,
            components: Optional["Components"] = None,
            files: Optional[list[tuple[str, str | bytes]]] = None,
            mentions: Optional[list] = [],
            flags: Optional[list[MessageFlags]] = None,
            other: Optional[dict] = None
    ) -> dict:
        return await self.__client.http.send_followup(self.__client.gateway.bot_user.id, self.token, content, title=title, custom_id=custom_id, embed=embed, embeds=embeds, components=components, files=files, mentions=mentions, flags=flags, other=other)

    async def delete(self):
        return await self.__client.http.interaction_delete(self.__client.gateway.bot_user.id, self.token)

# @dataclass
# class PingInteraction(Interaction[Literal[InteractionTypes.PING], None]):
#     type: Literal[InteractionTypes.PING]
#     data: None = None

# @dataclass
# class ApplicationCommandInteraction(Interaction[
#     Union[Literal[InteractionTypes.APPLICATION_COMMAND], Literal[InteractionTypes.APPLICATION_COMMAND_AUTOCOMPLETE]],
#     ApplicationCommandData
# ]):
#     type: Union[Literal[InteractionTypes.APPLICATION_COMMAND], Literal[InteractionTypes.APPLICATION_COMMAND_AUTOCOMPLETE]]
#     data: ApplicationCommandData

# @dataclass
# class MessageComponentInteraction(Interaction[Literal[InteractionTypes.MESSAGE_COMPONENT], MessageComponentData]):
#     type: Literal[InteractionTypes.MESSAGE_COMPONENT]
#     data: MessageComponentData

# @dataclass
# class ModalSubmitInteraction(Interaction[Literal[InteractionTypes.MODAL_SUBMIT], ModalSubmitData]):
#     type: Literal[InteractionTypes.MODAL_SUBMIT]
#     data: ModalSubmitData