import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

bot = commands.Bot(command_prefix="!")
load_dotenv()


@bot.event
async def on_ready():
    """
    :returns nothing
    """
    channel = discord.utils.get(
        bot.get_all_channels(), name=os.getenv("DISCORD_CHANNEL")
    )
    await channel.send("@here, DAG has started.")


@bot.event
async def on_dag_finish():
    """
    :returns nothing
    """
    channel = discord.utils.get(
        bot.get_all_channels(), name=os.getenv("DISCORD_CHANNEL")
    )
    await channel.send("@here, DAG has finished.")


bot.run(os.getenv("DISCORD_TOKEN"))
