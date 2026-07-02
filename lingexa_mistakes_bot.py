"""
Lingexa Mistakes - Fix Common English Errors
Stop making these advanced English mistakes
"""

import os, sys, json, random, asyncio, subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")
if not AI_MODEL:
    raise ValueError("AI_MODEL not set!")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
for d in [OUTPUT_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
TTS_VOICE = "en-US-GuyNeural"
CHANNEL_NAME = "Lingexa Mistakes"
WORDS_PER_VIDEO = 2
MISTAKE_HISTORY_FILE = HISTORY_DIR / "all_mistakes.json"
FONTS_DIR = Path(__file__).parent / "fonts"

def load_history():
    if MISTAKE_HISTORY_FILE.exists():
        with open(MISTAKE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mistakes": [], "last_updated": None}

def save_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(MISTAKE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_used(pid):
    h = load_history()
    return pid.lower().strip() in [x.lower().strip() for x in h.get("mistakes", [])]

def add_to_history(ids):
    h = load_history()
    for pid in ids:
        if pid.lower().strip() not in [x.lower().strip() for x in h.get("mistakes", [])]:
            h["mistakes"].append(pid.lower().strip())
    save_history(h)

def generate_mistake_data(num=WORDS_PER_VIDEO):
    max_attempts = 20
    cats = [
        "native speakers get this WRONG daily (I could care less vs I couldn't care less)",
        "embarrassing professional mistakes (per diem, ad hoc, bona fide pronunciation)",
        "words people use WRONG on LinkedIn/resumes everyday (utilize, leverage, actioned)",
        "common grammar mistakes that make you sound uneducated (less vs fewer, me vs I)",
        "words everyone mispronounces (nuclear, espresso, supposedly, etc.)",
        "writing mistakes that ruin credibility (its/it's, your/you're in professional emails)",
        "business jargon that's actually wrong (reach out, circle back, deep dive)",
        "controversial grammar rules people argue about (split infinitives, prepositions)",
        "spelling mistakes even smart people make (accommodate, embarrass, definitely)",
        "everyone says 'I could care less' but the REAL phrase is opposite",
        "commonly misused Latin phrases (per se, vice versa, eg/ie)",
        "tricky subject-verb agreement errors everyone makes",
        "false possessives and apostrophe disasters (1990's, CD's)",
        "preposition errors even advanced speakers make",
    ]
    collected = []
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}", "Content-Type": "application/json"}
            cat = cats[attempt % len(cats)]
            remaining = num - len(collected)
            print(f"[api] Attempt {attempt + 1}: {cat[:50]}... (need {remaining} more)")
            h = load_history()
            used_set = set(h.get("mistakes", [])[-50:])
            used_str = ", ".join(used_set) if used_set else "(none)"
            prompt = f"""Generate 15 interesting English mistakes from: {cat}

CRITICAL: These should be mistakes that EVEN NATIVE SPEAKERS commonly make. The kind that makes people say "Wait, I've been saying it wrong my whole life?"

NEVER repeat: {used_str}
Return ONLY JSON array.

Format:
[{{"pair":"I COULD CARE LESS vs I COULDN'T CARE LESS","wrong":"I could care less about the weather.","right":"I couldn't care less about the weather.","meaning":"If you 'could care less', it means you still care some. The correct phrase is 'couldn't care less' - meaning you care zero.","example_wrong":"She said she could care less about the meeting.","example_right":"She said she couldn't care less about the meeting.","tip":"If you could care less, that means you still care. You WANT zero care."}}]

REQUIREMENTS:
- Make people think "Oh no, I've been doing this wrong"
- 'meaning' field: explain WHY in ONE clear sentence
- 'tip' field: a UNFORGETTABLE memory trick in ONE sentence
- Pairs that professionals actually get wrong
Return ONLY the JSON array.""" 
            payload = {"model": AI_MODEL, "messages": [{"role": "system", "content": "Return ONLY valid JSON arrays."}, {"role": "user", "content": prompt}], "temperature": 1.3}
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            items = json.loads(content)
            if not isinstance(items, list):
                raise ValueError("Not a list")
            fresh = []
            for item in items:
                pair = item.get("pair", "").strip()
                if not pair:
                    continue
                pid = pair
                if pid.lower() in used_set:
                    continue
                fresh.append(item)
                used_set.add(pid.lower())
                if len(collected) + len(fresh) >= num:
                    break
            collected.extend(fresh)
            if len(collected) >= num:
                add_to_history([m["pair"] for m in collected[:num]])
                return collected[:num]
        except Exception as e:
            print(f"[api] Attempt {attempt + 1} FAILED: {e}")
    if collected:
        add_to_history([m["pair"] for m in collected])
        return collected
    raise RuntimeError("API failed")

def create_background():
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 252, 250, 250
        else:
            r = int(252 + (248 - 252) * ((ratio - 0.5) * 2))
            g = int(250 + (246 - 250) * ((ratio - 0.5) * 2))
            b = int(250 + (246 - 250) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img

async def gen_audio(text, voice, path):
    try:
        import edge_tts; await edge_tts.Communicate(text, voice).save(path); return True
    except: return False

async def gen_audio_retry(text, voice, path, r=3):
    for a in range(1, r+1):
        ok = await gen_audio(text, voice, path)
        if ok and Path(path).exists() and Path(path).stat().st_size > 100: return True
        await asyncio.sleep(2*a)
    return False

def get_audio_duration(file):
    if not Path(file).exists(): return 2.0
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",file], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 2.0

def generate_all_audio(items, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    af = []; total = 0.0
    for i, item in enumerate(items):
        pair = item.get("pair", "")
        wrong = item.get("wrong", "")
        right = item.get("right", "")
        meaning = item.get("meaning", "")
        tip = item.get("tip", "")
        text = f"Common mistake: {pair}. The wrong way: {wrong}. The correct way: {right}. Why? {meaning}. Quick tip: {tip}"
        fp = out_dir / f"m_{i}.mp3"
        ok = asyncio.run(gen_audio_retry(text, TTS_VOICE, str(fp)))
        if not ok:
            subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t","5",str(fp)], capture_output=True)
        dur = get_audio_duration(str(fp)); af.append({"file":str(fp),"duration":dur}); total += dur+0.3
    print(f"[audio] {len(af)} mistakes, {total:.1f}s")
    return af, total

def create_final_audio(audio_files, out_file):
    od = Path(out_file).parent; parts = []
    for i, af in enumerate(audio_files):
        p = od / f"pd_{i}.mp3"
        subprocess.run(["ffmpeg","-y","-i",str(af["file"]),"-af","apad=pad_dur=0.3","-ar","24000","-ac","1","-c:a","libmp3lame",str(p)], capture_output=True)
        parts.append(p)
    cl = od / "cl.txt"
    with open(cl,"w") as f:
        for p in parts: f.write(f"file '{str(p.resolve()).replace(chr(92),chr(47))}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(cl),"-c:a","libmp3lame",str(out_file)], capture_output=True)
    for p in parts:
        if p.exists(): p.unlink()
    if cl.exists(): cl.unlink()
    return Path(out_file).exists() and Path(out_file).stat().st_size > 100

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines = []; cur = []
    for w in words:
        t = ' '.join(cur + [w])
        if draw.textbbox((0,0),t,font=font)[2] <= max_w or not cur: cur.append(w)
        else: lines.append(' '.join(cur)); cur = [w]
    if cur: lines.append(' '.join(cur))
    return lines

def generate_word_image(item, bg_image, out_path):
    from PIL import Image, ImageDraw, ImageFont
    img = bg_image.copy().convert('RGBA')
    draw = ImageDraw.Draw(img)

    MARGIN_X = 90
    CENTER_X = VIDEO_WIDTH // 2
    CONTENT_WIDTH = VIDEO_WIDTH - MARGIN_X * 2

    fonts_bold = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf","/usr/share/fonts/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/segoeuib.ttf",
    ]
    fonts_regular = [
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf","/usr/share/fonts/noto/NotoSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf","C:/Windows/Fonts/segoeui.ttf",
    ]

    def load_font(paths, size):
        for p in paths:
            try:
                f = ImageFont.truetype(p, size)
                if draw.textbbox((0,0),"AW",font=f)[2] > size*0.5: return f
            except: continue
        return ImageFont.load_default()

    font_header = load_font(fonts_bold, 65)
    font_phrase = load_font(fonts_bold, 90)
    font_label = load_font(fonts_bold, 42)
    font_vs = load_font(fonts_bold, 48)
    font_def_label = load_font(fonts_bold, 38)
    font_def = load_font(fonts_regular, 52)
    font_tip_label = load_font(fonts_bold, 38)
    font_tip = load_font(fonts_regular, 42)
    font_footer = load_font(fonts_bold, 38)

    pair = item.get("pair", "COMMON MISTAKE").upper()
    wrong = item.get("wrong", "")
    right = item.get("right", "")
    meaning = item.get("meaning", "")
    tip = item.get("tip", "")

    H_CLR = (45, 35, 65)
    F_CLR = (45, 35, 65)

    draw.rectangle([(0,0),(VIDEO_WIDTH,90)], fill=H_CLR)
    draw.text((CENTER_X,45), CHANNEL_NAME.upper(), fill=(255,255,255), font=font_header, anchor="mm")

    y = 260

    # WRONG section
    draw.text((CENTER_X, y), "WRONG", fill=(200, 50, 50), font=font_label, anchor="mm")
    y += 52

    w_font = font_phrase
    wfs = 90
    ww = draw.textbbox((0,0),wrong,font=w_font)[2]
    while ww > CONTENT_WIDTH - 20 and wfs > 30:
        wfs -= 5; w_font = load_font(fonts_bold, wfs)
        ww = draw.textbbox((0,0),wrong,font=w_font)[2]
    wh = draw.textbbox((0,0),"Ay",font=w_font)[3] - draw.textbbox((0,0),"Ay",font=w_font)[1]
    draw.rounded_rectangle([(MARGIN_X-10,y-8),(VIDEO_WIDTH-MARGIN_X+10,y+wh+12)], radius=14, fill=(240,80,80,180))
    draw.text((CENTER_X, y+wh//2+2), wrong, fill=(255,255,255), font=w_font, anchor="mm")
    y += wh + 50

    # VS badge
    vs_b = draw.textbbox((0,0),"VS",font=font_vs)
    vs_w = vs_b[2]-vs_b[0]; vs_h = vs_b[3]-vs_b[1]
    draw.rounded_rectangle([(CENTER_X - vs_w//2 - 18, y-8),(CENTER_X + vs_w//2 + 18, y+vs_h+12)], radius=14, fill=H_CLR)
    draw.text((CENTER_X, y+vs_h//2+2), "VS", fill=(255,245,140), font=font_vs, anchor="mm")
    y += vs_h + 55

    # RIGHT section
    draw.text((CENTER_X, y), "RIGHT", fill=(60, 170, 60), font=font_label, anchor="mm")
    y += 52

    r_font = font_phrase
    rfs = 90
    rw = draw.textbbox((0,0),right,font=r_font)[2]
    while rw > CONTENT_WIDTH - 20 and rfs > 30:
        rfs -= 5; r_font = load_font(fonts_bold, rfs)
        rw = draw.textbbox((0,0),right,font=r_font)[2]
    rh = draw.textbbox((0,0),"Ay",font=r_font)[3] - draw.textbbox((0,0),"Ay",font=r_font)[1]
    draw.rounded_rectangle([(MARGIN_X-10,y-8),(VIDEO_WIDTH-MARGIN_X+10,y+rh+12)], radius=14, fill=(60,170,60,180))
    draw.text((CENTER_X, y+rh//2+2), right, fill=(255,255,255), font=r_font, anchor="mm")
    y += rh + 55

    # WHY section
    if meaning:
        draw.text((MARGIN_X, y), "WHY?", fill=(80, 65, 105), font=font_def_label, anchor="lm")
        y += 50
        ml = wrap_text(draw, meaning, font_def, CONTENT_WIDTH - 60)
        while len(ml) > 2 and font_def.size > 32:
            font_def = load_font(fonts_regular, font_def.size - 4)
            ml = wrap_text(draw, meaning, font_def, CONTENT_WIDTH - 60)
        mlh = draw.textbbox((0,0),"A",font=font_def)[3]-draw.textbbox((0,0),"A",font=font_def)[1]
        mls = int(mlh*1.5); mth = (len(ml)-1)*mls+mlh
        mpd = 35; mbh = mth + mpd*2
        mbox = Image.new('RGBA', (CONTENT_WIDTH, mbh), (65, 50, 95, 240))
        md = ImageDraw.Draw(mbox)
        md.rounded_rectangle([(0,0),(CONTENT_WIDTH,mbh)], radius=14, fill=(65, 50, 95, 240))
        for i,line in enumerate(ml):
            ly = mpd + (i*mls) + mlh//2
            md.text((CONTENT_WIDTH//2, ly), line, fill=(255,255,255), font=font_def, anchor="mm")
        img.paste(mbox, (MARGIN_X, y), mbox)
        y += mbh + 45

    # TIP section
    if tip and y < VIDEO_HEIGHT - 150:
        draw.text((MARGIN_X, y), "MEMORY TRICK", fill=(110, 75, 55), font=font_tip_label, anchor="lm")
        y += 48
        tl = wrap_text(draw, tip, font_tip, CONTENT_WIDTH - 60)
        while len(tl) > 2 and font_tip.size > 26:
            font_tip = load_font(fonts_regular, font_tip.size - 4)
            tl = wrap_text(draw, tip, font_tip, CONTENT_WIDTH - 60)
        tlh = draw.textbbox((0,0),"A",font=font_tip)[3]-draw.textbbox((0,0),"A",font=font_tip)[1]
        tls = int(tlh*1.5); tth = (len(tl)-1)*tls+tlh
        tpd = 28; tbh = tth + tpd*2
        tbox = Image.new('RGBA', (CONTENT_WIDTH, tbh), (255,210,160,200))
        td = ImageDraw.Draw(tbox)
        td.rounded_rectangle([(0,0),(CONTENT_WIDTH,tbh)], radius=12, fill=(255,210,160,200))
        for i,line in enumerate(tl):
            ly = tpd + (i*tls) + tlh//2
            td.text((CONTENT_WIDTH//2, ly), line, fill=(70,45,25), font=font_tip, anchor="mm")
        img.paste(tbox, (MARGIN_X, y), tbox)

    draw.rectangle([(0,VIDEO_HEIGHT-65),(VIDEO_WIDTH,VIDEO_HEIGHT)], fill=F_CLR)
    draw.text((CENTER_X,VIDEO_HEIGHT-32), f"Fix your English daily  |  {CHANNEL_NAME}", fill=(210,200,220), font=font_footer, anchor="mm")

    img = img.convert('RGB')
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=96, optimize=True)
    print(f"[image] {Path(out_path).name}")
    return out_path

def create_video(image_files, audio_files, out_file):
    print(f"[video] {len(image_files)} images...")
    clips = []
    for i, (ip, ai) in enumerate(zip(image_files, audio_files)):
        tc = Path(out_file).parent / f"c_{i}.mp4"
        d = ai["duration"]
        subprocess.run(["ffmpeg","-y","-loop","1","-i",str(ip),"-i",str(ai["file"]),
            "-vf",f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v","libx264","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
            "-t",f"{d}","-shortest",str(tc)], capture_output=True)
        ad = get_audio_duration(str(tc)); print(f"  Clip {i+1}: {ad:.1f}s"); clips.append(tc)
    if not clips: return False
    cf = Path(out_file).parent / "cl.txt"
    with open(cf,"w") as f:
        for c in clips: f.write(f"file '{str(c.resolve()).replace(chr(92),chr(47))}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(cf),"-c","copy",str(out_file)], capture_output=True)
    for c in clips:
        if c.exists(): c.unlink()
    if cf.exists(): cf.unlink()
    print(f"[video] {Path(out_file).name}")
    return True

def generate_reel():
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()}\n{'='*80}\n")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rd = VIDEO_DIR / f"mistakes_{ts}"; rd.mkdir()
    print("[1/3] Generating advanced mistakes...")
    items = generate_mistake_data(WORDS_PER_VIDEO)
    for i,m in enumerate(items,1): print(f"  {i}. {m['pair']}")
    print("\n[2/3] Generating images...")
    bg = create_background(); imgs = []
    for i,m in enumerate(items):
        ip = rd / f"m_{i}.jpg"; generate_word_image(m,bg,str(ip)); imgs.append(str(ip))
    print("\n[3/3] Generating audio & video...")
    af,td = generate_all_audio(items,str(rd)); fa=rd/"narration.mp3"; create_final_audio(af,str(fa))
    ov=rd/"final_reel.mp4"; create_video(imgs,af,str(ov))
    meta={"channel":CHANNEL_NAME,"mistakes":items,"timestamp":ts,"video":str(ov),"duration":td}
    with open(rd/"metadata.json","w") as f: json.dump(meta,f,indent=2)
    print(f"\n{'='*80}\n  COMPLETE! {td:.1f}s\n{'='*80}\n")
    return meta

if __name__=="__main__":
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()}\n{'='*80}\n"); generate_reel()
