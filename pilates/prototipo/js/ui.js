// Piccoli attrezzi per costruire l'interfaccia senza librerie.

/** el("div", { classe: "x", onclick }, [figli]) → un nodo del DOM. */
export function el(tag, attributi = {}, figli = []) {
  const nodo = document.createElement(tag);
  for (const [chiave, valore] of Object.entries(attributi || {})) {
    if (valore === null || valore === undefined || valore === false) continue;
    if (chiave === "classe") nodo.className = valore;
    else if (chiave === "testo") nodo.textContent = valore;
    else if (chiave === "html") nodo.innerHTML = valore;
    else if (chiave.startsWith("on")) nodo.addEventListener(chiave.slice(2), valore);
    else if (chiave === "stile") nodo.style.cssText = valore;
    else nodo.setAttribute(chiave, valore === true ? "" : valore);
  }
  for (const figlio of [].concat(figli)) {
    if (figlio === null || figlio === undefined || figlio === false) continue;
    nodo.append(figlio instanceof Node ? figlio : document.createTextNode(String(figlio)));
  }
  return nodo;
}

const SVG_NS = "http://www.w3.org/2000/svg";

/** Come el(), per gli elementi SVG. */
export function svg(tag, attributi = {}, figli = []) {
  const nodo = document.createElementNS(SVG_NS, tag);
  for (const [chiave, valore] of Object.entries(attributi || {})) {
    if (valore === null || valore === undefined) continue;
    nodo.setAttribute(chiave === "classe" ? "class" : chiave, valore);
  }
  for (const figlio of [].concat(figli)) if (figlio) nodo.append(figlio);
  return nodo;
}

/** Le icone: tratti semplici, tutti 24×24 e dello stesso spessore. */
const TRATTI = {
  calendario: "M4 7h16M8 3v4M16 3v4M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z",
  lista: "M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01",
  pacchetto: "M4 8.5 12 4l8 4.5v7L12 20l-8-4.5Zm0 0 8 4.5m0 0 8-4.5M12 13v7",
  persona: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0",
  persone: "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm-6 9a6 6 0 0 1 12 0M16 4.5a3.5 3.5 0 0 1 0 6.5M18 14.5a6 6 0 0 1 3 5.5",
  campana: "M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15ZM10 20.5a2 2 0 0 0 4 0",
  megafono: "M4 10v4h3l7 4V6L7 10Zm14-1.5a4 4 0 0 1 0 7",
  grafico: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  oggi: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
  chat: "M4 19.5 5.3 16A8 8 0 1 1 8 18.7Z",
  freccia: "m9 6 6 6-6 6",
  indietro: "m15 6-6 6 6 6",
  chiudi: "M6 6l12 12M18 6 6 18",
  spunta: "m5 12.5 4.5 4.5L19 7",
  orologio: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
  lucchetto: "M7 11V8a5 5 0 0 1 10 0v3M6 11h12v9H6Z",
  piu: "M12 5v14M5 12h14",
  matita: "M5 19h4L19 9l-4-4L5 15Zm9-13 4 4",
  esci: "M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10",
  condividi: "M12 15V4m0 0L8 8m4-4 4 4M6 12v7h12v-7",
  stella: "M12 4.5 14.3 9l5 .7-3.6 3.5.9 5-4.6-2.4-4.6 2.4.9-5L4.7 9.7l5-.7Z",
};

export function icona(nome, classe = "icona") {
  return svg("svg", { classe, viewBox: "0 0 24 24", "aria-hidden": "true" }, [
    svg("path", { d: TRATTI[nome] || "" }),
  ]);
}

/** Un messaggio breve in basso, che sparisce da solo. */
export function avviso(testo, tipo = "") {
  document.querySelector(".toast")?.remove();
  const nodo = el("div", { classe: `toast ${tipo}`, role: "status" }, [
    tipo === "ok" ? icona("spunta", "icona piccola") : null,
    el("span", { testo }),
  ]);
  document.body.append(nodo);
  requestAnimationFrame(() => nodo.classList.add("dentro"));
  setTimeout(() => {
    nodo.classList.remove("dentro");
    setTimeout(() => nodo.remove(), 300);
  }, 2600);
}

/** Un foglio che sale dal basso. Ritorna { chiudi }. */
export function foglio(contenuto, { titolo, sottotitolo } = {}) {
  const velo = el("div", { classe: "velo" });
  const pannello = el("div", { classe: "foglio", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "maniglia" }),
    titolo
      ? el("div", { classe: "foglio-testa" }, [
          el("div", {}, [
            el("h2", { testo: titolo }),
            sottotitolo ? el("div", { classe: "sotto", testo: sottotitolo }) : null,
          ]),
          el("button", { classe: "tondo", type: "button", "aria-label": "Chiudi", onclick: () => chiudi() }, [
            icona("chiudi"),
          ]),
        ])
      : null,
    contenuto,
  ]);
  velo.addEventListener("click", () => chiudi());
  document.body.append(velo, pannello);
  requestAnimationFrame(() => {
    velo.classList.add("dentro");
    pannello.classList.add("dentro");
  });
  function chiudi() {
    velo.classList.remove("dentro");
    pannello.classList.remove("dentro");
    setTimeout(() => {
      velo.remove();
      pannello.remove();
    }, 280);
  }
  return { chiudi, pannello };
}

/** I tre pallini dei reformer: pieni = occupati. */
export function pallini(occupati, totale, classe = "") {
  const lista = [];
  for (let i = 0; i < totale; i++) lista.push(el("i", { classe: i < occupati ? "preso" : "" }));
  return el("span", { classe: `pallini ${classe}`, "aria-label": `${totale - occupati} posti liberi su ${totale}` }, lista);
}
