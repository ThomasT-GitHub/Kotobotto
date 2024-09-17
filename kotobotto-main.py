import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

token = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def printUserInfo(ctx, user: discord.User):
    await ctx.send(f'User ID: {user.id}\nUsername: {user.name}\nDiscriminator: {user.discriminator}')


bot.run(token)
