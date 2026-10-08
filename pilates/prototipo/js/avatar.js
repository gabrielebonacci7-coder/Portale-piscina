// Greta ed Elisa: gli avatar che accolgono le clienti e spiegano l'app.
//
// I ritratti vengono da un'unica illustrazione delle due insieme
// (pilates/risorse/avatar-originale.png): il viso di ciascuna è ritagliato
// da lì, e l'immagine intera apre e chiude la guida di benvenuto.

import { el } from "./ui.js";

const RITRATTI = {
  greta: "immagini/greta.webp",
  elisa: "immagini/elisa.webp",
};
export const INSIEME = "immagini/insieme.webp";

const NOMI = { greta: "Greta", elisa: "Elisa" };

/** L'avatar di Greta o di Elisa, nella misura che serve. */
export function avatar(chi, classe = "") {
  return el("span", { classe: `avatar avatar-${chi} ${classe}` }, [
    el("img", { src: RITRATTI[chi], alt: "", decoding: "async" }),
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
  const chiParla = el("div", { classe: "chi-parla" });
  const parlato = el("div", { classe: "parlato" }, [chiParla, fumetto]);
  const punti = el("div", { classe: "punti" });
  const avanti = el("button", { classe: "bottone", type: "button" });

  const scena = el("div", { classe: "benvenuto", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "benvenuto-fondo", "aria-hidden": "true" }, [el("i"), el("i"), el("i")]),
    el("div", { classe: "benvenuto-testa" }, [
      el("img", { src: "immagini/marchio.png", alt: "", classe: "benvenuto-marchio" }),
      el("div", { classe: "benvenuto-nome", testo: "Pilates G&E" }),
    ]),
    palco,
    parlato,
    punti,
    el("div", { classe: "comandi" }, [
      el("button", { classe: "salta", type: "button", testo: "Salta", onclick: chiudi }),
      avanti,
    ]),
  ]);

  /** All'inizio e alla fine: le due insieme. */
  const insieme = () => el("figure", { classe: "insieme" }, [
    el("img", { src: INSIEME, alt: "Greta ed Elisa", decoding: "async" }),
    el("figcaption", {}, [el("span", { testo: "Greta" }), el("span", { testo: "Elisa" })]),
  ]);

  /** In mezzo: una alla volta, ognuna entra dal suo lato. */
  const sola = (chi) => el("div", { classe: `sola da-${chi}` }, [
    avatar(chi, "ritratto"),
    el("div", { classe: "persona-nome", testo: NOMI[chi] }),
  ]);

  function disegna() {
    const passo = passi[indice];
    const testo = (passo.testo || "").replaceAll("{nome}", nome || "").replace(/\s+!/, "!").replace(/ ,/, ",");
    const mostra = passo.vetrina && vetrina ? vetrina(passo.vetrina) : null;
    const entrambe = passo.chi === "entrambe";

    palco.replaceChildren(
      mostra ? el("div", { classe: "vetrina" }, [mostra]) : entrambe ? insieme() : sola(passo.chi)
    );
    palco.classList.toggle("con-vetrina", Boolean(mostra));

    // Chi parla sta dalla sua parte del fumetto: Greta a sinistra, Elisa a
    // destra, come nell'illustrazione. Così l'alternarsi si vede.
    parlato.className = `parlato da-${entrambe ? "entrambe" : passo.chi}`;
    chiParla.replaceChildren(
      ...(entrambe ? ["greta", "elisa"] : [passo.chi]).map((chi) => avatar(chi, "parla")),
      el("span", { testo: entrambe ? "Greta ed Elisa" : NOMI[passo.chi] })
    );
    fumetto.textContent = testo;
    for (const nodo of [fumetto, chiParla]) {
      nodo.classList.remove("entra");
      void nodo.offsetWidth;
      nodo.classList.add("entra");
    }

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
