#!/usr/bin/env python3
"""Генератор иконок приложения (гантель на синем диагональном градиенте, мягкая тень).
Запуск: python3 make-icons.py"""
from PIL import Image, ImageDraw, ImageFilter


def gradient_bg(size):
    """Диагональный градиент top-left → bottom-right."""
    img = Image.new("RGBA", (size, size))
    tl, br = (0x62, 0xa0, 0xff), (0x2c, 0x52, 0xd6)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px[x, y] = tuple(int(tl[i] + (br[i] - tl[i]) * t) for i in range(3)) + (255,)
    return img


def draw_dumbbell(S, scale=1.0):
    """Гантель белым на прозрачном слое S×S (scale сжимает к центру для maskable)."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = (255, 255, 255, 255)
    cx0, cy = S / 2, S / 2

    def rr(cx, half_w, half_h, rad):
        d.rounded_rectangle([cx-half_w, cy-half_h, cx+half_w, cy+half_h], radius=rad, fill=w)

    s = scale
    # рукоятка
    d.rounded_rectangle([cx0-0.17*S*s, cy-0.05*S*s, cx0+0.17*S*s, cy+0.05*S*s],
                        radius=0.025*S*s, fill=w)
    # внутренние плиты (выше)
    rr(cx0-0.205*S*s, 0.045*S*s, 0.185*S*s, 0.03*S*s)
    rr(cx0+0.205*S*s, 0.045*S*s, 0.185*S*s, 0.03*S*s)
    # внешние плиты (ниже)
    rr(cx0-0.295*S*s, 0.042*S*s, 0.125*S*s, 0.028*S*s)
    rr(cx0+0.295*S*s, 0.042*S*s, 0.125*S*s, 0.028*S*s)
    return layer


def compose(size, maskable):
    bg = gradient_bg(size)
    if maskable:
        img = bg.copy()
        scale = 0.78  # safe zone ~80% для maskable
    else:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size-1, size-1],
                                            radius=int(size*0.225), fill=255)
        img.paste(bg, (0, 0), m)
        scale = 1.0

    db = draw_dumbbell(size, scale)

    # мягкая тень: тёмная версия гантели, смещена вниз и размыта
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    alpha = db.split()[3].point(lambda a: int(a * 0.45))
    dark = Image.new("RGBA", (size, size), (0x16, 0x2a, 0x66, 255))
    shadow.paste(dark, (0, 0), alpha)
    shadow = shadow.transform(size and (size, size), Image.AFFINE,
                              (1, 0, 0, 0, 1, -size*0.018))  # сдвиг вниз
    shadow = shadow.filter(ImageFilter.GaussianBlur(size*0.018))

    img = Image.alpha_composite(img, shadow)
    img = Image.alpha_composite(img, db)
    return img


for s in (192, 512):
    compose(s, False).save(f"icon-{s}.png")
    compose(s, True).save(f"icon-{s}-mask.png")
compose(180, False).save("icon-180.png")  # apple-touch-icon
print("icons written")
