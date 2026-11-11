"""Qarmasha v4 ad renderer: writes raw 1080x1920 RGB frames to stdout (30 fps)."""
import sys, math
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 12.0
rng = np.random.default_rng(11)
FONT = "/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf"

def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_back(x):
    x = min(max(x, 0), 1); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def load_fit(path):
    im = cv2.imread(path)
    s = W / im.shape[1]
    im = cv2.resize(im, (W, int(im.shape[0] * s)), interpolation=cv2.INTER_AREA)
    y0 = (im.shape[0] - H) // 2
    return im[y0:y0 + H].astype(np.float32)

def affine(img, zoom, cx, cy, tx=0, ty=0, rot=0, border=0):
    M = cv2.getRotationMatrix2D((cx, cy), rot, zoom)
    M[0, 2] += tx; M[1, 2] += ty
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT if border == 0 else cv2.BORDER_REFLECT)

# ---------------- shot A: crack ----------------
crack = load_fit("crack.png")
g = cv2.cvtColor(crack.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
alpha = np.clip((g - 14) / 40, 0, 1)
box = np.zeros((H, W), np.float32)
box[590:1270, 30:1040] = 1
left = np.zeros_like(box); left[:, :527] = 1
_m = (g > 95).astype(np.uint8)
_n, _lab, _st, _ = cv2.connectedComponentsWithStats(_m, 8)
_top = np.argsort(-_st[1:, 4])[:2] + 1
_top = sorted(_top, key=lambda i: _st[i, 0])
def _solid(i):
    m = (_lab == i).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    ff = m.copy(); fm = np.zeros((H + 2, W + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 255)
    m = m | cv2.bitwise_not(ff)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.5) * np.clip(alpha * 1.5, 0, 1)
aL = _solid(_top[0]); aR = _solid(_top[1])
sil = np.clip(aL + aR, 0, 1)
aD = alpha * (1 - sil)
C = (527.0, 928.0)
premul = crack * alpha[..., None]

def layer(a, dx, dy, rot, zoom=1.0, cx=C[0], cy=C[1]):
    rgb = affine(crack * a[..., None], zoom, cx, cy, dx, dy, rot)
    al = affine(a, zoom, cx, cy, dx, dy, rot)
    return rgb, al

def shot_crack(t):
    T0 = 0.9
    u = (t - T0) / 0.8
    frame = np.zeros((H, W, 3), np.float32)
    # warm glow behind
    glow = np.exp(-(((XX - C[0]) ** 2 + (YY - C[1]) ** 2) / (2 * 420 ** 2)))
    frame += glow[..., None] * np.array([10, 28, 55], np.float32) * (0.6 + (0.8 if t > T0 else 0.0) * math.exp(-max(t - T0, 0) * 3))
    if t < T0:
        off = 30; jit = (t / T0) ** 3 * 5
        dxj = jit * math.sin(t * 90); dyj = jit * math.cos(t * 77)
        rL, aL_ = layer(aL, off + dxj, dyj, 0)
        rR, aR_ = layer(aR, -off + dxj, dyj, 0)
        frame = frame * (1 - aL_[..., None]) + rL
        frame = frame * (1 - aR_[..., None]) + rR
    else:
        e = ease_out(u); slow = max(t - T0 - 0.8, 0)
        off = 30 * (1 - e)
        rL, aL_ = layer(aL, off - 55 * slow, -8 * slow, (1 - e) * -6 - 2 * slow)
        rR, aR_ = layer(aR, -off + 55 * slow, 6 * slow, (1 - e) * 6 + 2 * slow)
        s = 0.06 + 0.94 * e + 0.05 * slow
        rD, aD_ = layer(aD, 0, 0, 0, zoom=s)
        frame = frame * (1 - aD_[..., None]) + rD
        frame = frame * (1 - aL_[..., None]) + rL
        frame = frame * (1 - aR_[..., None]) + rR
        # flash
        fl = math.exp(-(t - T0) * 14)
        frame += fl * 140
    zoom = 1.0 + 0.10 * (t / 3.4)
    shake = 0
    if t > T0:
        shake = 16 * math.exp(-(t - T0) * 6)
    frame = affine(frame, zoom, C[0], C[1], shake * math.sin(t * 95), shake * math.cos(t * 83))
    return frame

# ---------------- shot B: honey ----------------
honey = load_fit("honey.png")
hsv = cv2.cvtColor(honey.astype(np.uint8), cv2.COLOR_BGR2HSV)
smask = ((hsv[..., 0] > 8) & (hsv[..., 0] < 32) & (hsv[..., 1] > 120) & (hsv[..., 2] > 90)).astype(np.float32)
smask[880:] = 0; smask[:, :430] = 0; smask[:, 760:] = 0
smask = cv2.GaussianBlur(smask, (0, 0), 5)
pool = np.zeros((H, W), np.float32)
cv2.ellipse(pool, (535, 1060), (150, 120), 0, 0, 360, 1, -1)
pool = cv2.GaussianBlur(pool, (0, 0), 30)

def shot_honey(t):  # t local 0..3
    dx = smask * 2.0 * np.sin(2 * np.pi * (YY / 140.0 - t * 1.3))
    dy = -smask * 6 * np.sin(2 * np.pi * (YY / 300.0 - t * 0.9)) + pool * 6 * math.sin(t * 2.2)
    dx += pool * (XX - 535) * 0.025 * math.sin(t * 2.2)
    f = cv2.remap(honey, XX + dx, YY + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    f *= (1 + 0.10 * smask * np.sin(2 * np.pi * (YY / 110.0 - t * 2.2)))[..., None]
    zoom = 1.04 + 0.10 * ease_out(t / 3.0)
    return affine(f, zoom, 540, 1050, 0, -30 * t / 3.0, 0, border=1)

# ---------------- rain sprites ----------------
hard = np.clip((g - 40) / 35, 0, 1)
a8 = (hard > 0.4).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(a8, 8)
sprites = []
for i in range(1, n):
    x, y, w, h, area = st[i]
    if 900 < area < 60000 and x > 2 and y > 2 and x + w < W - 2 and y + h < H - 2:
        m = (lab[y:y + h, x:x + w] == i).astype(np.float32)
        m = cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3))), (0, 0), 1) * hard[y:y + h, x:x + w]
        sprites.append((crack[y:y + h, x:x + w].copy(), m))
for a_ in (aL, aR):
    ys, xs = np.where(a_ > 0.3)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sprites.append((crack[y0:y1, x0:x1].copy() * 1.0, a_[y0:y1, x0:x1]))
big_idx = [len(sprites) - 2, len(sprites) - 1]
inst = []
for k in range(34):
    z = rng.uniform(0.35, 1.35)
    si = int(rng.choice(big_idx)) if rng.random() < 0.28 else int(rng.integers(0, len(sprites) - 2))
    base = 0.32 if si in big_idx else 1.0
    inst.append(dict(si=si, z=z, sc=base * (0.55 + 0.6 * z), x=rng.uniform(-60, W + 60), y0=rng.uniform(0, H + 400),
                     sp=380 * z + 120, rot0=rng.uniform(0, 360), rs=rng.uniform(-120, 120)))
inst.sort(key=lambda d: d['z'])
bgrad = np.exp(-(((XX - 540) ** 2) / (2 * 520 ** 2) + ((YY - 900) ** 2) / (2 * 800 ** 2)))[..., None] * np.array([8, 22, 42], np.float32) \
    if False else None

def rain(t, speed=1.0, dim=1.0):
    f = (np.exp(-(((XX - 540) ** 2) / (2 * 560 ** 2) + ((YY - 900) ** 2) / (2 * 900 ** 2)))[..., None]
         * np.array([10, 26, 48], np.float32))
    for d in inst:
        sp, sm = sprites[d['si']]
        sc = d['sc']
        h0, w0 = sp.shape[:2]
        w, h = max(4, int(w0 * sc)), max(4, int(h0 * sc))
        s = cv2.resize(sp, (w, h)); m = cv2.resize(sm, (w, h))
        ang = d['rot0'] + d['rs'] * t * speed
        D = int(math.hypot(w, h)) + 4
        M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0); M[0, 2] += (D - w) / 2; M[1, 2] += (D - h) / 2
        s = cv2.warpAffine(s, M, (D, D)); m = cv2.warpAffine(m, M, (D, D))
        z = d['z']
        if z < 0.6 or z > 1.15:
            r = 2.5 * abs(z - 0.85) * 4
            s = cv2.GaussianBlur(s, (0, 0), r); m = cv2.GaussianBlur(m, (0, 0), r)
        light = (0.45 + 0.55 * min(z, 1.0)) * dim
        y = (d['y0'] + d['sp'] * t * speed) % (H + 400) - 200
        x0 = int(d['x'] - D / 2); y0 = int(y - D / 2)
        xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + D, W), min(y0 + D, H)
        if xb > xa and yb > ya:
            mm = m[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
            f[ya:yb, xa:xb] = f[ya:yb, xa:xb] * (1 - mm) + s[ya - y0:yb - y0, xa - x0:xb - x0] * light * mm
    return f

# ---------------- text ----------------
def make_text(txt, size):
    font = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    bb = tmp.textbbox((0, 0), txt, font=font, direction="rtl", language="ar")
    tw, th = bb[2] - bb[0] + 80, bb[3] - bb[1] + 80
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).text((40 - bb[0], 40 - bb[1]), txt, font=font, fill=255, direction="rtl", language="ar")
    m = np.asarray(mask).astype(np.float32) / 255
    yy = np.linspace(0, 1, th)[:, None]
    top = np.array([150, 230, 255], np.float32); bot = np.array([30, 140, 215], np.float32)  # BGR gold
    grad = (top * (1 - yy[..., None]) + bot * yy[..., None]) * np.ones((th, tw, 1))
    glow = cv2.GaussianBlur(m, (0, 0), size / 9)
    shadow = cv2.GaussianBlur(m, (0, 0), size / 14)
    return grad.astype(np.float32), m, glow, shadow

TEXTS = [  # text, size, start, end, center y
    ("قرمشة", 250, 0.95, 2.0, 1500),
    ("جرانولا تفتح النفس", 104, 2.05, 3.35, 1500),
    ("قرمشة وطعم", 160, 3.75, 5.6, 1660),
    ("والله ما تشبع منها", 108, 6.65, 8.6, 960),
    ("قرمشة", 240, 8.95, 12.5, 830),
    ("جرّبها اليوم", 112, 9.6, 12.5, 1110),
]
TX = [(make_text(t, s), st_, en, cy) for t, s, st_, en, cy in TEXTS]

def draw_texts(f, t):
    for (grad, m, glow, shadow), st_, en, cy in TX:
        a = t - st_
        if a < 0 or t > en + 0.25: continue
        sc = 1.35 - 0.35 * ease_back(a / 0.35)
        op = min(1, a / 0.12) * (1 if t < en else max(0, 1 - (t - en) / 0.25))
        blur = 9 * (1 - min(a / 0.22, 1))
        h0, w0 = m.shape
        w, h = int(w0 * sc), int(h0 * sc)
        g_ = cv2.resize(grad, (w, h)); m_ = cv2.resize(m, (w, h)); gl = cv2.resize(glow, (w, h)); sh = cv2.resize(shadow, (w, h))
        if blur > 0.3:
            m_ = cv2.GaussianBlur(m_, (0, 0), blur)
        # light sweep
        sw = (a - 0.35) / 0.7
        if 0 < sw < 1:
            xs = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.4
            band = np.exp(-((xs - sw * (w + h * 0.4)) ** 2) / (2 * (w * 0.05) ** 2))
            g_ = g_ + (band[..., None] * 160) * m_[..., None]
        x0 = W // 2 - w // 2; y0 = cy - h // 2
        xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
        sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
        reg = f[ya:yb, xa:xb]
        reg[:] = reg * (1 - 0.75 * op * sh[sl][..., None])
        reg[:] = reg + gl[sl][..., None] * np.array([40, 110, 190], np.float32) * 0.55 * op
        mm = (m_[sl] * op)[..., None]
        reg[:] = reg * (1 - mm) + g_[sl] * mm
    return f

# ---------------- main ----------------
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
vig = (1 - 0.55 * (((XX - 540) / 760) ** 2 + ((YY - 960) / 1250) ** 2)).clip(0.25, 1)[..., None]
bottom = np.clip((YY - 1350) / 570, 0, 1) ** 1.5

def whip(f, k):
    if k <= 0: return f
    L = int(4 + 80 * k)
    ker = np.zeros((L, 1), np.float32); ker[:, 0] = 1 / L
    return cv2.filter2D(f, -1, ker) * (1 + 0.6 * k)

N = int(DUR * FPS)
out = sys.stdout.buffer
for i in range(N):
    t = i / FPS
    if t < 3.4:
        f = shot_crack(t)
    elif t < 6.4:
        f = shot_honey(t - 3.4)
        f = f * (1 - 0.65 * bottom[..., None])
    elif t < 8.8:
        f = rain(t - 6.4)
    else:
        f = rain(t - 6.4, speed=0.35 + 0.65 * math.exp(-(t - 8.8) * 4), dim=0.55)
    # whip transitions around cuts
    for cut in (3.4, 6.4, 8.8):
        d = abs(t - cut)
        if d < 0.12: f = whip(f, 1 - d / 0.12)
    f = draw_texts(f, t)
    f = f * vig
    if t > DUR - 0.5: f *= max(0, (DUR - t) / 0.5)
    grain = rng.normal(0, 5, (H // 2, W // 2, 1)).astype(np.float32)
    f = f + cv2.resize(grain, (W, H))[..., None]
    out.write(np.clip(f, 0, 255).astype(np.uint8)[..., ::-1].tobytes())
