import sys
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TODAY = sys.argv[1]
API_KEY = sys.argv[2]
JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
today_str = now.strftime("%Y-%m-%d %H:%M JST")

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="ignore")
    except:
        return ""

def fetch_reddit(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 WOSCodeTracker/1.0 (personal use)"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            posts = data.get("data", {}).get("children", [])
            results = []
            for post in posts:
                d = post.get("data", {})
                title = d.get("title", "")
                body = d.get("selftext", "")
                if any(w in (title + body).lower() for w in ["gift code", "giftcode", "code"]):
                    results.append(title + " " + body[:300])
            return results
    except:
        return []

CODE_PATTERN = re.compile(r'\b([A-Z][A-Za-z0-9]{4,14})\b')

SKIP_WORDS = {
    "Active", "Allow", "Also", "Amazon", "America", "Analysis", "Android", "Anime",
    "Answer", "Apple", "April", "Arena", "Arial", "Article", "Articles", "Asia",
    "Auto", "About", "Array", "Account", "Address", "After", "Again", "Against",
    "Advertise", "Alliance", "Alpine", "Analytics", "Apex", "Arknights",
    "Back", "Ball", "Basic", "Best", "Beyond", "Black", "Blood", "Blog",
    "Bookmark", "Boys", "Brawl", "Breaking", "Build",
    "Call", "Canada", "Cards", "Capture", "Careers", "Center", "Century",
    "Channel", "Check", "Chess", "Chief", "City", "Claim", "Clash",
    "Classic", "Click", "Clans", "Close", "Coal", "Color", "Community",
    "Component", "Conditions", "Connection", "Container", "Content", "Contents",
    "Continue", "Cookie", "Cookies", "Copyright", "Crystal",
    "Daily", "Dark", "Data", "Date", "Default", "Delta", "Design",
    "Desktop", "Deutsch", "Diablo", "Disney", "Discount", "Double",
    "Download", "Dragon", "Duty",
    "Early", "Earn", "Edition", "Eggy", "Email", "Emoji", "Endfield",
    "English", "Enter", "Entertainment", "Error", "Ensure", "Escape",
    "Event", "Events", "Every", "Evil", "Exclusive", "Expert", "Experts",
    "Facebook", "Failed", "Fire", "Find", "First", "Floating", "Follow",
    "Food", "Footer", "Force", "Form", "Fortnite", "Frame", "Frost",
    "Function", "Full", "Fruits",
    "Games", "Gaming", "Gate", "Gear", "Gears", "General", "Generator",
    "Genshin", "Global", "Goddess", "Gold", "Golden", "Google", "Grand",
    "Guide", "Guides",
    "Hard", "Head", "Header", "Hello", "Height", "Help", "Heroes",
    "High", "History", "Home", "Honkai", "Horror", "Human", "Hunter",
    "Hulu", "Hide",
    "Icon", "Impact", "India", "Instagram", "Internet", "Info", "Items",
    "January", "Journey", "Join", "July",
    "Keep", "Keys", "Kingdom", "Knowledge",
    "Language", "Later", "Launch", "Layer", "League", "Learn", "Legacy",
    "Legends", "Level", "Links", "List", "Login", "Lucky",
    "Magic", "Main", "Make", "Mario", "Marvel", "Math", "Matches",
    "Meat", "Mecha", "Meet", "Member", "Members", "Microsoft", "Minecraft",
    "Mobile", "Module", "Monster", "Movies", "Mystery",
    "Navigation", "Netflix", "Network", "Neue", "News", "Newsletter",
    "Nintendo", "Notice", "Number",
    "Object", "Official", "Only", "Open", "Origin", "Other", "Overwatch",
    "Party", "Path", "Payment", "Person", "Plans", "Play", "Players",
    "Plus", "Pocket", "Points", "Pokemon", "Popular", "Portal", "POST",
    "Power", "Prime", "Privacy", "Profile", "Program", "Promise", "Prevent",
    "Question", "Quick",
    "Rail", "Reddit", "Reborn", "Redeem", "Redeeming", "Redemption",
    "Region", "Related", "Remove", "Required", "Research", "Resources",
    "Review", "Reviews", "Rivals", "Roblox", "Roboto",
    "Save", "Search", "Season", "Secure", "Security", "Segoe", "Select",
    "Server", "Services", "Settings", "Seven", "Share", "Show", "Simple",
    "Since", "Site", "Skip", "Skin", "Smooth", "Social", "Sports",
    "Spotify", "Stars", "State", "Stay", "Steam", "Stone", "Store",
    "Strategy", "Streaming", "Strike", "String", "Subscribe", "Subscription",
    "Support", "Symbol",
    "Table", "Team", "Teams", "Tech", "Telegram", "Terms", "There",
    "Third", "Three", "Tier", "TikTok", "Tips", "Tower", "Track",
    "Trending", "Twitter", "Type",
    "Ubuntu", "Unit", "Unknown", "Unlock", "Update", "Updated",
    "Valorant", "Value", "Video", "Videos", "View", "Visit",
    "Want", "Warcraft", "Waves", "Welcome", "Where", "While", "Widget",
    "Wood", "World", "Working",
    "Xbox", "YouTube", "Zone",
    "DOMContentLoaded", "XMLHttpRequest", "URLSearchParams", "AbortController",
    "CustomEvent", "TypeError", "ImageObject", "Organization", "WebSite",
    "WebPage", "ItemList", "ListItem", "BreadcrumbList", "BlogPosting",
    "SameSite", "FFFFFF", "GDPR", "COUNTRY", "CURRENCY",
    "Whiteout", "Survival", "Kingshot", "Destiny", "Battlefield",
    "Counter", "Minecraft", "Warcraft", "Discord",
    "LOGIN", "SUCCESS", "ACTIVE", "SPONSORED", "ABOUT", "START",
    "SUBSCRIPTION", "GamesRadar", "WhiteoutSurvival",
    # 期限切れ確認済みコード
    "RamadanJoy2026", "GW2026JP", "Herstory26", "EidMubarak2026",
    "Earth26", "WOS3YS", "VpqG7dDK7", "HowieLovesWOS", "WOS0408",
    "HappyMayDay", "YearoftheHorse", "A7D9K2Q", "INS200K",
    "OUNF42TI553", "WOS1220", "EasterBunny26", "AprilFool2026",
    "RW23UIE", "WOS26TGS", "Shamrock", "WOSHappyBirthday",
    "T120407", "Teamwork", "WOS3ANNIVERSARY", "VDay2026",
    "DiscordMilestone", "DCMilestone", "FBmilestone", "GPBestOf2025",
    "Byebye2025", "WOS1231", "WOS1105", "WOS1027",
    "WOS1020", "WOS1008", "WOS0128", "HangulDay2025", "RedLeaves2025",
    "BrightMoon", "TrickorTreat25", "A7F9K2R", "Feast25",
    "Pepero1111", "NAVERCPL2025", "Tiktok10Kfans", "Tiktok10Kfan",
    "V255xR64w", "Blessing", "HappyFriday", "Jangsusang25",
    "WOS3ANNIVERSARY", "WOS1220", "WOS1231", "WOS1105", "WOS1027",
    "GAECHEONJEOL", "Neverness", "Everness", "Jangsusang25",
    "SeijinNoHi2026", "seijin2026",
}

def is_likely_code(s):
    if len(s) < 5 or len(s) > 15:
        return False
    if s in SKIP_WORDS:
        return False
    has_digit = bool(re.search(r'\d', s))
    has_mixed = bool(re.search(r'[A-Z]', s[1:])) and bool(re.search(r'[a-z]', s))
    all_upper = s.isupper() and len(s) >= 5
    return has_digit or has_mixed or all_upper

EXPIRED_CONTEXT = [
    "expired", "no longer", "not working", "invalid code",
    "期限切れ", "無効", "使用不可"
]

def extract_codes_with_context(html, source_name):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    for marker in [
        "Expired Codes", "expired codes", "No Longer Working",
        "These codes have expired", "期限切れ", "Expired Gift Codes",
        "Expired WOS", "no longer work", "have expired", "recently expired",
        "Codes That No Longer", "Old Codes", "Dead Codes",
        "codes that have expired", "expired gift codes",
        "Whiteout Survival codes that", "codes have since expired",
        "Above are some of the more recent",
    ]:
        idx = text.lower().find(marker.lower())
        if idx > 0:
            text = text[:idx]
            break

    results = []
    tokens = text.split()
    for i, token in enumerate(tokens):
        context = " ".join(tokens[max(0, i-5):i+5]).lower()
        if any(w in context for w in EXPIRED_CONTEXT):
            continue
        m = CODE_PATTERN.fullmatch(token.strip('.,;:()[]'))
        if m:
            code = m.group(1)
            if is_likely_code(code):
                results.append(code)
    return list(set(results))

code_sources = defaultdict(set)

sources = [
    ("https://wosrewards.com/", "wosrewards"),
    ("https://www.gamesradar.com/games/survival/whiteout-survival-codes-gift/", "gamesradar"),
    ("https://www.dexerto.com/codes/whiteout-survival-codes-3295120/", "dexerto"),
    ("https://buffbuff.com/blog/whiteout-survival-gift-codes", "buffbuff"),
    ("https://www.pockettactics.com/whiteout-survival/codes", "pockettactics"),
    ("https://www.mrguider.org/codes/whiteout-survival-codes-gift/", "mrguider"),
    ("https://www.gamsgo.com/blog/whiteout-survival-gift-codes", "gamsgo"),
    ("https://lootbar.gg/blog/en/whiteout-survival-newest-codes.html", "lootbar"),
    ("https://www.eldorado.gg/blog/whiteout-survival-newest-codes/", "eldorado"),
    ("https://www.whiteoutsurvival.wiki/giftcodes/", "wiki"),
    ("https://digitalrevenuestudio.co", "digitalrevenuestudio"),
    ("https://whiteoutsurvival.app/gift-code/", "wosapp"),
]

print("Fetching sources...")
for url, name in sources:
    html = fetch_url(url)
    if html:
        codes = extract_codes_with_context(html, name)
        for code in codes:
            code_sources[code].add(name)
        print(f"  {name}: {len(codes)} candidates")
    else:
        print(f"  {name}: blocked")

for url in [
    "https://www.reddit.com/r/whiteoutsurvival/search.json?q=gift+code&sort=new&restrict_sr=1&limit=10",
    "https://www.reddit.com/r/whiteoutsurvival/new.json?limit=25",
]:
    posts = fetch_reddit(url)
    for text in posts:
        for token in text.split():
            m = CODE_PATTERN.fullmatch(token.strip('.,;:()[]'))
            if m and is_likely_code(m.group(1)):
                code_sources[m.group(1)].add("reddit")
print(f"  reddit: fetched")

print(f"\nAll candidates: {len(code_sources)}")

valid_codes = []
for code, srcs in sorted(code_sources.items(), key=lambda x: -len(x[1])):
    if len(srcs) >= 3:
        print(f"  VALID ({len(srcs)} sources): {code}")
        valid_codes.append({
            "code": code,
            "rewards": "報酬情報を確認してください",
            "deadline": None,
            "note": None
        })

print(f"\nValid codes (3+ sources): {len(valid_codes)}")

try:
    with open("codes.json", "r") as f:
        existing = json.load(f)
    existing_map = {c["code"]: c for c in existing.get("codes", [])}
except:
    existing_map = {}

final_codes = []
for c in valid_codes:
    if c["code"] in existing_map:
        c["rewards"] = existing_map[c["code"]].get("rewards", c["rewards"])
        c["deadline"] = existing_map[c["code"]].get("deadline")
        c["note"] = existing_map[c["code"]].get("note")
    final_codes.append(c)

output = {"updated": today_str, "codes": final_codes}
with open("codes.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Updated: {len(final_codes)} codes saved")
