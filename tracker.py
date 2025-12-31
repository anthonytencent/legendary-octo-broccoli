import requests
import os
import sys
import json

# Configuration
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
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
                if last_players is None:
                    change = "⭐ NEW!"
                    growth = 0
                else:
                    diff = current_players - last_players
                    change = f"{diff:+,}"
                    growth = diff

                all_games.append({
                    "name": name,
                    "players": current_players,
                    "change": change,
                    "growth": growth,
                    "url": f"https://www.roblox.com/games/{place_id}"
                })

        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        # Sort: Winners (by growth) and then list
        all_games.sort(key=lambda x: x['players'], reverse=True)
        return all_games

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def send_to_discord(games):
    if not games:
        requests.post(WEBHOOK_URL, json={"content": "📉 No games hit 10k CCU today."})
        return

    # Create a nice looking "Embed" message
    embed = {
        "title": "🚀 Roblox Daily CCU Report",
        "color": 5814783, # Nice Blue
        "fields": []
    }

    # Add top 10 games to the embed (Discord limits)
    for g in games[:10]:
        embed["fields"].append({
            "name": g['name'],
            "value": f"👥 Players: **{g['players']:,}** ({g['change']})\n🔗 [Play Now]({g['url']})",
            "inline": False
        })

    payload = {
        "content": "Today's Roblox Tracker is ready!",
        "embeds": [embed]
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("✅ Discord message sent!")
    else:
        print(f"❌ Failed: {response.status_code}")

if __name__ == "__main__":
    game_data = get_roblox_games()
    send_to_discord(game_data)
