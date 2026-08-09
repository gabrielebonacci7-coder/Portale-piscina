// Pezzi riusabili: formattazione, elementi, pannelli, avvisi.

// ---------- Costruzione di elementi ----------
/** Crea un elemento. `props.testo` imposta textContent (sicuro con dati utente). */
export function el(tag, props = {}, figli = []) {
  const nodo = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "testo") nodo.textContent = v;
    else if (k === "html") nodo.innerHTML = v; // solo per icone nostre, mai dati utente
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

export function svuota(nodo) {
  nodo.replaceChildren();
  return nodo;
}

// ---------- Date e numeri ----------
const GIORNI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"];
export const GIORNI_LUNGHI = [
  "lunedì",
  "martedì",
  "mercoledì",
  "giovedì",
  "venerdì",
  "sabato",
  "domenica",
];

const fData = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "short" });
const fOra = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });
const fCompleta = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
  hour: "2-digit",
  minute: "2-digit",
});

/** "mer 12 set · 08:00–13:00" */
export function quando(inizioIso, fineIso) {
  const inizio = new Date(inizioIso);
  // getDay(): 0 = domenica; qui la settimana comincia da lunedì.
  const giorno = GIORNI[(inizio.getDay() + 6) % 7];
  let testo = `${giorno} ${fData.format(inizio)} · ${fOra.format(inizio)}`;
  if (fineIso) testo += `–${fOra.format(new Date(fineIso))}`;
  return testo;
}

export const quandoEsteso = (iso) => fCompleta.format(new Date(iso));

/** "oggi 14:30", "ieri", "12 set" — per l'elenco delle conversazioni. */
export function quandoRelativo(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const oggi = new Date();
  const stessoGiorno = d.toDateString() === oggi.toDateString();
  if (stessoGiorno) return fOra.format(d);
  const ieri = new Date(oggi);
  ieri.setDate(oggi.getDate() - 1);
  if (d.toDateString() === ieri.toDateString()) return "ieri";
  return fData.format(d);
}

export const ora = (iso) => fOra.format(new Date(iso));

/** Da "14:00:00" a "14:00". */
export const oraBreve = (t) => (t || "").slice(0, 5);

export function euro(importo, tipo) {
  if (importo === null || importo === undefined) return "da concordare";
  const n = Number(importo);
  const unita = {
    orario: "/h",
    giornaliero: "/giorno",
    a_turno: "/turno",
    mensile: "/mese",
    da_concordare: "",
  }[tipo] ?? "";
  return { valore: `${n.toFixed(2).replace(".", ",")} €`, unita };
}

// ---------- Etichette leggibili ----------
export const ETICHETTE = {
  tipo_turno: {
    turno_fisso: "Turno fisso",
    sostituzione_urgente: "Sostituzione",
    evento_serale: "Evento serale",
    stagionale: "Stagionale",
    weekend: "Weekend",
    altro: "Altro",
  },
  tipo_struttura: {
    comunale: "Piscina comunale",
    hotel: "Hotel",
    condominio: "Condominio",
    centro_sportivo: "Centro sportivo",
    palestra: "Palestra",
    parco_acquatico: "Parco acquatico",
    camping: "Camping",
    privata: "Privata",
    altro: "Altro",
  },
  stato: {
    bozza: "Bozza",
    aperto: "Aperto",
    assegnato: "Assegnato",
    chiuso: "Chiuso",
    scaduto: "Scaduto",
  },
  candidatura: {
    inviata: "In attesa",
    accettata: "Accettata",
    rifiutata: "Non selezionata",
    ritirata: "Ritirata",
  },
  brevetto: {
    P: "P — piscina",
    IP: "IP — acque interne",
    MIP: "MIP — mare",
    altro: "Altro ente",
  },
  compenso: {
    orario: "all'ora",
    giornaliero: "al giorno",
    a_turno: "a turno",
    mensile: "al mese",
    da_concordare: "da concordare",
  },
};

export const etichetta = (gruppo, chiave) => ETICHETTE[gruppo]?.[chiave] ?? chiave ?? "";

// ---------- Elementi ----------
export const chip = (testo, colore) =>
  el("span", { classe: `chip ${colore || ""}`.trim(), testo });

export function stelle(valore, totale = 5) {
  const contenitore = el("span", { classe: "stelle", "aria-label": `${valore} su ${totale}` });
  for (let i = 1; i <= totale; i++) {
    contenitore.append(el("span", { classe: i <= Math.round(valore) ? "" : "spenta", testo: "★" }));
  }
  return contenitore;
}

export const vuoto = (messaggio, dettaglio) =>
  el("div", { classe: "vuoto" }, [
    el("p", { testo: messaggio, style: "font-weight:600" }),
    dettaglio && el("p", { classe: "sommesso", testo: dettaglio }),
  ]);

export const caricamento = () => el("div", { classe: "caricamento", testo: "Caricamento…" });

export const avviso = (testo, tipo = "errore") =>
  // Senza la frase di scorta un errore imprevisto darebbe una fascia colorata
  // e vuota: l'utente non capirebbe niente e chi sviluppa nemmeno.
  el("div", { classe: `avviso ${tipo}`, testo: testo || "Qualcosa non ha funzionato" });

// ---------- Foto ----------
/** Avatar: la foto se c'è, altrimenti le iniziali. */
export function avatar(urlFoto, nome, grande = false) {
  const misura = grande ? "avatar grande" : "avatar";
  if (urlFoto) {
    return el("img", {
      classe: misura,
      src: urlFoto,
      alt: nome ? `Foto di ${nome}` : "Foto profilo",
      loading: "lazy",
    });
  }
  const iniziali = (nome || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
  return el("div", {
    classe: `${misura} avatar-vuoto${grande ? " grande" : ""}`,
    "aria-hidden": "true",
    testo: iniziali,
  });
}

export const ETICHETTE_FOTO = {
  ingresso: "Ingresso",
  vasca: "Vasca",
  spogliatoi: "Spogliatoi",
  altro: "Altro",
};

/** Striscia di foto scorrevole. `alTogli` la rende modificabile. */
export function galleria(foto, alTogli) {
  const striscia = el("div", { classe: "galleria" });
  for (const f of foto) {
    const riquadro = el("figure", {}, [
      el("img", {
        src: f.anteprima_url,
        alt: f.didascalia || ETICHETTE_FOTO[f.tipo] || "Foto della struttura",
        loading: "lazy",
      }),
      el("span", { classe: "targhetta", testo: ETICHETTE_FOTO[f.tipo] ?? f.tipo }),
      f.didascalia && el("figcaption", { testo: f.didascalia }),
    ]);
    if (alTogli) {
      riquadro.append(
        el("button", {
          classe: "togli",
          type: "button",
          "aria-label": "Elimina foto",
          html: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
          onclick: () => alTogli(f),
        }),
      );
    }
    striscia.append(riquadro);
  }
  return striscia;
}

// ---------- Zone ----------
/** Raggruppa le zone per area, mantenendo l'ordine in cui arrivano. */
export function perArea(zone) {
  const gruppi = new Map();
  for (const z of zone) {
    const area = z.area || "Altre zone";
    if (!gruppi.has(area)) gruppi.set(area, []);
    gruppi.get(area).push(z);
  }
  return gruppi;
}

/** Opzioni di un <select> divise per area.

    Con una trentina di zone un elenco piatto è scomodo da scorrere sul
    telefono: le intestazioni di gruppo fanno trovare subito la propria. */
export function opzioniZone(zone, selezionata) {
  const opzioni = [];
  for (const [area, elenco] of perArea(zone)) {
    opzioni.push(
      el(
        "optgroup",
        { label: area },
        elenco.map((z) =>
          el("option", {
            value: z.id,
            testo: z.macro_area ? `${z.nome} — ${z.macro_area}` : z.nome,
            selected: String(z.id) === String(selezionata),
          }),
        ),
      ),
    );
  }
  return opzioni;
}

/** Caselle di scelta multipla delle zone, con l'intestazione dell'area. */
export function caselleZone(zone, selezionate = []) {
  const scelte = new Set(selezionate.map(String));
  const contenitore = el("div", { classe: "zone-scelta" });
  for (const [area, elenco] of perArea(zone)) {
    contenitore.append(
      el("span", { classe: "etichetta", testo: area }),
      el(
        "div",
        { classe: "zone-griglia" },
        elenco.map((z) =>
          el("label", {}, [
            el("input", {
              type: "checkbox",
              name: "zona",
              value: z.id,
              checked: scelte.has(String(z.id)),
            }),
            el("span", { testo: z.nome }),
          ]),
        ),
      ),
    );
  }
  return contenitore;
}

// ---------- Pannello a scomparsa ----------
export function pannello(titolo, contenuto, { azione } = {}) {
  const chiudi = () => velo.remove();

  const corpo = el("div", { classe: "pannello", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "pannello-testa" }, [
      el("h2", { testo: titolo }),
      azione,
      el("button", {
        classe: "btn-icona",
        "aria-label": "Chiudi",
        html: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
        onclick: chiudi,
      }),
    ]),
    contenuto,
  ]);

  const velo = el("div", { classe: "velo", onclick: (e) => e.target === velo && chiudi() }, corpo);
  document.addEventListener("keydown", function esc(e) {
    if (e.key === "Escape") {
      chiudi();
      document.removeEventListener("keydown", esc);
    }
  });

  document.body.append(velo);
  return { chiudi, corpo };
}

/** Messaggio che scompare da solo. */
export function brindisi(testo) {
  document.querySelector(".brindisi")?.remove();
  const n = el("div", { classe: "brindisi", role: "status", testo });
  document.body.append(n);
  setTimeout(() => n.remove(), 2600);
}

// ---------- Icone ----------
export const ICONE = {
  bacheca: '<svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg>',
  candidature:
    '<svg viewBox="0 0 24 24"><path d="M9 11l2 2 4-4"/><rect x="4" y="4" width="16" height="16" rx="2.5"/></svg>',
  messaggi:
    '<svg viewBox="0 0 24 24"><path d="M21 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.4A8 8 0 1 1 21 11.5z"/></svg>',
  profilo:
    '<svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.5"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg>',
  // Uno scudo: il pannello di gestione è il posto dove si controlla chi entra.
  gestione:
    '<svg viewBox="0 0 24 24"><path d="M12 3l7 3v5.5c0 4.3-2.9 7.8-7 9.5-4.1-1.7-7-5.2-7-9.5V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>',
  piu: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  filtro: '<svg viewBox="0 0 24 24"><path d="M3 6h18M7 12h10M10 18h4"/></svg>',
  indietro: '<svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg>',
  invia: '<svg viewBox="0 0 24 24"><path d="M4 12l16-8-6 16-2.5-6.5L4 12z"/></svg>',
  esci: '<svg viewBox="0 0 24 24"><path d="M15 12H4m3-3l-3 3 3 3"/><path d="M11 4h6a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"/></svg>',
};

/** Il marchio: un salvagente rosso e bianco, lo stesso segno dell'icona.

    Sta su una piastra scura perché il bianco abbia contrasto. La piastra è
    legata a un token: nel tema scuro va schiarita, altrimenti sparisce nel
    fondo. Il file dell'icona resta invece a colori fissi, perché viene
    caricato come immagine e il CSS della pagina non lo raggiunge. */
export const LOGO = `<svg viewBox="0 0 64 64" role="img" aria-label="Guardlink">
  <rect width="64" height="64" rx="14" fill="var(--marchio-piastra)"/>
  <circle cx="32" cy="32" r="19" fill="none" stroke="#ffffff" stroke-width="10"/>
  <circle cx="32" cy="32" r="19" fill="none" stroke="#d63e26" stroke-width="10"
          stroke-dasharray="14.92 14.92" stroke-dashoffset="7.46"/>
</svg>`;
