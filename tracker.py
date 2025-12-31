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
    # Using Rolimon's API because the official Roblox 'list' API was deleted.
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
            print("API responded but success was False.")
            return []

        games_dict = data.get('games', {})
        print(f"Scanning {len(games_dict)} games for {CCU_THRESHOLD}+ players...")
        
        trending = []
        # Rolimon's format: "PlaceID": ["Name", PlayerCount, "IconURL"]
        for place_id, info in games_dict.items():
            name = info[0]
            players = info[1]
            
            if players >= CCU_THRESHOLD:
                game_url = f"https://www.roblox.com/games/{place_id}"
                trending.append(f"🔥 {name}: {players:,} players\n🔗 {game_url}\n")
        
        # Sort by player count (highest first)
        trending.sort(key=lambda x: int(x.split(': ')[1].split(' ')[0].replace(',', '')), reverse=True)
        return trending

    except Exception as e:
        print(f"ERROR: Could not get game data: {e}")
        sys.exit(1)

def send_email(game_list):
    if not SMTP_USER or not SMTP_KEY:
        print("ERROR: Brevo credentials missing!")
        sys.exit(1)

    try:
        msg = EmailMessage()
        msg['Subject'] = f"🚀 Roblox Tracker: {len(game_list)} Games over 10k CCU"
        msg['From'] = SMTP_USER
        msg['To'] = TARGET_EMAIL
        
        body = "Here are the top Roblox games currently over the 10,000 player threshold:\n\n"
        if game_list:
            body += "\n".join(game_list)
        else:
            body += "No games currently meet the threshold."
            
        msg.set_content(body)

        print(f"Sending email via Brevo...")
        with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_KEY)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"ERROR sending email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    games = get_roblox_games()
    send_email(games)
