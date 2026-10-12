#!/usr/bin/env python3
"""Cartas One Piece — agrega / quita cartas en cartas.json.

Ejemplos:
  python3 agregar_carta.py OP01-001                      # busca datos, precio e imagen y la agrega (cantidad 1, NM)
  python3 agregar_carta.py OP05-119 --alt --cantidad 2 --estado LP --notas "Comprada en tienda X"
  python3 agregar_carta.py ST01-012 --precio 3500         # fija a mano el precio de venta CLP (no lo toca --actualizar-precios)
  python3 agregar_carta.py --manual OP09-999 --nombre "Carta X" --color Rojo --tipo Character --rareza SR --set "OP-09 ..."
  python3 agregar_carta.py --listar
  python3 agregar_carta.py --quitar 3                     # quita la carta con id 3 (o resta 1 si --restar)
  python3 agregar_carta.py --actualizar-precios           # recalcula precios de todas las cartas

Precios: precio_referencia = mercado TCGplayer (USD) × dólar, redondeado a $10 (dato crudo).
precio_venta_clp (el que muestra la página y suma los totales) = regla de David:
  referencia < $500 → referencia + $50; y nunca menos de $100. Desde $500 queda igual.
  Ej.: 50→100, 40→100, 70→120, 450→500, 1590→1590. Un --precio manual manda (precio_manual: true).

Datos y precios: optcgapi.com (precio de mercado TCGplayer en USD). Dólar: open.er-api.com / mindicador.cl.
Imagen (sin marca de agua): por defecto se recorta la carta desde las fotos de David con --foto
(o las fotos de la carpeta $CARTAS_FOTOS), ver recortar_foto.py. Las imágenes oficiales traen
"SAMPLE" encima, así que solo se usan como último recurso (queda imagen_marca_agua: true y se avisa).
  python3 agregar_carta.py OP11-041 --estado LP --foto ~/fotos/lote7.jpg
  python3 agregar_carta.py --recortar-fotos ~/fotos/*.jpg     # reemplaza las imágenes con SAMPLE que queden
Si una carta igual (código + variante + estado + idioma) ya existe, solo suma la cantidad.
"""
import argparse, datetime, io, json, os, re, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(BASE, "cartas.json")
IMG = os.path.join(BASE, "img")
UA = {"User-Agent": "CartasOnePiece/1.0 (catalogo personal David)"}
COLOR_ES = {"red": "Rojo", "green": "Verde", "blue": "Azul", "purple": "Morado", "black": "Negro", "yellow": "Amarillo"}
CODE_RE = re.compile(r"^(OP|ST|EB|PRB|P)(\d{0,2})-(\d{3})$", re.I)

def get_json(url, timeout=15):
    with urllib.request.urlopen(urllib.request.Request(url, headers={**UA, "Accept": "application/json"}), timeout=timeout) as r:
        return json.load(r)

def dolar():
    for url, f in [("https://open.er-api.com/v6/latest/USD", lambda d: d["rates"]["CLP"]),
                   ("https://mindicador.cl/api/dolar", lambda d: d["serie"][0]["valor"])]:
        try: return round(float(f(get_json(url, 10))), 2)
        except Exception: pass
    return None

def api_card(code, alt=False):
    """Devuelve el registro de optcgapi.com para el código (versión normal o parallel/alt art)."""
    pre = code.split("-")[0].upper()
    kind = "decks" if pre.startswith("ST") else "promos" if pre == "P" else "sets"
    try:
        rows = get_json(f"https://optcgapi.com/api/{kind}/card/{code}/")
    except Exception as e:
        print("  aviso: optcgapi.com no respondió:", e); return None
    if not isinstance(rows, list) or not rows: return None
    alts = [r for r in rows if "parallel" in r.get("card_name", "").lower() or "alternate" in r.get("card_name", "").lower()]
    # versión normal: sin sufijos como (Reprint), (Jolly Roger Foil), (Full Art); se permite el número "(033)"
    base = [r for r in rows if r not in alts and not re.search(r"\((?!\d{3}\))[^)]*\)", r.get("card_name", ""))] \
        or [r for r in rows if r not in alts]
    if alt and not alts: print("  aviso: optcgapi.com no tiene versión Parallel/Alt Art de esta carta; uso los datos de la normal (revisa el precio, o fíjalo con --precio).")
    pool = (alts if alt else base) or rows
    return pool[0]

def num(v):
    try: return int(str(v).replace(",", ""))
    except Exception: return None

def limpiar_nombre(n):
    return re.sub(r"\s*\((\d{3}|Parallel|Alternate Art|Alt Art)\)", "", n or "").strip()

def fotos_por_defecto(lista):
    if lista: return lista
    carpeta = os.environ.get("CARTAS_FOTOS")
    if carpeta and os.path.isdir(carpeta):
        return sorted(os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    return []

def imagen_limpia(code, alt, fotos):
    """Imagen sin SAMPLE: recorte desde las fotos de David. Devuelve 'img/...' o None."""
    if not fotos: return None
    from recortar_foto import recortar
    return recortar(code, alt, fotos)

def descargar_imagen(code, alt):
    """Último recurso: imagen oficial (trae la marca de agua SAMPLE)."""
    os.makedirs(IMG, exist_ok=True)
    sufijo = "_p1" if alt else ""
    url = f"https://en.onepiece-cardgame.com/images/cardlist/card/{code}{sufijo}.png"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r: raw = r.read()
    except Exception as e:
        print("  aviso: no se pudo bajar la imagen oficial:", e); return None
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        if im.width > 600: im = im.resize((600, round(im.height * 600 / im.width)), Image.LANCZOS)
        name = f"{code}{sufijo}.webp"; im.save(os.path.join(IMG, name), "WEBP", quality=82, method=6)
    except ImportError:
        name = f"{code}{sufijo}.png"; open(os.path.join(IMG, name), "wb").write(raw)
    return f"img/{name}"

def cargar():
    return json.load(open(JSON, encoding="utf-8"))

def guardar(d):
    d["actualizado"] = datetime.date.today().isoformat()
    json.dump(d, open(JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2); open(JSON, "a").write("\n")

def precio_clp(usd, dol):
    """Precio de referencia crudo: mercado USD × dólar, redondeado a $10."""
    return None if usd is None or not dol else int(round(usd * dol / 10) * 10)

PRECIO_MINIMO, UMBRAL, RECARGO = 100, 500, 50

def precio_venta(ref):
    """Regla de David: bajo $500 se suman $50; piso de $100. Desde $500 queda igual."""
    if ref is None: return None
    v = ref + RECARGO if ref < UMBRAL else ref
    return max(v, PRECIO_MINIMO)

def fijar_precios(c, usd=None, dol=None, manual=None):
    """Actualiza precio_referencia (crudo) y precio_venta_clp (mostrado) de una carta."""
    if usd is not None or dol is not None:
        c["precio_mercado_usd"] = usd; c["dolar_clp"] = dol
    ref = precio_clp(c.get("precio_mercado_usd"), c.get("dolar_clp"))
    if ref is None: ref = c.get("precio_referencia", c.get("precio_ref_clp"))   # sin datos nuevos: conserva el guardado
    c["precio_referencia"] = ref
    if manual is not None:
        c["precio_venta_clp"] = manual; c["precio_manual"] = True
    elif not c.get("precio_manual"):
        c["precio_venta_clp"] = precio_venta(c["precio_referencia"])
    c.pop("precio_ref_clp", None)

def agregar(a):
    code = a.codigo.upper()
    if not CODE_RE.match(code): sys.exit(f"Código inválido: {code} (ej. OP01-001, ST10-005, EB01-012, P-001)")
    d = cargar()
    for c in d["cartas"]:
        if c["codigo"] == code and bool(c.get("alt_art")) == a.alt and c.get("estado") == a.estado and c.get("idioma") == a.idioma:
            c["cantidad"] = c.get("cantidad", 1) + a.cantidad
            if a.notas: c["notas"] = a.notas
            if a.precio is not None: fijar_precios(c, manual=a.precio)
            guardar(d); print(f"✓ Ya existía (id {c['id']}): ahora cantidad {c['cantidad']}"); return
    r = None if a.manual else api_card(code, a.alt)
    if r is None and not a.manual and not a.nombre:
        sys.exit("No encontré la carta en optcgapi.com. Usa --manual con --nombre, --color, --tipo, --rareza, --set.")
    r = r or {}
    dol = a.dolar or dolar() or d.get("dolar_clp")
    usd = r.get("market_price")
    colores = [COLOR_ES.get(x.lower(), x) for x in (r.get("card_color") or "").split()] or (a.color.split("/") if a.color else [])
    carta = {
        "id": max([c["id"] for c in d["cartas"]] or [0]) + 1,
        "codigo": code,
        "nombre": a.nombre or limpiar_nombre(r.get("card_name")),
        "color": colores,
        "tipo": a.tipo or r.get("card_type") or "",
        "rareza": a.rareza or {"PR": "P"}.get(r.get("rarity"), r.get("rarity")) or "",
        "alt_art": a.alt,
        "set": a.set or (f"{r.get('set_id','')} {r.get('set_name','')}".strip()),
        "costo": a.costo if a.costo is not None else num(r.get("card_cost")),
        "poder": a.poder if a.poder is not None else num(r.get("card_power")),
        "counter": a.counter if a.counter is not None else num(r.get("counter_amount")),
        "vida": num(r.get("life")),
        "atributo": r.get("attribute") or "",
        "subtipos": r.get("sub_types") or "",
        "texto": (r.get("card_text") or "").replace("  This card has been officially errata'd.", "").strip(),
        "cantidad": a.cantidad,
        "estado": a.estado,
        "idioma": a.idioma,
        "precio_mercado_usd": usd,
        "dolar_clp": dol,
        "precio_referencia": None,
        "precio_venta_clp": None,
        "precio_manual": False,
        "notas": a.notas or "",
        "imagen": "",
        "fecha_alta": datetime.date.today().isoformat(),
    }
    if a.imagen: carta["imagen"] = a.imagen
    elif not a.sin_imagen:
        carta["imagen"] = imagen_limpia(code, a.alt, fotos_por_defecto(a.foto)) or ""
        if carta["imagen"]: carta["fuente_imagen"] = "foto de David (recorte con corrección de perspectiva y mejora)"
        else:
            print("  ⚠ sin foto donde recortarla: uso la imagen oficial (con SAMPLE). Repite con --foto para cambiarla.")
            carta["imagen"] = descargar_imagen(code, a.alt) or r.get("card_image") or ""
            carta["imagen_marca_agua"] = True
    fijar_precios(carta, manual=a.precio)
    if dol: d["dolar_clp"] = dol
    d["cartas"].append(carta); guardar(d)
    print(f"✓ Agregada id {carta['id']}: {carta['codigo']} {carta['nombre']} · {carta['rareza']}{' Alt Art' if a.alt else ''} · "
          f"x{carta['cantidad']} · venta ${carta['precio_venta_clp'] or '—'} CLP (ref. ${carta['precio_referencia'] or '—'})")

def main():
    p = argparse.ArgumentParser(description="Agrega cartas One Piece TCG a cartas.json")
    p.add_argument("codigo", nargs="?", help="Código de la carta, ej. OP01-001")
    p.add_argument("--cantidad", type=int, default=1)
    p.add_argument("--estado", default="NM", choices=["NM", "LP", "MP", "HP", "DMG"])
    p.add_argument("--idioma", default="Inglés")
    p.add_argument("--alt", action="store_true", help="Versión Parallel / Alt Art")
    p.add_argument("--precio", type=int, help="Precio de venta CLP fijado a mano (gana sobre la regla y no lo cambia --actualizar-precios)")
    p.add_argument("--dolar", type=float, help="Valor del dólar a usar (si no, se busca el del día)")
    p.add_argument("--notas", default="")
    p.add_argument("--imagen", help="URL o ruta de imagen propia")
    p.add_argument("--sin-imagen", action="store_true")
    p.add_argument("--foto", action="append", metavar="FOTO", help="Foto(s) de David donde aparece la carta; se recorta de ahí (sin SAMPLE). Repetible")
    p.add_argument("--recortar-fotos", nargs="+", metavar="FOTO", help="Recorta desde estas fotos las cartas que aún tienen imagen con SAMPLE (o todas con --todas)")
    p.add_argument("--todas", action="store_true", help="Con --recortar-fotos: rehace todas las imágenes encontradas")
    p.add_argument("--manual", action="store_true", help="No consultar optcgapi.com; usar solo los datos dados")
    for k in ["nombre", "color", "tipo", "rareza", "set"]: p.add_argument("--" + k)
    for k in ["costo", "poder", "counter"]: p.add_argument("--" + k, type=int)
    p.add_argument("--listar", action="store_true")
    p.add_argument("--quitar", type=int, metavar="ID")
    p.add_argument("--restar", action="store_true", help="Con --quitar: resta 1 en vez de borrar")
    p.add_argument("--actualizar-precios", action="store_true")
    p.add_argument("--aplicar-regla", action="store_true", help="Recalcula precio_venta_clp desde los datos guardados, sin consultar internet")
    a = p.parse_args()
    if a.listar:
        d = cargar()
        if not d["cartas"]: print("(colección vacía)")
        for c in d["cartas"]:
            print(f"{c['id']:>4}  {c['codigo']:<10} {c['nombre'][:32]:<32} {c['rareza']:<4}{' ALT' if c.get('alt_art') else '    '} x{c['cantidad']:<3} {c['estado']:<3} ${c.get('precio_venta_clp') or '—'}{' (manual)' if c.get('precio_manual') else ''}  ref ${c.get('precio_referencia') or '—'}")
        return
    if a.quitar:
        d = cargar(); c = next((c for c in d["cartas"] if c["id"] == a.quitar), None)
        if not c: sys.exit("No existe ese id")
        if a.restar and c["cantidad"] > 1: c["cantidad"] -= 1; print(f"✓ id {c['id']} ahora x{c['cantidad']}")
        else: d["cartas"].remove(c); print(f"✓ Quitada id {c['id']} {c['codigo']} {c['nombre']}")
        guardar(d); return
    if a.actualizar_precios:
        d = cargar(); dol = a.dolar or dolar() or d.get("dolar_clp"); d["dolar_clp"] = dol
        for c in d["cartas"]:
            if c.get("precio_usd_fijo"):   # impresión especial (reimpresión de starter deck, etc.): la API daría otra versión
                fijar_precios(c, c.get("precio_mercado_usd"), dol); print(f"  {c['codigo']} {c['nombre']}: impresión fija US${c.get('precio_mercado_usd')} → venta ${c.get('precio_venta_clp')}"); continue
            r = api_card(c["codigo"], c.get("alt_art"))
            if r and r.get("market_price") is not None:
                fijar_precios(c, r["market_price"], dol)
            else:
                fijar_precios(c)   # sin precio nuevo: solo reaplica la regla al dato guardado
            print(f"  {c['codigo']} {c['nombre']}: US${c.get('precio_mercado_usd')} → ref ${c.get('precio_referencia')} → venta ${c.get('precio_venta_clp')}{' (manual)' if c.get('precio_manual') else ''}")
        guardar(d); return
    if a.recortar_fotos:
        d = cargar(); n = 0
        for c in d["cartas"]:
            if c["codigo"] == "DON!!" or not (a.todas or c.get("imagen_marca_agua") or not c.get("imagen")): continue
            im = imagen_limpia(c["codigo"], bool(c.get("alt_art")), a.recortar_fotos)
            if im:
                c["imagen"] = im; c.pop("imagen_marca_agua", None); n += 1
                c["fuente_imagen"] = "foto de David (recorte con corrección de perspectiva y mejora)"
        guardar(d); print(f"✓ {n} imágenes recortadas desde fotos"); return
    if a.aplicar_regla:
        d = cargar()
        for c in d["cartas"]: fijar_precios(c)
        guardar(d); print("✓ Regla de precios aplicada a", len(d["cartas"]), "cartas"); return
    if not a.codigo: p.print_help(); return
    agregar(a)

if __name__ == "__main__":
    main()
