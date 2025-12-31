import requests
import os
import sys
import json

# Configuration
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
USER_ID = os.getenv("DISCORD_USER_ID")
CCU_THRESHOLD = 10000
HISTORY_FILE = "history.json"

def get_game_icons(universe_ids):
    """Fetches icon URLs for a list of Universe IDs from the Roblox API."""
    if not universe_ids:
        return {}
    
    # Roblox Thumbnail API allows batching up to 100 IDs
    ids_str = ",".join(map(str, universe_ids))
    url = f"https://thumbnails.roblox.com/v1/games/icons?universeIds={ids_str}&returnPolicy=PlaceHolder&size=150x150&format=Png"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('data', [])
        return {str(item['targetId']): item['imageUrl'] for item in data}
    except Exception as e:
        print(f"Warning: Could not fetch icons: {e}")
        return {}

def get_roblox_momentum():
    url = "https://api.rolimons.com/games/v1/gamelist"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        history = {}
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get('games', {})
        
        new_hits = []
        all_movers = []
        new_history = {}

        for pid, info in data.items():
            name, current = info[0], info[1]
            new_history[pid] = current
            prev = history.get(pid, 0)
            diff = current - prev

            # 1. Check for New Hits (Was below 10k, now above)
            if current >= CCU_THRESHOLD and prev < CCU_THRESHOLD and prev != 0:
                new_hits.append({"pid": pid, "name": name, "ccu": current, "url": f"https://www.roblox.com/games/{pid}"})

            # 2. Track CCU movement for Gainer/Loser analysis
            if current >= CCU_THRESHOLD or prev >= CCU_THRESHOLD:
                all_movers.append({"pid": pid, "name": name, "diff": diff, "ccu": current})

        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        # Sort Gainers and Losers
        all_movers.sort(key=lambda x: x['diff'], reverse=True)
        top_gainers = [g for g in all_movers if g['diff'] > 0][:5]
        top_losers = sorted([g for g in all_movers if g['diff'] < 0], key=lambda x: x['diff'])[:5]

        # Batch fetch icons for all relevant games
        ids_to_fetch = [g['pid'] for g in new_hits + top_gainers + top_losers]
        icons = get_game_icons(ids_to_fetch)

        # Attach icon URLs to the game data
        for g in new_hits: g['icon'] = icons.get(str(g['pid']))
        for g in top_gainers: g['icon'] = icons.get(str(g['pid']))
        for g in top_losers: g['icon'] = icons.get(str(g['pid']))

        return new_hits, top_gainers, top_losers

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def send_to_discord(new_hits, gainers, losers):
    if not (new_hits or gainers or losers):
        return

    ping = f"🔔 <@{USER_ID}>" if (new_hits and USER_ID) else ""
    embeds = []

    # Section 1: NEW HITS (Individual embeds to showcase icons)
    for hit in new_hits:
        embeds.append({
            "title": f"✨ Newly Hit 10k CCU: {hit['name']}",
            "description": f"Current: **{hit['ccu']:,}**\n[Play Game]({hit['url']})",
            "color": 16776960, # Yellow
            "thumbnail": {"url": hit['icon']} if hit['icon'] else None
        })

    # Section 2: GAINERS
    if gainers:
        val = "\n".join([f"📈 **{g['name']}**: +{g['diff']:,} (`{g['ccu']:,}`)" for g in gainers])
        embeds.append({
            "title": "🚀 Top 5 Gainers (12h)",
            "description": val,
            "color": 3066993, # Green
            "thumbnail": {"url": gainers[0]['icon']} if gainers[0]['icon'] else None
        })

    # Section 3: LOSERS
    if losers:
        val = "\n".join([f"📉 **{g['name']}**: {g['diff']:,} (`{g['ccu']:,}`)" for g in losers])
        embeds.append({
            "title": "🔻 Top 5 Losers (12h)",
            "description": val,
            "color": 15158332, # Red
            "thumbnail": {"url": losers[0]['icon']} if losers[0]['icon'] else None
        })

    # Discord has a limit of 10 embeds per message
    payload = {
        "content": f"{ping} **12-Hour Roblox Market Intelligence Report**", 
        "embeds": embeds[:10]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    new_hits, gainers, losers = get_roblox_momentum()
    send_to_discord(new_hits, gainers, losers)
