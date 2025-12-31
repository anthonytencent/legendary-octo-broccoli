import requests
import os
import sys
import json

# Configuration
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
USER_ID = os.getenv("DISCORD_USER_ID")
CCU_THRESHOLD = 10000
HISTORY_FILE = "history.json"

def get_roblox_games():
    url = "https://api.rolimons.com/games/v1/gamelist"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        history = {}
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        games_dict = data.get('games', {})
        all_games = []
        new_history = {}

        for place_id, info in games_dict.items():
            name, current_players = info[0], info[1]
            new_history[place_id] = current_players
            
            if current_players >= CCU_THRESHOLD:
                last_players = history.get(place_id)
                # Check if this game is brand new to the 10k club
                is_brand_new = last_players is None
                
                if is_brand_new:
                    change_text = "⭐ NEW!"
                    growth = 0
                else:
                    diff = current_players - last_players
                    change_text = f"{diff:+,}"
                    growth = diff

                all_games.append({
                    "name": name,
                    "players": current_players,
                    "change": change_text,
                    "growth": growth,
                    "is_brand_new": is_brand_new,
                    "url": f"https://www.roblox.com/games/{place_id}"
                })

        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        all_games.sort(key=lambda x: x['players'], reverse=True)
        return all_games

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def send_to_discord(games):
    if not games:
        return

    # 1. Identify new games for the ping
    new_game_names = [g['name'] for g in games if g['is_brand_new']]
    
    content = "📅 **Daily Roblox CCU Report is here!**"
    if new_game_names and USER_ID:
        # This creates the actual ping notification
        content = f"🔔 <@{USER_ID}> **New Games Hit 10k CCU:** {', '.join(new_game_names)}!"

    # 2. Create the visual report
    embed = {
        "title": "Roblox Market Trends",
        "description": "Top games currently over 10,000 players.",
        "color": 16738560, # Orange/Flame color
        "fields": []
    }

    for g in games[:10]:
        embed["fields"].append({
            "name": f"{'⭐ ' if g['is_brand_new'] else ''}{g['name']}",
            "value": f"👥 **{g['players']:,}** ({g['change']})\n🔗 [Play Game]({g['url']})",
            "inline": False
        })

    payload = {
        "content": content,
        "embeds": [embed]
    }
    
    requests.post(WEBHOOK_URL, json=payload)
    print("✅ Discord alert sent!")

if __name__ == "__main__":
    game_data = get_roblox_games()
    send_to_discord(game_data)
