"""
Lingexa Mistakes - Upload Script
"""
import os, sys, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path: sys.path.insert(0, str(upload_dir))
CHANNEL_NAME = "Lingexa Mistakes"

def get_latest():
    vd = Path("output/video")
    if not vd.exists(): return None
    reels = list(vd.glob("*/final_reel.mp4"))
    if not reels: return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    mf = latest.parent / "metadata.json"
    meta = {}
    if mf.exists():
        with open(mf, "r", encoding="utf-8") as f: meta = json.load(f)
    items = meta.get("mistakes", [])
    return {"video_path": str(latest), "metadata": meta, "mistakes": items, "word": items[0].get("wrong", "Mistake") if items else "Mistake"}

def gen_caption(data, platform="facebook"):
    ms = data.get("mistakes", [])
    if not ms: return f"Fix common mistakes with {CHANNEL_NAME}! #LingexaMistakes"
    lines = [f"❌ Fix 3 Common English Mistakes with {CHANNEL_NAME}!", f""]
    for i, m in enumerate(ms, 1):
        lines.append(f"{i}. Don't say: \"{m['wrong']}\"")
        lines.append(f"   Say: \"{m['right']}\"")
        lines.append(f"   Tip: {m.get('tip', '')}")
        lines.append(f"")
    lines.extend([f"💡 Save this to remember!", f"🔔 Follow {CHANNEL_NAME} for daily fixes!", f"", f"#LingexaMistakes #English #Grammar #LearnEnglish #CommonMistakes #ESL #EnglishGrammar #WritingTips #LanguageLearning"])
    return "\n".join(lines)

def main():
    d = get_latest()
    if not d: print("No reel!"); sys.exit(1)
    c = gen_caption(d, "facebook")
    print(f"Caption ({len(c)} chars)")
    print(c[:500])
if __name__ == "__main__": main()
