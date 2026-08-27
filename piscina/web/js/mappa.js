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
function grana(id, file, misura) {
  return svg("pattern", { id, width: misura, height: misura, patternUnits: "userSpaceOnUse" }, [
    svg("image", { href: `/immagini/${file}`, width: misura, height: misura }),
  ]);
}

function definizioni() {
  return svg("defs", {}, [
    grana("erba", "texture-erba.webp", 150),
    grana("acqua", "texture-acqua.webp", 190),
    grana("pietra", "texture-pavimento.webp", 95),

    // Il bordo della vasca è più scuro: dà la profondità dell'acqua.
    svg("radialGradient", { id: "fondale", cx: "0.5", cy: "0.5", r: "0.72" }, [
      svg("stop", { offset: "0.55", "stop-color": "#000", "stop-opacity": "0" }),
      svg("stop", { offset: "1", "stop-color": "#02405c", "stop-opacity": "0.45" }),
    ]),
    // Il sole in alto a sinistra, come nelle foto dall'alto di mezzogiorno.
    svg("filter", { id: "ombra", x: "-40%", y: "-40%", width: "200%", height: "200%" }, [
      svg("feDropShadow", {
        dx: "2.5", dy: "4", stdDeviation: "2.5",
        "flood-color": "#2a2010", "flood-opacity": "0.32",
      }),
    ]),
    svg("filter", { id: "ombra-grande", x: "-30%", y: "-30%", width: "180%", height: "180%" }, [
      svg("feDropShadow", {
        dx: "4", dy: "7", stdDeviation: "6",
        "flood-color": "#2a2010", "flood-opacity": "0.28",
      }),
    ]),
  ]);
}

// --- Scenografia -----------------------------------------------------------
function vasca(e) {
  const scaletta = [];
  // Una scaletta sul lato lungo: due corrimano e i gradini.
  const sx = e.x + e.w * 0.5 - 16;
  const sy = e.y + e.h;
  for (const dx of [0, 26]) {
    scaletta.push(svg("path", {
      classe: "sc-metallo",
      d: `M${sx + dx} ${sy - 26} q0 -14 6 -18`,
    }));
  }
  for (let i = 0; i < 3; i++) {
    scaletta.push(svg("line", {
      classe: "sc-metallo", x1: sx, y1: sy - 22 + i * 7, x2: sx + 26, y2: sy - 22 + i * 7,
    }));
  }

  return svg("g", { filter: "url(#ombra-grande)" }, [
    // Il bordo in pietra chiara attorno alla vasca.
    svg("rect", {
      classe: "sc-bordo-vasca",
      x: e.x - 9, y: e.y - 9, width: e.w + 18, height: e.h + 18, rx: 24,
    }),
    svg("rect", { classe: "sc-acqua", x: e.x, y: e.y, width: e.w, height: e.h, rx: 16 }),
    svg("rect", {
      fill: "url(#fondale)", x: e.x, y: e.y, width: e.w, height: e.h, rx: 16,
    }),
    ...scaletta,
    svg("text", {
      classe: "sc-testo", x: e.x + e.w / 2, y: e.y + e.h / 2 + 6, testo: e.etichetta,
    }),
  ]);
}

function palma(e) {
  const cx = e.x + e.w / 2;
  const cy = e.y + e.h / 2;
  const r = e.w / 2;

  // Ogni fronda è un'ellisse allungata che parte dal centro. Con le punte a
  // triangolo veniva fuori una stella marina; così si legge palma anche
  // quando è grande dieci pixel.
  const fronda = (gradi, lunghezza, classe) =>
    svg("g", { transform: `translate(${cx} ${cy}) rotate(${gradi})` }, [
      svg("ellipse", {
        classe,
        cx: lunghezza / 2,
        cy: 0,
        rx: lunghezza / 2,
        ry: lunghezza * 0.19,
      }),
    ]);

  const fronde = [];
  for (let i = 0; i < 6; i++) {
    const gradi = (i / 6) * 360;
    fronde.push(fronda(gradi, r, "sc-palma"));
    fronde.push(fronda(gradi + 30, r * 0.7, "sc-palma chiara"));
  }

  return svg("g", { filter: "url(#ombra)" }, [
    ...fronde,
    svg("circle", { classe: "sc-palma-cuore", cx, cy, r: r * 0.16 }),
  ]);
}

function edificioLegno(e, dettagli = []) {
  const assi = [];
  for (let y = e.y + 12; y < e.y + e.h - 6; y += 12) {
    assi.push(svg("line", { classe: "sc-asse", x1: e.x + 5, y1: y, x2: e.x + e.w - 5, y2: y }));
  }
  return svg("g", { filter: "url(#ombra)" }, [
    svg("rect", { classe: "sc-legno", x: e.x, y: e.y, width: e.w, height: e.h, rx: 10 }),
    ...assi,
    ...dettagli,
    svg("text", {
      classe: "sc-testo minuta scura",
      x: e.x + e.w / 2, y: e.y + e.h / 2 + 4, testo: e.etichetta,
    }),
  ]);
}

function scenografia(elementi) {
  const pezzi = [];
  for (const e of elementi) {
    if (e.tipo === "recinto") {
      pezzi.push(svg("g", { filter: "url(#ombra-grande)" }, [
        svg("rect", { classe: "sc-pavimento", x: e.x, y: e.y, width: e.w, height: e.h, rx: 26 }),
        svg("rect", {
          classe: "sc-cordolo", x: e.x + 4, y: e.y + 4, width: e.w - 8, height: e.h - 8, rx: 22,
        }),
      ]));
    } else if (e.tipo === "vasca") {
      pezzi.push(vasca(e));
    } else if (e.tipo === "palma") {
      pezzi.push(palma(e));
    } else if (e.tipo === "volley") {
      pezzi.push(svg("g", { filter: "url(#ombra)" }, [
        svg("rect", { classe: "sc-sabbia", x: e.x, y: e.y, width: e.w, height: e.h, rx: 8 }),
        svg("rect", {
          classe: "sc-riga-campo",
          x: e.x + 10, y: e.y + 8, width: e.w - 20, height: e.h - 16, rx: 4,
        }),
        svg("line", {
          classe: "sc-rete", x1: e.x + e.w / 2, y1: e.y + 6, x2: e.x + e.w / 2, y2: e.y + e.h - 6,
        }),
        svg("text", {
          classe: "sc-testo minuta scura", x: e.x + e.w / 2, y: e.y + e.h / 2 + 4, testo: e.etichetta,
        }),
      ]));
    } else if (e.tipo === "solarium") {
      pezzi.push(svg("g", {}, [
        svg("rect", { classe: "sc-solarium", x: e.x, y: e.y, width: e.w, height: e.h, rx: 14 }),
        svg("text", {
          classe: "sc-testo minuta scura", x: e.x + e.w / 2, y: e.y + 19, testo: e.etichetta,
        }),
      ]));
    } else if (e.tipo === "bagnino") {
      // La sedia alta con il suo ombrellino rosso, come in piscina.
      const cx = e.x + e.w / 2;
      pezzi.push(svg("g", { filter: "url(#ombra)" }, [
        // Il seggiolone con il suo parasole rosso, come si vede dall'alto.
        svg("rect", {
          classe: "sc-sedia",
          x: cx - 9, y: e.y + 18, width: 18, height: e.h - 20, rx: 5,
        }),
        svg("rect", {
          classe: "sc-seggiolino",
          x: cx - 5, y: e.y + 24, width: 10, height: e.h - 34, rx: 3,
        }),
        svg("ellipse", { classe: "sc-ombrellino", cx, cy: e.y + 14, rx: 19, ry: 15 }),
        svg("circle", { classe: "sc-ombrellino-cuore", cx, cy: e.y + 14, r: 2.6 }),
        svg("text", {
          classe: "sc-testo minuta scura", x: cx, y: e.y - 8, testo: e.etichetta,
        }),
      ]));
    } else if (e.tipo === "doccia") {
      pezzi.push(edificioLegno(e, [
        svg("circle", { classe: "sc-metallo-pieno", cx: e.x + e.w / 2, cy: e.y + 20, r: 6 }),
        svg("line", {
          classe: "sc-metallo",
          x1: e.x + e.w / 2, y1: e.y + 26, x2: e.x + e.w / 2, y2: e.y + 40,
        }),
      ]));
    } else if (e.tipo === "cassa") {
      pezzi.push(edificioLegno(e, [
        svg("rect", {
          classe: "sc-porta",
          x: e.x + e.w - 16, y: e.y + e.h / 2 - 24, width: 16, height: 48, rx: 4,
        }),
      ]));
    }
  }
  return svg("g", { classe: "scenografia" }, pezzi);
}

// --- Le postazioni ---------------------------------------------------------
/** Un lettino visto dall'alto: telaio, materassino, cuscino. */
function lettino(x, y, largo, alto) {
  return svg("g", {}, [
    svg("rect", {
      classe: "tinta lettino", x, y, width: largo, height: alto, rx: largo * 0.42,
    }),
    svg("rect", {
      classe: "cuscino",
      x: x + largo * 0.18, y: y + alto * 0.08,
      width: largo * 0.64, height: alto * 0.22, rx: largo * 0.2,
    }),
  ]);
}

/** Un ombrellone visto dall'alto: il telo a spicchi color panna.

    Sta un po' più in alto del centro, e i lettini gli stanno sotto: messo
    esattamente sopra li coprirebbe, e da lontano la postazione sembrerebbe
    un bottone e basta. */
const OMBRELLONE_Y = -8;
const RAGGIO_TELO = 11;

function ombrellone() {
  const spicchi = [];
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    spicchi.push(svg("line", {
      classe: "spicchio",
      x1: 0, y1: OMBRELLONE_Y,
      x2: Math.cos(a) * RAGGIO_TELO, y2: OMBRELLONE_Y + Math.sin(a) * RAGGIO_TELO,
    }));
  }
  return svg("g", {}, [
    svg("circle", { classe: "telo", cx: 0, cy: OMBRELLONE_Y, r: RAGGIO_TELO }),
    ...spicchi,
    svg("circle", { classe: "puntale", cx: 0, cy: OMBRELLONE_Y, r: 2.4 }),
  ]);
}

function disegnaPostazione(p, { fascia, scelte, rotazioni, lettiniDisegnati }) {
  const stato = statoDi(p);
  const scelta = scelte.has(p.codice);
  const utile = scegliibile(p, fascia);
  const rotazione = rotazioni[p.fila] || 0;

  const pezzi = [];
  if (p.tipo === "lettino") {
    pezzi.push(lettino(-8, -13, 16, 26));
  } else {
    // I due lettini affiancati, e l'ombrellone che li ripara da sopra.
    const posti = Math.min(lettiniDisegnati, 2);
    for (let i = 0; i < posti; i++) {
      pezzi.push(lettino(i === 0 ? -10.5 : 1.5, -2, 9, 23));
    }
    pezzi.push(ombrellone());
  }

  const corpo = svg("g", {
    classe: "corpo",
    transform: `rotate(${rotazione})`,
    filter: "url(#ombra)",
  }, pezzi);

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
      // L'alone: da lontano è l'unica cosa che si vede, ed è quella che dice
      // se il posto è libero.
      svg("circle", { classe: "alone tinta", cx: 0, cy: p.tipo === "lettino" ? 0 : 3, r: 18 }),
      corpo,
      svg("circle", { classe: "anello", cx: 0, cy: p.tipo === "lettino" ? 0 : 3, r: 19 }),
      rotazione || p.tipo === "lettino"
        ? svg("text", { classe: "etichetta a-lato", x: 21, y: 4, testo: p.codice })
        : svg("text", { classe: "etichetta", x: 0, y: 32, testo: p.codice }),
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
