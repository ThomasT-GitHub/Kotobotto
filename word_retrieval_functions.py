import json
import random
import discord


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

    embed.add_field(name="Reading", value="Hiragana - " + reading, inline=False)

    embed.add_field(name="Translation", value=translation, inline=False)

    embed.add_field(
        name="Sentence",
        value="Original Sentence\n"
        + sentence
        + "\n\nKana Sentence\n"
        + kanaSentence
        + "\n\nTranslated Sentence\n"
        + sentenceMenaing,
        inline=False,
    )

    embed.add_field(name="Part of Speech", value=pos, inline=False)

    embed.set_footer(text="React to save to your saved words")

    return embed
