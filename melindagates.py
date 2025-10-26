import csv
import requests
from openai import OpenAI
import environ

# ----------------------------------------------------------
# ⚙️ Load environment variables
# ----------------------------------------------------------
env = environ.Env()
env.read_env()

API_KEY = env("TWITTER_API_KEY")
OPENAI_API_KEY = env("OPENAI_API_KEY")
USERNAME = "melindagates"
BASE_URL = "https://api.twitterapi.io/twitter/user/last_tweets"

client = OpenAI(api_key=OPENAI_API_KEY)


# ----------------------------------------------------------
# 🧠 Check if tweet is health-related
# ----------------------------------------------------------
def is_health_related_tweet(text: str) -> bool:
    """Return True if the tweet is about health, disease, or public health topics."""

    # Quick keyword-based check first
    keywords = [
        "covid", "coronavirus", "disease", "virus", "infection", "health", "outbreak",
        "epidemiology", "prevention", "malaria", "cholera", "lassa", "ebola",
        "vaccine", "immunization", "public health", "hospital", "doctor",
        "ncdc", "who", "healthcare", "disease control"
    ]
    if any(k in text.lower() for k in keywords):
        return True

    # Skip short or generic tweets
    if len(text.split()) < 5:
        return False

    # AI-powered fallback check
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
# 🐦 Fetch latest tweets
# ----------------------------------------------------------
def get_latest_tweets(username, count=20):
    headers = {"X-API-Key": API_KEY}
    params = {"userName": username, "limit": count}

    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    data = response.json()
    tweets = data.get("tweets") or data.get("data", {}).get("tweets")
    if not tweets:
        print("Unexpected response format. Keys available:", data.keys())
        return []

    return tweets[:count]


# ----------------------------------------------------------
# 🚀 Main program
# ----------------------------------------------------------
if __name__ == "__main__":
    tweets = get_latest_tweets(USERNAME)
    print(f"\n✅ Found {len(tweets)} tweets from @{USERNAME}\n")

    all_tweets = []

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
            "Index": i,
            "Created At": created_at,
            "Tweet Text": text,
            "Health Related": label
        })

    # ----------------------------------------------------------
    # 💾 Save to CSV
    # ----------------------------------------------------------
    csv_filename = f"{USERNAME}_tweets.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Index", "Created At", "Tweet Text", "Health Related"])
        writer.writeheader()
        writer.writerows(all_tweets)

    print(f"\n✅ Done! Saved {len(all_tweets)} tweets to '{csv_filename}'.")
