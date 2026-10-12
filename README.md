# Cartas One Piece Card Game — colección de David Eduardo

Catálogo de mis cartas del **One Piece Card Game (OPTCG)**: código, nombre, color, tipo, rareza, set, costo, poder, counter, cantidad, estado, precio de referencia en pesos chilenos (CLP) y notas.

**Ver la página:** https://dacam32-del.github.io/cartas-one-piece/
**Vista de ejemplo (demo, cartas que NO son de la colección):** https://dacam32-del.github.io/cartas-one-piece/?demo=1

## Qué tiene la página
- Grilla de cartas con imagen, rareza, color, código y precio CLP.
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
`id, codigo, nombre, color (lista), tipo (Leader/Character/Event/Stage/DON!!), rareza (C/UC/R/SR/SEC/L/SP/TR/P), alt_art (true/false), set, costo, poder, counter, vida, atributo, subtipos, texto, cantidad, estado (NM/LP/MP/HP/DMG), idioma, precio_mercado_usd, precio_ref_clp, dolar_clp, notas, imagen, fecha_alta`.

## De dónde salen los datos, imágenes y precios
- **Datos de la carta y precio de mercado:** [optcgapi.com](https://optcgapi.com) (API pública; precio de mercado TCGplayer en USD). Endpoints `/api/sets/card/<código>/` (OP, EB, PRB), `/api/decks/card/<código>/` (ST) y `/api/promos/card/<código>/` (P).
- **Imágenes:** lista oficial de Bandai, `https://en.onepiece-cardgame.com/images/cardlist/card/<CÓDIGO>.png` (las Parallel/Alt Art usan el sufijo `_p1`, `_p2`…). El script la descarga, la reduce a 600 px y la guarda en `img/` como webp, para no depender del sitio externo. Si falla, usa la imagen de optcgapi.com. Nota: las imágenes oficiales vienen con la marca de agua "SAMPLE" (así las publica Bandai); si quieres fotos propias de tus cartas, guárdalas en `img/` y usa `--imagen img/archivo.jpg`.
- **Precio de referencia CLP** = precio de mercado USD × dólar del día ([open.er-api.com](https://open.er-api.com), respaldo [mindicador.cl](https://mindicador.cl)), redondeado a $10. Se puede fijar a mano con `--precio`.

One Piece Card Game © Eiichiro Oda / Shueisha, Toei Animation, Bandai. Sitio de colección personal, sin afiliación oficial.
