#!/usr/bin/env python3
"""Recorta cartas desde fotos de David (sin marca de agua 'SAMPLE').

Cómo funciona: baja la imagen oficial de la carta solo como *referencia* (no se publica),
la busca dentro de la foto con SIFT + homografía (ignorando la franja donde va el SAMPLE),
endereza la carta a 63×88 (630×880 px) con warpPerspective y la mejora un poco
(balance de blancos, denoise suave, CLAHE, nitidez).

Uso directo:
  python3 recortar_foto.py OP11-041 foto1.jpg [foto2.jpg ...]     # deja img/OP11-041.webp
Requiere: pip install opencv-python numpy pillow
"""
import io, os, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
UA = {"User-Agent": "CartasOnePiece/1.0 (catalogo personal David)"}
W, H = 630, 880          # proporción 63×88
RW, RH = 300, 419
MIN_INLIERS = 40

def _ref(code, alt):
    import cv2, numpy as np
    suf = "_p1" if alt else ""
    url = f"https://en.onepiece-cardgame.com/images/cardlist/card/{code}{suf}.png"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        buf = np.frombuffer(r.read(), np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)

def _mejorar(img):
    import cv2, numpy as np
    f = img.astype(np.float32)
    for ch in range(3):
        lo, hi = np.percentile(f[..., ch], (0.5, 99.5)); f[..., ch] = (f[..., ch] - lo) * 255 / max(hi - lo, 1)
    f = np.clip(f, 0, 255).astype(np.uint8)
    f = cv2.fastNlMeansDenoisingColored(f, None, 4, 4, 7, 21)
    l, a, b = cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2LAB))
    l = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(6, 6)).apply(l)
    f = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    f = cv2.addWeighted(f, 1.5, cv2.GaussianBlur(f, (0, 0), 1.6), -0.5, 0)
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.float32); hsv[..., 1] = np.clip(hsv[..., 1] * 1.08, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def ubicar(code, alt, fotos):
    """Devuelve (inliers, foto, quad) del mejor hallazgo de la carta en las fotos, o None."""
    import cv2, numpy as np
    g = cv2.resize(_ref(code, alt), (RW * 2, RH * 2))
    m = np.zeros_like(g); m[int(RH * 2 * .05):int(RH * 2 * .97), int(RW * 2 * .04):int(RW * 2 * .96)] = 255
    m[int(RH * 2 * .35):int(RH * 2 * .55)] = 0            # franja del SAMPLE fuera
    sift = cv2.SIFT_create(nfeatures=2000)
    kp, rd = sift.detectAndCompute(g, m); rp = np.float32([k.pt for k in kp]) / 2
    best = None
    for foto in fotos:
        im = cv2.imread(foto)
        if im is None: continue
        h, w = im.shape[:2]; s = 2000 / h
        q = cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(cv2.resize(im, (int(w * s), 2000), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY))
        kp2, D = cv2.SIFT_create().detectAndCompute(q, None); P = np.float32([k.pt for k in kp2])
        ms = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=60)).knnMatch(rd, D, k=2)
        good = [a for a, b in (x for x in ms if len(x) == 2) if a.distance < .8 * b.distance]
        if len(good) < 8: continue
        Hm, inl = cv2.findHomography(rp[[x.queryIdx for x in good]], P[[x.trainIdx for x in good]], cv2.RANSAC, 8.0)
        if Hm is None: continue
        quad = cv2.perspectiveTransform(np.float32([[0, 0], [RW, 0], [RW, RH], [0, RH]]).reshape(-1, 1, 2), Hm).reshape(-1, 2)
        if not cv2.isContourConvex(quad.reshape(-1, 1, 2)): continue
        wd, ht = np.linalg.norm(quad[1] - quad[0]), np.linalg.norm(quad[3] - quad[0])
        if ht < 300 or not (.6 < wd / ht < .85): continue
        n = int(inl.sum())
        if best is None or n > best[0]: best = (n, foto, quad / s)
    return best if best and best[0] >= MIN_INLIERS else None

def recortar(code, alt, fotos, salida=None):
    """Busca la carta en las fotos y guarda img/<code>[_p1].webp. Devuelve 'img/...' o None."""
    try:
        import cv2, numpy as np
        from PIL import Image
    except ImportError:
        print("  aviso: falta opencv-python / numpy / pillow para recortar fotos"); return None
    try:
        hit = ubicar(code, alt, fotos)
    except Exception as e:
        print("  aviso: no se pudo recortar desde fotos:", e); return None
    if not hit:
        print(f"  aviso: {code} no apareció con claridad en las fotos dadas"); return None
    n, foto, quad = hit
    M = cv2.getPerspectiveTransform(np.float32(quad), np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
    wp = cv2.warpPerspective(cv2.imread(foto), M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    out = _mejorar(wp)
    os.makedirs(IMG, exist_ok=True)
    name = salida or f"{code}{'_p1' if alt else ''}.webp"
    Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)).save(os.path.join(IMG, name), "WEBP", quality=86, method=6)
    print(f"  imagen: recortada de {os.path.basename(foto)} ({n} puntos coincidentes) → img/{name}")
    return f"img/{name}"

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    print(recortar(sys.argv[1].upper(), False, sys.argv[2:]) or "no encontrada")
