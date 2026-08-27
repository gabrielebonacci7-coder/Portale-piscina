// L'omino che accoglie chi entra e ringrazia chi ha prenotato.
//
// Il disegno è un'immagine con lo sfondo trasparente, ricavata dall'originale
// da `python -m piscina.scripts.ritaglia_omino`. Le battute invece arrivano da
// /api/info, cioè dal file piscina/dominio/struttura.py: per cambiare il
// discorso non si tocca né questo file né il disegno.

import { el } from "./ui.js";

export const IMMAGINE_OMINO = "/immagini/omino.webp";

const CHIAVE_NOME = "piscina-nome";
const CHIAVE_VISTO = "piscina-benvenuto-visto";

/** Il nome di chi usa il telefono, imparato dall'ultima prenotazione. */
export function nomeRicordato() {
  try {
    return localStorage.getItem(CHIAVE_NOME) || "";
  } catch {
    return ""; // navigazione privata: si saluta senza nome
  }
}

export function ricordaNome(nomeCompleto) {
  const primo = (nomeCompleto || "").trim().split(/\s+/)[0] || "";
  try {
    if (primo) localStorage.setItem(CHIAVE_NOME, primo);
  } catch {
    /* pazienza */
  }
}

/** Vero se questo telefono non ha mai visto il benvenuto. */
export function daMostrare() {
  try {
    return localStorage.getItem(CHIAVE_VISTO) !== "1";
  } catch {
    return true;
  }
}

export function segnaVisto() {
  try {
    localStorage.setItem(CHIAVE_VISTO, "1");
  } catch {
    /* la prossima volta lo rivede */
  }
}

/** "Buongiorno {nome}!" → "Buongiorno Marco!", oppure "Buongiorno!" */
function conNome(testo, nome) {
  return nome
    ? testo.replaceAll("{nome}", nome)
    : testo.replace(/\s*\{nome\}/g, "");
}

/**
 * L'omino a schermo intero, con le sue battute una alla volta.
 *
 * `discorso` è { battute, invito }; `intestazione` è quello che sta scritto
 * sopra la testa (nome della piscina, o "Prenotazione confermata").
 */
export function mostraOmino(discorso, { occhiello, titolo, nome, alTermine } = {}) {
  const battute = (discorso.battute || []).map((b) => conNome(b, nome));
  let indice = 0;

  const fumetto = el("div", { classe: "fumetto" });
  const punti = el("div", { classe: "punti" });
  const avanti = el("button", { classe: "bottone avanti", type: "button" });

  const scena = el("div", { classe: "benvenuto", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "insegna" }, [
      occhiello ? el("div", { classe: "occhiello", testo: occhiello }) : null,
      titolo ? el("h1", { testo: titolo }) : null,
    ]),
    el("div", { classe: "scena" }, [
      el("img", {
        classe: "omino",
        src: IMMAGINE_OMINO,
        alt: "",
        width: "600",
        height: "2010",
        decoding: "async",
      }),
      el("div", { classe: "parlato" }, [fumetto]),
    ]),
    punti,
    el("div", { classe: "comandi" }, [
      el("button", { classe: "salta", type: "button", testo: "Salta", onclick: chiudi }),
      avanti,
    ]),
  ]);

  function disegna() {
    fumetto.textContent = battute[indice] || "";
    avanti.textContent =
      indice === battute.length - 1 ? discorso.invito || "Iniziamo" : "Avanti";
    punti.replaceChildren(
      ...battute.map((_, i) => el("i", { classe: i === indice ? "attivo" : "" }))
    );
  }

  function chiudi() {
    scena.remove();
    document.body.style.overflow = "";
    alTermine?.();
  }

  avanti.addEventListener("click", () => {
    if (indice < battute.length - 1) {
      indice += 1;
      disegna();
    } else {
      chiudi();
    }
  });

  disegna();
  document.body.style.overflow = "hidden";
  document.body.append(scena);
  avanti.focus();
  return { chiudi };
}
