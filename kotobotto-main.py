import os
import discord
from discord.ext import commands

token = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(a + b)


bot.run(token)
