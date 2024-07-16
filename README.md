# femcord

femcord is a lightweight Discord library designed for creating smaller bots. This repository serves as part of my portfolio and is intended for use with my personal bots.

## Installation

**Python 3.12 or higher is required**

```bash
$ git clone https://github.com/czubix/femcord.git
$ cd femcord
$ python3 -m pip install -U .
```

or

```bash
$ python3 -m pip install git+https://github.com/czubix/femcord.git
```

## Quick start

Below are some quick examples to help you get started with femcord. Detailed documentation will be provided later.

### Creating a bot

```py
import femcord
from femcord import commands

bot = commands.Bot(command_prefix="!", intents=femcord.Intents.all())

@bot.event
async def on_ready():
    print("Logged in as " + bot.gateway.bot_user.username)

bot.run("YOUR_BOT_TOKEN")
```

### Adding commands

```py
@bot.command()
async def ping(ctx: commands.Context):
    await ctx.reply("Pong!")

@bot.command(aliases=["say"])
async def echo(ctx: commands.Context, *, content: str):
    await ctx.reply(content)
```

### Handling events

```py
@bot.event
async def on_message_create(message: femcord.types.Message):
    if message.author.bot:
        return

    if "uwu" in message.content.lower():
        return await message.reply(":3")
```

### Links
- [Discord server](https://discord.gg/poligon-704439884340920441)