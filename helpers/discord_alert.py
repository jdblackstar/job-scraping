import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()


@bot.event
async def on_dag_status_change(status):
    """
    :param status: 'start' or 'finish'
    :returns nothing
    """
    channel_name = os.getenv("DISCORD_CHANNEL")
    channel = discord.utils.get(
        bot.get_all_channels(), name=channel_name, type=discord.ChannelType.text
    )
    if channel is None or not isinstance(channel, discord.TextChannel):
        print(f"Error: Channel '{channel_name}' not found.")
        return
    await channel.send(f"@here, DAG has {status}ed.")


token = os.getenv("DISCORD_TOKEN")

if not token:
    print("Error: DISCORD_TOKEN is not set in the environment variables.")
    exit(1)

bot.run(token)
