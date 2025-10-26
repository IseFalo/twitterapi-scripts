import csv
import requests
from openai import OpenAI
import time
import environ

# ----------------------------------------------------------
# ⚙️ Load environment variables
# ----------------------------------------------------------
env = environ.Env()
env.read_env()

API_KEY = env("TWITTER_API_KEY")
OPENAI_API_KEY = env("OPENAI_API_KEY")
BASE_URL = "https://api.twitterapi.io/twitter/user/last_tweets"

# 🧠 OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# 👥 List of usernames to process
USERNAMES = [
    "melindagates",
    "officialABAT",
    "EmmanuelMacron",
    "CapitaineIb226",
    "CyrilRamaphosa",
    "SassouNGuesso_",
    "realDonaldTrump",
    "MoetiTshidi",
    "Foster_Mohale",
    "fredvalletoux",
    "GabrielAttal",
    "MokokiG",
    "GSK",
    "JoeBiden",
    "DrManaouda",
    "muhammadpate",
    "SonkoOfficiel",
    "DrTedros",
    "DrTunjiAlausa",
    "WilliamsRuto",
    "KagutaMuseveni",
]

# ----------------------------------------------------------
# 🧠 Check if tweet is health-related (AI only)
# ----------------------------------------------------------
def is_health_related_tweet(text: str) -> bool:
    """Return True if the tweet is about health, disease, or public health topics (AI-only version)."""
    if len(text.split()) < 5:
        return False

    prompt = f"""
    You are analyzing tweets to determine if they are **health-related**.

    Mark as "yes" ONLY if the tweet is about:
    - health, healthcare, or hospitals
    - diseases, infections, or outbreaks
    - disease prevention, vaccination, or medical topics
    - public health updates, advice, or statements

    Respond strictly with "yes" or "no".

    Tweet:
    "{text}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception as e:
        print(f"⚠️ AI health check failed: {e}")
        return False


# ----------------------------------------------------------
# 🐦 Fetch latest tweets for a username
# ----------------------------------------------------------
def get_latest_tweets(username, count=20):
    headers = {"X-API-Key": API_KEY}
    params = {"userName": username, "limit": count}
    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching @{username} ({response.status_code}): {response.text}")
        return []

    data = response.json()
    tweets = data.get("tweets") or data.get("data", {}).get("tweets")
    if not tweets:
        print(f"No tweets found for @{username}")
        return []

    return tweets[:count]


# ----------------------------------------------------------
# 🚀 Main program
# ----------------------------------------------------------
if __name__ == "__main__":
    all_tweets = []

    for username in USERNAMES:
        print(f"\n==============================")
        print(f"📥 Fetching tweets for @{username}")
        print(f"==============================")

        tweets = get_latest_tweets(username)
        print(f"✅ Found {len(tweets)} tweets from @{username}\n")

        for i, t in enumerate(tweets, start=1):
            created_at = t.get("createdAt") or "Unknown time"
            text = t.get("text", "").strip()
            if not text:
                continue

            is_health = is_health_related_tweet(text)
            label = "Yes" if is_health else "No"

            print(f"{i}. ({created_at}) → Health related: {label}")
            print(f"{text}\n")

            all_tweets.append({
                "Username": username,
                "Created At": created_at,
                "Tweet Text": text,
                "Health Related": label
            })

        # ⏳ Optional delay to avoid hitting API limits
        time.sleep(2)

    # ----------------------------------------------------------
    # 💾 Save all tweets to one CSV
    # ----------------------------------------------------------
    csv_filename = "all_accounts_tweets.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Username", "Created At", "Tweet Text", "Health Related"])
        writer.writeheader()
        writer.writerows(all_tweets)

    print(f"\n✅ Done! Saved {len(all_tweets)} tweets to '{csv_filename}'.")
