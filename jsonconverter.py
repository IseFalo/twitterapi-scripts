import json
import csv

def convert_json_to_csv(json_file_path, csv_file_path):
    """
    Convert JSON file with tweet data to CSV format.
    
    Args:
        json_file_path: Path to input JSON file
        csv_file_path: Path to output CSV file
    """
    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Open CSV file for writing
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['username', 'tweet_id', 'url', 'created_at', 'text', 'author'])
        
        # Write data rows
        for tweet in data:
            username = tweet.get('author', {}).get('userName', '')
            tweet_id = tweet.get('id', '')
            url = tweet.get('url', '')
            created_at = tweet.get('createdAt', '')
            text = tweet.get('text', '')
            author = tweet.get('author', {}).get('name', '')
            
            writer.writerow([username, tweet_id, url, created_at, text, author])
    
    print(f"Successfully converted {json_file_path} to {csv_file_path}")

if __name__ == "__main__":
    # Replace these with your actual file paths
    input_json = "data/CCSoludo_tweets_20251103_120004.json"
    output_csv = "CCSoludo_tweets.csv"
    
    convert_json_to_csv(input_json, output_csv)