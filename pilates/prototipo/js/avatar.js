// Greta ed Elisa: gli avatar che accolgono le clienti e spiegano l'app.
//
// Finché non arrivano i ritratti veri, al loro posto c'è una sagoma
// disegnata. Quando ci sono le immagini basta scrivere il percorso in
// RITRATTI: tutto il resto (benvenuto, video, contatti) le usa da solo.

import { el, svg } from "./ui.js";

const RITRATTI = {
  greta: null, // es. "immagini/greta.webp"
  elisa: null,
};

/** La sagoma segnaposto: busto, capelli raccolti diversi per ciascuna. */
function sagoma(chi) {
  const greta = chi === "greta";
  const pelle = "#E9C9AE";
  const capelli = greta ? "#5A3B2A" : "#2F2420";
  const maglia = greta ? "#1F4D3A" : "#9C7A54";
  return svg("svg", { classe: "sagoma", viewBox: "0 0 120 140", "aria-hidden": "true" }, [
    // capelli dietro
    greta
      ? svg("path", { d: "M34 58c0-22 12-36 26-36s26 14 26 36c0 14-4 26-8 32H42c-4-6-8-18-8-32Z", fill: capelli })
      : svg("circle", { cx: 60, cy: 18, r: 13, fill: capelli }),
    // collo e busto
    svg("path", { d: "M50 82h20v14H50z", fill: pelle }),
    svg("path", { d: "M18 140c0-26 18-44 42-44s42 18 42 44Z", fill: maglia }),
    svg("path", { d: "M48 96c3 7 7 10 12 10s9-3 12-10", fill: "none", stroke: pelle, "stroke-width": 5, "stroke-linecap": "round" }),
    // viso
    svg("ellipse", { cx: 60, cy: 58, rx: 21, ry: 25, fill: pelle }),
    // capelli davanti
    greta
      ? svg("path", { d: "M38 54c2-16 11-24 22-24 12 0 20 8 22 22-9-1-18-6-23-13-4 8-12 13-21 15Z", fill: capelli })
      : svg("path", { d: "M38 56c0-17 10-27 22-27s22 10 22 27c-6-8-14-12-22-12s-16 4-22 12Z", fill: capelli }),
    // occhi e sorriso, appena accennati
    svg("circle", { cx: 52, cy: 61, r: 1.9, fill: "#3A2A22" }),
    svg("circle", { cx: 68, cy: 61, r: 1.9, fill: "#3A2A22" }),
    svg("path", { d: "M53 71c4 4 10 4 14 0", fill: "none", stroke: "#B5715A", "stroke-width": 2, "stroke-linecap": "round" }),
  ]);
}

/** L'avatar di Greta o di Elisa, nella misura che serve. */
export function avatar(chi, classe = "") {
  const ritratto = RITRATTI[chi];
  return el("span", { classe: `avatar avatar-${chi} ${classe}` }, [
    ritratto ? el("img", { src: ritratto, alt: "", decoding: "async" }) : sagoma(chi),
  ]);
}

/**
 * La guida di benvenuto: Greta ed Elisa si danno il cambio, un fumetto alla
 * volta, e quando parlano di una sezione dell'app la fanno vedere.
 *
 * `passi` è [{ chi: "greta"|"elisa"|"entrambe", testo, vetrina? }].
 * `vetrina(nome)` costruisce l'anteprima da mostrare.
 */
export function mostraGuida(passi, { nome, vetrina, invito = "Iniziamo", alTermine } = {}) {
  let indice = 0;
  const palco = el("div", { classe: "guida-palco" });
  const fumetto = el("div", { classe: "fumetto" });
  const firma = el("div", { classe: "fumetto-firma" });
  const punti = el("div", { classe: "punti" });
  const avanti = el("button", { classe: "bottone", type: "button" });

  const scena = el("div", { classe: "benvenuto", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "benvenuto-fondo", "aria-hidden": "true" }, [el("i"), el("i"), el("i")]),
    el("div", { classe: "benvenuto-testa" }, [
      el("img", { src: "immagini/marchio.png", alt: "", classe: "benvenuto-marchio" }),
      el("div", { classe: "benvenuto-nome", testo: "Pilates G&E" }),
    ]),
    palco,
    el("div", { classe: "parlato" }, [firma, fumetto]),
    punti,
    el("div", { classe: "comandi" }, [
      el("button", { classe: "salta", type: "button", testo: "Salta", onclick: chiudi }),
      avanti,
    ]),
  ]);

  const coppia = (chiParla) =>
    el("div", { classe: "coppia" }, ["greta", "elisa"].map((chi) =>
      el("div", { classe: `persona ${chiParla === chi || chiParla === "entrambe" ? "parla" : "ascolta"}` }, [
        avatar(chi, "grande"),
        el("div", { classe: "persona-nome", testo: chi === "greta" ? "Greta" : "Elisa" }),
      ])
    ));

  function disegna() {
    const passo = passi[indice];
    const testo = (passo.testo || "").replaceAll("{nome}", nome || "").replace(/\s+!/, "!").replace(/ ,/, ",");
    const mostra = passo.vetrina && vetrina ? vetrina(passo.vetrina) : null;

    palco.replaceChildren(
      mostra
        ? el("div", { classe: "vetrina" }, [mostra])
        : coppia(passo.chi)
    );
    palco.classList.toggle("con-vetrina", Boolean(mostra));

    firma.replaceChildren(
      ...(passo.chi === "entrambe" ? ["greta", "elisa"] : [passo.chi]).map((chi) => avatar(chi, "mini")),
      el("span", { testo: passo.chi === "entrambe" ? "Greta ed Elisa" : passo.chi === "greta" ? "Greta" : "Elisa" })
    );
    fumetto.textContent = testo;
    fumetto.classList.remove("entra");
    void fumetto.offsetWidth;
    fumetto.classList.add("entra");

    avanti.textContent = indice === passi.length - 1 ? invito : "Avanti";
    punti.replaceChildren(...passi.map((_, i) => el("i", { classe: i === indice ? "attivo" : "" })));
  }

  function chiudi() {
    scena.classList.add("esce");
    setTimeout(() => scena.remove(), 260);
    alTermine?.();
  }

  avanti.addEventListener("click", () => {
    if (indice < passi.length - 1) {
      indice += 1;
      disegna();
    } else {
      chiudi();
    }
  });

  disegna();
  document.body.append(scena);
  return { chiudi };
}
