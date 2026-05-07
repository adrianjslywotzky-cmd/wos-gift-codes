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

# ギフトコードの特徴：
# - 5〜15文字
# - 数字を含む OR 大文字と小文字が混在 OR 全大文字で5文字以上
# - 一般的な英単語ではない
CODE_PATTERN = re.compile(r'\b([A-Z][A-Za-z0-9]{4,14})\b')

# 除外する一般的な英単語・HTMLワード（大文字始まり）
SKIP_WORDS = {
    # 一般英単語
    "Active", "Allow", "Also", "Amazon", "America", "Analysis", "Android", "Anime",
    "Answer", "Apple", "April", "Arena", "Arial", "Article", "Articles", "Asia",
    "Auto", "About", "Array", "Account", "Address", "After", "Again", "Against",
    "Advertise", "Alliance", "Alpine", "Analytics", "Apex", "Arknights",
    "Back", "Ball", "Basic", "Best", "Beyond", "Black", "Blood", "Blog",
    "Bookmark", "Boys", "Brawl", "Breaking", "Build", "Byebye",
    "Call", "Canada", "Cards", "Capture", "Careers", "Center", "Century",
    "Channel", "Check", "Chess", "Chief", "City", "Claim", "Clash",
    "Classic", "Click", "Clans", "Close", "Coal", "Color", "Community",
    "Component", "Conditions", "Connection", "Container", "Content", "Contents",
    "Continue", "Cookie", "Cookies", "Copyright", "Crystal",
    "Daily", "Dark", "Data", "Date", "Default", "Delta", "Design",
    "Desktop", "Deutsch", "Diablo", "Discord", "Disney", "Discount", "Double",
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
    # HTML/JS関連
    "DOMContentLoaded", "XMLHttpRequest", "URLSearchParams", "AbortController",
    "CustomEvent", "TypeError", "ImageObject", "Organization", "WebSite",
    "WebPage", "ItemList", "ListItem", "BreadcrumbList", "BlogPosting",
    "SameSite", "FFFFFF", "GDPR", "COUNTRY", "CURRENCY",
    # ゲーム名
    "Whiteout", "Survival", "Kingshot", "Fortnite", "Destiny", "Battlefield",
    "Valorant", "Counter", "Genshin", "Honkai", "Minecraft", "Warcraft",
    "Pokemon", "Roblox", "Discord", "Diablo", "Arknights",
    # その他
    "LOGIN", "SUCCESS", "ACTIVE", "SPONSORED", "ABOUT", "START",
    "SUBSCRIPTION", "GamesRadar", "WhiteoutSurvival",
}

# ギフトコードらしいパターンの判定
def is_likely_code(s):
    if len(s) < 5 or len(s) > 15:
        return False
    if s in SKIP_WORDS:
        return False
    # 数字を含む
    has_digit = bool(re.search(r'\d', s))
    # 大文字と小文字が混在（先頭以外）
    has_mixed = bool(re.search(r'[A-Z]', s[1:])) and bool(re.search(r'[a-z]', s))
    # 全大文字で5文字以上（WOS系）
    all_upper = s.isupper() and len(s) >= 5
    return has_digit or has_mixed or all_upper

# 期限切れキーワード（前後の文脈チェック用）
EXPIRED_CONTEXT = [
    "expired", "no longer", "not working", "invalid code",
    "期限切れ", "無効", "使用不可"
]

def extract_codes_with_context(html, source_name):
    # HTMLタグ除去
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # 期限切れセクションを除去（"expired"以降のテキストを切り捨て）
    for marker in ["Expired Codes", "expired codes", "No Longer Working",
                   "These codes have expired", "期限切れ", "Expired Gift Codes"]:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx]

    results = []
    tokens = text.split()
    for i, token in enumerate(tokens):
        # 前後5トークンのコンテキスト
        context = " ".join(tokens[max(0, i-5):i+5]).lower()
        # 期限切れコンテキストならスキップ
        if any(w in context for w in EXPIRED_CONTEXT):
            continue
        # コードパターンマッチ
        m = CODE_PATTERN.fullmatch(token.strip('.,;:()[]'))
        if m:
            code = m.group(1)
            if is_likely_code(code):
                results.append(code)
    return list(set(results))

# ソースごとにコードを収集
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

# Reddit
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

# 3ソース以上で確認されたコードのみ採用（精度向上）
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

# 既存データの報酬情報を引き継ぐ
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
