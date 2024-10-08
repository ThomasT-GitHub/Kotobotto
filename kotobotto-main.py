import asyncio
import datetime
import os
import random
from typing import Literal, Optional
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import word_retrieval_functions as wrf
import dummy_server as ds

# load_dotenv() # LEFT OUT FOR PRODUCTION

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
    await bot.tree.sync()  # Syncs the commands


# Dictionary to store roll data for each user
user_roll_data = {}


# Command to set target count
@bot.tree.command(name="st", description="Set the target count for rolling words")
@app_commands.describe(target_count="The target count for rolling words")
async def set_target(interaction: discord.Interaction, target_count: int):
    user_id = interaction.user.id

    # Check if the user has roll data, if not initialize it
    if user_id not in user_roll_data:
        user_roll_data[user_id] = {
            "last_roll_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "roll_count": 0,
            "target_count": target_count,
        }
    else:
        user_roll_data[user_id]["target_count"] = target_count

    await interaction.response.send_message(f"Target count set to {target_count}.")


# Command to roll for a word
@bot.tree.command(name="rw", description="Roll for a word!")
async def roll_word(interaction: discord.Interaction):
    user_id = interaction.user.id
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Get user roll data
    if user_id not in user_roll_data:
        user_roll_data[user_id] = {
            "last_roll_date": current_date,
            "roll_count": 1,
            "target_count": 10,
        }

    last_roll_date = user_roll_data[user_id]["last_roll_date"]
    roll_count = user_roll_data[user_id]["roll_count"]

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

    # Check if the user has rolled words today
    if last_roll_date == current_date:
        user_roll_data[user_id]["roll_count"] = roll_count + 1
        if (
            user_roll_data[user_id]["roll_count"]
            == user_roll_data[user_id]["target_count"]
        ):
            await interaction.followup.send(
                f"Congratulations! You've reached your target of {user_roll_data[user_id]['target_count']} words today!"
            )

    # Store the message ID in the dictionary with the user ID as the key
    last_message_ids[interaction.user.id] = message.id


# Command to show the user's saved words
@bot.tree.command(name="sw", description="Show saved words")
async def list_saved_words(interaction: discord.Interaction):
    user_data = wrf.get_user_data(interaction.user.id)
    if "liked_words" not in user_data or not user_data["liked_words"]:
        await interaction.response.send_message("You have no saved words.")
        return

    # Acknowledge the interaction
    await interaction.response.defer()

    # Array to hold embeds
    embeds = []

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
        embeds.append(embed)

    # Send the embeds in chunks of 10
    for i in range(0, len(embeds), 10):
        await interaction.followup.send(embeds=embeds[i : i + 10])


# Command to delete a saved word
@bot.tree.command(name="dw", description="Delete a saved word")
@app_commands.describe(word="The word to delete", delete_all="Delete all saved words")
async def delete_saved_word(
    interaction: discord.Interaction, word: str, delete_all: Optional[bool] = False
):
    user_data = wrf.get_user_data(interaction.user.id)
    if "liked_words" not in user_data:
        await interaction.response.send_message("You have no saved words.")
        return

    # Acknowledge the interaction
    await interaction.response.defer()

    # Check if the user wants to delete all saved words; if so, clear the list
    if delete_all:
        # Delete all saved words by clearing the list and saving the updated data
        user_data["liked_words"] = []
        wrf.save_user_data(interaction.user.id, user_data)
        await interaction.followup.send("Deleted all saved words.")
        return

    # Check if the word is in the user's saved words
    for saved_word in user_data["liked_words"]:
        if saved_word["Vocab-expression"] == word:
            user_data["liked_words"].remove(saved_word)
            wrf.save_user_data(interaction.user.id, user_data)
            await interaction.followup.send(f"Deleted {word}.")
            return

    await interaction.followup.send(f"{word} not found in your saved words.")


# Command to quiz the user on saved words (User can choose the number of questions, default is 10)
@bot.tree.command(name="qw", description="Quiz on saved words")
@app_commands.describe(
    number_of_questions="The number of questions to ask (default is 10)"
)
async def quiz_saved_words(
    interaction: discord.Interaction, number_of_questions: Optional[int] = 10
):
    # Retrieve the user's saved words data
    user_data = wrf.get_user_data(interaction.user.id)
    if "liked_words" not in user_data:
        await interaction.response.send_message("You have no saved words.")
        return

    # Check if there are enough saved words to quiz the user
    if len(user_data["liked_words"]) < number_of_questions:
        await interaction.response.send_message(
            "You don't have enough saved words to take the quiz of this length."
        )
        return

    # Acknowledge the interaction
    await interaction.response.defer()

    # Stores visited words so we don't repeat questions
    visited_words = []
    correct_count = 0
    question_results = []

    # Runs the quiz for number_of_questions times
    for i in range(number_of_questions):
        # Select a random word from the user's saved words
        word = random.choice(user_data["liked_words"])
        # Ensure the word hasn't been used in this quiz session
        while word in visited_words:
            word = random.choice(user_data["liked_words"])

        # Add the word to visited words to avoid repetition
        visited_words.append(word)

        # Send the quiz question to the user
        await interaction.followup.send(
            embed=wrf.create_quiz_embed(word["Vocab-expression"], i + 1)
        )

        # Define a check function to validate the user's response
        def check(m):
            return (
                m.author == interaction.user
                and (m.content.startswith("!respond") or m.content == "!quit")
                and m.channel == interaction.channel
            )

        try:
            # Wait for the user's response with a timeout of 60 seconds
            response = await bot.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            # If the user takes too long to respond, notify them and end the quiz
            await interaction.followup.send("You took too long to respond!")
            break

        # Check if the user wants to quit the quiz
        if response.content == "!quit":
            await interaction.followup.send("Quiz ended by user.")
            break

        # Extract the user's response from the message
        user_response = response.content[len("!respond ") :].strip()
        # Get the correct answers for the word
        correct_answers = [
            meaning.strip().lower() for meaning in word["Vocab-meaning"].split(", ")
        ]

        # Check if the user's response is correct
        if user_response.lower() in correct_answers:
            await interaction.followup.send("Correct!")
            correct_count += 1
            question_results.append((word["Vocab-expression"], True))
        else:
            # If the response is incorrect, provide the correct answers
            await interaction.followup.send(
                f"Incorrect! The correct answer(s) were {', '.join(word['Vocab-meaning'].split(','))}."
            )
            question_results.append((word["Vocab-expression"], False))

    # Calculate the percentage of correct answers
    total_questions = len(visited_words)
    percent_correct = (correct_count / total_questions) * 100

    # Create a list of question results with check or X emoji
    results_list = [
        f"{'✅' if result[1] else '❌'} {result[0]}" for result in question_results
    ]

    # Send the quiz stats to the user
    embed = discord.Embed(
        title="Quiz Results",
        description=(
            f"You answered {correct_count} out of {total_questions} questions correctly!\n"
            f"Percentage: {int(percent_correct)}% ({correct_count}/{total_questions})\n\n"
            "Questions:\n" + "\n".join(results_list)
        ),
        color=0xF5CC00,
    )
    await interaction.followup.send(embed=embed)


# Help command to explain to the user how to use the bot
@bot.tree.command(name="help", description="Show help")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Kotobotto Help",
        description="Here are the commands you can use with Kotobotto:",
        color=0x00FF00,
    )
    embed.add_field(name="/rw", value="Roll for a word.", inline=False)
    embed.add_field(name="/sw", value="Show your saved words.", inline=False)
    embed.add_field(name="/dw <word>", value="Delete a saved word.", inline=False)
    embed.add_field(
        name="/dw <word> --delete_all", value="Delete all saved words.", inline=False
    )
    embed.add_field(
        name="/qw <number_of_questions>",
        value="Quiz yourself on saved words.",
        inline=False,
    )
    embed.add_field(
        name="/st <target_count>",
        value="Set the target count for rolling words.",
        inline=False,
    )
    embed.set_footer(text="Kotobotto - Your friendly word bot!")

    await interaction.response.send_message(embed=embed)


# Save the word to the user's saved words
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

            # Check if the word is already in the user's liked words
            word_to_add = {
                "Vocab-expression": reaction.message.embeds[0].fields[0].value,
                "Vocab-kana": reaction.message.embeds[0].fields[1].value,
                "Vocab-meaning": reaction.message.embeds[0].fields[2].value,
                "Vocab-pos": reaction.message.embeds[0].fields[6].value,
                "Sentence-expression": reaction.message.embeds[0].fields[3].value,
                "Sentence-kana": reaction.message.embeds[0].fields[4].value,
                "Sentence-meaning": reaction.message.embeds[0].fields[5].value,
            }

            if word_to_add not in user_data["liked_words"]:
                user_data["liked_words"].append(word_to_add)

                # Save the updated user data
                wrf.save_user_data(user.id, user_data)

            else:
                await reaction.message.channel.send(
                    f"{user.mention} You already saved this word!"
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
