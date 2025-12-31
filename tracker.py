import requests
import os
import sys
import json

# Configuration
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
USER_ID = os.getenv("DISCORD_USER_ID")
CCU_THRESHOLD = 10000
HISTORY_FILE = "history.json"

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

            # 1. Check for New Hits (Milestone Alert)
            if current >= CCU_THRESHOLD and prev < CCU_THRESHOLD and prev != 0:
                new_hits.append({"name": name, "ccu": current, "url": f"https://www.roblox.com/games/{pid}"})

            # 2. Track CCU movement for all games
            all_movers.append({"name": name, "diff": diff, "ccu": current})

        # Save data for the next 12h comparison
        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        # Sort and get Top 10
        all_movers.sort(key=lambda x: x['diff'], reverse=True)
        top_gainers = [m for m in all_movers if m['diff'] > 0][:10]
        top_losers = sorted([m for m in all_movers if m['diff'] < 0], key=lambda x: x['diff'])[:10]

        return new_hits, top_gainers, top_losers

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def send_to_discord(new_hits, gainers, losers):
    if not (new_hits or gainers or losers):
        return

    ping = f"🔔 <@{USER_ID}>" if (new_hits and USER_ID) else ""
    embeds = []

    # Section 1: NEW HITS (Alerts)
    if new_hits:
        hit_list = "\n".join([f"✨ **{g['name']}** ({g['ccu']:,} CCU) — [Play]({g['url']})" for g in new_hits])
        embeds.append({
            "title": "🆕 Newly Hit 10k CCU",
            "description": hit_list,
            "color": 16776960 # Yellow
        })

    # Section 2: TOP 10 GAINERS
    if gainers:
        val = "\n".join([f"`#{i+1:02}` 📈 **{g['name']}**: +{g['diff']:,} (`{g['ccu']:,}`)" for i, g in enumerate(gainers)])
        embeds.append({
            "title": "🚀 Top 10 Gainers (12h)",
            "description": val,
            "color": 3066993 # Green
        })

    # Section 3: TOP 10 LOSERS
    if losers:
        val = "\n".join([f"`#{i+1:02}` 📉 **{g['name']}**: {g['diff']:,} (`{g['ccu']:,}`)" for i, g in enumerate(losers)])
        embeds.append({
            "title": "🔻 Top 10 Losers (12h)",
            "description": val,
            "color": 15158332 # Red
        })

    payload = {
        "content": f"{ping} **12-Hour Roblox Market Intelligence Report**", 
        "embeds": embeds
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    new_hits, gainers, losers = get_roblox_momentum()
    send_to_discord(new_hits, gainers, losers)
