// L'omino che accoglie chi entra e ringrazia chi ha prenotato.
//
// Il disegno è un'immagine con lo sfondo trasparente, ricavata dall'originale
// da `python -m piscina.scripts.ritaglia_omino`. Il discorso invece arriva da
// /api/info, cioè dal file piscina/dominio/struttura.py: per cambiarlo non si
// tocca né questo file né il disegno.
//
// Non è un monologo: è una guida. Ogni paragrafo può portarsi dietro una
// "vetrina", e mentre l'omino racconta una sezione l'app la fa vedere.

import { el, svg } from "./ui.js";
import { vetrina } from "./vetrine.js";

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

/** Il fondale della schermata di benvenuto.
 *
 * Cielo, sole, nuvole, due rondini, le fronde delle palme che incorniciano
 * dall'alto e in fondo l'acqua della vasca — la stessa grana che si vede
 * nella mappa, così le due schermate sembrano lo stesso posto.
 *
 * Sta dietro a tutto e non intercetta i tocchi: è scenografia, non interfaccia.
 */
function fondale() {
  const fronda = (x, y, gradi, lungo, classe) =>
    svg("g", { transform: `translate(${x} ${y}) rotate(${gradi})` }, [
      svg("ellipse", {
        classe: `fondale-fronda ${classe}`,
        cx: lungo / 2, cy: 0, rx: lungo / 2, ry: lungo * 0.13,
      }),
    ]);

  /** Una palma appoggiata a un angolo, con il tronco che scende fuori campo. */
  const palma = (x, y, daDestra, misura) => {
    const verso = daDestra ? -1 : 1;
    const fronde = [];
    for (let i = 0; i < 7; i++) {
      const gradi = (daDestra ? 180 : 0) + verso * (-14 + i * 32);
      const lungo = misura * (i % 2 ? 0.78 : 1);
      fronde.push(fronda(x, y, gradi, lungo, i % 2 ? "chiara" : ""));
    }
    return svg("g", {}, [
      svg("path", {
        classe: "fondale-tronco",
        d: `M${x} ${y} q${verso * 26} 90 ${verso * 14} 220`,
      }),
      ...fronde,
      svg("circle", { classe: "fondale-cuore", cx: x, cy: y, r: misura * 0.09 }),
    ]);
  };

  const nuvola = (x, y, scala, opacita) =>
    svg("g", { transform: `translate(${x} ${y}) scale(${scala})`, opacity: opacita }, [
      svg("path", {
        classe: "fondale-nuvola",
        d: "M0 0 a18 18 0 0 1 34 -6 a22 22 0 0 1 40 6 z",
      }),
    ]);

  const rondine = (x, y, scala) =>
    svg("path", {
      classe: "fondale-rondine",
      transform: `translate(${x} ${y}) scale(${scala})`,
      d: "M0 0 q7 -8 13 0 q6 -8 13 0",
    });

  return svg("svg", {
    classe: "fondale",
    viewBox: "0 0 400 800",
    preserveAspectRatio: "xMidYMid slice",
    "aria-hidden": "true",
  }, [
    svg("defs", {}, [
      svg("linearGradient", { id: "cielo", x1: "0", y1: "0", x2: "0.2", y2: "1" }, [
        svg("stop", { offset: "0", "stop-color": "#38a8d4" }),
        svg("stop", { offset: "0.5", "stop-color": "#0f6b98" }),
        svg("stop", { offset: "1", "stop-color": "#07405e" }),
      ]),
      svg("radialGradient", { id: "sole", cx: "0.5", cy: "0.5", r: "0.5" }, [
        svg("stop", { offset: "0", "stop-color": "#fff3cf", "stop-opacity": "0.6" }),
        svg("stop", { offset: "1", "stop-color": "#fff3cf", "stop-opacity": "0" }),
      ]),
      svg("linearGradient", { id: "fondoScuro", x1: "0", y1: "0", x2: "0", y2: "1" }, [
        svg("stop", { offset: "0", "stop-color": "#04293d", "stop-opacity": "0" }),
        svg("stop", { offset: "1", "stop-color": "#04293d", "stop-opacity": "0.75" }),
      ]),
    ]),

    svg("rect", { x: 0, y: 0, width: 400, height: 800, fill: "url(#cielo)" }),
    svg("circle", { cx: 330, cy: 84, r: 200, fill: "url(#sole)" }),

    nuvola(24, 128, 1.15, 0.15),
    nuvola(252, 74, 0.85, 0.12),
    nuvola(140, 205, 1.4, 0.08),
    rondine(92, 92, 1.15),
    rondine(124, 74, 0.85),

    // Le palme incorniciano dall'alto, come si guardasse da sotto una di loro.
    palma(-10, 36, false, 150),
    palma(410, 88, true, 132),

    // Niente linea dell'acqua: l'omino è vestito, e una vasca che gli taglia
    // il torace lo farebbe sembrare immerso in tuta. In fondo solo un'ombra,
    // che lo appoggia a terra invece di lasciarlo sospeso.
    svg("rect", { classe: "fondale-fondo", x: -10, y: 520, width: 420, height: 300 }),
  ]);
}

/** "Buongiorno {nome}!" → "Buongiorno Marco!", oppure "Buongiorno!" */
function conNome(testo, nome) {
  return nome
    ? testo.replaceAll("{nome}", nome)
    : testo.replace(/\s*\{nome\}/g, "");
}

/**
 * La guida: l'omino parla un paragrafo alla volta e, quando racconta una
 * sezione, la mostra davvero (`vetrina`).
 *
 * `discorso` è { passi, invito }; `ctx` serve alle vetrine, che pescano dati
 * veri (la mappa di oggi, il listino in corso).
 */
export function mostraOmino(discorso, { occhiello, titolo, nome, ctx, alTermine } = {}) {
  const passi = discorso.passi || [];
  let indice = 0;

  const fumetto = el("div", { classe: "fumetto" });
  const corpo = el("div", { classe: "scena" });
  const punti = el("div", { classe: "punti" });
  const avanti = el("button", { classe: "bottone avanti", type: "button" });

  const immagine = (classe) =>
    el("img", {
      classe: `omino ${classe}`,
      src: IMMAGINE_OMINO,
      alt: "",
      width: "600",
      height: "2015",
      decoding: "async",
    });

  const scena = el("div", { classe: "benvenuto", role: "dialog", "aria-modal": "true" }, [
    fondale(),
    el("div", { classe: "insegna" }, [
      occhiello ? el("div", { classe: "occhiello", testo: occhiello }) : null,
      titolo ? el("h1", { testo: titolo }) : null,
    ]),
    corpo,
    punti,
    el("div", { classe: "comandi" }, [
      el("button", { classe: "salta", type: "button", testo: "Salta", onclick: chiudi }),
      avanti,
    ]),
  ]);

  function disegna() {
    const passo = passi[indice] || {};
    const parla = nome && passo.testo_con_nome ? passo.testo_con_nome : passo.testo;
    fumetto.textContent = conNome(parla || "", nome);

    const mostra = passo.vetrina && ctx ? vetrina(passo.vetrina, ctx) : null;
    corpo.classList.toggle("compatta", Boolean(mostra));
    corpo.replaceChildren(
      ...(mostra
        // Con la vetrina l'omino si fa da parte: comanda quello che mostra.
        ? [mostra, el("div", { classe: "guida" }, [immagine("mini"), fumetto])]
        : [immagine("intero"), el("div", { classe: "parlato" }, [fumetto])])
    );

    avanti.textContent =
      indice === passi.length - 1 ? discorso.invito || "Iniziamo" : "Avanti";
    punti.replaceChildren(
      ...passi.map((_, i) => el("i", { classe: i === indice ? "attivo" : "" }))
    );
  }

  function chiudi() {
    scena.remove();
    document.body.style.overflow = "";
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
  document.body.style.overflow = "hidden";
  document.body.append(scena);
  avanti.focus();
  return { chiudi };
}

