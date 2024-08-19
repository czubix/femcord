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

from .extension import Command, Group, AppCommand

from .enums import CommandTypes

from typing import Callable

def command(**kwargs) -> Callable[[Callable[..., None]], Command]:
    def decorator(func: Callable[..., None]) -> Command:
        kwargs["type"] = CommandTypes.COMMAND
        kwargs["callback"] = func

        return Command(**kwargs)

    return decorator

def group(**kwargs) -> Callable[[Callable[..., None]], Group]:
    def decorator(func: Callable[..., None]) -> Group:
        kwargs["type"] = CommandTypes.GROUP
        kwargs["callback"] = func

        return Group(**kwargs)

    return decorator

def app_command(**kwargs) -> Callable[[Callable[..., None]], AppCommand]:
    def decorator(func: Callable[..., None]) -> AppCommand:
        kwargs["callback"] = func

        return AppCommand(**kwargs)

    return decorator

def hybrid_command(**kwargs) -> Callable[[Callable[..., None]], tuple[Command, AppCommand]]:
    def decorator(func: Callable[..., None]) -> tuple[Command, AppCommand]:
        kwargs["callback"] = func

        command = Command(**(kwargs | {"type": CommandTypes.COMMAND}))
        app_command = AppCommand(**kwargs)

        return command, app_command

    return decorator