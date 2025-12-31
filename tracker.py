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
        gainers = []
        new_history = {}

        for pid, info in data.items():
            name, current = info[0], info[1]
            new_history[pid] = current
            prev = history.get(pid, 0)
            diff = current - prev

            # 1. Check for New Hits (Was below 10k, now above)
            if current >= CCU_THRESHOLD and prev < CCU_THRESHOLD:
                new_hits.append({"name": name, "ccu": current, "url": f"https://www.roblox.com/games/{pid}"})

            # 2. Track CCU movement for games currently in the high-traffic zone
            if current >= CCU_THRESHOLD or prev >= CCU_THRESHOLD:
                gainers.append({"name": name, "diff": diff, "ccu": current})

        # Save all data for 12-hour comparison
        with open(HISTORY_FILE, "w") as f:
            json.dump(new_history, f)

        # Sort Gainers and Losers
        gainers.sort(key=lambda x: x['diff'], reverse=True)
        top_gainers = [g for g in gainers if g['diff'] > 0][:5]
        top_losers = sorted([g for g in gainers if g['diff'] < 0], key=lambda x: x['diff'])[:5]

        return new_hits, top_gainers, top_losers

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def send_to_discord(new_hits, gainers, losers):
    if not (new_hits or gainers or losers):
        return

    ping = f"🔔 <@{USER_ID}>" if (new_hits and USER_ID) else ""
    
    embeds = []

    # Section 1: NEW HITS (The most important part)
    if new_hits:
        hit_list = "\n".join([f"✨ **{g['name']}** ({g['ccu']:,} CCU)\n🔗 [Play]({g['url']})" for g in new_hits])
        embeds.append({
            "title": "🆕 Newly Hit 10k CCU",
            "description": hit_list,
            "color": 16776960 # Yellow
        })

    # Section 2: GAINERS & LOSERS
    trends_fields = []
    if gainers:
        val = "\n".join([f"📈 **{g['name']}**: +{g['diff']:,} (`{g['ccu']:,}` total)" for g in gainers])
        trends_fields.append({"name": "🚀 Top 5 Gainers", "value": val, "inline": False})
    
    if losers:
        val = "\n".join([f"📉 **{g['name']}**: {g['diff']:,} (`{g['ccu']:,}` total)" for g in losers])
        trends_fields.append({"name": "🔻 Top 5 Losers", "value": val, "inline": False})

    if trends_fields:
        embeds.append({
            "title": "📊 12h Momentum Trends",
            "color": 3447003, # Blue
            "fields": trends_fields
        })

    payload = {"content": f"{ping} **12-Hour Market Intelligence Report**", "embeds": embeds}
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    new_hits, gainers, losers = get_roblox_momentum()
    send_to_discord(new_hits, gainers, losers)
