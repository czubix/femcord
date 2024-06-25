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

from .types import Message

from typing import Union

class Typing:
    def __init__(self, message: Message) -> None:
        self.loop = asyncio.get_event_loop()
        self.message = message

    def send(self) -> Union[dict, str]:
        return self.message.channel.start_typing()

    async def do_typing(self) -> None:
        for _ in range(12):
            await asyncio.sleep(5)
            await self.send()

    def start(self) -> None:
        return self.__aenter__()

    def stop(self) -> None:
        return self.__aexit__(None, None, None)

    async def __aenter__(self) -> None:
        await self.send()
        self.task = self.loop.create_task(self.do_typing())

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.task.cancel()