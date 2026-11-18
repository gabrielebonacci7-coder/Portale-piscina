// La vista dall'alto del solarium.
//
// Disegna quello che arriva da /api/mappa: prima la scenografia (vasche,
// cassa, docce, campo da beach volley, palme), poi le postazioni. Nessuna
// coordinata è scritta qui dentro: se la piscina cambia disposizione si tocca
// piscina/dominio/piantina.py e la mappa segue.
//
// Lo stile è quello di una piscina vera vista dal drone: prato, pavimento in
// pietra chiara, acqua con i riflessi. Le tre grane (erba, acqua, pietra) sono
// piastrelle disegnate una volta sola da `python -m piscina.scripts.
// genera_texture` e qui ripetute: la stessa cosa fatta con i filtri dell'SVG
// si ricalcolerebbe a ogni zoom, e su un telefono di tre anni fa la mappa
// diventerebbe una diapositiva.
//
// Il colore dello stato sta sui lettini e in un alone sotto l'ombrellone: gli
// ombrelloni restano color panna, come sono davvero, e la mappa non diventa un
// semaforo. Da lontano si legge l'alone, da vicino l'ombrellone.
//
// Il tocco non usa il bersaglio dell'SVG ma il centro più vicino: su un
// telefono un ombrellone è largo pochi pixel, e chiedere di centrarlo sarebbe
// come chiedere di infilare un ago.

import { svg, el } from "./ui.js";

const RAGGIO_TOCCO = 34; // unità della mappa: quanto lontano può cadere il dito

export function statoDi(p) {
  if (!p.attiva) return "spenta";
  if (p.libera_mattina && p.libera_pomeriggio) return "libera";
  if (!p.libera_mattina && !p.libera_pomeriggio) return "occupata";
  return "mezza";
}

/** La postazione si può prendere per la fascia che si sta cercando? */
export function scegliibile(p, fascia) {
  if (!p.attiva) return false;
  if (fascia === "mattina") return p.libera_mattina;
  if (fascia === "pomeriggio") return p.libera_pomeriggio;
  return p.libera_mattina && p.libera_pomeriggio;
}

/** Com'è messa la postazione, detto in italiano.

    Dice sempre la verità sul giorno, non sulla fascia che si sta cercando:
    "libera solo la mattina" resta l'informazione utile anche quando è la
    mattina che si sta prenotando, perché avvisa che il pomeriggio è di un
    altro e alle 14 bisogna liberare il posto. */
export function perche(p) {
  const stato = statoDi(p);
  if (stato === "spenta") return p.nota || "Non disponibile";
  if (stato === "occupata") return "Occupata tutto il giorno";
  if (stato === "mezza") {
    return p.libera_mattina ? "Libera solo la mattina" : "Libera solo il pomeriggio";
  }
  return "Libera tutto il giorno";
}

// --- Definizioni riusabili -------------------------------------------------
function definizioni() {
  return svg("defs", {}, [
    // La cupola del parasole: la luce viene da sopra a sinistra, come a mezzogiorno.
    svg("radialGradient", { id: "cupola", cx: "0.36", cy: "0.28", r: "0.8" }, [
      svg("stop", { offset: "0", "stop-color": "#fff", "stop-opacity": "0.5" }),
      svg("stop", { offset: "0.55", "stop-color": "#fff", "stop-opacity": "0" }),
      svg("stop", { offset: "1", "stop-color": "#16242f", "stop-opacity": "0.22" }),
    ]),
    // Il fondo della vasca: più scuro dove è profonda.
    svg("linearGradient", { id: "fondale", x1: "0", y1: "0", x2: "0", y2: "1" }, [
      svg("stop", { offset: "0", "stop-color": "#9ff0ff", "stop-opacity": "0.42" }),
      svg("stop", { offset: "0.45", "stop-color": "#fff", "stop-opacity": "0" }),
      svg("stop", { offset: "1", "stop-color": "#00435f", "stop-opacity": "0.42" }),
    ]),
    svg("filter", { id: "ombra", x: "-60%", y: "-60%", width: "220%", height: "220%" }, [
      svg("feDropShadow", {
        dx: "2", dy: "3.4", stdDeviation: "2.6",
        "flood-color": "#3a1f16", "flood-opacity": "0.42",
      }),
    ]),
    svg("filter", { id: "ombra-grande", x: "-30%", y: "-30%", width: "180%", height: "180%" }, [
      svg("feDropShadow", {
        dx: "5", dy: "9", stdDeviation: "7",
        "flood-color": "#3a1f16", "flood-opacity": "0.26",
      }),
    ]),
  ]);
}

// --- Scenografia -----------------------------------------------------------
/** Il pavimento di cotto, col suo reticolo di piastrelle. */
function pavimento(e) {
  const punti = e.punti.map((p) => p.join(",")).join(" ");
  const xs = e.punti.map((p) => p[0]);
  const ys = e.punti.map((p) => p[1]);
  const [x0, x1] = [Math.min(...xs), Math.max(...xs)];
  const [y0, y1] = [Math.min(...ys), Math.max(...ys)];

  const fughe = [];
  const passo = 22; // 1,10 m: la piastrella vera del solarium
  for (let x = x0; x <= x1; x += passo) {
    fughe.push(svg("line", { classe: "sc-fuga", x1: x, y1: y0, x2: x, y2: y1 }));
  }
  for (let y = y0; y <= y1; y += passo) {
    fughe.push(svg("line", { classe: "sc-fuga", x1: x0, y1: y, x2: x1, y2: y }));
  }

  return svg("g", {}, [
    svg("defs", {}, [svg("clipPath", { id: "ritaglio-cotto" }, [svg("polygon", { points: punti })])]),
    svg("polygon", { classe: "sc-cotto", points: punti, filter: "url(#ombra-grande)" }),
    svg("g", { "clip-path": "url(#ritaglio-cotto)" }, fughe),
  ]);
}

/** Una vasca: bordo di travertino, acqua, corsie, scaletta. */
function vasca(e) {
  const pezzi = [
    svg("rect", {
      classe: "sc-bordo-vasca",
      x: e.x - 11, y: e.y - 11, width: e.w + 22, height: e.h + 22, rx: 14,
    }),
    svg("rect", { classe: "sc-acqua", x: e.x, y: e.y, width: e.w, height: e.h, rx: 8 }),
    svg("rect", {
      fill: "url(#fondale)", x: e.x, y: e.y, width: e.w, height: e.h, rx: 8,
    }),
  ];

  // Le corsie, con i galleggianti gialli come nella vasca vera.
  if (e.corsie) {
    for (let i = 1; i < e.corsie; i++) {
      const y = e.y + (e.h * i) / e.corsie;
      pezzi.push(svg("line", {
        classe: "sc-corsia", x1: e.x + 8, y1: y, x2: e.x + e.w - 8, y2: y,
      }));
    }
  }

  // Una scaletta sul lato corto, verso l'ingresso.
  const sx = e.x + e.w - 30;
  const sy = e.y + e.h;
  pezzi.push(svg("g", { classe: "sc-scaletta" }, [
    svg("line", { x1: sx, y1: sy, x2: sx, y2: sy + 11 }),
    svg("line", { x1: sx + 16, y1: sy, x2: sx + 16, y2: sy + 11 }),
    svg("line", { x1: sx, y1: sy + 6, x2: sx + 16, y2: sy + 6 }),
  ]));

  pezzi.push(svg("text", {
    classe: "sc-testo", x: e.x + e.w / 2, y: e.y + e.h / 2 + 6, testo: e.etichetta,
  }));
  return svg("g", { filter: "url(#ombra-grande)" }, pezzi);
}

/** Spogliatoi, bar, cassa, docce: un corpo di fabbrica col tetto di coppi. */
function edificio(e) {
  const pezzi = [
    svg("rect", {
      classe: e.tetto ? "sc-tetto" : "sc-servizio",
      x: e.x, y: e.y, width: e.w, height: e.h, rx: 7,
    }),
  ];
  if (e.tetto) {
    for (let x = e.x + 18; x < e.x + e.w - 6; x += 18) {
      pezzi.push(svg("line", { classe: "sc-coppo", x1: x, y1: e.y + 4, x2: x, y2: e.y + e.h - 4 }));
    }
  }
  if (e.etichetta) {
    pezzi.push(svg("text", {
      classe: "sc-testo scura", x: e.x + e.w / 2, y: e.y + e.h / 2 + 5, testo: e.etichetta,
    }));
  }
  return svg("g", { filter: "url(#ombra)" }, pezzi);
}

function albero(e) {
  return svg("g", { filter: "url(#ombra)" }, [
    svg("circle", { classe: "sc-chioma", cx: e.x, cy: e.y, r: e.r }),
    svg("circle", {
      classe: "sc-chioma chiara", cx: e.x - e.r * 0.28, cy: e.y - e.r * 0.28, r: e.r * 0.62,
    }),
  ]);
}

function scenografia(elementi) {
  const pezzi = [];
  for (const e of elementi) {
    if (e.tipo === "siepe") {
      pezzi.push(svg("polyline", {
        classe: "sc-siepe",
        points: e.punti.map((p) => p.join(",")).join(" "),
        "stroke-width": e.spessore,
      }));
    } else if (e.tipo === "pavimento") {
      pezzi.push(pavimento(e));
    } else if (e.tipo === "vasca") {
      pezzi.push(vasca(e));
    } else if (e.tipo === "edificio") {
      pezzi.push(edificio(e));
    } else if (e.tipo === "albero") {
      pezzi.push(albero(e));
    } else if (e.tipo === "bagnino") {
      // Il salvagente del bagnino: dice dov'è il punto di primo soccorso.
      pezzi.push(svg("g", { filter: "url(#ombra)" }, [
        svg("circle", { classe: "sc-salvagente", cx: e.x, cy: e.y, r: e.r }),
        svg("circle", { classe: "sc-salvagente-cuore", cx: e.x, cy: e.y, r: e.r * 0.44 }),
      ]));
    }
  }
  return svg("g", { classe: "scenografia" }, pezzi);
}

// --- Le postazioni ---------------------------------------------------------
const RAGGIO_TELO = 22;   // 1,10 m: un parasole aperto misura poco più di due metri

/** Il telo a spicchi, come i parasoli bianchi e blu della piscina: qui gli
    spicchi pari prendono il colore dello stato, così da lontano la mappa si
    legge senza dover ingrandire. */
function telo(r) {
  const n = 12;
  const pezzi = [];
  for (let i = 0; i < n; i++) {
    const t0 = ((2 * Math.PI * i) / n) - Math.PI / 2;
    const t1 = ((2 * Math.PI * (i + 1)) / n) - Math.PI / 2;
    const x0 = (r * Math.cos(t0)).toFixed(2);
    const y0 = (r * Math.sin(t0)).toFixed(2);
    const x1 = (r * Math.cos(t1)).toFixed(2);
    const y1 = (r * Math.sin(t1)).toFixed(2);
    pezzi.push(svg("path", {
      classe: i % 2 === 0 ? "spicchio tinta" : "spicchio chiaro",
      d: `M 0 0 L ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1} Z`,
    }));
  }
  return pezzi;
}

function ombrellone() {
  return svg("g", {}, [
    svg("circle", { classe: "telo-fondo", cx: 0, cy: 0, r: RAGGIO_TELO + 1.4 }),
    ...telo(RAGGIO_TELO),
    svg("circle", { fill: "url(#cupola)", cx: 0, cy: 0, r: RAGGIO_TELO }),
    svg("circle", { classe: "telo-bordo", cx: 0, cy: 0, r: RAGGIO_TELO }),
    svg("circle", { classe: "puntale", cx: 0, cy: 0, r: 3 }),
  ]);
}

/** Un lettino visto dall'alto: telaio chiaro, telo, poggiatesta. */
function lettino() {
  return svg("g", {}, [
    svg("rect", { classe: "telaio", x: -8, y: -20, width: 16, height: 40, rx: 6 }),
    svg("rect", { classe: "tinta tela", x: -6, y: -18, width: 12, height: 36, rx: 4.4 }),
    svg("rect", { classe: "poggiatesta", x: -6, y: -9, width: 12, height: 2.4 }),
  ]);
}

function disegnaPostazione(p, { fascia, scelte }) {
  const stato = statoDi(p);
  const scelta = scelte.has(p.codice);
  const utile = scegliibile(p, fascia);
  const raggio = p.tipo === "lettino" ? 21 : RAGGIO_TELO + 2;

  const corpo = svg("g", { classe: "corpo", filter: "url(#ombra)" }, [
    p.tipo === "lettino" ? lettino() : ombrellone(),
  ]);

  return svg(
    "g",
    {
      classe: `posto stato-${stato}${scelta ? " scelta" : ""}${utile ? "" : " non-scegliibile"}`,
      transform: `translate(${p.x} ${p.y})`,
      "data-codice": p.codice,
      role: "img",
      "aria-label": `${p.codice}: ${perche(p)}`,
    },
    [
      corpo,
      svg("circle", { classe: "anello", cx: 0, cy: 0, r: raggio }),
      svg("text", { classe: "etichetta", x: 0, y: raggio + 15, testo: p.codice }),
    ]
  );
}

/**
 * Disegna la mappa dentro `guscio`.
 * `dati` è la risposta di /api/mappa; `scelte` è un Set di codici.
 */
export function disegnaMappa(guscio, dati, { fascia, scelte, alTocco }) {
  const [, , larghezza, altezza] = dati.viewbox.split(" ").map(Number);

  const tela = svg("svg", {
    viewBox: dati.viewbox,
    width: larghezza,
    height: altezza,
    preserveAspectRatio: "xMidYMid meet",
    role: "group",
    "aria-label": "Mappa del solarium",
  }, [
    definizioni(),
    svg("rect", { classe: "sc-prato", x: 0, y: 0, width: larghezza, height: altezza }),
    scenografia(dati.scenografia),
    svg(
      "g",
      { classe: "postazioni" },
      dati.postazioni.map((p) =>
        disegnaPostazione(p, {
          fascia,
          scelte,
          rotazioni: dati.rotazioni || {},
          lettiniDisegnati: dati.lettini_disegnati ?? 2,
        })
      )
    ),
  ]);

  tela.addEventListener("click", (evento) => {
    const punto = tela.createSVGPoint();
    punto.x = evento.clientX;
    punto.y = evento.clientY;
    const dentro = punto.matrixTransform(tela.getScreenCTM().inverse());

    let vicina = null;
    let minima = RAGGIO_TOCCO;
    for (const p of dati.postazioni) {
      const distanza = Math.hypot(p.x - dentro.x, p.y - dentro.y);
      if (distanza < minima) {
        minima = distanza;
        vicina = p;
      }
    }
    if (vicina) alTocco(vicina);
  });

  const scorri = el("div", { classe: "mappa-scorri" }, tela);
  guscio.replaceChildren(scorri);
  return { tela, scorri, larghezza, altezza };
}

/** Rimpicciolisce la mappa finché ci sta tutta nella sua scatola.

    Serve alla vetrina della guida, dove la mappa si guarda intera e non si
    scorre: adattarla alla sola larghezza le taglierebbe le file in fondo. */
export function adattaDentro(vista) {
  const { tela, scorri, larghezza, altezza } = vista;
  const scala = Math.min(
    scorri.clientWidth / larghezza,
    scorri.clientHeight / altezza
  );
  if (!Number.isFinite(scala) || scala <= 0) return;
  tela.setAttribute("width", larghezza * scala);
  tela.setAttribute("height", altezza * scala);
}

/** I comandi dello zoom. Restituisce il nodo da appoggiare sopra la mappa. */
export function comandiZoom(vista, { adattaSubito = true } = {}) {
  const { tela, scorri, larghezza, altezza } = vista;
  let scala = 1;

  const applica = (nuova, centro) => {
    const primaX = scorri.scrollLeft + scorri.clientWidth / 2;
    const primaY = scorri.scrollTop + scorri.clientHeight / 2;
    const rapporto = nuova / scala;
    scala = nuova;
    tela.setAttribute("width", larghezza * scala);
    tela.setAttribute("height", altezza * scala);
    if (centro) {
      scorri.scrollLeft = centro.x * scala - scorri.clientWidth / 2;
      scorri.scrollTop = centro.y * scala - scorri.clientHeight / 2;
    } else {
      scorri.scrollLeft = primaX * rapporto - scorri.clientWidth / 2;
      scorri.scrollTop = primaY * rapporto - scorri.clientHeight / 2;
    }
  };

  const adatta = () => applica(scorri.clientWidth / larghezza);

  if (adattaSubito) {
    // Dopo il primo disegno: prima di allora `clientWidth` è ancora zero.
    requestAnimationFrame(adatta);
  }

  const comandi = el("div", { classe: "mappa-comandi" }, [
    el("button", {
      type: "button", "aria-label": "Ingrandisci", testo: "+",
      onclick: () => applica(Math.min(scala * 1.5, 6)),
    }),
    el("button", {
      type: "button", "aria-label": "Rimpicciolisci", testo: "−",
      onclick: () => applica(Math.max(scala / 1.5, 0.2)),
    }),
    el("button", {
      type: "button", "aria-label": "Vedi tutta la mappa", html: "⤢", onclick: adatta,
    }),
  ]);

  return { comandi, vaiA: (p) => applica(Math.max(scala, 2), p), adatta };
}
