// Chat interna: elenco conversazioni e finestra di conversazione.

import { api } from "../api.js";
import { aggiornaNonLetti, stato } from "../stato.js";
import {
  ICONE,
  avviso,
  brindisi,
  caricamento,
  el,
  ora,
  pannello,
  quandoRelativo,
  vuoto,
} from "../ui.js";

export function vistaMessaggi(navigazione) {
  const contenitore = el("div");
  const elenco = el("div", { classe: "elenco" });
  contenitore.append(elenco);

  async function carica() {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.conversazioni();
      if (!pagina.elementi.length) {
        elenco.replaceChildren(
          vuoto(
            "Nessun messaggio",
            "Scrivi a una struttura da un annuncio, o a un collega dal suo profilo.",
          ),
        );
        return;
      }
      elenco.replaceChildren(
        ...pagina.elementi.map((c) =>
          rigaConversazione(c, () => apriConversazione(c.id, c.interlocutore, carica, navigazione)),
        ),
      );
      await aggiornaNonLetti();
      navigazione?.aggiornaPallini?.();
    } catch (e) {
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  contenitore.ricarica = carica;
  return contenitore;
}

function rigaConversazione(c, alClic) {
  const nonLetti = c.non_letti > 0;
  return el("button", { classe: "scheda", type: "button", onclick: alClic }, [
    el("div", { classe: "scheda-testa" }, [
      el("h3", {
        style: "flex:1",
        testo: c.interlocutore?.nome_visualizzato ?? "Conversazione",
      }),
      el("span", { classe: "dato sommesso", testo: quandoRelativo(c.ultimo_messaggio_il) }),
    ]),
    el("div", { style: "display:flex;align-items:center;gap:8px" }, [
      el("p", {
        style: `flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;${
          nonLetti ? "font-weight:600" : "color:var(--muted)"
        }`,
        testo: c.ultimo_messaggio ?? "Nessun messaggio",
      }),
      nonLetti &&
        el("span", {
          classe: "chip rosso dato",
          testo: String(c.non_letti),
        }),
    ]),
  ]);
}

/** Finestra di conversazione: messaggi + composizione. */
export async function apriConversazione(conversazioneId, interlocutore, alCambio, navigazione) {
  const nome = interlocutore?.nome_visualizzato ?? "Conversazione";
  const chat = el("div", { classe: "chat" }, caricamento());
  const contenuto = el("div");

  const testo = el("textarea", {
    placeholder: "Scrivi un messaggio…",
    rows: 1,
    maxlength: 4000,
    onkeydown: (e) => {
      // Invio manda, Maiusc+Invio va a capo: come in qualsiasi chat.
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        invia();
      }
    },
  });

  const bottoneInvia = el("button", {
    classe: "btn",
    type: "button",
    "aria-label": "Invia",
    html: ICONE.invia,
    onclick: () => invia(),
  });

  const composizione = el("div", { classe: "composizione" }, [testo, bottoneInvia]);
  contenuto.append(chat, composizione);

  const azioneBlocca = interlocutore
    ? el("button", {
        classe: "btn-icona",
        "aria-label": "Blocca utente",
        title: "Blocca utente",
        html: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/></svg>',
        onclick: () => confermaBlocco(interlocutore, chiudi, alCambio),
      })
    : null;

  const { chiudi } = pannello(nome, contenuto, { azione: azioneBlocca });

  async function carica() {
    try {
      const pagina = await api.messaggi(conversazioneId);
      if (!pagina.elementi.length) {
        chat.replaceChildren(vuoto("Nessun messaggio", "Scrivi tu per primo."));
      } else {
        chat.replaceChildren(...pagina.elementi.map(bolla));
      }
      // Sempre in fondo, sull'ultimo messaggio.
      chat.lastElementChild?.scrollIntoView({ block: "end" });
      await aggiornaNonLetti();
      navigazione?.aggiornaPallini?.();
    } catch (e) {
      chat.replaceChildren(avviso(e.dettaglio));
    }
  }

  async function invia() {
    const contenutoTesto = testo.value.trim();
    if (!contenutoTesto) return;
    bottoneInvia.disabled = true;
    try {
      const m = await api.rispondi(conversazioneId, contenutoTesto);
      testo.value = "";
      if (chat.querySelector(".vuoto")) chat.replaceChildren();
      chat.append(bolla(m));
      chat.lastElementChild.scrollIntoView({ block: "end" });
      alCambio?.();
    } catch (e) {
      alert(e.dettaglio);
    } finally {
      bottoneInvia.disabled = false;
    }
  }

  carica();
}

function bolla(m) {
  const mia = m.mittente_id === stato.utente.id;
  return el("div", { classe: `bolla ${mia ? "mia" : "altrui"}` }, [
    el("span", { testo: m.testo }),
    el("span", { classe: "ora", testo: ora(m.creato_il) }),
  ]);
}

/** Apre (o crea) la conversazione con un utente e ci scrive dentro. */
export async function apriChatCon(utenteId, nome, navigazione, extra = {}) {
  const testo = el("textarea", {
    placeholder: `Scrivi a ${nome ?? "questo utente"}…`,
    maxlength: 4000,
    required: true,
  });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    el("div", { classe: "campo" }, [testo]),
    el("button", { type: "submit", classe: "btn largo", testo: "Invia" }),
  ]);

  const { chiudi } = pannello(nome ? `Scrivi a ${nome}` : "Nuovo messaggio", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    const invio = form.querySelector("button[type=submit]");
    invio.disabled = true;
    try {
      const m = await api.scriviNuova({
        destinatario_id: utenteId,
        testo: testo.value.trim(),
        ...extra,
      });
      brindisi("Messaggio inviato");
      chiudi();
      await aggiornaNonLetti();
      navigazione?.vai?.("messaggi");
      return m;
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
      invio.disabled = false;
    }
  });
}

function confermaBlocco(interlocutore, chiudiChat, alCambio) {
  const motivo = el("input", { type: "text", maxlength: 255, placeholder: "Facoltativo" });

  const form = el("form", {}, [
    el("p", {
      testo: `Bloccando ${interlocutore.nome_visualizzato} nessuno dei due potrà più scrivere all'altro. Puoi sbloccare quando vuoi dal tuo profilo.`,
    }),
    el("div", { classe: "campo", style: "margin-top:16px" }, [
      el("label", { testo: "Motivo" }),
      motivo,
    ]),
    el("div", { classe: "azioni" }, [
      el("button", {
        type: "button",
        classe: "btn secondario",
        testo: "Annulla",
        onclick: () => chiudi(),
      }),
      el("button", { type: "submit", classe: "btn pericolo", testo: "Blocca" }),
    ]),
  ]);

  const { chiudi } = pannello("Bloccare questo utente?", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api.blocca(interlocutore.id, motivo.value.trim() || null);
      brindisi("Utente bloccato");
      chiudi();
      chiudiChat();
      alCambio?.();
    } catch (err) {
      alert(err.dettaglio);
    }
  });
}
