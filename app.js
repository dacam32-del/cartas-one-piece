// Cartas One Piece — catálogo estático. Lee cartas.json (o demo.json con ?demo=1).
const DEMO = new URLSearchParams(location.search).has("demo");
const SRC = DEMO ? "demo.json" : "cartas.json";
const COLOR_ORDER = ["Rojo","Verde","Azul","Morado","Negro","Amarillo","Multicolor"];
const COLOR_VAR = {Rojo:"var(--Rojo)",Verde:"var(--Verde)",Azul:"var(--Azul)",Morado:"var(--Morado)",Negro:"var(--Negro)",Amarillo:"var(--Amarillo)",Multicolor:"var(--Multi)"};
const TYPE_ORDER = ["Leader","Character","Event","Stage","DON!!"];
const TYPE_ES = {Leader:"Líder",Character:"Personaje",Event:"Evento",Stage:"Escenario","DON!!":"DON!!"};
const RAR_ORDER = ["L","C","UC","R","SR","SEC","SP","TR","P","PR","Alt Art"];
const RAR_NAME = {L:"Leader",C:"Común",UC:"Infrecuente",R:"Rara",SR:"Super Rara",SEC:"Secreta",SP:"Special (SP)",TR:"Treasure Rare",P:"Promo","Alt Art":"Alt Art / Parallel"};
const RAR_COL = {L:"#ff6b6b",C:"#b9bec4",UC:"#9fd3c7",R:"#7fb2ff",SR:"#e3c16f",SEC:"#ff9f43",SP:"#c77dff",TR:"#ffd166",P:"#7ee2a8","Alt Art":"#f0a6ff"};
const ESTADO = {NM:"Near Mint",LP:"Lightly Played",MP:"Moderately Played",HP:"Heavily Played",DMG:"Dañada"};
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const clp = n => n==null ? "—" : "$" + Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const usd = n => n==null ? "s/d" : "US$" + Number(n).toFixed(2).replace(".", ",");
const norm = s => String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const colores = c => Array.isArray(c.color) ? c.color : (c.color ? String(c.color).split(/[\/,]\s*/) : []);
const colorKey = c => { const cs = colores(c); return cs.length > 1 ? "Multicolor" : (cs[0] || "—"); };
const accent = c => { const cs = colores(c); return cs.length > 1 ? `linear-gradient(90deg,${cs.map(x=>COLOR_VAR[x]||"#888").join(",")})` : (COLOR_VAR[cs[0]] || "#888"); };
const accentSolid = c => COLOR_VAR[colores(c)[0]] || "#888";
const qty = c => c.cantidad ?? 1;
const pv = c => c.precio_venta_clp ?? c.precio_ref_clp ?? null;   // precio de venta mostrado (regla de David)
const effect = t => esc(t).replace(/\[([^\]]+)\]/g, '<span class="kw">$1</span>');

let cards = [], DATA = {}, list = [], cur = 0;
const groups = [
  {key:"color",label:"Color",get:c=>colores(c).length>1?[...colores(c),"Multicolor"]:colores(c),order:COLOR_ORDER},
  {key:"tipo",label:"Tipo",get:c=>[c.tipo||"—"],order:TYPE_ORDER,fmt:v=>TYPE_ES[v]||v},
  {key:"rareza",label:"Rareza",get:c=>[...(c.rareza?[c.rareza]:[]),...(c.alt_art?["Alt Art"]:[])],order:RAR_ORDER},
  {key:"set",label:"Set",get:c=>[c.set||"—"],order:null},
  {key:"estado",label:"Estado",get:c=>[c.estado||"—"],order:["NM","LP","MP","HP","DMG"]},
];
const state = {q:"", sort:"recientes", sel:Object.fromEntries(groups.map(g=>[g.key,new Set()]))};

function buildFilters(){
  const box = document.getElementById("filters"); box.innerHTML = "";
  for (const g of groups){
    const counts = {}; cards.forEach(c => g.get(c).forEach(v => counts[v]=(counts[v]||0)+qty(c)));
    const vals = Object.keys(counts).sort((a,b)=>{ if(g.order){ const ia=g.order.indexOf(a), ib=g.order.indexOf(b); return (ia<0?99:ia)-(ib<0?99:ib) || a.localeCompare(b,"es"); } return a.localeCompare(b,"es",{numeric:true}); });
    if (vals.length < 1) continue;
    const row = document.createElement("div"); row.className = "fgroup";
    row.innerHTML = `<span class="flabel">${g.label}</span>` + vals.map(v => {
      const dot = g.key==="color" ? `<span class="dot" style="background:${COLOR_VAR[v]||"#888"}"></span>` : g.key==="rareza" ? `<span class="dot" style="background:${RAR_COL[v]||"#777"}"></span>` : "";
      return `<button class="chip" data-group="${g.key}" data-value="${esc(v)}" title="${esc(g.key==="rareza"?RAR_NAME[v]||v:"")}">${dot}${esc(g.fmt?g.fmt(v):v)} <span class="n">${counts[v]}</span></button>`; }).join("");
    box.appendChild(row);
  }
}
document.getElementById("filters").addEventListener("click", e => { const b = e.target.closest(".chip"); if(!b) return;
  const s = state.sel[b.dataset.group], v = b.dataset.value; s.has(v)?s.delete(v):s.add(v); b.classList.toggle("on", s.has(v)); render(); });

function filtered(){
  const q = norm(state.q).trim();
  const out = cards.filter(c => (!q || q.split(/\s+/).every(w => c._search.includes(w))) &&
    groups.every(g => { const s = state.sel[g.key]; return !s.size || g.get(c).some(v => s.has(v)); }));
  const byName = (a,b) => (a.nombre||"").localeCompare(b.nombre||"","es");
  const S = {
    recientes:(a,b)=>(b.fecha_alta||"").localeCompare(a.fecha_alta||"")||(b.id||0)-(a.id||0),
    codigo:(a,b)=>(a.codigo||"").localeCompare(b.codigo||"","es",{numeric:true}),
    precio_desc:(a,b)=>(pv(b)??-1)-(pv(a)??-1)||byName(a,b),
    precio_asc:(a,b)=>(pv(a)??1e12)-(pv(b)??1e12)||byName(a,b),
    nombre:byName,
    costo:(a,b)=>(a.costo??-1)-(b.costo??-1)||byName(a,b),
    poder:(a,b)=>(b.poder??-1)-(a.poder??-1)||byName(a,b)};
  return out.sort(S[state.sort]);
}
function img(c, cls){ return c.imagen ? `<img src="${esc(c.imagen)}" alt="${esc(c.nombre)}" loading="lazy" decoding="async" onerror="this.outerHTML='<div class=&quot;noimg&quot;>Sin imagen</div>'">` : `<div class="noimg">Sin imagen</div>`; }
function tile(c, idx){
  const q = qty(c);
  return `<button class="tile" data-idx="${idx}" aria-label="${esc(c.nombre)}">${img(c)}
    ${pv(c)!=null?`<span class="ptag">${clp(pv(c))}</span>`:""}${q>1?`<span class="qbadge">x${q}</span>`:""}${c.alt_art?'<span class="altb">ALT</span>':""}</button>`;
}
function render(){
  list = filtered();
  const vacio = cards.length === 0;
  document.getElementById("vacio").hidden = !vacio;
  document.querySelector(".top .row").hidden = vacio;
  document.getElementById("grid").innerHTML = list.map(tile).join("");
  document.getElementById("empty").style.display = (!vacio && !list.length) ? "block" : "none";
  const any = state.q || Object.values(state.sel).some(s=>s.size);
  const n = list.reduce((a,c)=>a+qty(c),0);
  const nf = Object.values(state.sel).reduce((a,s)=>a+s.size,0);
  document.getElementById("count").textContent = `${n} ${n===1?"carta":"cartas"}`;
  document.getElementById("fstate").hidden = !any;
  const fc = document.getElementById("fcount"); fc.hidden = !nf; fc.textContent = nf;
  document.getElementById("apply").textContent = `Ver ${n} ${n===1?"carta":"cartas"}`;
}
const WA_NUM="56956592453";
const WA_ICON='<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.4.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2s.2-1.1.2-1.2-.2-.2-.4-.3z"/></svg>';
function waLink(t){ return "https://wa.me/"+WA_NUM+"?text="+encodeURIComponent(t); }
function detail(dx){
  const c = list[cur]; if(!c) return;
  const det = document.getElementById("det");
  det.classList.remove("anim"); void det.offsetWidth; det.style.setProperty("--dx",(dx||0)+"px"); det.classList.add("anim");
  const nums = [["Costo",c.costo],["Poder",c.poder],["Counter",c.counter],["Vida",c.vida]].filter(x=>x[1]!=null&&x[1]!=="");
  det.innerHTML = `<div class="bigimg">${img(c)}</div>
  <div style="--acc:${accentSolid(c)}"><div class="dh"><h2>${c.costo!=null?`<span class="cost">${esc(c.costo)}</span> `:""}${esc(c.nombre)}</h2>
    <div class="cod">${esc(c.codigo)} · ${esc(c.set||"")}</div></div>
    <div class="pricebox"><div><div class="big">${clp(pv(c))} <small>CLP</small></div>${c.precio_referencia!=null&&c.precio_referencia!==pv(c)?`<div style="font-size:12px;color:var(--mut,#9aa)">Ref. mercado ${clp(c.precio_referencia)}</div>`:""}<div class="stock" style="margin-top:6px;font-size:13px">Cantidad: ${qty(c)}</div></div>
      <div class="mk">Mercado TCGplayer<br><b style="color:var(--txt)">${usd(c.precio_mercado_usd)}</b></div></div>
    <a class="wabuy" href="${waLink(`Hola! Quiero comprar esta carta: ${c.nombre} (${c.codigo})${pv(c)!=null?` - ${clp(pv(c))} CLP`:""}`)}" target="_blank" rel="noopener">${WA_ICON} Comprar por WhatsApp</a>
    ${nums.length?`<div class="nums">${nums.map(([k,v])=>`<div class="num"><b>${esc(typeof v==="number"&&v>=1000?v.toLocaleString("es-CL"):v)}</b><span>${k}</span></div>`).join("")}</div>`:""}
    ${c.texto?`<div class="effect">${effect(c.texto)}</div>`:""}
    <dl>
      <dt>Tipo</dt><dd>${esc(TYPE_ES[c.tipo]||c.tipo||"—")}${c.tipo&&TYPE_ES[c.tipo]&&TYPE_ES[c.tipo]!==c.tipo?` <span style="color:var(--mut)">(${esc(c.tipo)})</span>`:""}</dd>
      <dt>Color</dt><dd>${colores(c).map(k=>`<span class="dot" style="background:${COLOR_VAR[k]||"#888"}"></span> ${esc(k)}`).join(" &nbsp;")||"—"}</dd>
      <dt>Rareza</dt><dd>${esc(c.rareza||"—")} ${RAR_NAME[c.rareza]?`<span style="color:var(--mut)">· ${esc(RAR_NAME[c.rareza])}</span>`:""}${c.alt_art?" · Alt Art ✨":""}</dd>
      <dt>Set</dt><dd>${esc(c.set||"—")}</dd>
      ${c.subtipos?`<dt>Subtipos</dt><dd>${esc(c.subtipos)}</dd>`:""}
      ${c.atributo?`<dt>Atributo</dt><dd>${esc(c.atributo)}</dd>`:""}
      <dt>Estado</dt><dd>${esc(c.estado||"—")}${ESTADO[c.estado]?` <span style="color:var(--mut)">· ${ESTADO[c.estado]}</span>`:""}</dd>
      <dt>Idioma</dt><dd>${esc(c.idioma||"—")}</dd>
      <dt>Ingreso</dt><dd>${esc(c.fecha_alta||"—")}</dd>
    </dl>
    ${c.notas?`<div class="nota">ⓘ ${esc(c.notas)}</div>`:""}
    <a class="sf" href="https://en.onepiece-cardgame.com/cardlist/?freewords=${encodeURIComponent(c.codigo||c.nombre)}" target="_blank" rel="noopener">Ver en la lista oficial ↗</a>
  </div>`;
  document.getElementById("pos").textContent = `${cur+1} / ${list.length}`;
  document.getElementById("prev").disabled = cur===0;
  document.getElementById("next").disabled = cur===list.length-1;
  document.querySelector("#modal .stage").scrollTop = 0;
  history.replaceState(null, "", location.search + "#carta-" + c.id);
}
function openAt(i){ cur=i; document.getElementById("modal").classList.add("open"); document.body.style.overflow="hidden"; detail(0); }
function closeM(){ document.getElementById("modal").classList.remove("open"); document.body.style.overflow=""; history.replaceState(null,"",location.pathname+location.search); }
function go(d){ const n=cur+d; if(n<0||n>=list.length) return; cur=n; detail(d>0?40:-40); }

document.getElementById("grid").addEventListener("click", e => { const t=e.target.closest(".tile"); if(t) openAt(+t.dataset.idx); });
document.getElementById("prev").onclick = () => go(-1);
document.getElementById("next").onclick = () => go(1);
document.getElementById("close").onclick = closeM;
document.addEventListener("keydown", e => { if(!document.getElementById("modal").classList.contains("open")) return;
  if(e.key==="ArrowRight") go(1); else if(e.key==="ArrowLeft") go(-1); else if(e.key==="Escape") closeM(); });
(() => { const st=document.querySelector("#modal .stage"); let x0=null,y0=null;
  st.addEventListener("touchstart", e => { x0=e.changedTouches[0].clientX; y0=e.changedTouches[0].clientY; }, {passive:true});
  st.addEventListener("touchend", e => { if(x0==null) return; const dx=e.changedTouches[0].clientX-x0, dy=e.changedTouches[0].clientY-y0;
    if(Math.abs(dx)>50 && Math.abs(dx)>Math.abs(dy)*1.3) go(dx<0?1:-1); x0=null; }, {passive:true}); })();
document.getElementById("q").addEventListener("input", e => { state.q=e.target.value; render(); });
document.getElementById("sort").addEventListener("change", e => { state.sort=e.target.value; render(); });
function openF(o){ const dr=document.getElementById("drawer"); dr.classList.toggle("open",o); dr.setAttribute("aria-hidden",!o);
  document.getElementById("scrim").hidden=!o; document.getElementById("fbtn").setAttribute("aria-expanded",o); document.body.style.overflow=o?"hidden":""; }
document.getElementById("fbtn").onclick = () => openF(true);
document.getElementById("fclose").onclick = document.getElementById("scrim").onclick = document.getElementById("apply").onclick = () => openF(false);
document.addEventListener("keydown", e => { if(e.key==="Escape" && document.getElementById("drawer").classList.contains("open")) openF(false); });
document.getElementById("clear2").onclick = () => document.getElementById("clear").click();
document.getElementById("clear").onclick = () => { state.q=""; document.getElementById("q").value=""; Object.values(state.sel).forEach(s=>s.clear());
  document.querySelectorAll(".chip.on").forEach(b=>b.classList.remove("on")); render(); };

fetch(SRC + "?t=" + Date.now()).then(r => { if(!r.ok) throw new Error(r.status); return r.json(); }).then(d => {
  DATA = d;
  cards = (d.cartas||[]).map((c,i) => ({...c, id:c.id??i+1,
    _search: norm([c.codigo,c.nombre,c.nombre_en,c.tipo,TYPE_ES[c.tipo],c.set,c.rareza,RAR_NAME[c.rareza],colores(c).join(" "),c.subtipos,c.atributo,c.texto,c.notas].join(" "))}));
  document.getElementById("demoBanner").hidden = !DEMO;
  const tq = cards.reduce((a,c)=>a+qty(c),0);
  document.getElementById("tot").textContent = tq ? `${tq} cartas · ${clp(cards.reduce((a,c)=>a+(pv(c)||0)*qty(c),0))}` : "";
  document.getElementById("foot").innerHTML = `Precios de referencia: ${esc(d.fuente_precios||"—")}${d.dolar_clp?` · Dólar $${esc(String(d.dolar_clp).replace(".",","))} CLP`:""}<br>Actualizado ${esc(d.actualizado||"—")} · El valor real depende del estado de cada carta.<br>One Piece Card Game © Eiichiro Oda / Shueisha, Toei Animation, Bandai. Sitio de colección personal, sin afiliación oficial.`;
  buildFilters(); render();
  const m = location.hash.match(/^#carta-(\d+)$/); if(m){ const i=list.findIndex(c=>String(c.id)===m[1]); if(i>=0) openAt(i); }
}).catch(err => { document.getElementById("vacio").hidden = false; document.querySelector(".vacio h2").textContent = "No se pudo cargar " + SRC; document.querySelector(".vacio p").textContent = String(err); });
