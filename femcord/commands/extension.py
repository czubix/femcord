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

from .enums import CommandTypes

from ..enums import ApplicationCommandTypes

from ..utils import get_index

from typing import Callable, Awaitable, Optional, Any, NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Context, AppContext

Callback = Callable[..., Awaitable[None]]

class Command:
    def __init__(self, **kwargs) -> None:
        self.type: CommandTypes = kwargs["type"]
        self.parent: Optional[str] = kwargs.get("parent", None)
        self.cog: Optional[Cog] = kwargs.get("cog", None)

        self.callback: Callback = kwargs["callback"]
        self.name: str = kwargs.get("name") or self.callback.__name__
        self.description: Optional[str] = kwargs.get("description")
        self.usage: Optional[str] = kwargs.get("usage")
        self.enabled: bool = kwargs.get("enabled", True)
        self.hidden: bool = kwargs.get("hidden", False)
        self.aliases: list[str] = kwargs.get("aliases", [])
        self.guild_id: Optional[str] = kwargs.get("guild_id", None)
        self.other: dict[str, Any] = kwargs.get("other", {})

    async def __call__(self, context: "Context", *args, **kwargs) -> None:
        if self.cog is not None:
            return await self.callback(self.cog, context, *args, **kwargs)

        return await self.callback(context, *args, **kwargs)

class Group(Command):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.subcommands: list[Command] = []

    def command(self, **kwargs) -> Callable[..., Command]:
        def decorator(func: Callback) -> Command:
            kwargs["type"] = CommandTypes.SUBCOMMAND
            kwargs["parent"] = self.name
            kwargs["callback"] = func

            subcommand = Command(**kwargs)
            self.subcommands.append(subcommand)

            return subcommand

        return decorator

    def group(self, **kwargs) -> Callable[..., "Group"]:
        def decorator(func: Callback) -> "Group":
            kwargs["type"] = CommandTypes.GROUP
            kwargs["callback"] = func

            group = Group(**kwargs)
            self.subcommands.append(group)

            return group

        return decorator

    def get_subcommand(self, command: str) -> Optional[Command]:
        index = get_index(self.subcommands, command, key=lambda c: c.name)

        if index is None:
            for command_object_index, command_object in enumerate(self.subcommands):
                if command in command_object.aliases:
                    index = command_object_index

        if index is None:
            return

        return self.subcommands[index]

    def walk_subcommands(self) -> list[Command]:
        commands = []

        for command in self.subcommands:
            if command.type == CommandTypes.GROUP:
                commands.extend(command.walk_subcommands())

            commands.append(command)

        return commands

class AppCommand:
    def __init__(self, **kwargs) -> None:
        self.cog: Optional[Cog] = kwargs.get("cog", None)

        self.type: ApplicationCommandTypes = kwargs.get("type", ApplicationCommandTypes.CHAT_INPUT)
        self.callback: Callback = kwargs["callback"]
        self.name: str = kwargs.get("name") or self.callback.__name__
        self.description: Optional[str] = kwargs.get("description")

    async def __call__(self, context: "AppContext", *args, **kwargs) -> None:
        if self.cog is not None:
            return await self.callback(self.cog, context, *args, **kwargs)

        return await self.callback(context, *args, **kwargs)

class Listener:
    def __init__(self, callback: Callback, *, name: Optional[str] = None) -> None:
        self.callback = callback
        self.cog: Optional[Cog] = None
        self.__name__ = name or callback.__name__

    def __str__(self) -> str:
        return f"{self.callback!r}"

    def __repr__(self) -> str:
        return f"{self.callback!r}"

    async def __call__(self, *args, **kwargs) -> None:
        if self.cog is not None:
            return await self.callback(self.cog, *args, **kwargs)

        return await self.callback(*args, **kwargs)

class Cog:
    name: str
    description: Optional[str]
    hidden: bool
    listeners: list[Listener]
    commands: list[Command]
    app_commands: list[AppCommand]

    def __init__(self) -> NoReturn:
        raise NotImplementedError

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass

    def walk_commands(self) -> list[Command]:
        commands = []

        for command in self.commands:
            if command.type == CommandTypes.GROUP:
                commands.extend(command.walk_subcommands())

            commands.append(command)

        return commands