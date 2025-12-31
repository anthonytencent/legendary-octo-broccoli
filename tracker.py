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
    # We add a User-Agent so Roblox doesn't block the script
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = "https://games.roblox.com/v1/games/list?model.maxRows=100&model.sortToken=TopPlayingNow"
    
    try:
        print("Fetching data from Roblox...")
        response = requests.get(url, headers=headers)
        response.raise_for_status() # This will trigger an error if Roblox blocks us
        
        data = response.json()
        games = data.get('games', [])
        
        print(f"Found {len(games)} games total. Filtering for {CCU_THRESHOLD}+ CCU...")
        
        trending = []
        for g in games:
            if g.get('playerCount', 0) >= CCU_THRESHOLD:
                # Adding a link to the game
                game_url = f"https://www.roblox.com/games/{g['universeId']}"
                trending.append(f"🔥 {g['name']}: {g['playerCount']:,} players\n🔗 Link: {game_url}\n")
        
        return trending
    except Exception as e:
        print(f"ERROR fetching Roblox data: {e}")
        sys.exit(1) # This tells GitHub the script failed

def send_email(game_list):
    if not SMTP_USER or not SMTP_KEY:
        print("ERROR: Brevo credentials missing in Secrets!")
        sys.exit(1)

    try:
        msg = EmailMessage()
        msg['Subject'] = f"📅 Roblox Tracker: {len(game_list)} Games @ 10k+ CCU"
        # IMPORTANT: The 'From' must be the email you used for Brevo
        msg['From'] = SMTP_USER 
        msg['To'] = TARGET_EMAIL
        
        body = "Today's high-traffic Roblox games:\n\n"
        body += "\n".join(game_list) if game_list else "No games hit the 10k threshold today."
        msg.set_content(body)

        print(f"Connecting to Brevo as {SMTP_USER}...")
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
