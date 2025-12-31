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
HISTORY_FILE = "history.txt"

def get_roblox_games():
    url = "https://api.rolimons.com/games/v1/gamelist"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        # 1. Load history of IDs from previous run
        history = set()
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = set(line.strip() for line in f)

        print("Fetching data from Rolimon's...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        games_dict = data.get('games', {})
        filtered_games = []
        current_ids = []

        for place_id, info in games_dict.items():
            name, players = info[0], info[1]
            if players >= CCU_THRESHOLD:
                is_new = place_id not in history
                filtered_games.append({
                    "name": name,
                    "players": players,
                    "url": f"https://www.roblox.com/games/{place_id}",
                    "is_new": is_new
                })
                current_ids.append(place_id)

        # 2. Save current IDs for tomorrow
        with open(HISTORY_FILE, "w") as f:
            for pid in current_ids:
                f.write(f"{pid}\n")

        # 3. Sort and Format
        filtered_games.sort(key=lambda x: x['players'], reverse=True)
        
        email_lines = []
        for g in filtered_games:
            tag = "⭐ NEW!" if g['is_new'] else "🔥"
            email_lines.append(f"{tag} {g['name']}: {g['players']:,} players\n🔗 {g['url']}\n")
            
        return email_lines

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def send_email(game_list):
    msg = EmailMessage()
    msg['Subject'] = f"🚀 Roblox Tracker: {len(game_list)} Games @ 10k+ CCU"
    msg['From'] = SMTP_USER
    msg['To'] = TARGET_EMAIL
    
    body = "Games currently over the 10,000 player threshold:\n\n"
    body += "\n".join(game_list) if game_list else "No games meet the threshold."
    msg.set_content(body)

    with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_KEY)
        server.send_message(msg)
    print("✅ Email sent!")

if __name__ == "__main__":
    games = get_roblox_games()
    send_email(games)
