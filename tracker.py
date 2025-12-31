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
        # 1. Load historical counts
        history = {}
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)

        print("Fetching current data...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        games_dict = data.get('games', {})
        all_games_data = []
        new_history = {}

        # 2. Process all data
        for place_id, info in games_dict.items():
            name, current_players = info[0], info[1]
            new_history[place_id] = current_players # Save for tomorrow
            
            last_players = history.get(place_id)
            numeric_change = 0
            
            if last_players is None:
                change_text = "⭐ NEW!"
                numeric_change = 0
            else:
                numeric_change = current_players - last_players
                change_text = f"{numeric_change:+,}"

            if current_players >= CCU_THRESHOLD:
                all_games_data.append({
                    "name": name,
                    "players": current_players,
                    "change": change_text,
                    "numeric_change": numeric_change,
                    "url": f"https://www.roblox.com/games/{place_id}"
                })

        # 3. Save current counts for tomorrow
        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        # 4. Identify Top 3 Winners (Highest Growth)
        # We only count games that were NOT "New" to get accurate growth
        winners = [g for g in all_games_data if g["change"] != "⭐ NEW!"]
        winners.sort(key=lambda x: x['numeric_change'], reverse=True)
        top_3 = winners[:3]

        # 5. Sort Main List by Player Count
        all_games_data.sort(key=lambda x: x['players'], reverse=True)
        
        # 6. Build Email Body
        email_body = ""
        
        if top_3:
            email_body += "🏆 --- TOP 3 GROWTH WINNERS ---\n"
            for i, w in enumerate(top_3, 1):
                email_body += f"{i}. {w['name']} (+{w['numeric_change']:,} players)\n"
            email_body += "-------------------------------\n\n"

        email_body += "📋 ALL GAMES OVER 10K CCU:\n\n"
        for g in all_games_data:
            email_body += f"🎮 {g['name']}\n👥 {g['players']:,} players ({g['change']})\n🔗 {g['url']}\n\n"
            
        return email_body

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def send_email(content):
    if not content:
        content = "No games hit the 10,000 player threshold today."

    msg = EmailMessage()
    msg['Subject'] = f"📈 Roblox Tracker: Daily CCU Report"
    msg['From'] = f"Roblox Monitor <{SMTP_USER}>"
    msg['To'] = TARGET_EMAIL
    msg.set_content(content)

    print("Connecting to Brevo...")
    with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_KEY)
        server.send_message(msg)
    print("✅ Email delivered.")

if __name__ == "__main__":
    report_content = get_roblox_games()
    send_email(report_content)
