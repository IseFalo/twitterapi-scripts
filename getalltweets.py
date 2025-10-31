import requests
import json
import os
import time
from datetime import datetime
from openai import OpenAI
import environ

# ----------------------------------------------------------
# ⚙️ Load environment variables
# ----------------------------------------------------------
env = environ.Env()
env.read_env()

API_KEY = env("TWITTER_API_KEY")
OPENAI_API_KEY = env("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
BASE_URL = "https://api.twitterapi.io/twitter/user/last_tweets"


# === 1. FETCH ALL TWEETS ===
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
        
        # Add cursor only if we have one
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

        # Get tweets - they're nested in data.tweets
        data_obj = data.get("data", {})
        new_tweets = data_obj.get("tweets", [])
        
        if not new_tweets:
            print("⚠️ No tweets in this batch")
            # Check if this is truly empty or an error
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


# === 2. AI HEALTH CLASSIFIER ===
def is_health_related(text):
    """Check if tweet is health-related using OpenAI API."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You classify if text is about health, medicine, diseases, wellbeing, medical research, healthcare, mental health, fitness, or nutrition. Reply only 'True' or 'False'."
                },
                {
                    "role": "user", 
                    "content": f"Is this health-related?\n\n{text}"
                }
            ],
            max_tokens=10,
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip().lower()
        return "true" in answer
        
    except Exception as e:
        print(f"⚠️ OpenAI error: {e}")
        return False


# === 3. SAVE HEALTH-RELATED TWEETS TO JSON ===
def save_health_tweets(username, tweets):
    """Save filtered tweets to JSON file."""
    folder = "data"
    os.makedirs(folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"{username}_health_tweets_{timestamp}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved {len(tweets)} health-related tweets to {path}")
    return path


# === 4. TEST API CONNECTION ===
def test_api_connection(username):
    """Test if the API is working correctly."""
    print(f"\n🔧 Testing API connection for @{username}...")
    
    params = {"userName": username, "includeReplies": False}
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            data_obj = data.get("data", {})
            tweet_count = len(data_obj.get("tweets", []))
            print(f"✅ API working! Found {tweet_count} tweets in first batch")
            
            if tweet_count > 0:
                print("\n📋 Sample tweet:")
                sample = data_obj["tweets"][0]
                print(f"  ID: {sample.get('id')}")
                print(f"  Date: {sample.get('createdAt')}")
                print(f"  Text: {sample.get('text', '')[:100]}...")
                return True
            else:
                print("⚠️ API returned 0 tweets. Possible reasons:")
                print("  - Account has no tweets")
                print("  - Account is private")
                print("  - Username is incorrect")
                print("\nFull response:")
                print(json.dumps(data, indent=2))
                return False
        else:
            print(f"❌ API error: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


# === 5. MAIN LOGIC ===
def main(username, max_tweets=None, test_mode=False):
    """
    Main function to fetch and filter health tweets.
    
    Args:
        username: Twitter username without @
        max_tweets: Maximum tweets to fetch (None = all)
        test_mode: If True, only test API connection
    """
    
    if test_mode:
        test_api_connection(username)
        return
    
    print(f"🐦 Fetching tweets for @{username}...")
    all_tweets = fetch_all_tweets(username, max_tweets=max_tweets)
    
    print(f"\n📊 Total tweets fetched: {len(all_tweets)}")

    if not all_tweets:
        print("\n❌ No tweets found!")
        print("💡 Try running in test mode: main('melindagates', test_mode=True)")
        return

    # Analyze for health content
    health_tweets = []
    print(f"\n🏥 Analyzing {len(all_tweets)} tweets for health content...")
    
    for i, tweet in enumerate(all_tweets, 1):
        text = tweet.get("text", "")
        
        if not text:
            continue
            
        print(f"🔄 [{i}/{len(all_tweets)}] Analyzing...", end="\r")
        
        if is_health_related(text):
            health_tweets.append({
                "username": username,
                "tweet_id": tweet.get("id"),
                "url": tweet.get("url"),
                "created_at": tweet.get("createdAt"),
                "text": text,
                "likes": tweet.get("likeCount", 0),
                "retweets": tweet.get("retweetCount", 0),
                "replies": tweet.get("replyCount", 0),
                "author": tweet.get("author", {}).get("name")
            })
            print(f"✅ [{i}/{len(all_tweets)}] Health-related! Total found: {len(health_tweets)}")

    print(f"\n\n🏥 Found {len(health_tweets)} health-related tweets out of {len(all_tweets)} total")
    
    if health_tweets:
        save_health_tweets(username, health_tweets)
    else:
        print("💡 No health-related tweets found")


# === RUN ===
if __name__ == "__main__":
    # Test API connection first
    # main("melindagates", test_mode=True)
    
    # Then run full scrape (fetch all tweets)
    main("CyrilRamaphosa")
    
    # Or limit to first 100 tweets for testing
    # main("melindagates", max_tweets=100)