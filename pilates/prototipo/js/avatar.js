// Greta ed Elisa: gli avatar che accolgono le clienti e spiegano l'app.
//
// I ritratti vengono da un'unica illustrazione delle due insieme
// (pilates/risorse/avatar-originale.png): il viso di ciascuna è ritagliato
// da lì. Compaiono solo dove serve sapere chi insegna: le lezioni, il giorno
// scelto, l'orario, i contatti. La guida di benvenuto non li usa.

import { el } from "./ui.js";

const RITRATTI = {
  greta: "immagini/greta.webp",
  elisa: "immagini/elisa.webp",
};

/** L'avatar di Greta o di Elisa, nella misura che serve. */
export function avatar(chi, classe = "") {
  return el("span", { classe: `avatar avatar-${chi} ${classe}` }, [
    el("img", { src: RITRATTI[chi], alt: "", decoding: "async" }),
  ]);
}

/**
 * La guida di benvenuto: un fumetto alla volta e, quando si parla di una
 * sezione dell'app, la sezione stessa in anteprima. All'inizio e alla fine
 * c'è il marchio dello studio.
 *
 * `passi` è [{ testo, vetrina? }]; `vetrina(nome)` costruisce l'anteprima.
 */
export function mostraGuida(passi, { nome, vetrina, invito = "Iniziamo", alTermine } = {}) {
  let indice = 0;
  const palco = el("div", { classe: "guida-palco" });
  const fumetto = el("div", { classe: "fumetto" });
  const punti = el("div", { classe: "punti" });
  const avanti = el("button", { classe: "bottone", type: "button" });

  const scena = el("div", { classe: "benvenuto", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "benvenuto-fondo", "aria-hidden": "true" }, [el("i"), el("i"), el("i")]),
    el("div", { classe: "benvenuto-testa" }, [el("div", { classe: "benvenuto-nome", testo: "RE FORMER" })]),
    palco,
    el("div", { classe: "parlato" }, [fumetto]),
    punti,
    el("div", { classe: "comandi" }, [
      el("button", { classe: "salta", type: "button", testo: "Salta", onclick: chiudi }),
      avanti,
    ]),
  ]);

  const marchio = () => el("div", { classe: "guida-marchio" }, [
    el("img", { src: "immagini/marchio.png", alt: "" }),
  ]);

  function disegna() {
    const passo = passi[indice];
    const testo = (passo.testo || "").replaceAll("{nome}", nome || "").replace(/\s+!/, "!").replace(/ ,/, ",");
    const mostra = passo.vetrina && vetrina ? vetrina(passo.vetrina) : null;
    palco.replaceChildren(mostra ? el("div", { classe: "vetrina" }, [mostra]) : marchio());
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
