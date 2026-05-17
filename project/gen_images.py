"""
Генератор изображений для карточек товаров.
Создаёт PNG 600x600 с фирменным оформлением для каждого напитка,
затем записывает путь в БД (поле Product.image).
"""
import os, sys, math, random, sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = Path(__file__).resolve().parent
MEDIA = BASE / 'media' / 'products'
MEDIA.mkdir(parents=True, exist_ok=True)
DB = BASE / 'db.sqlite3'

W, H = 600, 600

# ---------- Загрузка шрифтов ----------
def find_font():
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

FONT_BOLD = find_font() or ''
FONT_REG = FONT_BOLD.replace('-Bold', '') if FONT_BOLD else ''

def font(sz, bold=True):
    p = FONT_BOLD if bold else (FONT_REG or FONT_BOLD)
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()

# ---------- Утилиты рисования ----------
def vgradient(img, c1, c2):
    """Вертикальный градиент во весь холст."""
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))

def radial_highlight(img, cx, cy, radius, color, alpha=120):
    """Мягкая радиальная подсветка."""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -4):
        a = int(alpha * (1 - r / radius) ** 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=(color[0], color[1], color[2], a))
    img.alpha_composite(overlay)

def draw_bubbles(img, n=25, tint=(255, 255, 255)):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    random.seed(hash(tint) & 0xFFFF)
    for _ in range(n):
        x = random.randint(20, W - 20)
        y = random.randint(20, H - 20)
        r = random.randint(4, 22)
        a = random.randint(40, 150)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(*tint, a), width=2)
    img.alpha_composite(overlay)

def draw_drops(img, n=18, tint=(255, 255, 255)):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    random.seed(42)
    for _ in range(n):
        x = random.randint(30, W - 30)
        y = random.randint(30, H - 30)
        r = random.randint(3, 9)
        a = random.randint(60, 180)
        d.ellipse([x - r, y - r * 1.4, x + r, y + r * 1.4], fill=(*tint, a))
    img.alpha_composite(overlay)

def draw_bottle(img, body_color, cap_color=(60, 60, 60),
                label_color=(255, 255, 255), shape='bottle'):
    """Стилизованная бутылка/банка по центру холста."""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    cx = W // 2
    if shape == 'can':
        # банка: скруглённый прямоугольник
        bw, bh = 200, 360
        x0, y0 = cx - bw // 2, 150
        x1, y1 = cx + bw // 2, y0 + bh
        d.rounded_rectangle([x0, y0, x1, y1], radius=22,
                            fill=body_color, outline=(0, 0, 0, 120), width=2)
        # верхний обод
        d.rounded_rectangle([x0 + 6, y0 - 8, x1 - 6, y0 + 14], radius=6,
                            fill=(190, 190, 190, 255), outline=(80, 80, 80, 200), width=1)
        # блик
        d.rounded_rectangle([x0 + 18, y0 + 30, x0 + 42, y1 - 30], radius=10,
                            fill=(255, 255, 255, 70))
        # этикетка
        lx0, ly0 = x0 + 14, y0 + 110
        lx1, ly1 = x1 - 14, y1 - 90
        d.rounded_rectangle([lx0, ly0, lx1, ly1], radius=8,
                            fill=label_color, outline=(0, 0, 0, 60), width=1)
        img.alpha_composite(overlay)
        return (lx0, ly0, lx1, ly1)

    # Классическая PET-бутылка
    neck_top = 120
    neck_bottom = 175
    body_top = 200
    body_bottom = 480
    neck_w = 70
    body_w = 210

    # Крышка
    cap_w = 80
    d.rounded_rectangle(
        [cx - cap_w // 2, neck_top - 30, cx + cap_w // 2, neck_top + 5],
        radius=8, fill=cap_color, outline=(0, 0, 0, 120), width=2)
    # резьба (тонкие линии)
    for i, y in enumerate(range(neck_top - 26, neck_top + 2, 6)):
        d.line([cx - cap_w // 2 + 4, y, cx + cap_w // 2 - 4, y],
               fill=(0, 0, 0, 60), width=1)

    # Горлышко
    d.polygon([
        (cx - neck_w // 2, neck_top),
        (cx + neck_w // 2, neck_top),
        (cx + neck_w // 2 + 5, neck_bottom - 10),
        (cx + body_w // 2, body_top),
        (cx - body_w // 2, body_top),
        (cx - neck_w // 2 - 5, neck_bottom - 10),
    ], fill=body_color, outline=(0, 0, 0, 100))

    # Тело
    d.rounded_rectangle(
        [cx - body_w // 2, body_top, cx + body_w // 2, body_bottom],
        radius=28, fill=body_color, outline=(0, 0, 0, 100), width=2)

    # Блик слева
    d.rounded_rectangle(
        [cx - body_w // 2 + 14, body_top + 20,
         cx - body_w // 2 + 38, body_bottom - 20],
        radius=12, fill=(255, 255, 255, 80))

    # Этикетка
    lx0 = cx - body_w // 2 + 8
    lx1 = cx + body_w // 2 - 8
    ly0 = body_top + 80
    ly1 = body_bottom - 60
    d.rounded_rectangle([lx0, ly0, lx1, ly1], radius=10,
                        fill=label_color, outline=(0, 0, 0, 60), width=1)

    img.alpha_composite(overlay)
    return (lx0, ly0, lx1, ly1)

def text_fit(draw, text, max_w, start_size, font_bold=True):
    """Подобрать размер шрифта, чтобы текст влез по ширине."""
    sz = start_size
    while sz > 10:
        f = font(sz, font_bold)
        bbox = draw.textbbox((0, 0), text, font=f)
        if bbox[2] - bbox[0] <= max_w:
            return f, bbox
        sz -= 2
    return font(sz, font_bold), draw.textbbox((0, 0), text, font=f)

def wrap_text(draw, text, max_w, f):
    """Разбить текст на строки по словам."""
    words = text.split()
    lines, cur = [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        bbox = draw.textbbox((0, 0), test, font=f)
        if bbox[2] - bbox[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_label_text(img, label_box, name, volume, text_color=(30, 30, 30)):
    d = ImageDraw.Draw(img)
    lx0, ly0, lx1, ly1 = label_box
    lw = lx1 - lx0 - 20
    # Название — подобрать шрифт
    f = font(34, True)
    lines = wrap_text(d, name, lw, f)
    while len(lines) > 2 and f.size > 18:
        f = font(f.size - 2, True)
        lines = wrap_text(d, name, lw, f)
    line_h = f.size + 4
    total_h = line_h * len(lines)
    y = ly0 + (ly1 - ly0) // 2 - total_h // 2 - 10
    for line in lines:
        bbox = d.textbbox((0, 0), line, font=f)
        tw = bbox[2] - bbox[0]
        d.text((lx0 + (lx1 - lx0 - tw) // 2, y), line,
               font=f, fill=text_color)
        y += line_h
    # Объём
    fv = font(22, True)
    bbox = d.textbbox((0, 0), volume, font=fv)
    tw = bbox[2] - bbox[0]
    d.text((lx0 + (lx1 - lx0 - tw) // 2, ly1 - 34), volume,
           font=fv, fill=text_color)

def draw_volume_badge(img, volume, color=(255, 255, 255), bg=(0, 0, 0, 180)):
    """Бейдж с объёмом в правом нижнем углу."""
    d = ImageDraw.Draw(img)
    f = font(26, True)
    bbox = d.textbbox((0, 0), volume, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 14
    x1, y1 = W - 24, H - 24
    x0, y0 = x1 - tw - pad * 2, y1 - th - pad * 2
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    ov.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=bg)
    img.alpha_composite(overlay)
    d.text((x0 + pad, y0 + pad - 2), volume, font=f, fill=color)

def draw_category_tag(img, tag, color=(255, 255, 255, 230), text_color=(20, 20, 20)):
    """Метка категории сверху слева."""
    d = ImageDraw.Draw(img)
    f = font(18, True)
    bbox = d.textbbox((0, 0), tag, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 10
    x0, y0 = 24, 24
    x1, y1 = x0 + tw + pad * 2, y0 + th + pad * 2
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    ov.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=color)
    img.alpha_composite(overlay)
    d.text((x0 + pad, y0 + pad - 2), tag, font=f, fill=text_color)

# ---------- Палитра под каждый товар ----------
# (bg1, bg2, bottle_color, cap_color, label_color, label_text_color, shape, tag, decor)
# decor: 'bubbles' | 'drops' | None
PRESETS = {
    'legenda-gor':      ((173, 216, 230), (25, 90, 160),  (180, 220, 235, 210), (70, 80, 90),   (255, 255, 255), (20, 60, 110), 'bottle', 'ВОДА', 'drops'),
    'aqua-bishkek':     ((200, 230, 250), (40, 120, 200), (220, 240, 255, 210), (50, 60, 70),   (255, 255, 255), (20, 80, 150), 'bottle', 'ВОДА', 'drops'),
    'tamchy':           ((150, 210, 220), (20, 80, 130),  (200, 230, 240, 210), (60, 70, 80),   (245, 250, 255), (10, 70, 120), 'bottle', 'ВОДА', 'drops'),

    'rich-orange':      ((255, 220, 160), (230, 120, 20),  (255, 170, 60, 255),  (120, 60, 0),   (255, 240, 210), (180, 80, 0),  'bottle', 'СОК',  'drops'),
    'dobry-apple':      ((220, 245, 200), (70, 150, 40),   (180, 220, 90, 255),  (90, 60, 30),   (255, 255, 230), (60, 110, 30), 'bottle', 'СОК',  'drops'),
    'j7-multi':         ((255, 230, 200), (220, 90, 60),   (240, 140, 80, 255),  (80, 40, 20),   (255, 245, 220), (160, 50, 30), 'bottle', 'СОК',  'drops'),
    'moya-semya-cherry':((255, 200, 200), (150, 20, 40),   (180, 30, 50, 255),   (60, 20, 20),   (255, 230, 230), (110, 10, 30), 'bottle', 'СОК',  'drops'),

    'coca-cola':        ((230, 40, 40),   (120, 0, 0),     (30, 30, 30, 255),    (200, 30, 30),  (220, 30, 30),   (255, 255, 255),'bottle','ГАЗИРОВКА','bubbles'),
    'fanta-orange':     ((255, 170, 60),  (210, 80, 0),    (255, 140, 30, 255),  (40, 110, 40),  (255, 140, 30),  (255, 255, 255),'bottle','ГАЗИРОВКА','bubbles'),
    'sprite':           ((180, 230, 140), (30, 120, 50),   (160, 220, 120, 255), (60, 60, 60),   (40, 160, 70),   (255, 255, 255),'bottle','ГАЗИРОВКА','bubbles'),
    'shoro-maksym':     ((210, 180, 130), (110, 70, 30),   (180, 140, 90, 255),  (60, 40, 20),   (245, 230, 200), (90, 50, 20),  'bottle','ГАЗИРОВКА','bubbles'),
    'shoro-chalap':     ((230, 220, 200), (130, 110, 80),  (240, 230, 210, 255), (70, 60, 40),   (255, 250, 235), (90, 70, 30),  'bottle','ГАЗИРОВКА','bubbles'),

    'fuze-tea-lemon':   ((255, 230, 120), (180, 140, 30),  (245, 210, 80, 255),  (40, 80, 30),   (255, 245, 200), (120, 90, 20), 'bottle','ЧАЙ',   None),
    'lipton-peach':     ((255, 210, 140), (200, 110, 40),  (250, 200, 130, 255), (230, 180, 30), (255, 230, 190), (150, 80, 20), 'bottle','ЧАЙ',   None),
    'arizona-green':    ((190, 230, 180), (40, 110, 60),   (170, 210, 150, 255), (200, 30, 40),  (230, 250, 210), (30, 90, 40),  'bottle','ЧАЙ',   None),

    'nescafe-latte':    ((210, 170, 130), (90, 50, 20),    (230, 190, 140, 255), (140, 30, 30),  (180, 40, 40),   (255, 255, 255),'can',   'КОФЕ',  None),
    'burn-macchiato':   ((180, 130, 90),  (40, 20, 10),    (60, 40, 30, 255),    (200, 30, 30),  (60, 40, 30),    (255, 210, 120),'can',   'КОФЕ',  None),

    'red-bull':         ((130, 170, 210), (30, 60, 130),   (50, 80, 150, 255),   (200, 170, 40), (230, 200, 60),  (30, 50, 120), 'can',   'ЭНЕРГЕТИК','bubbles'),
    'monster-energy':   ((40, 60, 40),    (10, 20, 10),    (20, 25, 20, 255),    (80, 200, 40),  (20, 25, 20),    (120, 230, 60),'can',   'ЭНЕРГЕТИК','bubbles'),
    'adrenaline-rush':  ((180, 40, 40),   (60, 10, 10),    (50, 30, 30, 255),    (200, 50, 50),  (180, 40, 40),   (255, 230, 60),'can',   'ЭНЕРГЕТИК','bubbles'),

    'bishkek-sut-ayran':((245, 235, 215), (180, 160, 120), (255, 250, 240, 255), (60, 110, 170), (255, 250, 240), (30, 70, 130), 'bottle','МОЛОЧНЫЙ', None),
    'kumys':            ((240, 230, 210), (160, 140, 100), (250, 245, 230, 255), (120, 80, 30),  (250, 245, 230), (90, 50, 20),  'bottle','МОЛОЧНЫЙ', None),
    'aktual-peach':     ((255, 220, 200), (220, 140, 110), (255, 210, 180, 255), (200, 80, 60),  (255, 230, 210), (170, 70, 40), 'bottle','МОЛОЧНЫЙ', None),
}

# ---------- Генерация ----------
def generate(slug, name, volume):
    preset = PRESETS.get(slug)
    if not preset:
        # запасной вариант
        preset = ((220, 220, 220), (90, 90, 90), (180, 180, 180, 255),
                  (60, 60, 60), (255, 255, 255), (30, 30, 30), 'bottle', 'НАПИТОК', None)
    bg1, bg2, body, cap, label, text_col, shape, tag, decor = preset

    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # фон-градиент
    bg = Image.new('RGB', (W, H))
    vgradient(bg, bg1, bg2)
    img.paste(bg, (0, 0))
    img = img.convert('RGBA')

    # мягкое свечение за бутылкой
    radial_highlight(img, W // 2, H // 2 + 40, 320, (255, 255, 255), alpha=90)

    # декор
    if decor == 'bubbles':
        draw_bubbles(img, n=30, tint=(255, 255, 255))
    elif decor == 'drops':
        draw_drops(img, n=22, tint=(255, 255, 255))

    # бутылка/банка
    label_box = draw_bottle(img, body_color=body, cap_color=cap,
                            label_color=label, shape=shape)

    # текст на этикетке
    draw_label_text(img, label_box, name, volume, text_color=text_col)

    # метка категории и бейдж объёма
    draw_category_tag(img, tag)
    draw_volume_badge(img, volume)

    # лёгкая виньетка
    vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for i in range(40):
        vd.rectangle([i, i, W - i, H - i],
                     outline=(0, 0, 0, 3), width=1)
    img.alpha_composite(vignette)

    out = MEDIA / f'{slug}.png'
    img.convert('RGB').save(out, 'PNG', optimize=True)
    return out

# ---------- Основной проход ----------
def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT id, name, slug, volume FROM store_product ORDER BY id')
    rows = cur.fetchall()
    print(f'Товаров к обработке: {len(rows)}')
    for pid, name, slug, volume in rows:
        path = generate(slug, name, volume)
        rel = f'products/{path.name}'
        cur.execute('UPDATE store_product SET image = ? WHERE id = ?', (rel, pid))
        print(f'  [{pid:2d}] {name:28s} → {rel}')
    conn.commit()
    conn.close()
    print('\nГотово. Все картинки записаны в media/products/ и прописаны в БД.')

if __name__ == '__main__':
    main()
