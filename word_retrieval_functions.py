import json
import requests
import base64
import random
import discord
from dotenv import load_dotenv
import os

# Load the environment variables
load_dotenv()

# Github Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Github Repository Information
GITHUB_USERNAME = "ThomasT-GitHub"
REPO_NAME = "Kotobotto"
# The path to the file in the repository
FILE_PATH_TEMPLATE = "data/user_data_{user_id}.json"


def get_random_word():
    with open("vocabulary-list.json", "r", encoding="utf-8") as file:
        vocab_list = json.load(file)
    return random.choice(vocab_list)


def create_word_embed(
    word, reading, translation, pos, sentence, kanaSentence, sentenceMenaing
):
    embed = discord.Embed(title="Heres your word!", colour=0x940000)

    embed.set_author(name="Kotobotto")

    embed.add_field(name="Word", value=word, inline=False)

    embed.add_field(name="Reading", value=reading, inline=False)

    embed.add_field(name="Translation", value=translation, inline=False)

    embed.add_field(
        name="Sentence",
        value=sentence,
        inline=False,
    )

    embed.add_field(
        name="Kana Sentence",
        value=kanaSentence,
        inline=False,
    )

    embed.add_field(
        name="Sentence Meaning",
        value=sentenceMenaing,
        inline=False,
    )

    embed.add_field(name="Part of Speech", value=pos, inline=False)

    embed.set_footer(text="React to save to your saved words")

    return embed


def save_user_data(user_id, data, message="Update user data"):
    file_path = FILE_PATH_TEMPLATE.format(user_id=user_id)
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{file_path}?ref=user-data"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get the current file content to get the SHA
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
    else:
        sha = None

    # Encode the data to base64
    encoded_data = base64.b64encode(json.dumps(data).encode()).decode()

    payload = {
        "message": message,
        "content": encoded_data,
        "sha": sha,
        "branch": "user-data",
    }

    response = requests.put(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 201 or response.status_code == 200:
        print("File updated successfully")
    else:
        print(f"Failed to update file: {response.json()}")


def get_user_data(user_id):
    file_path = FILE_PATH_TEMPLATE.format(user_id=user_id)
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{file_path}?ref=user-data"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded_data = base64.b64decode(content).decode()
        return json.loads(decoded_data)
    else:
        print(f"User does not exist!: {response.json()}")
        return {}
