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

from .extension import Command, AppCommand

from ..enums import InteractionCallbackTypes
from ..utils import MISSING

from typing import Union, Optional, Any, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .bot import Bot
    from ..types import Message, Interaction, User, Channel, Role

class Context:
    def __init__(self, bot: "Bot", message: "Message") -> None:
        self.bot = bot
        self.bot_user = self.bot.gateway.bot_user

        self.guild = message.guild
        self.channel = message.channel or message.thread

        if isinstance(self.channel, str):
            self.channel = self.guild.get_channel(self.channel)

        self.message = message

        self.author = message.author
        self.member = message.member

        self.command: Command = MISSING
        self.arguments: list[Any] = []
        self.error: Optional[Exception] = None

        self.send = self.channel.send
        self.reply = self.message.reply

    def __str__(self) -> None:
        return "<Context guild={!r} channel={!r} message={!r} command={!r} arguments={!r}>".format(self.guild, self.channel, self.message, self.command, self.arguments)

    def __repr__(self) -> None:
        return "<Context guild={!r} channel={!r} message={!r} command={!r} arguments={!r}>".format(self.guild, self.channel, self.message, self.command, self.arguments)

class AppContext:
    def __init__(self, bot: "Bot", interaction: "Interaction", command: "AppCommand") -> None:
        self.bot = bot
        self.bot_user = bot.gateway.bot_user

        self.interaction = interaction

        self.guild = interaction.guild
        self.channel = interaction.channel

        self.message = None

        self.author = interaction.user or interaction.member.user
        self.member = interaction.member

        self.command = command
        self.arguments: list[Union["User", "Channel", "Role", str, float, int, bool]] = []
        self.error: Exception = MISSING

        self.replied = False
        self.to_edit = False

        self.reply = self.send
        self.edit = self.interaction.edit

    def __str__(self) -> None:
        return "<AppContext guild={!r} channel={!r} interaction={!r}>".format(self.guild, self.channel, self.interaction)

    def __repr__(self) -> None:
        return "<AppContext guild={!r} channel={!r} interaction={!r}>".format(self.guild, self.channel, self.interaction)

    def think(self) -> Awaitable[None]:
        self.to_edit = True
        return self.interaction.callback(InteractionCallbackTypes.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE)

    def send(self, *args, **kwargs) -> Awaitable[None]:
        if self.to_edit:
            self.to_edit = False
            self.replied = True
            return self.edit(*args, **kwargs)
        if self.replied:
            return self.interaction.send(*args, **kwargs)
        self.replied = True
        return self.interaction.callback(InteractionCallbackTypes.CHANNEL_MESSAGE_WITH_SOURCE, *args, **kwargs)