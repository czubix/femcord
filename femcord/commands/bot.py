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

from ..client import Client
from ..http import Route
from ..intents import Intents
from ..types import User, Channel, Role
from ..errors import InvalidArgument
from ..enums import ApplicationCommandTypes, InteractionTypes, CommandOptionTypes
from ..utils import get_index

from .extension import Cog, Command, Group, AppCommand, Listener
from .enums import CommandTypes
from .context import Context, AppContext

from .errors import *

from dataclasses import is_dataclass
from types import CoroutineType, ModuleType, UnionType

import importlib.util, inspect, traceback, sys

from typing import Callable, Awaitable, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import Message, Interaction

BeforeAfterFunction = Callable[[Context | AppContext], Awaitable[None]]

class Bot(Client):
    def __init__(self, *, name: Optional[str] = None, command_prefix: Callable[["Message"], Awaitable[str]] | str, intents: Optional[Intents] = None, messages_limit: int = 1000, last_latencies_limit: int = 100, mobile: bool = False, owners: Optional[tuple[str] | list[str]] = None, context: Optional[Context] = None, app_context: Optional[AppContext] = None) -> None:
        super().__init__(intents=intents or Intents.all(), messages_limit=messages_limit, last_latencies_limit=last_latencies_limit, mobile=mobile)

        self.name = name
        self.owners = list(owners or [])
        self.original_prefix = self.command_prefix = command_prefix

        self.context = context or Context
        self.app_context = app_context or AppContext

        if not callable(self.command_prefix):
            async def command_prefix(self, _):
                return self.original_prefix

            self.command_prefix = command_prefix

        self.extensions: list[ModuleType] = []
        self.cogs: list[Cog] = []
        self.commands: list[Command] = []
        self.app_commands: list[AppCommand] = []

        self.before_call_functions: list[BeforeAfterFunction] = []
        self.after_call_functions: list[BeforeAfterFunction] = []

        @self.event
        async def on_interaction_create(interaction: "Interaction") -> None:
            if interaction.type is not InteractionTypes.APPLICATION_COMMAND:
                return

            await self.process_interaction_commands(interaction)

        @self.event
        async def on_message_create(message: "Message") -> None:
            if message.author.bot:
                return

            await self.process_commands(message)

    def __str__(self) -> str:
        return self.name or self.gateway.bot_user.username

    def __repr__(self) -> str:
        return f"<Bot name={str(self)!r}>"

    def before_call(self, func: BeforeAfterFunction) -> None:
        self.before_call_functions.append(func)

    def after_call(self, func: BeforeAfterFunction) -> None:
        self.after_call_functions.append(func)

    async def register_app_commands(self) -> None:
        commands = []

        types = {
            str: CommandOptionTypes.STRING,
            int: CommandOptionTypes.INTEGER,
            float: CommandOptionTypes.NUMBER,
            bool: CommandOptionTypes.BOOLEAN,
            User: CommandOptionTypes.USER,
            Channel: CommandOptionTypes.CHANNEL,
            Role: CommandOptionTypes.ROLE,
            inspect._empty: CommandOptionTypes.STRING
        }

        def get_type(_type: User | Channel | Role | str | int | float | bool | UnionType) -> CommandOptionTypes:
            if _type in types:
                return types[_type]

            if isinstance(_type, UnionType):
                for _type in _type.__args__:
                    if _type in types:
                        return types[_type]

            raise TypeError(f"'{_type}' type is not supported")

        for command in self.app_commands:
            skip_arguments = 1

            if command.cog is not None:
                skip_arguments += 1

            command_arguments = []

            if command.type is ApplicationCommandTypes.CHAT_INPUT:
                command_arguments = list(inspect.signature(command.callback).parameters.values())[skip_arguments:]

            commands.append({
                "type": command.type.value,
                "name": command.name,
                **(
                    {
                        "description": command.description or command.name
                    }
                    if command.type is ApplicationCommandTypes.CHAT_INPUT else
                    {

                    }
                ),
                "options": [
                    {
                        "type": get_type(argument.annotation).value,
                        "name": argument.name,
                        "description": argument.name,
                        "required": argument.default == argument.empty
                    }
                    for argument in command_arguments
                ],
                "integration_types": [0, 1],
                "contexts": [0, 1, 2],
                "nsfw": command.nsfw
            })

        await self.http.request(Route("PUT", "applications", self.gateway.bot_user.id, "commands"), data=commands)

    def command(self, **kwargs) -> Callable[[Callable[..., None]], Command]:
        def decorator(func: Callable[..., None]) -> Command:
            kwargs["type"] = CommandTypes.COMMAND
            kwargs["callback"] = func

            command = Command(**kwargs)
            self.commands.append(command)

            return command

        return decorator

    def group(self, **kwargs) -> Callable[[Callable[..., None]], Group]:
        def decorator(func: Callable[..., None]) -> Group:
            kwargs["type"] = CommandTypes.GROUP
            kwargs["callback"] = func

            group = Group(**kwargs)
            self.commands.append(group)

            return group

        return decorator

    def app_command(self, **kwargs) -> Callable[[Callable[..., None]], AppCommand]:
        def decorator(func: Callable[..., None]) -> AppCommand:
            kwargs["callback"] = func

            command = AppCommand(**kwargs)
            self.app_commands.append(command)

            return command

        return decorator

    def hybrid_command(self, **kwargs) -> Callable[[Callable[..., None]], tuple[Command, AppCommand]]:
        def decorator(func: Callable[..., None]) -> tuple[Command, AppCommand]:
            kwargs["callback"] = func

            command = Command(**(kwargs | {"type": CommandTypes.COMMAND}))
            app_command = AppCommand(**kwargs)

            self.commands.append(command)
            self.app_commands.append(app_command)

            return command, app_command

        return decorator

    def get_command(self, command: str, *, guild_id: Optional[str] = None) -> Optional[Command | Group]:
        commands = self.commands

        if guild_id is not None:
            commands = [command for command in commands if command.guild_id and command.guild_id == guild_id]

        index = get_index(commands, command, key=lambda command: command.name)

        if index is None:
            for command_object_index, command_object in enumerate(commands):
                if command in command_object.aliases:
                    index = command_object_index

        if index is None:
            return

        return commands[index]

    def get_app_command(self, command: str) -> Optional[AppCommand]:
        index = get_index(self.app_commands, command, key=lambda command: command.name)

        if index is None:
            return

        return self.app_commands[index]

    def remove_command(self, command: Command | str) -> None:
        if isinstance(command, str):
            index = get_index(self.commands, command, key=lambda command: command.name)

            if index is None:
                raise CommandNotFound(command)

            command = self.commands[index]

        if command.cog is not None:
            command.cog.commands.remove(command)

        self.commands.remove(command)

    def remove_app_command(self, command: AppCommand | str) -> None:
        if isinstance(command, str):
            index = get_index(self.app_commands, command, key=lambda command: command.name)

            if index is None:
                raise CommandNotFound(command)

            command = self.app_commands[index]

        if command.cog is not None:
            command.cog.app_commands.remove(command)

        self.app_commands.remove(command)

    def walk_commands(self) -> list[Command]:
        commands = []

        for command in self.commands:
            commands.append(command)

            if command.type == CommandTypes.GROUP:
                commands += command.walk_subcommands()

        return commands

    def load_cog(self, cog: Cog) -> None:
        if cog.__class__ in (cog.__class__ for cog in self.cogs):
            raise CogAlreadyLoaded(cog.__class__.__name__)

        cog.name = getattr(cog, "name", cog.__class__.__name__)
        cog.description = getattr(cog, "description", None)
        cog.hidden = getattr(cog, "hidden", False)

        cog.commands = []
        cog.app_commands = []
        cog.listeners = []

        for attr in dir(cog):
            attr = getattr(cog, attr)

            if isinstance(attr, Command):
                cog.commands.append(attr)
            elif isinstance(attr, AppCommand):
                cog.app_commands.append(attr)
            elif isinstance(attr, Listener):
                cog.listeners.append(attr)
            elif isinstance(attr, tuple):
                if len(attr) == 2 and isinstance(attr[0], Command) and isinstance(attr[1], AppCommand):
                    cog.commands.append(attr[0])
                    cog.app_commands.append(attr[1])

        for command in cog.commands + cog.app_commands:
            command.cog = cog

        for listener in cog.listeners:
            listener.cog = cog

        self.commands += [command for command in cog.commands if not command.type == CommandTypes.SUBCOMMAND]
        self.app_commands += cog.app_commands
        self.listeners += cog.listeners

        self.cogs.append(cog)

        cog.on_load()

    def get_cog(self, cog: Cog) -> Optional[Cog]:
        index = get_index(self.cogs, cog, key=lambda cog: cog.name)

        if index is None:
            return

        return self.cogs[index]

    def unload_cog(self, cog: Cog | str) -> None:
        if isinstance(cog, str):
            index = get_index(self.cogs, cog, key=lambda cog: cog.__class__.__name__)

            if index is None:
                raise CogNotFound(cog)

            cog = self.cogs[index]

        cog.on_unload()

        for command in cog.commands:
            self.remove_command(command)

        for listener in cog.listeners:
            self.listeners.remove(listener)

        self.cogs.remove(cog)

    def load_extension(self, name: str) -> None:
        name = importlib.util.resolve_name(name, None)

        if name in (name.__name__ for name in self.extensions):
            raise ExtensionAlreadyLoaded(name)

        spec = importlib.util.find_spec(name)

        if spec is None:
            raise ExtensionNotFound(name)
        elif spec.loader is None:
            raise ExtensionNotLoaded(name)

        extension = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extension)

        sys.modules[name] = extension

        setup = getattr(extension, "setup")
        setup(self)

        self.extensions.append(extension)

    def get_extension(self, extension: ModuleType) -> Optional[ModuleType]:
        index = get_index(self.extensions, extension, key=lambda command: command.__name__)

        if index is None:
            return

        return self.extensions[index]

    def unload_extension(self, name: str) -> None:
        name = importlib.util.resolve_name(name, None)
        index = get_index(self.extensions, name, key=lambda extension: extension.__name__)

        if index is None:
            raise ExtensionNotLoaded(name)

        for cog in self.cogs:
            if inspect.getmodule(cog) == self.extensions[index]:
                self.unload_cog(cog)

        del sys.modules[name]
        del self.extensions[index]

    async def process_interaction_commands(self, interaction: "Interaction") -> None:
        on_error = "on_error" in (listener.__name__ for listener in self.listeners)

        command = self.get_app_command(interaction.data.name)

        if not command:
            return

        context = self.app_context(self, interaction, command)

        args = []
        kwargs = {}

        if interaction.data.type is not ApplicationCommandTypes.CHAT_INPUT:
            args.append(interaction.data.target)

        if interaction.data.options:
            for option in interaction.data.options:
                kwargs[option.name] = option.value

        context.arguments = list(kwargs.values())

        async def run_command():
            try:
                await command(context, *args, **kwargs)
            except Exception as error:
                context.error = error

                if not on_error:
                    return traceback.print_exc()

                await self.gateway.dispatch("error", context, error)

        self.loop.create_task(run_command())

    async def process_commands(self, message: "Message", *, before_call_functions: list | BeforeAfterFunction = [], after_call_functions: list | BeforeAfterFunction = []) -> None:
        if callable(before_call_functions):
            before_call_functions = [before_call_functions]
        if callable(after_call_functions):
            after_call_functions = [after_call_functions]

        prefixes = prefix = await self.command_prefix(self, message)

        if not isinstance(prefix, str):
            for _prefix in prefixes:
                if len(message.content) > len(_prefix) and message.content[:len(_prefix)] == _prefix:
                    prefix = _prefix

        if not (len(message.content) > len(prefix) and message.content[:len(prefix)] == prefix):
            return

        on_error = "on_error" in (listener.__name__ for listener in self.listeners)

        command, *arguments = message.content[len(prefix):].split(maxsplit=1)
        if arguments:
            arguments = arguments[0].split(" ")

        context = self.context(self, message)

        command_object = self.get_command(command)
        skip_arguments = 1

        if command_object and command_object.guild_id and not context.guild.id == command_object.guild_id:
            command_object = self.get_command(command, guild_id=context.guild.id)

        while command_object and arguments and command_object.type is CommandTypes.GROUP:
            command_object = command_object.get_subcommand(arguments[0])
            arguments = arguments[1:]

        if command_object is None:
            error = CommandNotFound(f"{command} was not found")
            context.arguments = arguments

            if not on_error:
                raise error

            return await self.gateway.dispatch("error", context, error)

        if command_object.cog is not None:
            skip_arguments += 1

        context.command = command = command_object
        command_arguments = list(inspect.signature(command.callback).parameters.values())[skip_arguments:]
        default_arguments = [argument for argument in command_arguments if argument.default != argument.empty]

        if command.enabled is False:
            error = CommandDisabled(f"{command.name} command is disabled", command)

            if not on_error:
                raise error

            return await self.gateway.dispatch("error", context, error)

        args = []
        kwargs = {}

        if not len(arguments) >= len(command_arguments) - len(default_arguments):
            command_argument = command_arguments[len(arguments)].name
            error = MissingArgument(f"{command_argument} was not specified", command, command_arguments, arguments, command_argument)
            context.arguments = arguments

            if not on_error:
                raise error

            return await self.gateway.dispatch("error", context, error)

        for index, command_argument in enumerate(command_arguments):
            annotations = [command_argument.annotation]

            if isinstance(annotations[0], UnionType):
                annotations = annotations[0].__args__

            if annotations[0] == command_argument.empty:
                annotations = [str]

            if index + 1 > len(arguments) and command_argument.default != command_argument.empty:
                break

            errors = []

            for annotation in annotations:
                parsed_argument = None

                try:
                    if is_dataclass(annotation) is True:
                        annotation: Any = getattr(annotation, "from_arg", annotation)
                        parsed_argument = annotation(context, arguments[index])
                    else:
                        parsed_argument = annotation(arguments[index])

                    if isinstance(parsed_argument, CoroutineType):
                        parsed_argument = await parsed_argument

                    if parsed_argument is None:
                        raise InvalidArgument()

                    arguments[index] = parsed_argument
                    break
                except Exception:
                    errors.append(annotation.__name__)

            if (len(errors), len(annotations)) == (1, 1):
                error = InvalidArgumentType(f"'{annotations[0].__name__}' type is not valid for '{command_argument.name}' argument", command, command_arguments, arguments, command_argument.name)
                context.arguments = arguments

                if not on_error:
                    raise error

                return await self.gateway.dispatch("error", context, error)

            if len(errors) == len(annotations):
                apostrophe = "'"
                error = InvalidArgumentType(f"{', '.join(apostrophe + annotation.__name__ + apostrophe for annotation in annotations[:-1]) + ' and ' + apostrophe + annotations[-1].__name__ + apostrophe} types are not valid for '{command_argument.name}' argument", command, command_arguments, arguments, command_argument.name)
                context.arguments = arguments

                if not on_error:
                    raise error

                return await self.gateway.dispatch("error", context, error)

            if command_argument.kind == command_argument.POSITIONAL_OR_KEYWORD:
                argument = arguments[index]
                context.arguments.append(argument)
                args.append(argument)

            elif command_argument.kind == command_argument.VAR_POSITIONAL:
                argument = arguments[index:]
                context.arguments.append(argument)
                args.append(argument)

            elif command_argument.kind == command_argument.KEYWORD_ONLY:
                argument = arguments[index:][0]
                if all(isinstance(x, str) for x in arguments[index:]):
                    argument = " ".join(arguments[index:])
                context.arguments.append(argument)
                kwargs[command_argument.name] = argument

        async def run_command():
            for before_call in self.before_call_functions + before_call_functions:
                await before_call(context)

            try:
                await command(context, *args, **kwargs)
            except Exception as error:
                context.arguments = arguments
                context.error = error

                if not on_error:
                    return traceback.print_exc()

                await self.gateway.dispatch("error", context, error)

            for after_call in self.after_call_functions + after_call_functions:
                await after_call(context)

        self.loop.create_task(run_command())