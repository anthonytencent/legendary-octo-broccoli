import requests
import smtplib
import os
import sys
import json
from email.message import EmailMessage

# Configuration
SMTP_USER = os.getenv("BREVO_USER")
SMTP_KEY = os.getenv("BREVO_KEY")
TARGET_EMAIL = os.getenv("TARGET_EMAIL")
CCU_THRESHOLD = 10000
HISTORY_FILE = "history.json"

def get_roblox_games():
    url = "https://api.rolimons.com/games/v1/gamelist"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        # 1. Load historical counts from yesterday
        history = {}
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)

        print("Fetching current data...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        games_dict = data.get('games', {})
        filtered_games = []
        new_history = {}

        # 2. Process ALL games to save history, but filter for the email
        for place_id, info in games_dict.items():
            name, current_players = info[0], info[1]
            new_history[place_id] = current_players # Save for tomorrow
            
            if current_players >= CCU_THRESHOLD:
                last_players = history.get(place_id)
                
                if last_players is None:
                    change_text = "⭐ NEW!"
                else:
                    change = current_players - last_players
                    # Format as +5,000 or -1,200
                    change_text = f"{change:+,}" 

                filtered_games.append({
                    "name": name,
                    "players": current_players,
                    "change": change_text,
                    "url": f"https://www.roblox.com/games/{place_id}"
                })

        # 3. Save current counts for tomorrow's comparison
        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        # 4. Sort by players (Highest first)
        filtered_games.sort(key=lambda x: x['players'], reverse=True)
        
        email_lines = []
        for g in filtered_games:
            email_lines.append(f"🎮 **{g['name']}**\n👥 {g['players']:,} players ({g['change']})\n🔗 {g['url']}\n")
            
        return email_lines

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def send_email(game_list):
    msg = EmailMessage()
    msg['Subject'] = f"📈 Roblox Tracker: {len(game_list)} Games @ 10k+ CCU"
    msg['From'] = f"Roblox Monitor <{SMTP_USER}>"
    msg['To'] = TARGET_EMAIL
    
    body = "Today's high-traffic games and their 24h change:\n\n"
    body += "\n".join(game_list) if game_list else "No games hit the threshold."
    msg.set_content(body)

    with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_KEY)
        server.send_message(msg)
    print("✅ Report sent!")

if __name__ == "__main__":
    games = get_roblox_games()
    send_email(games)
