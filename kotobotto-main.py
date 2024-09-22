import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import word_retrieval_functions as wrf  # Imports the word retrieval functions

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


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    # Check if the reaction is on the bot's last sent message for this user
    if reaction.message.id == last_message_ids.get(user.id):
        if reaction.emoji == "❤️":
            await reaction.message.channel.send(
                f"{user.mention} REALLY loves this word!"
            )

            # Clears the last message ID for the user, preventing users from reacting twice and triggering the function again
            last_message_ids[user.id] = None


bot.run(token)
