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
                is_brand_new = last_players is None
                
                growth = 0 if is_brand_new else current_players - last_players
                change_text = "⭐ NEW!" if is_brand_new else f"{growth:+,}"

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

        # Sort by player count
        all_games.sort(key=lambda x: x['players'], reverse=True)
        return all_games

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def create_embed(title, games_slice, start_rank):
    embed = {
        "title": title,
        "color": 3447003, # Elegant Blue
        "fields": []
    }
    
    for i, g in enumerate(games_slice, start=start_rank):
        # Add special emojis for top 3
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**#{i}**")
        
        new_tag = " 🆕" if g['is_brand_new'] else ""
        
        embed["fields"].append({
            "name": f"{rank_emoji} {g['name']}{new_tag}",
            "value": f"👤 `{g['players']:,}` | 📈 `{g['change']}` | [Play]({g['url']})",
            "inline": True # This makes it look like a grid/table
        })
    return embed

def send_to_discord(games):
    if not games:
        return

    # 1. Pings and Summary
    new_count = sum(1 for g in games if g['is_brand_new'])
    ping_text = f"🔔 <@{USER_ID}>" if USER_ID and new_count > 0 else "📊 **Daily Update**"
    
    # 2. Split 30 games into two embeds (15 each) for a "prettier" grid layout
    embed1 = create_embed("🏆 Top Roblox Games (1-15)", games[:15], 1)
    embed2 = create_embed("📈 Top Roblox Games (16-30)", games[15:30], 16)

    payload = {
        "content": f"{ping_text}\nFound **{len(games)}** games over 10k CCU today!",
        "embeds": [embed1, embed2]
    }
    
    requests.post(WEBHOOK_URL, json=payload)
    print("✅ Prettier report sent!")

if __name__ == "__main__":
    game_data = get_roblox_games()
    send_to_discord(game_data)
