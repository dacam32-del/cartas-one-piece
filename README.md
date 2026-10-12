# Cartas One Piece Card Game — colección de David Eduardo

Catálogo de mis cartas del **One Piece Card Game (OPTCG)**: código, nombre, color, tipo, rareza, set, costo, poder, counter, cantidad, estado, precio de referencia en pesos chilenos (CLP) y notas.

**Ver la página:** https://dacam32-del.github.io/cartas-one-piece/
**Vista de ejemplo (demo, cartas que NO son de la colección):** https://dacam32-del.github.io/cartas-one-piece/?demo=1

## Qué tiene la página
- Diseño "cartas primero": grilla de imágenes grandes (2 columnas en celular, más en escritorio) con solo una etiqueta de precio y la cantidad (xN) cuando hay más de una.
- Encabezado compacto (título + total de cartas y valor). Los filtros y el orden están en un panel **Filtros** que se abre al tocar el botón (cerrado por defecto).
- Búsqueda por nombre, código (`OP01-001`), subtipo, texto o notas (sin importar tildes).
- Filtros por **color** (Rojo, Verde, Azul, Morado, Negro, Amarillo, Multicolor), **tipo** (Líder, Personaje, Evento, Escenario, DON!!), **rareza** (L, C, UC, R, SR, SEC, SP, TR, P, Alt Art), **set** y **estado**.
- Orden por más recientes, código, precio, nombre, costo o poder.
- Ficha de detalle con costo/poder/counter/vida, efecto, subtipos, estado, idioma y notas; navegación con flechas, teclado o deslizando en el celular. Cada carta tiene enlace propio (`#carta-ID`).
- Totales: cartas, cartas distintas y valor de referencia en CLP.

## Archivos
| Archivo | Para qué |
|---|---|
| `cartas.json` | **Única fuente de datos**: cada carta es un objeto dentro de `"cartas"`. |
| `demo.json` | 3 cartas de ejemplo, solo para `?demo=1`. No es la colección. |
| `index.html`, `style.css`, `app.js` | La página (estática, lee `cartas.json`). |
| `img/` | Imágenes de las cartas descargadas por el script (webp). |
| `agregar_carta.py` | Agrega / quita cartas y actualiza precios. |
| `publicar.sh` | Hace commit y push a `main` (GitHub Pages se actualiza solo). |

## Agregar una carta
```bash
python3 agregar_carta.py OP01-001                         # normal, NM, inglés, x1
python3 agregar_carta.py OP05-119 --alt --cantidad 2 --estado LP --notas "Regalo"
python3 agregar_carta.py ST01-012 --precio 3500            # precio CLP fijado a mano
python3 agregar_carta.py --listar
python3 agregar_carta.py --quitar 3            # o --quitar 3 --restar (resta 1)
python3 agregar_carta.py --actualizar-precios
./publicar.sh "Agregar cartas OP01"
```
Si la carta ya existe con el mismo código, variante, estado e idioma, solo se suma la cantidad.
Para una carta que no esté en la API: `--manual --nombre ... --color Rojo/Verde --tipo Character --rareza SR --set "OP-09 ..." --costo 4 --poder 6000 --counter 1000`.

También se puede editar `cartas.json` a mano. Campos de cada carta:
`id, codigo, nombre, color (lista), tipo (Leader/Character/Event/Stage/DON!!), rareza (C/UC/R/SR/SEC/L/SP/TR/P), alt_art (true/false), set, costo, poder, counter, vida, atributo, subtipos, texto, cantidad, estado (NM/LP/MP/HP/DMG), idioma, precio_mercado_usd, dolar_clp, precio_referencia (crudo), precio_venta_clp (mostrado), precio_manual, notas, imagen, fuente_imagen, imagen_marca_agua, fecha_alta`.

## De dónde salen los datos, imágenes y precios
- **Datos de la carta y precio de mercado:** [optcgapi.com](https://optcgapi.com) (API pública; precio de mercado TCGplayer en USD). Endpoints `/api/sets/card/<código>/` (OP, EB, PRB), `/api/decks/card/<código>/` (ST) y `/api/promos/card/<código>/` (P).
- **Imágenes (sin "SAMPLE"):** las imágenes oficiales de Bandai traen la marca de agua "SAMPLE", así que **todas las imágenes del catálogo son recortes de las fotos de David**: `recortar_foto.py` baja la imagen oficial solo como referencia, encuentra la carta en la foto (SIFT + homografía, ignorando la franja del SAMPLE), la endereza a proporción 63×88 (630×880 px) y la mejora un poco (balance de blancos, denoise, contraste, nitidez). Se guarda en `img/<CÓDIGO>.webp`.
  - Al agregar: `python3 agregar_carta.py OP11-041 --estado LP --foto lote.jpg` (o deja las fotos en una carpeta y exporta `CARTAS_FOTOS=/ruta/fotos`).
  - Si no hay foto, se usa la imagen oficial como último recurso, queda marcada `imagen_marca_agua: true` y se puede arreglar después con `python3 agregar_carta.py --recortar-fotos fotos/*.jpg`.
  - Fotos propias sueltas: `--imagen img/archivo.webp`.
- **Precio de referencia CLP** = precio de mercado USD × dólar del día ([open.er-api.com](https://open.er-api.com), respaldo [mindicador.cl](https://mindicador.cl)), redondeado a $10 → `precio_referencia`.
- **Precio de venta (el que se muestra y suma el total)** → `precio_venta_clp`: si la referencia es menor a $500 se le suman $50, y nunca baja de $100 (ej. 40→100, 70→120, 450→500, 1590→1590). Un `--precio` manual manda. `--aplicar-regla` la reaplica sin internet.

One Piece Card Game © Eiichiro Oda / Shueisha, Toei Animation, Bandai. Sitio de colección personal, sin afiliación oficial.
