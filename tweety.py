import requests
import json
import os
import time
from datetime import datetime
import environ

# ----------------------------------------------------------
# ⚙️ Load environment variables
# ----------------------------------------------------------
env = environ.Env()
env.read_env()

API_KEY = env("TWITTER_API_KEY")
BASE_URL = "https://api.twitterapi.io/twitter/user/last_tweets"


def fetch_all_tweets(username, max_tweets=None, delay=1):
    """
    Fetch tweets from a user.
    
    Args:
        username: Twitter username (without @)
        max_tweets: Maximum number of tweets to fetch (None = all)
        delay: Delay between API calls in seconds
    """
    tweets = []
    next_cursor = ""
    page = 0

    while True:
        page += 1
        print(f"\n📄 Fetching page {page}...")
        
        params = {
            "userName": username,
            "includeReplies": False
        }
        
        if next_cursor:
            params["cursor"] = next_cursor
            
        headers = {"X-API-Key": API_KEY}

        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
            print(f"📡 Status: {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            break

        # Handle non-200 responses
        if response.status_code == 429:
            print("⏳ Rate limited. Waiting 60 seconds...")
            time.sleep(60)
            continue
        elif response.status_code == 404:
            print(f"❌ User '@{username}' not found")
            break
        elif response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text[:500]}")
            break

        try:
            data = response.json()
        except Exception as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Response text: {response.text[:500]}")
            break

        # Check API status
        if data.get("status") == "error":
            print(f"❌ API Error: {data.get('message', 'Unknown error')}")
            break

        # Get tweets
        data_obj = data.get("data", {})
        new_tweets = data_obj.get("tweets", [])
        
        if not new_tweets:
            print("⚠️ No tweets in this batch")
            if page == 1:
                print("\n🔍 Full response for debugging:")
                print(json.dumps(data, indent=2)[:1000])
            break

        print(f"✅ Found {len(new_tweets)} tweets")
        tweets.extend(new_tweets)

        # Check if we've hit the max
        if max_tweets and len(tweets) >= max_tweets:
            print(f"🎯 Reached max tweets limit ({max_tweets})")
            tweets = tweets[:max_tweets]
            break

        # Check for next page
        has_next = data.get("has_next_page", False) or data_obj.get("has_next_page", False)
        if not has_next:
            print("✅ No more pages available")
            break
            
        next_cursor = data.get("next_cursor", "") or data_obj.get("next_cursor", "")
        if not next_cursor:
            print("⚠️ has_next_page=true but no cursor provided")
            break

        # Rate limiting
        if delay > 0:
            print(f"⏳ Waiting {delay}s before next request...")
            time.sleep(delay)

    return tweets


def save_tweets(username, tweets):
    """Save tweets to JSON file."""
    folder = "data"
    os.makedirs(folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"{username}_tweets_{timestamp}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved {len(tweets)} tweets to {path}")
    return path


def main(username, max_tweets=None):
    """
    Main function to fetch and save all tweets.
    
    Args:
        username: Twitter username without @
        max_tweets: Maximum tweets to fetch (None = all)
    """
    print(f"🐦 Fetching tweets for @{username}...")
    all_tweets = fetch_all_tweets(username, max_tweets=max_tweets)
    
    print(f"\n📊 Total tweets fetched: {len(all_tweets)}")

    if not all_tweets:
        print("\n❌ No tweets found!")
        return

    save_tweets(username, all_tweets)
    print(f"\n✅ Done! Fetched {len(all_tweets)} tweets from @{username}")


if __name__ == "__main__":
    # Fetch all tweets
    main("MoghaluGeorge")
    
    # Or limit to specific number for testing
    # main("CyrilRamaphosa", max_tweets=100)