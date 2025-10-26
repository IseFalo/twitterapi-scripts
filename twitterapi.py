import requests

import environ

# ----------------------------------------------------------
# ⚙️ Load environment variables
# ----------------------------------------------------------
env = environ.Env()
env.read_env()

API_KEY = env("TWITTER_API_KEY")
USERNAME = "officialABAT"
BASE_URL = "https://api.twitterapi.io/twitter/user/last_tweets"

def get_latest_tweets(username, count=20):
    headers = {"X-API-Key": API_KEY}
    params = {"userName": username, "limit": count}

    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    data = response.json()

    # ✅ tweets may be nested under "data"
    tweets = data.get("tweets") or data.get("data", {}).get("tweets")
    if not tweets:
        print("Unexpected response format. Keys available:", data.keys())
        return []

    return tweets[:count]


if __name__ == "__main__":
    tweets = get_latest_tweets(USERNAME)
    print(f"\n✅ Last {len(tweets)} tweets from @{USERNAME}:\n")

    for i, t in enumerate(tweets, start=1):
        created_at = t.get("createdAt") or "Unknown time"
        text = t.get("text", "").strip()

        print(f"{i}. ({created_at})")
        print(f"{text}\n")
