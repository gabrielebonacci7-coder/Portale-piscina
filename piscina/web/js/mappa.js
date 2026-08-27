// La vista dall'alto del solarium.
//
// Disegna quello che arriva da /api/mappa: prima la scenografia (vasche,
// cassa, docce, campo da beach volley), poi le postazioni. Nessuna coordinata
// è scritta qui dentro: se la piscina cambia disposizione si tocca il file
// piscina/dominio/piantina.py e la mappa segue.
//
// Il tocco non usa il bersaglio dell'SVG ma il centro più vicino: su un
// telefono un ombrellone è largo pochi pixel, e chiedere di centrarlo
// sarebbe come chiedere di infilare un ago. Si tocca "lì attorno" e prende
// quello giusto.

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

export function perche(p, fascia) {
  const stato = statoDi(p);
  if (stato === "spenta") return p.nota || "Non disponibile";
  if (scegliibile(p, fascia)) return "Libera";
  if (stato === "occupata") return "Occupata tutto il giorno";
  return p.libera_mattina ? "Libera solo la mattina" : "Libera solo il pomeriggio";
}

// --- Disegno ---------------------------------------------------------------
function definizioni() {
  return svg("defs", {}, [
    svg("linearGradient", { id: "acqua", x1: "0", y1: "0", x2: "0.35", y2: "1" }, [
      svg("stop", { offset: "0", "stop-color": "#3fb3e0" }),
      svg("stop", { offset: "1", "stop-color": "#0d76a8" }),
    ]),
  ]);
}

function vasca(e) {
  const pezzi = [
    svg("rect", {
      classe: "sc-vasca",
      x: e.x, y: e.y, width: e.w, height: e.h, rx: 16,
    }),
  ];
  // Due onde: bastano a far leggere "acqua" invece di "rettangolo azzurro".
  const passo = e.h / 3;
  for (let i = 1; i < 3; i++) {
    const y = e.y + passo * i;
    pezzi.push(
      svg("path", {
        classe: "sc-onda",
        d: `M${e.x + 22} ${y} q ${(e.w - 44) / 4} -9 ${(e.w - 44) / 2} 0 t ${(e.w - 44) / 2} 0`,
      })
    );
  }
  pezzi.push(
    svg("text", { classe: "sc-testo chiaro", x: e.x + e.w / 2, y: e.y + e.h / 2 + 6, testo: e.etichetta })
  );
  return svg("g", {}, pezzi);
}

function edificio(e, dettaglio) {
  return svg("g", {}, [
    svg("rect", { classe: "sc-edificio", x: e.x, y: e.y, width: e.w, height: e.h, rx: 10 }),
    dettaglio,
    svg("text", {
      classe: "sc-testo minuta",
      x: e.x + e.w / 2,
      y: e.y + e.h / 2 + 4,
      testo: e.etichetta,
    }),
  ]);
}

function scenografia(elementi) {
  const pezzi = [];
  for (const e of elementi) {
    if (e.tipo === "recinto") {
      pezzi.push(svg("rect", { classe: "sc-recinto", x: e.x, y: e.y, width: e.w, height: e.h, rx: 24 }));
    } else if (e.tipo === "vasca") {
      pezzi.push(vasca(e));
    } else if (e.tipo === "volley") {
      pezzi.push(
        svg("g", {}, [
          svg("rect", { classe: "sc-sabbia", x: e.x, y: e.y, width: e.w, height: e.h, rx: 8 }),
          svg("line", {
            classe: "sc-rete",
            x1: e.x + e.w / 2, y1: e.y + 8, x2: e.x + e.w / 2, y2: e.y + e.h - 8,
          }),
          svg("text", {
            classe: "sc-testo minuta",
            x: e.x + e.w / 2, y: e.y + e.h / 2 + 4, testo: e.etichetta,
          }),
        ])
      );
    } else if (e.tipo === "solarium") {
      pezzi.push(
        svg("g", {}, [
          svg("rect", { classe: "sc-solarium", x: e.x, y: e.y, width: e.w, height: e.h, rx: 12 }),
          svg("text", {
            classe: "sc-testo minuta", x: e.x + e.w / 2, y: e.y + 20, testo: e.etichetta,
          }),
        ])
      );
    } else if (e.tipo === "bagnino") {
      // La sedia alta: due gambe e il seggiolino.
      pezzi.push(
        svg("g", {}, [
          svg("path", {
            classe: "sc-dettaglio",
            d: `M${e.x + 8} ${e.y + e.h} L${e.x + 16} ${e.y + 14} L${e.x + e.w - 16} ${e.y + 14}
                L${e.x + e.w - 8} ${e.y + e.h} Z`,
          }),
          svg("rect", {
            classe: "sc-dettaglio", x: e.x + 10, y: e.y, width: e.w - 20, height: 16, rx: 4,
          }),
          svg("text", {
            classe: "sc-testo minuta", x: e.x + e.w / 2, y: e.y - 8, testo: e.etichetta,
          }),
        ])
      );
    } else if (e.tipo === "doccia") {
      pezzi.push(
        edificio(
          e,
          svg("g", {}, [
            svg("circle", { classe: "sc-dettaglio", cx: e.x + e.w / 2, cy: e.y + 22, r: 7 }),
            svg("line", {
              classe: "sc-rete", x1: e.x + e.w / 2, y1: e.y + 30, x2: e.x + e.w / 2, y2: e.y + 44,
            }),
          ])
        )
      );
    } else if (e.tipo === "cassa") {
      pezzi.push(
        edificio(
          e,
          svg("rect", {
            classe: "sc-dettaglio",
            x: e.x + e.w - 14, y: e.y + e.h / 2 - 22, width: 14, height: 44, rx: 4,
          })
        )
      );
    }
  }
  return svg("g", { classe: "scenografia" }, pezzi);
}

/** Un ombrellone visto dall'alto: i lettini sotto, il telo a spicchi sopra. */
function disegnoOmbrellone(lettiniDisegnati) {
  const pezzi = [];
  const offset = [-11, 11];
  for (let i = 0; i < Math.min(lettiniDisegnati, 2); i++) {
    pezzi.push(
      svg("rect", {
        classe: "lettino",
        x: offset[i] - 4.5, y: -12, width: 9, height: 24, rx: 4,
      })
    );
  }
  // Il telo: un cerchio con quattro spicchi chiari, come le fette di un
  // ombrellone a righe visto da sopra.
  pezzi.push(svg("circle", { classe: "tinta telo", cx: 0, cy: 0, r: 11.5 }));
  for (const angolo of [0, 90, 180, 270]) {
    pezzi.push(
      svg("path", {
        classe: "spicchio",
        d: "M0 0 L11.5 0 A11.5 11.5 0 0 1 8.13 8.13 Z",
        transform: `rotate(${angolo + 22.5})`,
      })
    );
  }
  pezzi.push(svg("circle", { classe: "palo", cx: 0, cy: 0, r: 2.2 }));
  return pezzi;
}

/** Un lettino singolo del solarium. */
function disegnoLettino() {
  return [
    svg("rect", { classe: "tinta", x: -8, y: -13, width: 16, height: 26, rx: 5 }),
    svg("rect", { classe: "spicchio", x: -5.5, y: -10, width: 11, height: 7, rx: 3 }),
  ];
}

function disegnaPostazione(p, { fascia, scelte, rotazioni, lettiniDisegnati }) {
  const stato = statoDi(p);
  const scelta = scelte.has(p.codice);
  const utile = scegliibile(p, fascia);
  const rotazione = rotazioni[p.fila] || 0;

  const corpo = svg(
    "g",
    { classe: "corpo", transform: `rotate(${rotazione})` },
    p.tipo === "lettino" ? disegnoLettino() : disegnoOmbrellone(lettiniDisegnati)
  );

  return svg(
    "g",
    {
      classe: `posto stato-${stato}${scelta ? " scelta" : ""}${utile ? "" : " non-scegliibile"}`,
      transform: `translate(${p.x} ${p.y})`,
      "data-codice": p.codice,
      role: "img",
      "aria-label": `${p.codice}: ${perche(p, fascia)}`,
    },
    [
      corpo,
      svg("circle", { classe: "anello", cx: 0, cy: 0, r: 17 }),
      // L'etichetta sta sotto solo dove c'è posto: nella fila girata e fra i
      // lettini del solarium finirebbe addosso alla postazione dopo.
      rotazione || p.tipo === "lettino"
        ? svg("text", { classe: "etichetta a-lato", x: 20, y: 4, testo: p.codice })
        : svg("text", { classe: "etichetta", x: 0, y: 27, testo: p.codice }),
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
    svg("rect", { classe: "sc-fondo", x: 0, y: 0, width: larghezza, height: altezza }),
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

  // Il tocco: si converte il punto in coordinate della mappa e si cerca il
  // centro più vicino. Così anche un dito impreciso prende la postazione
  // giusta, e le zone vuote non rispondono.
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
