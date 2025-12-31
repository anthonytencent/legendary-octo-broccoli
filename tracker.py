import requests
import smtplib
import os
from email.message import EmailMessage

# Configuration from GitHub Secrets
SMTP_USER = os.getenv("BREVO_USER")
SMTP_KEY = os.getenv("BREVO_KEY")
TARGET_EMAIL = os.getenv("TARGET_EMAIL")
CCU_THRESHOLD = 10000

def get_roblox_games():
    # This hits the 'Top Playing Now' sort to find popular games
    url = "https://games.roblox.com/v1/games/list?model.maxRows=100&model.sortToken=TopPlayingNow"
    try:
        response = requests.get(url).json()
        games = response.get('games', [])
        
        # Filter games that are over our player threshold
        trending = []
        for g in games:
            if g['playerCount'] >= CCU_THRESHOLD:
                trending.append(f"🔥 {g['name']}: {g['playerCount']:,} players")
        return trending
    except Exception as e:
        return [f"Error fetching data: {e}"]

def send_email(game_list):
    msg = EmailMessage()
    msg['Subject'] = f"📅 Roblox Tracker: {len(game_list)} Games @ 10k+ CCU"
    msg['From'] = f"Roblox Monitor <{SMTP_USER}>"
    msg['To'] = TARGET_EMAIL
    
    body = "Today's high-traffic Roblox games:\n\n"
    body += "\n".join(game_list) if game_list else "No games hit the 10k threshold today."
    msg.set_content(body)

    # Connect to Brevo's SMTP server
    with smtplib.SMTP('smtp-relay.brevo.com', 587) as server:
        server.starttls() # Secure the connection
        server.login(SMTP_USER, SMTP_KEY)
        server.send_message(msg)
    print("Email sent successfully!")

if __name__ == "__main__":
    games = get_roblox_games()
    send_email(games)
