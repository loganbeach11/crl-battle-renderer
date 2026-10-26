"""CRL 20-Win battle cards. Uses API card icon URLs, not Google Slides."""
import io
import json
import os
import re
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 2400, 1120
BG = (9, 15, 30)
WHITE = (248, 250, 255)
GOLD = (255, 203, 66)
CYAN = (62, 203, 253)
MAGENTA = (199, 117, 249)
MUTED = (179, 198, 223)
ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)


def font(size, bold=True):
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def fit_text(draw, text, size, max_width, min_size=24):
    text = str(text or '')
    while size > min_size and draw.textbbox((0, 0), text, font=font(size))[2] > max_width:
        size -= 2
    if draw.textbbox((0, 0), text, font=font(size))[2] > max_width:
        while text and draw.textbbox((0, 0), text + '…', font=font(size))[2] > max_width:
            text = text[:-1]
        text += '…'
    return text, font(size)


def image_url(card):
    urls = card.get('iconUrls') or {}
    return urls.get('evolutionMedium') if card.get('evolutionLevel') and urls.get('evolutionMedium') else urls.get('medium', '')


def fetch_art(url):
    if not url or not url.startswith('https://'):
        return None
    try:
        res = requests.get(url, timeout=12, headers={'User-Agent': 'CRL-Battle-Renderer/1.0'})
        res.raise_for_status()
        return Image.open(io.BytesIO(res.content)).convert('RGBA')
    except Exception as e:
        print('Card art unavailable:', str(e)[:120])
        return None


def card_slot(canvas, draw, card, x, y, width=220, height=273):
    draw.rounded_rectangle((x - 4, y - 4, x + width + 4, y + height + 4), radius=15, fill=(36, 54, 79), outline=(69, 94, 129), width=3)
    pic = fetch_art(image_url(card))
    if pic:
        # Card images have differing aspect ratios; contain rather than distort.
        pic.thumbnail((width, height), Image.Resampling.LANCZOS)
        canvas.alpha_composite(pic, (int(x + (width-pic.width)/2), int(y + (height-pic.height)/2)))
    else:
        name, f = fit_text(draw, card.get('name', '?'), 24, width - 18, 18)
        draw.text((x + width/2, y + height/2), name, anchor='mm', font=f, fill=WHITE)


def make_image(event):
    milestone = int(event.get('milestone', 17))
    player = event.get('player') or {}
    opponent = event.get('opponent') or {}
    canvas = Image.new('RGBA', (W,H), (*BG,255))
    draw = ImageDraw.Draw(canvas)
    # Atmospheric background, high-res drawn natively.
    bloom = Image.new('RGBA', (W,H), (0,0,0,0))
    glow = ImageDraw.Draw(bloom)
    glow.ellipse((260, -700, 1650, 560), fill=(24, 102, 158, 88))
    glow.ellipse((1200, -580, 2740, 620), fill=(101, 42, 155, 82))
    bloom = bloom.filter(ImageFilter.GaussianBlur(170))
    canvas.alpha_composite(bloom)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0,0,W,11), fill=GOLD)
    draw.text((W//2, 54), 'CRL 20-WIN CHALLENGE', anchor='mt', font=font(80), fill=WHITE, stroke_width=1)
    draw.text((W//2, 166), f'{milestone} WINS', anchor='mt', font=font(112), fill=GOLD, stroke_width=2, stroke_fill=(95, 63, 12))
    result = f"{event.get('crownsFor', 0)}  -  {event.get('crownsAgainst', 0)}"
    draw.text((W//2, 307), result, anchor='mt', font=font(79), fill=WHITE)
    draw.rounded_rectangle((46,56,334,132), radius=16, fill=(19, 122, 98))
    draw.text((190,92),'VICTORY',anchor='mm',font=font(41),fill=WHITE)
    draw.line([(60, 408),(1110,408)], fill=CYAN, width=8)
    draw.line([(1290,408),(2340,408)], fill=MAGENTA, width=8)
    # Two name areas.
    for side, p, color in [('left', player, CYAN), ('right', opponent, MAGENTA)]:
        x = 64 if side == 'left' else 1274
        name, f = fit_text(draw, p.get('name') or 'Unknown', 60, 1040)
        draw.text((x, 439), name, font=f, fill=WHITE)
        clan = (p.get('clan') or {}).get('name') or 'No clan'
        clan, cf = fit_text(draw, clan, 39, 1040, 22)
        draw.text((x, 520), clan, font=cf, fill=color)
        draw.rounded_rectangle((x-12, 585, x+1062, 1068), radius=30, fill=(20, 34, 57, 235), outline=(45, 67, 98), width=3)
        cards = p.get('cards') or []
        for idx, card in enumerate(cards[:8]):
            # 4 columns, 2 rows, 220px art cards; 3x screenshot size.
            cx = x + 20 + (idx % 4)*257
            cy = 613 + (idx // 4)*224
            card_slot(canvas, draw, card, cx, cy, 207, 193)
    return canvas.convert('RGB')


def post_discord(file_path, event):
    hook = os.getenv('DISCORD_WEBHOOK', '').strip()
    if not hook:
        print('No webhook secret: preview only.')
        return
    # Don't echo player names into GitHub Actions logs; send title within attachment instead.
    message = {'content': f"**CRL 20-Win Challenge — {event['milestone']} wins**", 'allowed_mentions': {'parse': []}}
    for attempt in range(1, 4):
        with open(file_path, 'rb') as f:
            res = requests.post(hook, data={'payload_json': json.dumps(message)}, files={'files[0]': (file_path.name, f, 'image/png')}, timeout=35)
        if 200 <= res.status_code < 300:
            print('Discord delivery successful')
            return
        if res.status_code == 429:
            try:
                retry = float(res.json().get('retry_after', 15))
            except Exception:
                retry = 15
            retry = min(100, max(2, retry))
            print(f'Discord rate limit; retry delay {retry}s')
            if attempt < 3:
                time.sleep(retry)
                continue
        raise RuntimeError(f'Discord delivery failed: HTTP {res.status_code}; response prefix: {res.text[:90]}')
    raise RuntimeError('Discord rate limit did not clear')


def main():
    payload = os.getenv('PAYLOAD_JSON', '{}')
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        event = {}
    if not event or not event.get('player'):
        # Manual workflow_dispatch is only a connectivity check, no fake battle posted.
        print('No battle payload: run via Apps Script dispatch to render a real match.')
        return
    if int(event.get('milestone', 0)) not in [17,18,19,20]:
        raise ValueError('Only 17–20 win milestones supported')
    img = make_image(event)
    name = re.sub(r'[^A-Za-z0-9_-]', '_', str(event.get('milestone', 'win')))
    dst = OUTPUT / f'crl_{name}_wins.png'
    img.save(dst, format='PNG', optimize=True)
    print(f'Generated {dst.name}: {img.width}x{img.height}')
    if event.get('previewOnly') is not True:
        post_discord(dst, event)

if __name__ == '__main__':
    main()
