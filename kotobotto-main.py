import os
from typing import Literal, Optional
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import word_retrieval_functions as wrf
import dummy_server as ds

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

# Dictionary to store the last message ID for each user
last_message_ids = {}


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    keep_alive_bot_ping.start()  # Keeps the bot alive on Discord


@bot.tree.command(name="rw", description="Roll for a word!")
async def roll_word(interaction: discord.Interaction):
    word = wrf.get_random_word()  # Gets a random word
    embed = wrf.create_word_embed(
        word["Vocab-expression"],
        word["Vocab-kana"],
        word["Vocab-meaning"],
        word["Vocab-pos"],
        word["Sentence-expression"],
        word["Sentence-kana"],
        word["Sentence-meaning"],
    )
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await message.add_reaction("❤️")

    # Store the message ID in the dictionary with the user ID as the key
    last_message_ids[interaction.user.id] = message.id


@bot.tree.command(name="sw", description="Show saved words")
async def list_saved_words(interaction: discord.Interaction):
    user_data = wrf.get_user_data(interaction.user.id)
    if "liked_words" not in user_data:
        await interaction.response.send_message("You have no saved words.")
        return

    for word in user_data["liked_words"]:
        embed = wrf.create_word_embed(
            word["Vocab-expression"],
            word["Vocab-kana"],
            word["Vocab-meaning"],
            word["Vocab-pos"],
            word["Sentence-expression"],
            word["Sentence-kana"],
            word["Sentence-meaning"],
        )
        await interaction.response.send_message(embed=embed)


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    # Check if the reaction is on the bot's last sent message for this user
    if reaction.message.id == last_message_ids.get(user.id):
        if reaction.emoji == "❤️":
            await reaction.message.channel.send(f"{user.mention} Word Saved!")

            # Retrieve the user's data
            user_data = wrf.get_user_data(user.id)
            if "liked_words" not in user_data:
                user_data["liked_words"] = []

            # Add the liked word to the user's data
            user_data["liked_words"].append(
                {
                    "Vocab-expression": reaction.message.embeds[0].fields[0].value,
                    "Vocab-kana": reaction.message.embeds[0].fields[1].value,
                    "Vocab-meaning": reaction.message.embeds[0].fields[2].value,
                    "Vocab-pos": reaction.message.embeds[0].fields[6].value,
                    "Sentence-expression": reaction.message.embeds[0].fields[3].value,
                    "Sentence-kana": reaction.message.embeds[0].fields[4].value,
                    "Sentence-meaning": reaction.message.embeds[0].fields[5].value,
                }
            )

            # Save the updated user data
            wrf.save_user_data(user.id, user_data)

            # Clears the last message ID for the user, preventing users from reacting twice and triggering the function again
            last_message_ids[user.id] = None


# Keeps the bot alieve on Discord
@tasks.loop(seconds=60)
async def keep_alive_bot_ping():
    print("Sending keep-alive ping")
    try:
        # Send a ping to keep the connection alive
        latency = bot.ws.latency

    except Exception as e:
        print(f"Error sending ping: {e}")


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


ds.keep_alive()
bot.run(token)
