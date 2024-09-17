from typing import Literal, Optional
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
from word_retrieval_functions import get_random_word

load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")

bot = commands.Bot(
    command_prefix="/",
    intents=discord.Intents.all(),
    description="A Discord bot",
    case_insensitive=True,
    help_command=commands.DefaultHelpCommand(),
    allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False),
    activity=discord.Game(name="Roll for words!"),
    status=discord.Status.online,
)


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
    ctx: commands.Context,
    guilds: commands.Greedy[discord.Object],
    spec: Optional[Literal["~", "*", "^"]] = None,
) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.tree.command(name="rw", description="Roll for a word!")
async def roll_word(interaction: discord.Interaction):
    word = await get_random_word()  # Gets a random word
    await interaction.response.send_message(word)


bot.run(token)
