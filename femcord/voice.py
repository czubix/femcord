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

import aiohttp
import socket
import select

import nacl.secret
import struct

import threading
import time

from enum import Enum

from .opus import Encoder, OPUS_SILENCE

from .utils import MISSING

from typing import Callable, Awaitable, Any, IO, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client

class Opcodes(Enum):
    IDENTIFY = 0
    SELECT_PROTOCOL = 1
    READY = 2
    HEARTBEAT = 3
    SESSION_DESCRIPTION = 4
    SPEAKING = 5
    HEARTBEAT_ACK = 6
    RESUME = 7
    HELLO = 8
    RESUMED = 9
    _11 = 11
    VIDEO = 12
    CLIENT_DISCONNECT = 13
    SESSION_UPDATE = 14
    MEDIA_SINK_WANTS = 15
    VOICE_BACKEND_VERSION = 16
    CHANNEL_OPTIONS_UPDATE = 17
    _18 = 18
    _20 = 20

class PCMAudio:
    def __init__(self, stream: IO) -> None:
        self.stream = stream

    def read(self) -> bytes:
        data = self.stream.read(Encoder.FRAME_SIZE)
        if len(data) != Encoder.FRAME_SIZE:
            return b""
        return data

class SocketReader(threading.Thread):
    def __init__(self, socket: socket.socket) -> None:
        super().__init__(daemon=True, name=f"VoiceSocket:{id(self):#x}")

        self.socket = socket

        self._end = threading.Event()

        self._callbacks: list[Callable[[bytes], Any]] = []

    def register(self, callback: Callable[[bytes], Any]) -> None:
        self._callbacks.append(callback)

    def unregister(self, callback: Callable[[bytes], Any]) -> None:
        self._callbacks.remove(callback)

    def stop(self) -> None:
        self._end.set()

    def run(self) -> None:
        while not self._end.is_set():
            try:
                readable, _, _ = select.select([self.socket], [], [], 30)
            except (ValueError, TypeError, OSError):
                continue

            if not readable:
                continue

            try:
                data = self.socket.recv(2048)
            except OSError:
                continue
            else:
                for callback in self._callbacks:
                    try:
                        callback(data)
                    except Exception:
                        continue

class VoiceHeartbeat:
    def __init__(self, voice: "VoiceWebSocket", interval: float) -> None:
        self.loop = asyncio.get_event_loop()
        self.voice = voice
        self.heartbeat_interval = interval
        self.heartbeat_task: asyncio.Task = MISSING
        self.time: float = MISSING

    def send(self) -> Awaitable[None]:
        return self.voice.send(Opcodes.HEARTBEAT, time.time() * 1000)

    async def heartbeat_loop(self) -> None:
        await self.send()

        while True:
            self.time = time.time()
            await asyncio.sleep(self.heartbeat_interval / 1000)
            await self.send()

    def start(self) -> None:
        self.heartbeat_task = self.loop.create_task(self.heartbeat_loop())

    def stop(self) -> None:
        self.heartbeat_task.cancel()

class VoiceWebSocket:
    async def __new__(cls, *args, **kwargs) -> "VoiceWebSocket":
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self, client: "Client", *, token: str, guild_id: str, endpoint: str) -> None:
        self.client = client
        self.token = token
        self.guild_id = guild_id
        self.endpoint = endpoint
        self.url = "wss://" + self.endpoint + "?v=4"

        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.ws = await self.session.ws_connect(self.url)

        self.ssrc: int = MISSING
        self.sequence = 0
        self.timestamp = 0

        self.address: tuple[str, int] = MISSING
        self.ip: str = MISSING
        self.port: int = MISSING

        self.secret_key: bytes = MISSING

        self.ready = False

        self.encoder = Encoder()

        self.socket: socket.socket = MISSING

        self.heartbeat: VoiceHeartbeat = MISSING
        self.socket_reader: SocketReader = MISSING

        self.task = self.loop.create_task(self.run())

    def send(self, opcode: Opcodes, data: dict | float) -> Awaitable[None]:
        return self.ws.send_json({"op": opcode.value, "d": data})

    def get_voice_packet(self, data: bytes) -> bytes:
        header = bytearray(12)

        header[0] = 0x80
        header[1] = 0x78

        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.ssrc)

        return self.encrypt(header, data)

    def encrypt(self, header: bytes, data: bytes) -> bytes:
        box = nacl.secret.SecretBox(self.secret_key)

        nonce = bytearray(24)
        nonce[:12] = header

        return header + box.encrypt(data, bytes(nonce)).ciphertext

    def send_voice_packet(self, data: bytes) -> None:
        self.sequence += 1

        if self.sequence > 65535:
            self.sequence = 0

        packet = self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
        packet = self.get_voice_packet(packet)

        try:
            self.socket.sendall(packet)
        except OSError:
            pass

        self.timestamp += Encoder.SAMPLES_PER_FRAME

        if self.timestamp + Encoder.SAMPLES_PER_FRAME > 4294967295:
            self.timestamp = 0

    async def discover_ip(self) -> None:
        packet = bytearray(74)

        struct.pack_into(">H", packet, 0, 1)
        struct.pack_into(">H", packet, 2, 70)
        struct.pack_into(">I", packet, 4, self.ssrc)

        await self.loop.sock_sendall(self.socket, packet)

        future = self.loop.create_future()

        def callback(data: bytes) -> None:
            if data[1] == 0x02 and len(data) == 74:
                self.loop.call_soon_threadsafe(future.set_result, data)

        future.add_done_callback(lambda _: self.socket_reader.unregister(callback))
        self.socket_reader.register(callback)

        data = await future

        self.ip = data[8:data.index(0, 8)].decode()
        self.port = struct.unpack_from(">H", data, len(data) - 2)[0]

    async def speak(self, speak: bool = True) -> None:
        await self.send(Opcodes.SPEAKING, {
            "speaking": 1 if speak else 0,
            "delay": 0,
            "ssrc": self.ssrc
        })

    async def run(self) -> None:
        await self.send(Opcodes.IDENTIFY, {
            "server_id": self.guild_id,
            "user_id": self.client.gateway.bot_user.id,
            "session_id": self.client.gateway.session_id,
            "token": self.token
        })

        async for message in self.ws:
            if message.type in (aiohttp.WSMsgType.error, aiohttp.WSMsgType.closed):
                break

            if message.type is aiohttp.WSMsgType.text:
                data = message.json()
                op, data = Opcodes(data["op"]), data["d"]

                match op:
                    case Opcodes.HELLO:
                        self.heartbeat = VoiceHeartbeat(self, data["heartbeat_interval"])
                        self.heartbeat.start()
                    case Opcodes.READY:
                        self.ssrc = data["ssrc"]
                        self.address = data["ip"], data["port"]

                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        self.socket.setblocking(False)

                        await self.loop.sock_connect(self.socket, self.address)

                        self.socket_reader = SocketReader(self.socket)
                        self.socket_reader.start()

                        await self.discover_ip()

                        await self.send(Opcodes.SELECT_PROTOCOL, {
                            "protocol": "udp",
                            "data": {
                                "address": self.ip,
                                "port": self.port,
                                "mode": "xsalsa20_poly1305"
                            }
                        })
                    case Opcodes.SESSION_DESCRIPTION:
                        self.secret_key = bytes(data["secret_key"])
                        self.ready = True

class AudioPlayer(threading.Thread):
    DELAY = Encoder.FRAME_LENGTH / 1000

    def __init__(self, player: "Player", source: PCMAudio) -> None:
        super().__init__(daemon=True, name=f"AudioPlayer:{id(self):#x}")

        self.player = player
        self.source = source

        self.running = threading.Event()
        self.paused = threading.Event()

        self.loops: int = MISSING
        self._start: float = MISSING

    def run(self) -> None:
        self.loops = 0
        self._start = time.perf_counter()

        while not self.running.is_set():
            if self.paused.is_set():
                for _ in range(5):
                    self.player.websocket.socket.sendall(OPUS_SILENCE)
                continue

            data = self.source.read()

            if not data:
                break

            self.player.websocket.send_voice_packet(data)

            self.loops += 1
            next_time = self._start + self.DELAY * self.loops
            delay = max(0, self.DELAY + (next_time - time.perf_counter()))

            time.sleep(delay)

class Player:
    async def __new__(cls, *args, **kwargs) -> "Player":
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self, client: "Client", **kwargs) -> None:
        self.client = client
        self.websocket = await VoiceWebSocket(client, **kwargs)

        self.audio_player: AudioPlayer = MISSING

        while not self.websocket.ready:
            await asyncio.sleep(1)

        await self.websocket.speak()

    def play(self, source: PCMAudio) -> None:
        self.audio_player = AudioPlayer(self, source)
        self.audio_player.start()

    def stop(self) -> None:
        self.audio_player.running.set()

    def pause(self) -> None:
        self.audio_player.paused.set()

    def resume(self) -> None:
        self.audio_player.paused.clear()