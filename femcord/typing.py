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

import asyncio

from .commands import Context, AppContext

from typing import Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Channel

class Typing:
    def __init__(self, channel: "Channel") -> None:
        self.loop = asyncio.get_event_loop()
        self.channel = channel

    def send(self) -> Awaitable:
        return self.channel.start_typing()

    async def do_typing(self) -> None:
        for _ in range(12):
            await asyncio.sleep(5)
            await self.send()

    def start(self) -> Awaitable:
        return self.__aenter__()

    def stop(self) -> Awaitable:
        return self.__aexit__(None, None, None)

    async def __aenter__(self) -> None:
        await self.send()
        self.task = self.loop.create_task(self.do_typing())

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.channel.type is None:
            return

        self.task.cancel()

class HybridTyping:
    def __init__(self, context: "Context | AppContext") -> None:
        self.context = context
        self.typing: Typing | None = None

    async def __aenter__(self) -> None:
        if isinstance(self.context, AppContext):
            await self.context.think()
        else:
            self.typing = Typing(self.context.channel)
            await self.typing.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.typing is not None:
            await self.typing.stop()