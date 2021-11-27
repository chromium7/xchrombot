import os
from twitchio.ext import commands

bot = commands.Bot(
    # set up the bot
    token=os.environ['TMI_TOKEN'],
    client_id=os.environ['CLIENT_ID'],
    nick=os.environ['BOT_NICK'],
    prefix=os.environ['BOT_PREFIX'],
    initial_channels=[os.environ['CHANNEL']]
)


@bot.event
async def event_ready() -> None:
    """
    Called once when the bot goes online
    """
    print(f"{os.environ['BOT_NICK']} is online!")
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(os.environ['CHANNEL'], f"/me has landed!")


@bot.event
async def event_message(ctx) -> None:
    """
    Runs everytime a message is sent in chat
    """

    # Ignores bot and streamer
    if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
        return

    await ctx.channel.send(ctx.content)


@bot.command(name='test')
async def test(ctx) -> None:
    await ctx.send('test 123')


if __name__ == "__main__":
    bot.run()
