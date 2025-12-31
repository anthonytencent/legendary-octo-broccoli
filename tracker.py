import requests
import smtplib
import os
import sys
from email.message import EmailMessage

# Configuration from GitHub Secrets
SMTP_USER = os.getenv("BREVO_USER")
SMTP_KEY = os.getenv("BREVO_KEY")
TARGET_EMAIL = os.getenv("TARGET_EMAIL")
CCU_THRESHOLD = 10000

def get_roblox_games():
    url = "https://api.rolimons.com/games/v1/gamelist"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    
    try:
        print("Fetching data from Rolimon's API...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('success'):
            print("API error: Success was False")
            return []

        games_dict = data.get('games', {})
        print(f"Scanning {len(games_dict)} games...")
        
        # 1. Collect structured data first
        filtered_games = []
        for place_id, info in games_dict.items():
            name = info[0]
            players = info[1]
            
            if players >= CCU_THRESHOLD:
                filtered_games.append({
                    "name": name,
                    "players": players,
                    "url": f"https://www.roblox.com/games/{place_id}"
                })
        
        # 2. Sort numerically by player count (Highest first)
        filtered_games.sort(key=lambda x: x['players'], reverse=True)
        
        # 3. Format into strings for the email
        trending_strings = []
        for g in filtered_games:
            trending_strings.append(f"🔥 {g['name']}: {g['players']:,} players\n🔗 {g['url']}\n")
            
        return trending_strings

    except Exception as e:
        print(f"ERROR: Could not process data: {e}")
        sys.exit(1)

def send_email(game_list):
    if not SMTP_USER or not SMTP_KEY:
        print("ERROR: Secrets are missing!")
        sys.exit(1)

    try:
        msg = EmailMessage()
        msg['Subject'] = f"🚀 Roblox Tracker: {len(game_list)} Games over 10k CCU"
        msg['From'] = SMTP_USER
        msg['To'] = TARGET_EMAIL
        
        body = "Top Roblox games currently over the 10,000 player threshold:\n\n"
        body += "\n".join(game_list) if game_list else "No games meet the threshold today."
        msg.set_content(body)

        print(f"Sending email via Brevo to {TARGET_EMAIL}...")
        with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_KEY)
            server.send_message(msg)
        print("✅ Success! Check your inbox.")
    except Exception as e:
        print(f"ERROR sending email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    games = get_roblox_games()
    send_email(games)
