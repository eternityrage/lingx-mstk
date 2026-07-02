"""
YouTube Upload - Lingexa Mistakes
"""
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
load_dotenv()
CHANNEL_NAME = "Lingexa Mistakes"

def get_auth():
    cid = (os.getenv('YOUTUBE_CLIENT_ID') or os.getenv('YT_CLIENT_ID', '')).strip()
    cs = (os.getenv('YOUTUBE_CLIENT_SECRET') or os.getenv('YT_CLIENT_SECRET', '')).strip()
    rt = (os.getenv('YOUTUBE_REFRESH_TOKEN') or os.getenv('YT_REFRESH_TOKEN', '')).strip()
    if not all([cid, cs, rt]): raise ValueError("Missing YouTube credentials!")
    creds = Credentials(None, refresh_token=rt, token_uri="https://oauth2.googleapis.com/token", client_id=cid, client_secret=cs, scopes=["https://www.googleapis.com/auth/youtube"])
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def gen_meta(words_data, reel_data=None):
    if not words_data:
        return f"English Mistakes - {CHANNEL_NAME}", f"Fix English mistakes with {CHANNEL_NAME}!", ["english mistakes", "grammar", CHANNEL_NAME.replace(' ', '')]
    first = [m.get("wrong", "") for m in words_data[:3]]
    title = f"Don't Say These! Fix {len(words_data)} Common English Mistakes - {', '.join(first)}"
    lines = [f"❌ Fix {len(words_data)} common English mistakes with {CHANNEL_NAME}!", f""]
    for i, m in enumerate(words_data, 1):
        lines.append(f"{i}. WRONG: \"{m['wrong']}\"")
        lines.append(f"   RIGHT: \"{m['right']}\"")
        lines.append(f"   {m.get('explanation', '')}")
        lines.append(f"   Tip: {m.get('tip', '')}")
        lines.append(f"")
    lines.extend([f"=== ABOUT {CHANNEL_NAME.upper()} ===", f"", f"Fix your English every day!", f"🔔 Subscribe!", f"", f"=== HASHTAGS ===", f"#LingexaMistakes #English #Grammar #LearnEnglish #CommonMistakes #ESL #EnglishGrammar #WritingTips #Shorts"])
    return title, "\n".join(lines), ["english mistakes", "grammar", "learn english", "common mistakes", "english grammar", "writing tips", "esl", CHANNEL_NAME.replace(' ', '').lower()] + [m.get("wrong", "").lower() for m in words_data[:5]]

def upload_to_youtube(vp, title, desc, tags=None, cid='27'):
    if tags is None: tags = ['english mistakes', 'grammar', CHANNEL_NAME.replace(' ', '').lower()]
    yt = get_auth()
    body = {'snippet': {'title': title[:100], 'description': desc, 'tags': tags, 'categoryId': cid}, 'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}}
    media = MediaFileUpload(vp, chunksize=1024*1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None: status, resp = req.next_chunk()
    print(f"[youtube] Video ID: {resp.get('id')}")
    return {"status": "success", "video_id": resp.get('id'), "title": title}
