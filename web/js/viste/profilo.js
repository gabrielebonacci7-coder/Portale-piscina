// Il proprio profilo: dati, brevetti, esperienze, disponibilità, recensioni
// ricevute, utenti bloccati e uscita.

import { api } from "../api.js";
import { caricaProfilo, eBagnino, esci, stato } from "../stato.js";
import {
  GIORNI_LUNGHI,
  avviso,
  brindisi,
  caricamento,
  chip,
  el,
  etichetta,
  oraBreve,
  pannello,
  stelle,
} from "../ui.js";

export function vistaProfilo(navigazione) {
  const contenitore = el("div", {}, caricamento());

  async function carica() {
    await caricaProfilo();
    const p = stato.profilo;
    contenitore.replaceChildren();

    if (!p) {
      contenitore.append(avviso("Profilo non ancora creato", "info"));
      return;
    }

    contenitore.append(eBagnino() ? testaBagnino(p, carica) : testaPiscina(p, carica));

    if (eBagnino()) {
      contenitore.append(
        sezioneBrevetti(p, carica),
        sezioneEsperienze(p, carica),
        sezioneDisponibilita(p, carica),
      );
    }

    contenitore.append(sezioneRecensioni(), sezioneBlocchi(), sezioneAccount(navigazione));
  }

  carica();
  contenitore.ricarica = carica;
  return contenitore;
}

// ---------- Testa del profilo ----------
function testaBagnino(p, ricarica) {
  return el("div", { classe: "blocco" }, [
    el("h2", { testo: `${p.nome} ${p.cognome}` }),
    el("div", { classe: "riga-meta", style: "margin-top:6px" }, [
      p.eta && el("span", { testo: `${p.eta} anni` }),
      el("span", { testo: `· ${p.citta}` }),
      el("span", { testo: `· ${p.anni_esperienza} anni di esperienza` }),
    ]),
    el("div", { classe: "chips" }, [
      p.abilitato ? chip("Abilitato", "verde") : chip("Nessun brevetto valido", "rosso"),
      p.cerca_lavoro ? chip("Visibile in bacheca", "acqua") : chip("Nascosto", "ambra"),
      p.disponibile_chiamata_singola && chip("Anche turni singoli"),
    ]),
    p.bio && el("p", { style: "margin-top:12px", testo: p.bio }),
    el("div", { classe: "azioni" }, [
      el("button", {
        classe: "btn secondario piccolo",
        testo: "Modifica",
        onclick: () => modificaBagnino(p, ricarica),
      }),
    ]),
  ]);
}

function testaPiscina(p, ricarica) {
  return el("div", { classe: "blocco" }, [
    el("h2", { testo: p.nome_struttura }),
    el("div", { classe: "riga-meta", style: "margin-top:6px" }, [
      el("span", { testo: etichetta("tipo_struttura", p.tipo_struttura) }),
      p.zona && el("span", { testo: `· ${p.zona.nome}` }),
    ]),
    p.indirizzo && el("p", { classe: "sommesso", style: "margin-top:6px", testo: p.indirizzo }),
    p.referente_nome &&
      el("p", { classe: "sommesso", testo: `Referente: ${p.referente_nome}` }),
    el("div", { classe: "azioni" }, [
      el("button", {
        classe: "btn secondario piccolo",
        testo: "Modifica",
        onclick: () => modificaPiscina(p, ricarica),
      }),
    ]),
  ]);
}

// ---------- Brevetti ----------
function sezioneBrevetti(p, ricarica) {
  const blocco = el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Brevetti" }),
  ]);

  if (!p.brevetti.length) {
    blocco.append(
      el("p", {
        classe: "sommesso",
        testo: "Senza un brevetto valido non puoi candidarti ai turni che lo richiedono.",
      }),
    );
  } else {
    p.brevetti.forEach((b) =>
      blocco.append(
        el("div", { classe: "voce" }, [
          el("div", { classe: "voce-corpo" }, [
            el("strong", { testo: etichetta("brevetto", b.tipo) }),
            el("div", { classe: "sommesso dato" }, [
              b.data_scadenza
                ? `scade il ${b.data_scadenza.split("-").reverse().join("/")}`
                : "senza scadenza",
            ]),
          ]),
          b.valido ? chip("Valido", "verde") : chip("Scaduto", "rosso"),
          bottoneElimina(() => api.eliminaBrevetto(b.id), ricarica),
        ]),
      ),
    );
  }

  blocco.append(
    el("button", {
      classe: "btn fantasma piccolo",
      style: "margin-top:12px",
      testo: "+ Aggiungi brevetto",
      onclick: () => aggiungiBrevetto(ricarica),
    }),
  );
  return blocco;
}

function aggiungiBrevetto(ricarica) {
  const tipo = el(
    "select",
    {},
    Object.entries({
      P: "P — piscina",
      IP: "IP — acque interne e piscina",
      MIP: "MIP — mare, acque interne e piscina",
      altro: "Altro ente",
    }).map(([v, t]) => el("option", { value: v, testo: t })),
  );
  const scadenza = el("input", { type: "date" });
  const numero = el("input", { type: "text", maxlength: 64 });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    campo("Tipo", tipo),
    campo("Scadenza", scadenza, "Senza scadenza il brevetto risulta da verificare."),
    campo("Numero (facoltativo)", numero),
    el("button", { type: "submit", classe: "btn largo", testo: "Aggiungi" }),
  ]);

  const { chiudi } = pannello("Nuovo brevetto", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api.aggiungiBrevetto({
        tipo: tipo.value,
        data_scadenza: scadenza.value || null,
        numero: numero.value.trim() || null,
      });
      brindisi("Brevetto aggiunto");
      chiudi();
      ricarica();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
    }
  });
}

// ---------- Esperienze ----------
function sezioneEsperienze(p, ricarica) {
  const blocco = el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Esperienza" }),
  ]);

  if (!p.esperienze.length) {
    blocco.append(el("p", { classe: "sommesso", testo: "Nessuna esperienza inserita." }));
  } else {
    p.esperienze.forEach((e) =>
      blocco.append(
        el("div", { classe: "voce" }, [
          el("div", { classe: "voce-corpo" }, [
            el("strong", { testo: e.struttura }),
            el("div", { classe: "sommesso" }, [
              [e.mansione, e.stagioni && `${e.stagioni} stagioni`].filter(Boolean).join(" · "),
            ]),
          ]),
          bottoneElimina(() => api.eliminaEsperienza(e.id), ricarica),
        ]),
      ),
    );
  }

  blocco.append(
    el("button", {
      classe: "btn fantasma piccolo",
      style: "margin-top:12px",
      testo: "+ Aggiungi esperienza",
      onclick: () => aggiungiEsperienza(ricarica),
    }),
  );
  return blocco;
}

function aggiungiEsperienza(ricarica) {
  const struttura = el("input", { type: "text", required: true, maxlength: 150 });
  const mansione = el("input", { type: "text", maxlength: 120 });
  const inizio = el("input", { type: "date" });
  const fine = el("input", { type: "date" });
  const stagioni = el("input", { type: "number", min: 0, max: 60 });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    campo("Struttura", struttura),
    campo("Mansione", mansione),
    el("div", { classe: "riga-campi" }, [campo("Dal", inizio), campo("Al", fine)]),
    campo("Stagioni", stagioni),
    el("button", { type: "submit", classe: "btn largo", testo: "Aggiungi" }),
  ]);

  const { chiudi } = pannello("Nuova esperienza", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api.aggiungiEsperienza({
        struttura: struttura.value.trim(),
        mansione: mansione.value.trim() || null,
        data_inizio: inizio.value || null,
        data_fine: fine.value || null,
        stagioni: stagioni.value === "" ? null : Number(stagioni.value),
      });
      brindisi("Esperienza aggiunta");
      chiudi();
      ricarica();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
    }
  });
}

// ---------- Disponibilità ----------
function sezioneDisponibilita(p, ricarica) {
  const blocco = el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Disponibilità settimanale" }),
  ]);

  if (!p.disponibilita.length) {
    blocco.append(el("p", { classe: "sommesso", testo: "Nessuna fascia indicata." }));
  } else {
    [...p.disponibilita]
      .sort((a, b) => a.giorno_settimana - b.giorno_settimana)
      .forEach((d) =>
        blocco.append(
          el("div", { classe: "voce" }, [
            el("span", { classe: "voce-corpo", testo: GIORNI_LUNGHI[d.giorno_settimana] }),
            el("span", {
              classe: "dato",
              testo: `${oraBreve(d.ora_inizio)}–${oraBreve(d.ora_fine)}`,
            }),
            bottoneElimina(() => api.eliminaDisponibilita(d.id), ricarica),
          ]),
        ),
      );
  }

  blocco.append(
    el("button", {
      classe: "btn fantasma piccolo",
      style: "margin-top:12px",
      testo: "+ Aggiungi fascia",
      onclick: () => aggiungiDisponibilita(ricarica),
    }),
  );
  return blocco;
}

function aggiungiDisponibilita(ricarica) {
  const giorno = el(
    "select",
    {},
    GIORNI_LUNGHI.map((g, i) => el("option", { value: i, testo: g })),
  );
  const inizio = el("input", { type: "time", value: "14:00", required: true });
  const fine = el("input", { type: "time", value: "20:00", required: true });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    campo("Giorno", giorno),
    el("div", { classe: "riga-campi" }, [campo("Dalle", inizio), campo("Alle", fine)]),
    el("button", { type: "submit", classe: "btn largo", testo: "Aggiungi" }),
  ]);

  const { chiudi } = pannello("Nuova disponibilità", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    try {
      await api.aggiungiDisponibilita({
        giorno_settimana: Number(giorno.value),
        ora_inizio: inizio.value,
        ora_fine: fine.value,
      });
      brindisi("Disponibilità aggiunta");
      chiudi();
      ricarica();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
    }
  });
}

// ---------- Recensioni ricevute ----------
function sezioneRecensioni() {
  const blocco = el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Recensioni ricevute" }),
    caricamento(),
  ]);

  api
    .recensioni(stato.utente.id)
    .then((r) => {
      blocco.replaceChildren(el("span", { classe: "etichetta", testo: "Recensioni ricevute" }));
      if (!r.totale) {
        blocco.append(el("p", { classe: "sommesso", testo: "Ancora nessuna recensione." }));
        return;
      }
      blocco.append(
        el("div", { style: "display:flex;align-items:center;gap:10px;margin-bottom:8px" }, [
          stelle(r.media_stelle),
          el("span", { classe: "dato", testo: r.media_stelle.toFixed(1) }),
          el("span", { classe: "sommesso", testo: `su ${r.totale}` }),
        ]),
        ...r.recensioni.map((rec) =>
          el("div", { classe: "voce" }, [
            el("div", { classe: "voce-corpo" }, [
              el("div", { style: "display:flex;gap:8px;align-items:center" }, [
                stelle(rec.stelle),
                el("strong", { style: "font-size:14px", testo: rec.autore_nome ?? "" }),
              ]),
              rec.commento && el("p", { style: "margin-top:4px", testo: rec.commento }),
            ]),
          ]),
        ),
      );
    })
    .catch(() => blocco.replaceChildren());

  return blocco;
}

// ---------- Utenti bloccati ----------
function sezioneBlocchi() {
  const blocco = el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Utenti bloccati" }),
  ]);

  async function carica() {
    const elenco = await api.blocchi();
    blocco.replaceChildren(el("span", { classe: "etichetta", testo: "Utenti bloccati" }));
    if (!elenco.length) {
      blocco.append(el("p", { classe: "sommesso", testo: "Nessuno." }));
      return;
    }
    elenco.forEach((b) =>
      blocco.append(
        el("div", { classe: "voce" }, [
          el("div", { classe: "voce-corpo" }, [
            el("strong", { testo: `Utente #${b.bloccato_id}` }),
            b.motivo && el("div", { classe: "sommesso", testo: b.motivo }),
          ]),
          el("button", {
            classe: "btn fantasma piccolo",
            testo: "Sblocca",
            onclick: async () => {
              await api.sblocca(b.bloccato_id);
              brindisi("Utente sbloccato");
              carica();
            },
          }),
        ]),
      ),
    );
  }

  carica().catch(() => {});
  return blocco;
}

// ---------- Account ----------
function sezioneAccount(navigazione) {
  return el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Account" }),
    el("p", { classe: "sommesso", testo: stato.utente.email }),
    el("div", { classe: "azioni" }, [
      el("button", {
        classe: "btn secondario",
        testo: "Cambia password",
        onclick: () => cambioPassword(),
      }),
      el("button", {
        classe: "btn pericolo",
        testo: "Esci",
        onclick: () => {
          esci();
          navigazione.allAccesso();
        },
      }),
    ]),
  ]);
}

function cambioPassword() {
  const attuale = el("input", { type: "password", required: true, autocomplete: "current-password" });
  const nuova = el("input", {
    type: "password",
    required: true,
    minlength: 8,
    autocomplete: "new-password",
  });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    campo("Password attuale", attuale),
    campo("Nuova password", nuova, "Almeno 8 caratteri."),
    el("button", { type: "submit", classe: "btn largo", testo: "Cambia" }),
  ]);

  const { chiudi } = pannello("Cambia password", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    try {
      await api.cambioPassword({
        password_attuale: attuale.value,
        password_nuova: nuova.value,
      });
      brindisi("Password aggiornata");
      chiudi();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
    }
  });
}

// ---------- Modifica profilo ----------
function modificaBagnino(p, ricarica) {
  const bio = el("textarea", { maxlength: 2000, value: p.bio ?? "" });
  const esperienza = el("input", { type: "number", min: 0, max: 60, value: p.anni_esperienza });
  const chiamata = el("input", { type: "checkbox", checked: p.disponibile_chiamata_singola });
  const cerca = el("input", { type: "checkbox", checked: p.cerca_lavoro });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    campo("Presentazione", bio),
    campo("Anni di esperienza", esperienza),
    el("label", { classe: "interruttore" }, [
      el("span", { testo: "Disponibile per turni singoli" }),
      chiamata,
    ]),
    el("label", { classe: "interruttore" }, [
      el("span", {}, [
        el("span", { testo: "Visibile in bacheca" }),
        el("span", {
          classe: "aiuto",
          style: "display:block",
          testo: "Se lo spegni, le strutture non ti trovano più nelle ricerche",
        }),
      ]),
      cerca,
    ]),
    el("button", { type: "submit", classe: "btn largo", style: "margin-top:16px", testo: "Salva" }),
  ]);

  const { chiudi } = pannello("Modifica profilo", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    try {
      await api.aggiornaProfiloBagnino({
        bio: bio.value.trim() || null,
        anni_esperienza: Number(esperienza.value),
        disponibile_chiamata_singola: chiamata.checked,
        cerca_lavoro: cerca.checked,
      });
      brindisi("Profilo aggiornato");
      chiudi();
      ricarica();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
    }
  });
}

function modificaPiscina(p, ricarica) {
  const descrizione = el("textarea", { maxlength: 2000, value: p.descrizione ?? "" });
  const referente = el("input", { type: "text", value: p.referente_nome ?? "" });
  const telefono = el("input", { type: "tel", value: p.referente_telefono ?? "" });
  const indirizzo = el("input", { type: "text", value: p.indirizzo ?? "" });
  const errore = el("div");

  const form = el("form", {}, [
    errore,
    campo("Descrizione", descrizione),
    campo("Indirizzo", indirizzo),
    campo("Referente", referente),
    campo("Telefono del referente", telefono),
    el("button", { type: "submit", classe: "btn largo", testo: "Salva" }),
  ]);

  const { chiudi } = pannello("Modifica struttura", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    try {
      await api.aggiornaProfiloPiscina({
        descrizione: descrizione.value.trim() || null,
        indirizzo: indirizzo.value.trim() || null,
        referente_nome: referente.value.trim() || null,
        referente_telefono: telefono.value.trim() || null,
      });
      brindisi("Profilo aggiornato");
      chiudi();
      ricarica();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
    }
  });
}

// ---------- Utilità ----------
function bottoneElimina(azione, ricarica) {
  return el("button", {
    classe: "btn-icona",
    "aria-label": "Elimina",
    html: '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13"/></svg>',
    onclick: async () => {
      if (!confirm("Eliminare questa voce?")) return;
      await azione();
      ricarica();
    },
  });
}

function campo(etichettaTesto, controllo, aiuto) {
  return el("div", { classe: "campo" }, [
    el("label", { testo: etichettaTesto }),
    controllo,
    aiuto && el("span", { classe: "aiuto", testo: aiuto }),
  ]);
}
