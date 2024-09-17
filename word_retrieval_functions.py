import http.client
import json


async def get_random_word():
    conn = http.client.HTTPSConnection("jisho.org")
    conn.request("GET", "/api/v1/search/words?keyword=%23jlpt-n5")
    response = conn.getresponse()
    if response.status == 200:
        data = response.read()
        word_data = json.loads(data)
        return word_data["data"][0]["slug"]
    else:
        return "Error: Could not fetch word"
