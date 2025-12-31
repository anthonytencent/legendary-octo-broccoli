import requests
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ---
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password" # Not your login password, a 'Gmail App Password'
TARGET_EMAIL = "your-email@gmail.com"
CCU_THRESHOLD = 10000

def get_trending_games():
    # Fetching from the "Top Playing" sort
    url = "https://games.roblox.com/v1/games/list?sortToken=TopPlayingNow"
    try:
        response = requests.get(url).json()
        games_list = []
        for game in response.get('games', []):
            if game['playerCount'] >= CCU_THRESHOLD:
                games_list.append(f"{game['name']} - {game['playerCount']:,} players")
        return games_list
    except Exception as e:
        return [f"Error fetching games: {e}"]

def send_email(games):
    msg = EmailMessage()
    msg['Subject'] = f"🚀 Roblox Daily Tracker: {len(games)} Games Over 10k CCU"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TARGET_EMAIL
    
    body = "Here are today's trending games with over 10,000 players:\n\n"
    body += "\n".join(games) if games else "No new games hit the 10k threshold today."
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    trending = get_trending_games()
    send_email(trending)
