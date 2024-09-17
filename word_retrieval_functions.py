import datetime
import http.client
import json

import discord


async def get_random_word():
    conn = http.client.HTTPSConnection("jisho.org")
    conn.request("GET", "/api/v1/search/words?keyword=%23jlpt-n5")
    response = conn.getresponse()
    if response.status == 200:
        data = response.read()
        word_data = json.loads(data)
        return word_data["data"][0]
    else:
        return "Error: Could not fetch word"


def create_word_embed(word, reading, translation):
    embed = discord.Embed(title="Heres your word!", colour=0x940000)

    embed.set_author(name="Kotobotto")

    embed.add_field(name="Word", value=word, inline=False)

    embed.add_field(name="Reading", value="Hiragana - " + reading, inline=False)

    embed.add_field(name="Translation", value=translation, inline=False)

    embed.set_footer(text="React to save to your saved words")

    return embed
