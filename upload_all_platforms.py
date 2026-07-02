import os, sys, json, io
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

upload_to_facebook = None
upload_to_instagram = None
upload_to_youtube = None

try:
    from upload_facebook import upload_to_facebook as fb_upload
    upload_to_facebook = fb_upload
except ImportError:
    pass
try:
    from upload_instagram import upload_to_instagram as ig_upload
    upload_to_instagram = ig_upload
except ImportError:
    pass
try:
    from upload_to_youtube import upload_to_youtube as yt_upload
    upload_to_youtube = yt_upload
except ImportError:
    pass

CHANNEL_NAME = "Lingexa Mistakes"

def get_latest_reel():
    video_dir = Path("output/video")
    if not video_dir.exists():
        return None
    reels = list(video_dir.glob("*/final_reel.mp4"))
    if not reels:
        return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    metadata_file = latest.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    mistakes_data = metadata.get("mistakes", [])
    all_wrong = [m.get("wrong", "") for m in mistakes_data]
    return {"video_path": str(latest), "metadata": metadata, "mistakes": mistakes_data, "word": all_wrong[0] if all_wrong else "Mistake"}

def generate_caption(reel_data, platform="facebook"):
    mistakes = reel_data.get("mistakes", [])
    if not mistakes:
        return f"Fix common mistakes with {CHANNEL_NAME}! #LingexaMistakes"
    if platform == "facebook":
        lines = [f"❌ Fix 3 Common English Mistakes with {CHANNEL_NAME}!", f""]
        for i, m in enumerate(mistakes, 1):
            lines.append(f"{i}. Don't say: \"{m['wrong']}\"")
            lines.append(f"   Say: \"{m['right']}\"")
            lines.append(f"   Tip: {m.get('tip', '')}")
            lines.append(f"")
        lines.extend([f"💡 Save this to remember!", f"🔔 Follow {CHANNEL_NAME} for daily fixes!", f"", f"#LingexaMistakes #English #Grammar #LearnEnglish #CommonMistakes #ESL #EnglishGrammar #WritingTips #LanguageLearning"])
    else:
        lines = [f"❌ Fix Common English Mistakes!", f""]
        for i, m in enumerate(mistakes[:3], 1):
            lines.append(f"{i}. \"{m['wrong']}\" → \"{m['right']}\"")
        lines.extend([f"", f"#LingexaMistakes #English #Grammar"])
    return "\n".join(lines)

def upload_to_all_platforms(video_path, caption, word, reel_data=None):
    results = {"timestamp": datetime.now().isoformat(), "word": word, "video": video_path, "uploads": {}, "platforms_attempted": [], "platforms_successful": [], "platforms_skipped": [], "platforms_failed": []}
    print(f"\n{'='*80}\n{CHANNEL_NAME.upper()} - MULTI-PLATFORM UPLOAD\n{'='*80}")
    if not Path(video_path).exists():
        return results
    platforms = [("facebook", upload_to_facebook, "Facebook"), ("instagram", upload_to_instagram, "Instagram"), ("youtube", upload_to_youtube, "YouTube")]
    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)
        if upload_func:
            try:
                if platform_name == "facebook":
                    upload_result = upload_func(video_path=video_path, description=caption, title=f"Common Mistake: {word}")
                elif platform_name == "instagram":
                    upload_result = upload_func(video_path=video_path, caption=caption, is_story=False)
                elif platform_name == "youtube":
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_description, yt_tags = generate_video_metadata(reel_data.get("mistakes", []), reel_data)
                    upload_result = upload_func(video_path=video_path, title=yt_title, description=yt_description, tags=yt_tags, category_id='27')
                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                else:
                    results["platforms_failed"].append(platform_name)
            except Exception as e:
                results["uploads"][platform_name] = {"status": "failed", "error": str(e)}
                results["platforms_failed"].append(platform_name)
        else:
            results["platforms_skipped"].append(platform_name)
    print(f"\nSuccessful: {len(results['platforms_successful'])}, Failed: {len(results['platforms_failed'])}, Skipped: {len(results['platforms_skipped'])}")
    return results

def main():
    reel = get_latest_reel()
    if not reel:
        print("No reel found! Run lingexa_mistakes_bot.py first.")
        sys.exit(1)
    caption = generate_caption(reel, platform="facebook")
    print(f"Caption ({len(caption)} chars)")
    print(caption[:500])
    print("\n" + "="*60)
    print("UPLOADING TO SOCIAL MEDIA...")
    print("="*60)
    upload_to_all_platforms(reel['video_path'], caption, reel['word'], reel)

if __name__ == "__main__":
    main()
