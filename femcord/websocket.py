"""
Copyright 2022-2025 czubix

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
import aiohttp
import zlib
import json
import logging

from .enums import Opcodes

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client
    from .gateway import Gateway

class WebSocket:
    URL = "wss://gateway.discord.gg/?v=9&encoding=json&compress=zlib-stream"

    async def __new__(cls, *args) -> "WebSocket":
        instance = super().__new__(cls)
        await instance.__init__(*args)
        return instance

    async def __init__(self, gateway: "Gateway", client: "Client") -> None:
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.gateway = gateway
        self.client = client

        self.ws = await self.session.ws_connect(WebSocket.URL)
        self.gateway.ws = self
        self.client.gateway = self.gateway

        self.buffer = bytearray()
        self.inflator = zlib.decompressobj()

        async for message in self.ws:
            if message.type in (aiohttp.WSMsgType.error, aiohttp.WSMsgType.closed):
                break

            if message.type is aiohttp.WSMsgType.binary:
                self.buffer.extend(message.data)

                if len(message.data) < 4 or not message.data[-4:] == b"\x00\x00\xff\xff":
                    continue

                data = self.inflator.decompress(self.buffer)
                self.buffer = bytearray()

                data = json.loads(data)
                op = data.get("op")
                d = data.get("d")
                s = data.get("s")
                t = data.get("t")

                logging.debug(f"op: {Opcodes(op).name}, data: {None if not isinstance(data, dict) else d}, sequence number: {s}, event name: {t}")

                await self.gateway.on_message(Opcodes(op), d, s, t)

        self.gateway.heartbeat.stop()
        await self.session.close()
        self.gateway.ready = False
        self.gateway.resuming = True
        self.gateway.last_sequence_number = self.gateway.sequence_number
        await WebSocket.__init__(self, self.gateway, self.client)

    async def send(self, op: Opcodes, data: dict, *, sequences: int = None) -> None:
        if self.ws.closed:
            return

        logging.debug(f"sent op: {op.name}, data: {data}, sequences: {sequences}".replace(self.client.token, "TOKEN"))

        ready_data = {
            "op": op.value,
            "d": data
        }

        if sequences is not None:
            ready_data["s"] = sequences

        while self.ws.closed:
            await asyncio.sleep(0.1)

        try:
            await self.ws.send_json(ready_data)
        except ConnectionResetError:
            pass