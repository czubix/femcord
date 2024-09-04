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

from .gateway import Gateway
from .http import HTTP
from .intents import Intents
from .utils import MISSING

from datetime import datetime

from typing import Callable, Optional

class Client:
    def __init__(self, *, intents: Intents = Intents.default(), messages_limit: int = 1000, last_latencies_limit: int = 100, mobile: bool = False) -> None:
        self.loop = asyncio.get_event_loop()
        self.token: str = MISSING
        self.bot: bool = MISSING
        self.intents = intents
        self.http: HTTP = MISSING
        self.gateway: Gateway = MISSING
        self.listeners: list[Callable[..., None]] = []
        self.waiting_for: list[tuple[str, asyncio.Future, Callable[..., bool]]] = []
        self.messages_limit = messages_limit
        self.last_latencies_limit = last_latencies_limit
        self.mobile = mobile
        self.started_at = datetime.now()

    def event(self, function: Callable[..., None], *, name: Optional[str] = None) -> None:
        if name:
            event = function
            def function(*args, **kwargs) -> None:
                event(*args, **kwargs)
            function.__name__ = name
        self.listeners.append(function)

    async def wait_for(self, event: str, check: Optional[Callable[..., bool]] = None, *, timeout: Optional[float] = None) -> asyncio.Future:
        future = self.loop.create_future()
        listener = event, future, check or (lambda *args: True)
        self.waiting_for.append(listener)

        if timeout is not None:
            try:
                return await asyncio.wait_for(future, timeout)
            except TimeoutError:
                self.waiting_for.remove(listener)
                raise

        return await future

    def run(self, token: str, *, bot: bool = True) -> None:
        self.token = token
        self.bot = bot

        self.loop.create_task(HTTP(self))
        self.loop.create_task(Gateway(self))

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            on_closes = [listener() for listener in self.listeners if listener.__name__ == "on_close"]

            for on_close in on_closes:
                self.loop.run_until_complete(on_close)

            self.gateway.heartbeat.stop()