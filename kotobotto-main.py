import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import word_retrieval_functions as wrf  # Imports the word retrieval functions
import dummy_server as ds  # Imports the dummy server

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


# Keeps the bot alieve on Discord
@tasks.loop(seconds=60)
async def keep_alive_bot_ping():
    print("Sending keep-alive ping")
    try:
        # Send a ping to keep the connection alive
        latency = bot.ws.latency

    except Exception as e:
        print(f"Error sending ping: {e}")


ds.keep_alive()  # Keeps the bot alive on Azure
bot.run(token)  # Runs the bot
