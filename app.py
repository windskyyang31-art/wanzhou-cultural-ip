import streamlit as st
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter


# ==========================
# 页面基础设置
# ==========================

st.set_page_config(
    page_title="万川汇流·山水风华",
    page_icon="🌊",
    layout="wide"
)


# ==========================
# 读取首页背景图片
# ==========================

image_path = Path("images/home_bg.jpg")

if image_path.exists():
    image_base64 = base64.b64encode(image_path.read_bytes()).decode()
else:
    image_base64 = ""


# ==========================
# 初始化状态
# ==========================

if "selected_scene" not in st.session_state:
    st.session_state.selected_scene = None

if "stamps" not in st.session_state:
    st.session_state.stamps = []

if "memories" not in st.session_state:
    st.session_state.memories = []

if "generated_card_bytes" not in st.session_state:
    st.session_state.generated_card_bytes = None

if "generated_ip_bytes" not in st.session_state:
    st.session_state.generated_ip_bytes = None

if "generated_ip_index" not in st.session_state:
    st.session_state.generated_ip_index = None


# ==========================
# 四幕内容数据库
# ==========================

SCENES = {
    "山静": {
        "icon": "⛰",
        "subtitle": "山之骨",
        "places": "太白岩｜天生城｜西山钟楼",
        "keywords": "厚重、守望、历史、静谧、城市记忆",
        "title": "山静：在山体与遗迹中看见万州的时间",
        "story": (
            "万州的山是静的。太白岩、天生城、西山钟楼共同构成了城市的历史骨架。"
            "它们并不喧哗，却长期守望着江岸、街巷与人群，承载着万州从旧城记忆到今日生活的时间层次。"
        ),
        "guide": (
            "欢迎游客上传登高、远眺、古迹打卡照片；欢迎本地居民上传山城日常、老城记忆、钟楼印象。"
            "这些照片将共同组成“山静记忆墙”。"
        ),
    },
    "水生": {
        "icon": "🌊",
        "subtitle": "水之脉",
        "places": "长江水系｜万州大瀑布｜高峡平湖",
        "keywords": "流动、连接、滋养、循环、生命力",
        "title": "水生：在江流与瀑布中感受生命的流动",
        "story": (
            "万州的水看似平静，却从未停止流动。长江连接百川，瀑布带来山水的冲击力，"
            "高峡平湖则呈现今日万州开阔、平稳而持续生长的城市气质。"
        ),
        "guide": (
            "欢迎上传江边散步、游船、瀑布、平湖、日落等照片。"
            "每一张照片都是一次水流中的个人记忆。"
        ),
    },
    "人聚": {
        "icon": "👥",
        "subtitle": "人之情",
        "places": "三峡移民｜城市生活｜江边烟火",
        "keywords": "相遇、重建、共享、生活、温度",
        "title": "人聚：在迁徙与重建中理解万州的生活温度",
        "story": (
            "万州的核心不只是山水，更是人。三峡移民在这里重新聚集、重新安家、重新分享生活。"
            "平静的江面之下，是一代代人勤劳建设、共同生活、不断向前的力量。"
        ),
        "guide": (
            "游客可以上传与朋友、家人、市集、街巷有关的照片；本地居民可以上传自己的日常生活、"
            "家庭记忆、老照片或新生活场景。人聚不是一句口号，而是在照片与文字中不断形成的共同记忆。"
        ),
    },
    "城兴": {
        "icon": "🏙",
        "subtitle": "城之生",
        "places": "三峡港湾｜高峡平湖｜今日万州",
        "keywords": "开放、连接、未来、生长、活力",
        "title": "城兴：在港湾与灯火中看见今日万州",
        "story": (
            "三峡港湾与城市灯火展现了今日万州的现代气象。港口运输、桥梁连接、江岸更新，"
            "让这座城市不只是山水之城，也是面向未来的开放之城。"
        ),
        "guide": (
            "欢迎上传港湾夜景、城市街道、桥梁、建筑、码头与现代生活场景。"
            "这些内容将共同呈现今日万州的城市生长。"
        ),
    },
}


# ==========================
# 字体与绘图工具函数
# ==========================

def get_font(size=36, bold=False):
    if bold:
        candidates = [
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

    for font_path in candidates:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                pass

    return ImageFont.load_default()


def wrap_text_by_width(draw, text, font, max_width):
    lines = []
    current = ""

    for char in text:
        test_line = current + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = char

    if current:
        lines.append(current)

    return lines


def add_rounded_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (0, 0, image.size[0], image.size[1]),
        radius=radius,
        fill=255
    )

    result = Image.new("RGBA", image.size)
    result.paste(image, (0, 0))
    result.putalpha(mask)
    return result


def circular_crop(image, size):
    image = ImageOps.exif_transpose(image.convert("RGB"))
    image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size))
    result.paste(image, (0, 0))
    result.putalpha(mask)
    return result


def draw_centered_text(draw, box, text, font, fill):
    x1, y1, x2, y2 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = x1 + (x2 - x1 - text_w) / 2
    y = y1 + (y2 - y1 - text_h) / 2 - 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_stamp_chip(draw, x1, y1, x2, y2, text, font, fill_color, outline_color, text_color):
    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=18,
        fill=fill_color,
        outline=outline_color,
        width=2
    )
    draw_centered_text(draw, (x1, y1, x2, y2), text, font, text_color)


def rgb_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def mix_color(c1, c2, ratio=0.5):
    r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
    g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
    b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
    return (r, g, b)


def lighten(c, amount=0.25):
    r = int(c[0] + (255 - c[0]) * amount)
    g = int(c[1] + (255 - c[1]) * amount)
    b = int(c[2] + (255 - c[2]) * amount)
    return (r, g, b)


def darken(c, amount=0.2):
    r = int(c[0] * (1 - amount))
    g = int(c[1] * (1 - amount))
    b = int(c[2] * (1 - amount))
    return (r, g, b)


def extract_main_color(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = ImageOps.exif_transpose(img)
    img = img.resize((1, 1))
    return img.getpixel((0, 0))


def draw_vertical_gradient(draw, x1, y1, x2, y2, top_color, bottom_color):
    height = y2 - y1
    for i in range(height):
        ratio = i / max(height - 1, 1)
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line((x1, y1 + i, x2, y1 + i), fill=(r, g, b))


# ==========================
# 装饰图形函数
# ==========================

def draw_cloud(draw, x, y, scale, fill):
    draw.ellipse((x, y, x + 50*scale, y + 36*scale), fill=fill)
    draw.ellipse((x + 28*scale, y - 10*scale, x + 88*scale, y + 34*scale), fill=fill)
    draw.ellipse((x + 70*scale, y, x + 120*scale, y + 36*scale), fill=fill)
    draw.rounded_rectangle((x + 14*scale, y + 18*scale, x + 102*scale, y + 42*scale), radius=int(10*scale), fill=fill)


def draw_mountain(draw, x, y, scale, fill):
    draw.polygon(
        [
            (x, y + 70*scale),
            (x + 45*scale, y),
            (x + 90*scale, y + 70*scale)
        ],
        fill=fill
    )
    draw.polygon(
        [
            (x + 55*scale, y + 75*scale),
            (x + 120*scale, y - 10*scale),
            (x + 190*scale, y + 75*scale)
        ],
        fill=fill
    )


def draw_wave(draw, x, y, scale, fill):
    for i in range(3):
        x0 = x + i * 72 * scale
        draw.arc((x0, y, x0 + 70*scale, y + 34*scale), start=180, end=360, fill=fill, width=max(2, int(4*scale)))
        draw.arc((x0 + 30*scale, y + 8*scale, x0 + 95*scale, y + 42*scale), start=180, end=360, fill=fill, width=max(2, int(4*scale)))


def draw_lantern(draw, x, y, scale, fill, line_color):
    draw.line((x + 20*scale, y, x + 20*scale, y + 18*scale), fill=line_color, width=max(2, int(3*scale)))
    draw.rounded_rectangle((x, y + 18*scale, x + 40*scale, y + 75*scale), radius=int(12*scale), fill=fill, outline=line_color, width=max(2, int(3*scale)))
    draw.line((x + 10*scale, y + 78*scale, x + 30*scale, y + 78*scale), fill=line_color, width=max(2, int(3*scale)))


def draw_skyline(draw, x, y, scale, fill):
    heights = [60, 80, 48, 92, 70, 55]
    widths = [28, 32, 25, 36, 30, 24]
    cursor = x
    for w, h in zip(widths, heights):
        draw.rectangle((cursor, y + (95-h)*scale, cursor + w*scale, y + 95*scale), fill=fill)
        cursor += (w + 10) * scale


def draw_bridge(draw, x, y, scale, fill):
    draw.line((x, y + 65*scale, x + 180*scale, y + 65*scale), fill=fill, width=max(2, int(5*scale)))
    draw.line((x + 55*scale, y + 10*scale, x + 55*scale, y + 65*scale), fill=fill, width=max(2, int(5*scale)))
    draw.line((x + 125*scale, y + 10*scale, x + 125*scale, y + 65*scale), fill=fill, width=max(2, int(5*scale)))
    draw.line((x + 55*scale, y + 10*scale, x + 20*scale, y + 65*scale), fill=fill, width=max(2, int(3*scale)))
    draw.line((x + 55*scale, y + 10*scale, x + 90*scale, y + 65*scale), fill=fill, width=max(2, int(3*scale)))
    draw.line((x + 125*scale, y + 10*scale, x + 90*scale, y + 65*scale), fill=fill, width=max(2, int(3*scale)))
    draw.line((x + 125*scale, y + 10*scale, x + 160*scale, y + 65*scale), fill=fill, width=max(2, int(3*scale)))


# ==========================
# 本地版 Q版IP 生成函数
# ==========================

def create_local_ip_image(memory):
    scene = memory["scene"]
    identity = memory.get("type", "").strip()
    if identity == "":
        identity = "万州记忆共创者"

    quote = memory.get("text", "").strip()
    if quote == "":
        quote = "我在万州，遇见山水与生活。"

    palettes = {
        "山静": {
            "main": (27, 104, 95),
            "accent": (214, 168, 79),
            "bg_top": (243, 249, 244),
            "bg_bottom": (232, 240, 235),
            "deco": (196, 221, 205),
        },
        "水生": {
            "main": (45, 118, 177),
            "accent": (112, 192, 232),
            "bg_top": (240, 248, 253),
            "bg_bottom": (225, 239, 248),
            "deco": (190, 220, 241),
        },
        "人聚": {
            "main": (126, 74, 136),
            "accent": (232, 126, 92),
            "bg_top": (251, 244, 247),
            "bg_bottom": (246, 233, 239),
            "deco": (231, 204, 220),
        },
        "城兴": {
            "main": (31, 92, 115),
            "accent": (233, 167, 79),
            "bg_top": (243, 247, 250),
            "bg_bottom": (232, 238, 243),
            "deco": (202, 214, 223),
        }
    }

    p = palettes[scene]
    main = p["main"]
    accent = p["accent"]
    bg_top = p["bg_top"]
    bg_bottom = p["bg_bottom"]
    deco = p["deco"]

    photo_color = extract_main_color(memory["image"])
    outfit_color = mix_color(main, photo_color, 0.35)
    hair_color = darken(mix_color(photo_color, (70, 55, 45), 0.35), 0.1)
    skin_color = (250, 226, 203)

    w, h = 1600, 2000
    canvas = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(canvas)

    draw_vertical_gradient(draw, 0, 0, w, h, bg_top, bg_bottom)

    draw.rounded_rectangle(
        (70, 60, 1530, 1940),
        radius=42,
        fill=(248, 245, 238),
        outline=(228, 219, 206),
        width=3
    )

    draw.rounded_rectangle(
        (120, 110, 1480, 330),
        radius=32,
        fill=(255, 255, 255),
        outline=rgb_hex(deco),
        width=2
    )

    title_font = get_font(68, bold=True)
    sub_font = get_font(30, bold=True)
    text_font = get_font(30, bold=False)
    chip_font = get_font(28, bold=True)
    section_font = get_font(40, bold=True)
    small_font = get_font(24, bold=False)

    draw.text((170, 155), "我的万州专属IP形象", font=title_font, fill=main)
    draw.text((172, 240), "本地模板生成版 · 可爱 Q 版文旅角色", font=sub_font, fill=accent)

    chip_text = f"{scene}｜{identity[:12] + ('...' if len(identity) > 12 else '')}"
    draw.rounded_rectangle(
        (1010, 168, 1410, 228),
        radius=24,
        fill=lighten(accent, 0.8),
        outline=accent,
        width=2
    )
    draw_centered_text(draw, (1010, 168, 1410, 228), chip_text, chip_font, main)

    photo = Image.open(BytesIO(memory["image"])).convert("RGB")
    photo_circle = circular_crop(photo, 180)
    canvas.paste(photo_circle, (1250, 380), photo_circle)
    draw.ellipse((1242, 372, 1438, 568), outline=accent, width=4)
    draw.text((1260, 580), "灵感照片", font=small_font, fill=main)

    draw.rounded_rectangle(
        (140, 360, 1460, 1320),
        radius=40,
        fill=(255, 255, 255),
        outline=rgb_hex(deco),
        width=2
    )

    for i in range(6):
        x = 180 + i * 200
        draw.ellipse((x, 420, x + 70, 490), fill=lighten(deco, 0.3))

    if scene == "山静":
        draw_cloud(draw, 250, 430, 1.1, lighten(deco, 0.4))
        draw_cloud(draw, 1080, 460, 1.0, lighten(deco, 0.4))
        draw_mountain(draw, 260, 1090, 1.2, lighten(main, 0.55))
        draw_mountain(draw, 980, 1080, 0.9, lighten(main, 0.65))
    elif scene == "水生":
        draw_wave(draw, 230, 1110, 1.6, lighten(main, 0.5))
        draw_wave(draw, 930, 1095, 1.2, lighten(main, 0.65))
        draw_cloud(draw, 280, 440, 1.0, lighten(deco, 0.5))
    elif scene == "人聚":
        draw_cloud(draw, 260, 450, 0.9, lighten(deco, 0.4))
        draw_lantern(draw, 310, 430, 1.1, lighten(accent, 0.5), accent)
        draw_lantern(draw, 1170, 440, 1.0, lighten(accent, 0.6), accent)
    elif scene == "城兴":
        draw_skyline(draw, 230, 1110, 2.2, lighten(main, 0.55))
        draw_bridge(draw, 950, 1085, 2.0, lighten(main, 0.45))
        draw_cloud(draw, 260, 440, 0.9, lighten(deco, 0.45))

    draw.ellipse((560, 1040, 1040, 1140), fill=lighten(deco, 0.1))

    draw.ellipse((555, 430, 1045, 920), fill=skin_color, outline=lighten(main, 0.6), width=3)
    draw.pieslice((520, 360, 1080, 900), start=180, end=360, fill=hair_color)
    draw.rounded_rectangle((580, 540, 1015, 640), radius=40, fill=hair_color)

    draw.pieslice((570, 430, 720, 640), start=20, end=180, fill=hair_color)
    draw.pieslice((690, 410, 860, 650), start=10, end=190, fill=hair_color)
    draw.pieslice((835, 430, 1000, 650), start=0, end=170, fill=hair_color)

    draw.ellipse((525, 610, 595, 715), fill=skin_color)
    draw.ellipse((1005, 610, 1075, 715), fill=skin_color)

    draw.ellipse((670, 660, 705, 700), fill=(50, 50, 60))
    draw.ellipse((895, 660, 930, 700), fill=(50, 50, 60))
    draw.ellipse((682, 670, 692, 680), fill=(255, 255, 255))
    draw.ellipse((907, 670, 917, 680), fill=(255, 255, 255))

    draw.ellipse((605, 735, 685, 785), fill=(248, 194, 197))
    draw.ellipse((915, 735, 995, 785), fill=(248, 194, 197))

    draw.arc((735, 770, 860, 840), start=10, end=170, fill=(200, 95, 105), width=4)

    draw.rounded_rectangle((620, 920, 980, 1320), radius=95, fill=outfit_color)
    draw.rounded_rectangle((530, 960, 650, 1180), radius=50, fill=outfit_color)
    draw.rounded_rectangle((950, 960, 1070, 1180), radius=50, fill=outfit_color)

    draw.ellipse((520, 1140, 590, 1215), fill=skin_color)
    draw.ellipse((1010, 1140, 1080, 1215), fill=skin_color)

    draw.rounded_rectangle((690, 1300, 785, 1515), radius=35, fill=skin_color)
    draw.rounded_rectangle((815, 1300, 910, 1515), radius=35, fill=skin_color)

    draw.rounded_rectangle((660, 1490, 800, 1565), radius=24, fill=darken(outfit_color, 0.18))
    draw.rounded_rectangle((800, 1490, 940, 1565), radius=24, fill=darken(outfit_color, 0.18))

    if scene == "山静":
        draw_mountain(draw, 685, 335, 0.8, accent)
        draw.polygon([(620, 970), (800, 1030), (980, 970), (980, 1065), (620, 1065)], fill=lighten(accent, 0.3))
    elif scene == "水生":
        draw_wave(draw, 655, 340, 1.0, accent)
        draw_wave(draw, 675, 1070, 0.8, lighten(accent, 0.15))
    elif scene == "人聚":
        draw.ellipse((730, 355, 780, 405), fill=accent)
        draw.ellipse((775, 355, 825, 405), fill=accent)
        draw.polygon([(720, 385), (835, 385), (777, 455)], fill=accent)
        draw.rounded_rectangle((655, 935, 945, 1000), radius=25, fill=lighten(accent, 0.2))
    elif scene == "城兴":
        draw_skyline(draw, 660, 335, 1.3, accent)
        draw_bridge(draw, 670, 1075, 0.9, lighten(accent, 0.15))

    draw.rounded_rectangle(
        (140, 1370, 1460, 1850),
        radius=38,
        fill=(255, 255, 255),
        outline=rgb_hex(deco),
        width=2
    )

    draw.text((190, 1430), "IP角色设定", font=section_font, fill=main)

    identity_lines = wrap_text_by_width(draw, f"记忆身份：{identity}", text_font, 1150)
    y_cursor = 1515
    for line in identity_lines[:2]:
        draw.text((190, y_cursor), line, font=text_font, fill=(70, 85, 92))
        y_cursor += 46

    quote_lines = wrap_text_by_width(draw, f"万州记忆：{quote}", text_font, 1150)
    for line in quote_lines[:3]:
        draw.text((190, y_cursor), line, font=text_font, fill=(70, 85, 92))
        y_cursor += 46

    draw.text((190, 1710), "可延展为：", font=text_font, fill=main)

    chips = ["明信片主角", "文创贴纸", "徽章挂件", "表情包", "礼盒插卡"]
    chip_x = 190
    chip_y = 1770
    chip_w = 185
    chip_h = 54
    gap = 18

    for idx, chip in enumerate(chips):
        x1 = chip_x + idx * (chip_w + gap)
        x2 = x1 + chip_w
        draw_stamp_chip(
            draw,
            x1, chip_y, x2, chip_y + chip_h,
            chip,
            small_font,
            lighten(accent, 0.82),
            accent,
            main
        )

    draw.text((190, 1888), "说明：当前为本地版模板生成，不调用外部AI模型。", font=small_font, fill=(120, 128, 135))
    draw.text((190, 1915), "Wanzhou Cute Cultural IP Generator", font=small_font, fill=accent)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================
# 高清明信片生成函数：支持自动放入IP
# ==========================

def create_memory_card(memory, stamps, ip_bytes=None):
    card_w = 1800
    card_h = 2500

    bg_color = "#F3EFE6"
    dark_green = "#0F5B66"
    orange = "#E67E3A"
    gold = "#D6A84F"
    warm_gray = "#5D6770"
    deep_text = "#2F3742"
    line_color = "#D8D1C6"
    pale_green = "#EAF4F2"
    pale_orange = "#FFF3E8"
    white = "#FFFFFF"

    card = Image.new("RGB", (card_w, card_h), bg_color)
    draw = ImageDraw.Draw(card)

    title_font = get_font(76, bold=True)
    sub_font = get_font(40, bold=True)
    tag_font = get_font(28, bold=True)
    section_font = get_font(42, bold=True)
    body_font = get_font(32, bold=False)
    small_font = get_font(25, bold=False)
    stamp_font = get_font(26, bold=True)

    identity = memory.get("type", "").strip()
    if identity == "":
        identity = "万州记忆共创者"

    short_identity = identity
    if len(short_identity) > 12:
        short_identity = short_identity[:12] + "..."

    draw.rounded_rectangle(
        (70, 60, 1730, 2440),
        radius=42,
        fill="#F8F4EC",
        outline="#E2D9CC",
        width=3
    )

    draw.rounded_rectangle(
        (120, 110, 1680, 1125),
        radius=38,
        fill=white,
        outline=line_color,
        width=3
    )

    draw.rounded_rectangle(
        (170, 165, 1630, 370),
        radius=32,
        fill=pale_green
    )

    draw.text(
        (210, 200),
        "万川汇流 · 山水风华",
        font=title_font,
        fill=dark_green
    )

    draw.text(
        (214, 295),
        "我的万州山水记忆明信片",
        font=sub_font,
        fill=orange
    )

    chip_text = f"{memory['scene']}｜{short_identity}"
    draw.rounded_rectangle(
        (1120, 210, 1580, 275),
        radius=25,
        fill=white,
        outline=orange,
        width=2
    )

    draw_centered_text(
        draw,
        (1120, 210, 1580, 275),
        chip_text,
        tag_font,
        orange
    )

    photo = Image.open(BytesIO(memory["image"])).convert("RGB")
    photo = ImageOps.exif_transpose(photo)
    photo = ImageOps.fit(photo, (1420, 620), method=Image.Resampling.LANCZOS)
    photo = photo.filter(ImageFilter.SHARPEN)
    photo = add_rounded_corners(photo, radius=30)
    card.paste(photo, (190, 440), photo)

    draw.rounded_rectangle(
        (205, 980, 520, 1042),
        radius=22,
        fill=white
    )

    draw.text(
        (235, 998),
        "万州现场记忆",
        font=small_font,
        fill=dark_green
    )

    if ip_bytes is not None:
        ip_img = Image.open(BytesIO(ip_bytes)).convert("RGB")
        ip_img = ImageOps.fit(ip_img, (330, 410), method=Image.Resampling.LANCZOS)
        ip_img = add_rounded_corners(ip_img, radius=26)

        draw.rounded_rectangle(
            (1240, 620, 1600, 1070),
            radius=32,
            fill=(255, 255, 255),
            outline=orange,
            width=4
        )

        card.paste(ip_img, (1255, 640), ip_img)

        draw.rounded_rectangle(
            (1270, 1010, 1585, 1060),
            radius=18,
            fill=pale_orange,
            outline=orange,
            width=2
        )
        draw_centered_text(
            draw,
            (1270, 1010, 1585, 1060),
            "专属IP已联名",
            small_font,
            orange
        )

    slogan = "沿长江之脉，感受山、水、人、城共同生长的力量"
    bbox = draw.textbbox((0, 0), slogan, font=body_font)
    slogan_w = bbox[2] - bbox[0]
    draw.text(
        ((card_w - slogan_w) / 2, 1070),
        slogan,
        font=body_font,
        fill=warm_gray
    )

    draw.rounded_rectangle(
        (120, 1195, 1680, 2350),
        radius=38,
        fill=white,
        outline=line_color,
        width=3
    )

    mid_x = 970
    draw.line(
        (mid_x, 1280, mid_x, 2250),
        fill=line_color,
        width=3
    )

    draw.text(
        (190, 1285),
        "我的万州记忆",
        font=section_font,
        fill=dark_green
    )

    memory_text = memory["text"].strip()
    if memory_text == "":
        memory_text = "这是一段属于我的万州记忆。"

    memory_lines = wrap_text_by_width(
        draw,
        memory_text,
        body_font,
        max_width=680
    )

    text_y = 1365
    for line in memory_lines[:8]:
        draw.text(
            (190, text_y),
            line,
            font=body_font,
            fill=deep_text
        )
        text_y += 58

    draw.text(
        (190, 1785),
        "已收集文化印章",
        font=section_font,
        fill=dark_green
    )

    if not stamps:
        stamps = ["暂未收集"]

    stamp_start_x = 190
    stamp_start_y = 1865
    stamp_w = 245
    stamp_h = 58
    stamp_gap_x = 26
    stamp_gap_y = 22

    for idx, stamp in enumerate(stamps[:8]):
        row = idx // 2
        col = idx % 2
        x1 = stamp_start_x + col * (stamp_w + stamp_gap_x)
        y1 = stamp_start_y + row * (stamp_h + stamp_gap_y)
        x2 = x1 + stamp_w
        y2 = y1 + stamp_h

        draw_stamp_chip(
            draw,
            x1, y1, x2, y2,
            stamp,
            stamp_font,
            pale_orange,
            orange,
            orange
        )

    draw.text(
        (1045, 1285),
        "万州寄语",
        font=section_font,
        fill=dark_green
    )

    if ip_bytes is not None:
        quote_lines = [
            "照片生成记忆，",
            "IP成为主角，",
            "万州故事被带回生活。"
        ]
    else:
        quote_lines = [
            "数字交互让文化被体验，",
            "共创记忆让万州被更多人共同讲述。"
        ]

    quote_y = 1368
    for line in quote_lines:
        draw.text(
            (1045, quote_y),
            line,
            font=body_font,
            fill=warm_gray
        )
        quote_y += 58

    line_start_y = 1570
    for i in range(6):
        y = line_start_y + i * 88
        draw.line(
            (1045, y, 1590, y),
            fill=line_color,
            width=2
        )

    draw.text(
        (1045, 2175),
        "万川汇流 · 山水风华",
        font=small_font,
        fill=orange
    )

    draw.text(
        (190, 2280),
        "Wanzhou Cultural Interactive Postcard",
        font=small_font,
        fill=warm_gray
    )

    draw.line((170, 405, 1630, 405), fill=gold, width=2)
    draw.line((170, 1160, 1630, 1160), fill=gold, width=2)

    buffer = BytesIO()
    card.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================
# 页面样式
# ==========================

st.markdown(
    f"""
<style>

.stApp {{
    background: linear-gradient(180deg, #FBF8F1 0%, #F3EFE6 100%);
}}

.block-container {{
    padding-top: 0.8rem;
    padding-bottom: 0.5rem;
    max-width: 1200px;
}}

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

header {{
    visibility: hidden;
}}

.hero {{
    height: 360px;
    border-radius: 24px;
    background-image:
        linear-gradient(
            rgba(5, 45, 52, 0.25),
            rgba(5, 45, 52, 0.45)
        ),
        url("data:image/jpg;base64,{image_base64}");
    background-size: cover;
    background-position: center 48%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: white;
    box-shadow: 0 12px 36px rgba(15, 91, 102, 0.18);
}}

.hero h1 {{
    font-size: 58px;
    letter-spacing: 4px;
    margin-bottom: 14px;
    font-weight: 900;
    text-shadow: 0 4px 14px rgba(0,0,0,0.45);
}}

.hero h2 {{
    font-size: 28px;
    margin: 8px 0;
    font-weight: 700;
    text-shadow: 0 3px 10px rgba(0,0,0,0.45);
}}

.hero h3 {{
    font-size: 22px;
    margin-top: 8px;
    font-weight: 600;
    text-shadow: 0 3px 10px rgba(0,0,0,0.45);
}}

.intro {{
    text-align: center;
    margin-top: 18px;
    margin-bottom: 14px;
}}

.intro h2 {{
    color: #0F5B66;
    font-size: 34px;
    margin-bottom: 8px;
    font-weight: 850;
}}

.intro p {{
    color: #4B5563;
    font-size: 17px;
    margin: 0;
}}

div.stButton > button {{
    width: 100%;
    min-height: 72px;
    border-radius: 18px;
    border: 1px solid rgba(15, 91, 102, 0.18);
    background: #F7F3EA;
    color: #0F5B66;
    font-size: 18px;
    font-weight: 800;
    box-shadow: 0 4px 16px rgba(15, 91, 102, 0.10);
    transition: all 0.2s ease-in-out;
}}

div.stButton > button:hover {{
    border: 1px solid #E66A2C;
    background: #FFF7EF;
    color: #E66A2C;
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(230, 106, 44, 0.18);
}}

.bottom-text {{
    text-align: center;
    color: #555;
    font-size: 15px;
    line-height: 1.8;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid rgba(15, 91, 102, 0.15);
}}

.highlight {{
    color: #E66A2C;
    font-weight: 800;
}}

</style>
""",
    unsafe_allow_html=True
)


# ==========================
# 首页主视觉
# ==========================

st.markdown(
    """
<div class="hero">
    <div>
        <h1>万川汇流 · 山水风华</h1>
        <h2>山静而不寂，水动而不喧</h2>
        <h3>人聚而成城，城兴而有生</h3>
    </div>
</div>
""",
    unsafe_allow_html=True
)


# ==========================
# 首页说明
# ==========================

st.markdown(
    """
<div class="intro">
    <h2>探索万州山水</h2>
    <p>沿长江之脉，感受山、水、人、城共同生长的力量</p>
</div>
""",
    unsafe_allow_html=True
)


# ==========================
# 四幕入口按钮
# ==========================

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("⛰ 山静\n山之骨", key="btn_shanjing"):
        st.session_state.selected_scene = "山静"

with col2:
    if st.button("🌊 水生\n水之脉", key="btn_shuisheng"):
        st.session_state.selected_scene = "水生"

with col3:
    if st.button("👥 人聚\n人之情", key="btn_renju"):
        st.session_state.selected_scene = "人聚"

with col4:
    if st.button("🏙 城兴\n城之生", key="btn_chengxing"):
        st.session_state.selected_scene = "城兴"


# ==========================
# 显示选中的场景内容
# ==========================

selected = st.session_state.selected_scene

if selected:
    scene = SCENES[selected]

    st.markdown("---")

    with st.container(border=True):
        st.markdown(f"## {scene['icon']} {selected} · {scene['subtitle']}")
        st.markdown(f"**代表地点：** {scene['places']}")
        st.markdown(f"**视觉关键词：** {scene['keywords']}")
        st.markdown(f"### {scene['title']}")
        st.write(scene["story"])

        st.info(f"共创引导：{scene['guide']}")

        stamp_name = f"{selected}印"

        if st.button(f"收集 {scene['icon']} {stamp_name}", key=f"collect_{selected}"):
            if stamp_name not in st.session_state.stamps:
                st.session_state.stamps.append(stamp_name)
                st.success(f"已获得：{stamp_name}")
            else:
                st.info(f"你已经收集过：{stamp_name}")


# ==========================
# 共创记忆上传区
# ==========================

st.markdown("---")
st.markdown("## 📷 万州共创记忆墙")
st.write(
    "游客可以上传旅行照片，本地居民可以上传生活照片。"
    "每一张照片都会成为万州山水、人群与城市记忆的一部分。"
)

upload_col, text_col = st.columns([1, 1])

with upload_col:
    uploaded_photo = st.file_uploader(
        "上传一张你的万州照片",
        type=["jpg", "jpeg", "png"]
    )

with text_col:
    memory_type_input = st.text_input(
        "请输入你的记忆身份",
        placeholder="例如：第一次来万州的游客 / 在万州长大的本地人 / 江边散步的人"
    )

    memory_scene = st.selectbox(
        "这张照片更接近哪个主题？",
        ["山静", "水生", "人聚", "城兴"]
    )

    memory_text = st.text_area(
        "写一句你的万州记忆",
        placeholder="例如：江面很安静，但这座城市一直在向前。"
    )

if st.button("加入万州记忆墙", key="add_memory"):
    if uploaded_photo is None:
        st.warning("请先上传一张照片。")
    elif memory_text.strip() == "":
        st.warning("请写一句你的万州记忆。")
    else:
        image_bytes = uploaded_photo.getvalue()
        memory_identity = memory_type_input.strip()
        if memory_identity == "":
            memory_identity = "万州记忆共创者"

        st.session_state.memories.append(
            {
                "image": image_bytes,
                "type": memory_identity,
                "scene": memory_scene,
                "text": memory_text.strip()
            }
        )

        if "共创印" not in st.session_state.stamps:
            st.session_state.stamps.append("共创印")

        st.session_state.generated_card_bytes = None
        st.session_state.generated_ip_bytes = None
        st.session_state.generated_ip_index = None

        st.success("已加入万州记忆墙，并获得：共创印。")


# ==========================
# 记忆墙展示
# ==========================

if st.session_state.memories:
    st.markdown("### 已生成的共创记忆")

    memory_cols = st.columns(3)

    for index, memory in enumerate(st.session_state.memories):
        with memory_cols[index % 3]:
            st.image(
                Image.open(BytesIO(memory["image"])),
                width="stretch"
            )
            st.markdown(f"**{memory['scene']}｜{memory['type']}**")
            st.write(memory["text"])
else:
    st.caption("当前还没有照片。上传第一张照片，开启万州共创记忆墙。")


# ==========================
# 文化印章
# ==========================

st.markdown("---")
st.markdown("## 🧾 我的万州文化印章")

if st.session_state.stamps:
    st.success(" ｜ ".join(st.session_state.stamps))
else:
    st.write("暂未收集印章。点击上方四幕入口，开始探索。")


# ==========================
# 生成专属IP形象
# ==========================

st.markdown("---")
st.markdown("## 🎨 第一步：生成我的万州专属IP形象")
st.write(
    "先生成一个可爱的 Q 版万州文旅角色。生成后，它会自动联动到后续明信片中，成为你的个人文创主角。"
)

selected_ip_index = None

if st.session_state.memories:
    ip_options = [
        f"{i + 1}. {m['scene']}｜{m['type']}｜{m['text'][:12]}..."
        for i, m in enumerate(st.session_state.memories)
    ]

    selected_ip_label = st.selectbox(
        "请选择一条记忆生成专属IP形象",
        ip_options,
        key="ip_select"
    )

    selected_ip_index = ip_options.index(selected_ip_label)
    selected_ip_memory = st.session_state.memories[selected_ip_index]

    if st.button("生成本地版专属IP", key="generate_local_ip"):
        ip_bytes = create_local_ip_image(selected_ip_memory)
        st.session_state.generated_ip_bytes = ip_bytes
        st.session_state.generated_ip_index = selected_ip_index
        st.session_state.generated_card_bytes = None
        st.success("本地版专属IP形象已生成。后续生成明信片时会自动放入。")

    if st.session_state.generated_ip_bytes is not None:
        st.markdown("### 专属IP预览")
        st.image(st.session_state.generated_ip_bytes, width=620)

        if st.session_state.generated_ip_index == selected_ip_index:
            st.success("当前IP与所选记忆匹配，可自动联动到明信片。")
        else:
            st.warning("当前预览IP来自另一条记忆。重新点击“生成本地版专属IP”即可匹配当前记忆。")

        st.download_button(
            label="下载 PNG 专属IP形象",
            data=st.session_state.generated_ip_bytes,
            file_name="万州专属IP形象_本地版.png",
            mime="image/png"
        )
else:
    st.info("请先上传至少一条照片记忆，再生成专属IP形象。")


# ==========================
# 生成联名明信片
# ==========================

st.markdown("---")
st.markdown("## 🖼 第二步：生成IP联名版万州山水记忆明信片")
st.write(
    "如果你已经生成了专属IP形象，系统会自动把IP形象放入明信片，形成“照片 + 记忆 + 印章 + 专属IP”的联名款。"
)

if st.session_state.memories:
    memory_options = [
        f"{i + 1}. {m['scene']}｜{m['type']}｜{m['text'][:12]}..."
        for i, m in enumerate(st.session_state.memories)
    ]

    selected_memory_label = st.selectbox(
        "请选择一条记忆生成明信片",
        memory_options,
        key="postcard_select"
    )

    selected_index = memory_options.index(selected_memory_label)
    selected_memory = st.session_state.memories[selected_index]

    matched_ip_bytes = None

    if (
        st.session_state.generated_ip_bytes is not None
        and st.session_state.generated_ip_index == selected_index
    ):
        matched_ip_bytes = st.session_state.generated_ip_bytes
        st.success("检测到匹配的专属IP：生成明信片时将自动放入。")
    else:
        st.info("当前没有匹配的专属IP。也可以直接生成普通高清明信片。")

    if st.button("生成IP联名版高清明信片", key="generate_card"):
        card_bytes = create_memory_card(
            selected_memory,
            st.session_state.stamps,
            ip_bytes=matched_ip_bytes
        )
        st.session_state.generated_card_bytes = card_bytes
        st.success("高清明信片已生成。")

    if st.session_state.generated_card_bytes is not None:
        st.markdown("### 明信片预览")
        st.image(st.session_state.generated_card_bytes, width=700)
        st.caption("页面预览会被缩放，下载后的 PNG 会比当前预览更清晰。")

        st.download_button(
            label="下载 PNG 高清明信片",
            data=st.session_state.generated_card_bytes,
            file_name="万州山水记忆明信片_IP联名版.png",
            mime="image/png"
        )
else:
    st.info("请先上传至少一条照片记忆，再生成明信片。")


# ==========================
# 底部理念
# ==========================

st.markdown(
    """
<div class="bottom-text">
    从山水到人群，从历史到今日，万州的风华不是单一景点的呈现，<br>
    而是<span class="highlight">山、水、人、城</span>共同生长的结果。<br>
    数字交互让文化被体验，共创记忆让万州被更多人共同讲述，专属IP让万州记忆拥有更鲜明的可爱表达。
</div>
""",
    unsafe_allow_html=True
)