// Modulo di pubblicazione di un annuncio.

import { api } from "../api.js";
import { caricaZone, eBagnino } from "../stato.js";
import { avviso, brindisi, el, opzioniZone, pannello } from "../ui.js";

/** Da datetime-local (ora locale) a ISO con fuso: il backend vuole un istante preciso. */
function aIso(valore) {
  return valore ? new Date(valore).toISOString() : null;
}

/** Valore per datetime-local: fra due ore, arrotondato all'ora. */
function fraDueOre() {
  const d = new Date(Date.now() + 2 * 3600_000);
  d.setMinutes(0, 0, 0);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export async function apriPubblica(alFatto) {
  const zone = await caricaZone();
  const errore = el("div");
  const bagnino = eBagnino();

  const titolo = el("input", {
    type: "text",
    required: true,
    maxlength: 150,
    placeholder: bagnino ? "es. Cerco sostituto per sabato" : "es. Turno pomeridiano vasca grande",
  });
  const inizio = el("input", { type: "datetime-local", required: true, value: fraDueOre() });
  const fine = el("input", { type: "datetime-local" });
  const zona = el("select", {}, [
    el("option", { value: "", testo: "—" }),
    ...opzioniZone(zone),
  ]);
  const indirizzo = el("input", { type: "text", maxlength: 200 });
  const compenso = el("input", { type: "number", min: 0, step: "0.5", placeholder: "es. 13" });
  const compensoTipo = el(
    "select",
    {},
    Object.entries({
      orario: "all'ora",
      giornaliero: "al giorno",
      a_turno: "a turno",
      mensile: "al mese",
      da_concordare: "da concordare",
    }).map(([v, t]) => el("option", { value: v, testo: t })),
  );
  const tipoTurno = el(
    "select",
    {},
    Object.entries({
      turno_fisso: "Turno fisso",
      sostituzione_urgente: "Sostituzione urgente",
      evento_serale: "Evento serale",
      stagionale: "Stagionale",
      weekend: "Weekend",
      altro: "Altro",
    }).map(([v, t]) => el("option", { value: v, testo: t })),
  );
  const brevetto = el(
    "select",
    {},
    [el("option", { value: "", testo: "Nessun requisito" })].concat(
      Object.entries({
        P: "P — piscina",
        IP: "IP — acque interne",
        MIP: "MIP — mare",
      }).map(([v, t]) => el("option", { value: v, testo: t })),
    ),
  );
  const urgente = el("input", { type: "checkbox" });
  const note = el("textarea", {
    maxlength: 2000,
    placeholder: "Dettagli utili: dimensioni della vasca, tipo di utenza, come arrivare…",
  });

  const form = el("form", {}, [
    errore,
    campo("Titolo", titolo),
    campo("Inizio", inizio),
    campo("Fine (facoltativa)", fine),
    el("div", { classe: "riga-campi" }, [campo("Zona", zona), campo("Tipo di turno", tipoTurno)]),
    campo("Indirizzo", indirizzo),
    el("div", { classe: "riga-campi" }, [
      campo("Compenso (€)", compenso),
      campo("Modalità", compensoTipo),
    ]),
    !bagnino && campo("Brevetto richiesto", brevetto, "Chi ha un brevetto superiore può candidarsi lo stesso."),
    el("label", { classe: "interruttore" }, [
      el("span", {}, [
        el("span", { testo: "Segna come urgente" }),
        el("span", { classe: "aiuto", style: "display:block", testo: "Comparirà in cima alla bacheca" }),
      ]),
      urgente,
    ]),
    campo("Note", note),
    el("button", { type: "submit", classe: "btn largo", style: "margin-top:8px", testo: "Pubblica" }),
  ]);

  const { chiudi } = pannello(bagnino ? "Cerca una sostituzione" : "Pubblica un turno", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    const invio = form.querySelector("button[type=submit]");
    invio.disabled = true;
    try {
      await api.pubblica({
        titolo: titolo.value.trim(),
        tipo: bagnino ? "bagnino_cerca_sostituzione" : "piscina_cerca_bagnino",
        data_inizio: aIso(inizio.value),
        data_fine: aIso(fine.value),
        zona_id: Number(zona.value) || null,
        indirizzo: indirizzo.value.trim() || null,
        compenso: compenso.value === "" ? null : compenso.value,
        compenso_tipo: compensoTipo.value,
        tipo_turno: tipoTurno.value,
        brevetto_richiesto: bagnino ? null : brevetto.value || null,
        urgente: urgente.checked,
        note: note.value.trim() || null,
      });
      brindisi("Annuncio pubblicato");
      chiudi();
      alFatto?.();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
      invio.disabled = false;
    }
  });
}

function campo(etichettaTesto, controllo, aiuto) {
  return el("div", { classe: "campo" }, [
    el("label", { testo: etichettaTesto }),
    controllo,
    aiuto && el("span", { classe: "aiuto", testo: aiuto }),
  ]);
}
