// Pezzi riusabili: costruzione di elementi, date, avvisi, fogli che salgono.

/** Crea un elemento. `testo` imposta textContent, e va usato sempre con i dati
    che arrivano dalle persone: `html` scriverebbe il markup così com'è. */
export function el(tag, props = {}, figli = []) {
  const nodo = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "testo") nodo.textContent = v;
    else if (k === "html") nodo.innerHTML = v; // solo icone nostre, mai dati altrui
    else if (k === "classe") nodo.className = v;
    else if (k.startsWith("on")) nodo.addEventListener(k.slice(2).toLowerCase(), v);
    else nodo.setAttribute(k, v === true ? "" : v);
  }
  for (const f of [].concat(figli)) {
    if (f === null || f === undefined || f === false) continue;
    nodo.append(typeof f === "string" ? document.createTextNode(f) : f);
  }
  return nodo;
}

/** Come `el`, ma per l'SVG: senza il namespace giusto il browser disegna il
    nulla, e non lo dice. */
export function svg(tag, props = {}, figli = []) {
  const nodo = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "testo") nodo.textContent = v;
    else if (k.startsWith("on")) nodo.addEventListener(k.slice(2).toLowerCase(), v);
    else nodo.setAttribute(k === "classe" ? "class" : k, v === true ? "" : v);
  }
  for (const f of [].concat(figli)) {
    if (f === null || f === undefined || f === false) continue;
    nodo.append(typeof f === "string" ? document.createTextNode(f) : f);
  }
  return nodo;
}

export const svuota = (nodo) => (nodo.replaceChildren(), nodo);

// --- Date ------------------------------------------------------------------
const GIORNI = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
const MESI = [
  "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
  "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
];

/** "2026-07-14" → Date locale. `new Date("2026-07-14")` la leggerebbe come
    UTC, e in Italia d'estate diventerebbe il 14 alle 2 di notte: a fine mese
    il giorno sbagliato. */
export function daIso(iso) {
  const [a, m, g] = iso.split("-").map(Number);
  return new Date(a, m - 1, g);
}

export const aIso = (data) =>
  `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}-${String(
    data.getDate()
  ).padStart(2, "0")}`;

export function giornoEsteso(iso) {
  const d = daIso(iso);
  return `${GIORNI[d.getDay()]} ${d.getDate()} ${MESI[d.getMonth()]}`;
}

export function giornoBreve(iso) {
  const d = daIso(iso);
  return `${GIORNI[d.getDay()].slice(0, 3)} ${d.getDate()}/${d.getMonth() + 1}`;
}

export function etichettaGiorno(iso, oggiIso) {
  if (iso === oggiIso) return "oggi";
  const domani = daIso(oggiIso);
  domani.setDate(domani.getDate() + 1);
  if (iso === aIso(domani)) return "domani";
  return giornoEsteso(iso);
}

// --- Soldi -----------------------------------------------------------------
export const euro = (cent) =>
  cent === 0 ? "gratis" : `${(cent / 100).toFixed(2).replace(".", ",")} €`;

export const plurale = (n, uno, molti) => `${n} ${n === 1 ? uno : molti}`;

// --- Avvisi e fogli --------------------------------------------------------
export const avviso = (tono, testo) => el("div", { classe: `avviso ${tono}`, testo });

/** Il foglio che sale dal basso. Si chiude toccando il velo o con Esc. */
export function foglio(contenuto, { alChiudere } = {}) {
  const dentro = el("div", { classe: "foglio", role: "dialog", "aria-modal": "true", tabindex: "-1" }, [
    el("div", { classe: "maniglia" }),
    contenuto,
  ]);

  const velo = el("div", {
    classe: "velo",
    onclick: (e) => {
      if (e.target === velo) chiudi();
    },
  }, dentro);

  function chiudi() {
    velo.remove();
    document.removeEventListener("keydown", allaTastiera);
    window.removeEventListener("hashchange", chiudi);
    document.body.style.overflow = "";
    alChiudere?.();
  }

  function allaTastiera(e) {
    if (e.key === "Escape") chiudi();
  }

  document.addEventListener("keydown", allaTastiera);
  // Cambiando sezione il foglio se ne va con la pagina: restando aperto,
  // il velo coprirebbe la sezione nuova e non si potrebbe più toccare niente.
  window.addEventListener("hashchange", chiudi);
  document.body.style.overflow = "hidden";
  document.body.append(velo);
  // Il fuoco entra nel foglio, ma non su un bottone: dargli il primo
  // farebbe sembrare scelta un'opzione che nessuno ha ancora toccato.
  dentro.focus();
  return { chiudi, nodo: dentro };
}

/** Messaggio breve in fondo allo schermo. */
export function brindisi(testo, tono = "info") {
  const nodo = el("div", {
    classe: `avviso ${tono}`,
    role: "status",
    style:
      "position:fixed;left:50%;transform:translateX(-50%);bottom:calc(var(--tab-h) + 16px);" +
      "z-index:70;max-width:min(92vw,520px);box-shadow:var(--ombra-alta);background:var(--superficie)",
    testo,
  });
  document.body.append(nodo);
  setTimeout(() => nodo.remove(), 3600);
}

// --- Icone (le uniche cose che passano da `html`) --------------------------
export const ICONE = {
  ombrellone: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
      stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/>
      <path d="M3 11a9 9 0 0 1 18 0z"/><path d="M12 21a2.5 2.5 0 0 0 4 0"/></svg>`,
  listino: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
      stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2z"/>
      <path d="M9 8h6M9 12h6M9 16h3"/></svg>`,
  mappa: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
      stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/>
      <circle cx="12" cy="10" r="2.5"/></svg>`,
  biglietto: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
      stroke-linecap="round" stroke-linejoin="round"><path d="M4 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2 2 2 0 0 0 0 4 2 2 0 0 1-2 2H6a2 2 0 0 1-2-2 2 2 0 0 0 0-4z"/>
      <path d="M14 6v10"/></svg>`,
};
