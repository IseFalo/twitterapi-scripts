import csv
import requests
from openai import OpenAI
import time
from datetime import datetime

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


def is_health_related_tweet(text: str) -> bool:
    """Return True if tweet is health-related using AI."""
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


def get_all_tweets_for_user(username, max_tweets=None):
    """
    Fetch ALL tweets for a user using pagination.
    
    Args:
        username: Twitter username
        max_tweets: Optional limit on total tweets (None = fetch all)
    
    Returns:
        List of all tweets
    """
    headers = {"X-API-Key": API_KEY}
    all_tweets = []
    cursor = ""  # Start with empty cursor for first page
    page = 1
    
    print(f"📥 Starting to fetch ALL tweets for @{username}...")
    
    while True:
        # Build params - only include cursor if it's not empty
        params = {"userName": username, "limit": 20}
        if cursor:
            params["cursor"] = cursor
        
        try:
            response = requests.get(BASE_URL, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Error fetching @{username} (page {page}): {response.status_code}")
                print(f"Response: {response.text}")
                break
            
            data = response.json()
            
            # Extract tweets
            tweets = data.get("tweets") or data.get("data", {}).get("tweets")
            if not tweets:
                print(f"✅ No more tweets found for @{username} (reached end)")
                break
            
            all_tweets.extend(tweets)
            print(f"   Page {page}: Fetched {len(tweets)} tweets (Total: {len(all_tweets)})")
            
            # Check if there's a next page
            has_next = data.get("has_next_page", False)
            next_cursor = data.get("next_cursor", "")
            
            if not has_next or not next_cursor:
                print(f"✅ Reached last page for @{username}")
                break
            
            # Check max_tweets limit
            if max_tweets and len(all_tweets) >= max_tweets:
                print(f"✅ Reached max_tweets limit ({max_tweets})")
                all_tweets = all_tweets[:max_tweets]
                break
            
            # Update cursor for next iteration
            cursor = next_cursor
            page += 1
            
            # Rate limiting delay
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Exception while fetching @{username}: {e}")
            break
    
    return all_tweets


if __name__ == "__main__":
    all_tweets_data = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 60)
    print("🚀 STARTING COMPLETE TWITTER HISTORY SCRAPER")
    print("=" * 60)
    
    for idx, username in enumerate(USERNAMES, 1):
        print(f"\n[{idx}/{len(USERNAMES)}] Processing @{username}")
        print("-" * 60)
        
        # Fetch ALL tweets for this user
        tweets = get_all_tweets_for_user(username)
        
        if not tweets:
            print(f"⚠️ No tweets collected for @{username}")
            continue
        
        print(f"\n🔍 Analyzing {len(tweets)} tweets for health content...")
        
        # Process each tweet
        for i, t in enumerate(tweets, start=1):
            created_at = t.get("createdAt") or "Unknown time"
            text = t.get("text", "").strip()
            
            if not text:
                continue
            
            # Check if health-related
            is_health = is_health_related_tweet(text)
            label = "Yes" if is_health else "No"
            
            if i % 10 == 0:  # Progress update every 10 tweets
                print(f"   Processed {i}/{len(tweets)} tweets...")
            
            all_tweets_data.append({
                "Username": username,
                "Created At": created_at,
                "Tweet Text": text,
                "Health Related": label
            })
        
        print(f"✅ Completed @{username}: {len(tweets)} tweets processed\n")
        
        # Delay between users to avoid rate limits
        if idx < len(USERNAMES):
            print("⏳ Waiting before next user...")
            time.sleep(3)
    
    # Save to CSV
    csv_filename = f"all_tweets_complete_{timestamp}.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["Username", "Created At", "Tweet Text", "Health Related"]
        )
        writer.writeheader()
        writer.writerows(all_tweets_data)
    
    print("\n" + "=" * 60)
    print("✅ SCRAPING COMPLETE!")
    print(f"📊 Total tweets collected: {len(all_tweets_data)}")
    print(f"💾 Saved to: {csv_filename}")
    print("=" * 60)