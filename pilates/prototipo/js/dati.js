// Il "finto server" del prototipo.
//
// Nell'app vera queste regole staranno sul server, con un database. Qui
// stanno nel telefono (localStorage), così il prototipo si prova da solo,
// senza installare niente, e si può rimettere com'era con "Ricomincia".
//
// Le regole però sono già quelle definitive: orari, istruttrici, 3 posti,
// disdetta fino a 12 ore prima, lista d'attesa, pagamento solo in studio.

export const POSTI = 3;
export const ORE_DISDETTA = 12;

export const ISTRUTTRICI = {
  greta: { id: "greta", nome: "Greta", cognome: "Lorenzetti", telefono: "393791567202", leggibile: "379 156 7202" },
  elisa: { id: "elisa", nome: "Elisa", cognome: "Bonacci", telefono: "393936506230", leggibile: "393 650 6230" },
};

/** Giorno della settimana (0 = domenica) → orari d'inizio. Lezioni da un'ora. */
export const ORARIO = {
  1: ["16:30", "17:30", "18:30"],
  2: ["16:30", "17:30", "18:30"],
  3: ["16:30", "17:30", "18:30"],
  4: ["16:30", "17:30", "18:30"],
  5: ["16:30", "17:30", "18:30"],
  6: ["11:30", "12:30"],
};

/** Lunedì, mercoledì, venerdì e sabato Greta; martedì e giovedì Elisa. */
export function istruttriceDel(giorno) {
  return [2, 4].includes(giorno) ? ISTRUTTRICI.elisa : ISTRUTTRICI.greta;
}

/** I prezzi arrivano domani: per ora i pacchetti hanno solo il numero di ingressi. */
export const PACCHETTI = [
  { id: "prova", nome: "Lezione di prova", ingressi: 1, prezzo: null },
  { id: "singola", nome: "Lezione singola", ingressi: 1, prezzo: null },
  { id: "p5", nome: "Pacchetto 5 lezioni", ingressi: 5, prezzo: null, validita: "2 mesi" },
  { id: "p10", nome: "Pacchetto 10 lezioni", ingressi: 10, prezzo: null, validita: "3 mesi" },
];

// ------------------------------------------------------------------ orologio
// ?ora=2026-10-12T09:00 ferma l'orologio: serve al video, che deve venire
// uguale ogni volta che lo si gira.
const ORA_FISSA = new URLSearchParams(location.search).get("ora");
const AVVIO = Date.now();
export function adesso() {
  if (!ORA_FISSA) return new Date();
  return new Date(new Date(ORA_FISSA).getTime() + (Date.now() - AVVIO));
}

export const GIORNI = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
export const GIORNI_CORTI = ["dom", "lun", "mar", "mer", "gio", "ven", "sab"];
export const MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
  "agosto", "settembre", "ottobre", "novembre", "dicembre"];

const due = (n) => String(n).padStart(2, "0");
export const chiaveGiorno = (d) => `${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())}`;
export const oraDi = (d) => `${due(d.getHours())}:${due(d.getMinutes())}`;
export const dataLunga = (d) => `${GIORNI[d.getDay()]} ${d.getDate()} ${MESI[d.getMonth()]}`;

export function quandoRelativo(d) {
  const oggi = new Date(adesso()); oggi.setHours(0, 0, 0, 0);
  const giorno = new Date(d); giorno.setHours(0, 0, 0, 0);
  const diff = Math.round((giorno - oggi) / 86400000);
  if (diff === 0) return "oggi";
  if (diff === 1) return "domani";
  if (diff === -1) return "ieri";
  return dataLunga(d);
}

// ------------------------------------------------------------------ archivio
const CHIAVE = "pilates-ge-prototipo-v1";

let stato = carica();

function carica() {
  try {
    const salvato = JSON.parse(localStorage.getItem(CHIAVE) || "null");
    if (salvato && salvato.versione === 1) return salvato;
  } catch {
    /* navigazione privata o dati rovinati: si riparte dai dati d'esempio */
  }
  return datiEsempio();
}

function salva() {
  try {
    localStorage.setItem(CHIAVE, JSON.stringify(stato));
  } catch {
    /* il prototipo funziona lo stesso, solo non ricorda */
  }
}

export function ricomincia() {
  try { localStorage.removeItem(CHIAVE); } catch { /* niente */ }
  stato = datiEsempio();
  salva();
}

// --------------------------------------------------------------- le lezioni
function idLezione(giorno, ora) {
  return `${chiaveGiorno(giorno)}_${ora}`;
}

function inizioDa(id) {
  const [g, o] = id.split("_");
  return new Date(`${g}T${o}:00`);
}

/** Le lezioni da `da` per `giorni` giorni, con iscritte e lista d'attesa. */
export function lezioni(da, giorni) {
  const elenco = [];
  const d = new Date(da); d.setHours(0, 0, 0, 0);
  for (let i = 0; i < giorni; i++, d.setDate(d.getDate() + 1)) {
    for (const ora of ORARIO[d.getDay()] || []) elenco.push(lezione(idLezione(d, ora)));
  }
  return elenco;
}

export function lezione(id) {
  const inizio = inizioDa(id);
  const fine = new Date(inizio.getTime() + 3600000);
  const iscritte = stato.prenotazioni[id] || [];
  return {
    id,
    inizio,
    fine,
    istruttrice: istruttriceDel(inizio.getDay()),
    titolo: stato.titoli[id] || "Reformer",
    iscritte,
    attesa: stato.attesa[id] || [],
    liberi: POSTI - iscritte.length,
    annullata: stato.annullate[id] || null,
    passata: inizio <= adesso(),
    presenze: stato.presenze[id] || {},
  };
}

/** Vero se mancano almeno 12 ore: si può ancora disdire. */
export function disdicibile(lez) {
  return lez.inizio.getTime() - adesso().getTime() >= ORE_DISDETTA * 3600000;
}

/** I giorni con lezioni a partire da oggi (la domenica lo studio è chiuso). */
export function prossimiGiorni(quanti) {
  const giorni = [];
  const d = new Date(adesso()); d.setHours(0, 0, 0, 0);
  while (giorni.length < quanti) {
    if (ORARIO[d.getDay()]) giorni.push(new Date(d));
    d.setDate(d.getDate() + 1);
  }
  return giorni;
}

// ---------------------------------------------------------------- le clienti
export const io = () => stato.clienti[stato.io];
export const cliente = (id) => stato.clienti[id];
export const clienti = () => Object.values(stato.clienti).sort((a, b) => a.cognome.localeCompare(b.cognome));
export const nomeCompleto = (c) => `${c.nome} ${c.cognome}`;

export function registra({ nome, cognome, telefono, email }) {
  const id = `c${Date.now()}`;
  stato.clienti[id] = {
    id, nome, cognome, telefono, email,
    ingressi: 0, scadenza: null, nuova: true,
    iscrittaIl: adesso().toISOString(),
  };
  stato.io = id;
  notifica(id, "Benvenuta! Il tuo account è attivo: puoi già prenotare. Il pacchetto si paga in studio.");
  salva();
  return stato.clienti[id];
}

/** Il prototipo parte con una cliente di prova già dentro. */
export function entraComeDemo() {
  stato.io = "sofia";
  salva();
}

// --------------------------------------------------------------- prenotare
export function prenota(idLez, idCliente = stato.io) {
  const lez = lezione(idLez);
  if (lez.annullata) throw new Error("Questa lezione è stata annullata.");
  if (lez.passata) throw new Error("La lezione è già iniziata.");
  if (lez.iscritte.includes(idCliente)) throw new Error("Sei già iscritta.");
  if (lez.liberi <= 0) throw new Error("La lezione è piena.");
  stato.prenotazioni[idLez] = [...lez.iscritte, idCliente];
  stato.attesa[idLez] = lez.attesa.filter((x) => x !== idCliente);
  stato.clienti[idCliente].ingressi -= 1;
  salva();
}

export function mettiInAttesa(idLez, idCliente = stato.io) {
  const lez = lezione(idLez);
  if (lez.attesa.includes(idCliente)) return lez.attesa.indexOf(idCliente) + 1;
  stato.attesa[idLez] = [...lez.attesa, idCliente];
  salva();
  return stato.attesa[idLez].length;
}

export function esciDallAttesa(idLez, idCliente = stato.io) {
  stato.attesa[idLez] = (stato.attesa[idLez] || []).filter((x) => x !== idCliente);
  salva();
}

/**
 * Disdire: solo fino a 12 ore prima, e l'ingresso torna nel pacchetto.
 * Il posto liberato va alla prima della lista d'attesa, che viene avvisata.
 * `daStudio` è Greta o Elisa che tolgono qualcuno a mano: per loro il
 * limite delle 12 ore non vale.
 */
export function disdici(idLez, idCliente = stato.io, { daStudio = false } = {}) {
  const lez = lezione(idLez);
  if (!daStudio && !disdicibile(lez)) {
    throw new Error(`Mancano meno di ${ORE_DISDETTA} ore: la lezione non si può più disdire.`);
  }
  stato.prenotazioni[idLez] = lez.iscritte.filter((x) => x !== idCliente);
  stato.clienti[idCliente].ingressi += 1;
  const prima = (stato.attesa[idLez] || [])[0];
  if (prima) {
    stato.attesa[idLez] = stato.attesa[idLez].slice(1);
    stato.prenotazioni[idLez].push(prima);
    stato.clienti[prima].ingressi -= 1;
    notifica(prima, `Si è liberato un posto: sei dentro alla lezione di ${quandoRelativo(lez.inizio)} alle ${oraDi(lez.inizio)}!`);
  }
  salva();
  return prima || null;
}

/** Le lezioni della cliente: in programma, in lista d'attesa, già fatte. */
export function lezioniDi(idCliente = stato.io) {
  const ora = adesso();
  const tutte = [...new Set([...Object.keys(stato.prenotazioni), ...Object.keys(stato.attesa)])]
    .map(lezione)
    .sort((a, b) => a.inizio - b.inizio);
  return {
    prossime: tutte.filter((l) => l.iscritte.includes(idCliente) && l.fine > ora && !l.annullata),
    attesa: tutte.filter((l) => l.attesa.includes(idCliente) && l.fine > ora && !l.annullata),
    fatte: tutte.filter((l) => l.iscritte.includes(idCliente) && l.fine <= ora && !l.annullata).reverse(),
  };
}

// ---------------------------------------------------------------- notifiche
export function notifica(idCliente, testo) {
  (stato.notifiche[idCliente] ||= []).unshift({ testo, quando: adesso().toISOString(), letta: false });
}

export function notificheDi(idCliente = stato.io) {
  const personali = (stato.notifiche[idCliente] || []).map((n) => ({ ...n, tipo: "personale" }));
  const avvisi = stato.avvisi.map((a) => ({ ...a, tipo: "avviso", letta: (stato.letti[idCliente] || []).includes(a.id) }));
  return [...personali, ...avvisi].sort((a, b) => b.quando.localeCompare(a.quando));
}

export function nonLette(idCliente = stato.io) {
  return notificheDi(idCliente).filter((n) => !n.letta).length;
}

export function segnaLette(idCliente = stato.io) {
  (stato.notifiche[idCliente] || []).forEach((n) => (n.letta = true));
  stato.letti[idCliente] = stato.avvisi.map((a) => a.id);
  salva();
}

// --------------------------------------------------------------- gestionale
export function cambiaTitolo(idLez, titolo) {
  stato.titoli[idLez] = titolo.trim() || "Reformer";
  salva();
}

/** Annulla la lezione: le iscritte riavranno l'ingresso e vengono avvisate. */
export function annullaLezione(idLez, motivo) {
  const lez = lezione(idLez);
  for (const id of lez.iscritte) {
    stato.clienti[id].ingressi += 1;
    notifica(id, `La lezione di ${dataLunga(lez.inizio)} alle ${oraDi(lez.inizio)} è annullata${motivo ? `: ${motivo}` : ""}. L'ingresso ti è stato restituito.`);
  }
  for (const id of lez.attesa) {
    notifica(id, `La lezione di ${dataLunga(lez.inizio)} alle ${oraDi(lez.inizio)} è annullata.`);
  }
  stato.annullate[idLez] = motivo || "annullata";
  stato.prenotazioni[idLez] = [];
  stato.attesa[idLez] = [];
  salva();
}

export function ripristinaLezione(idLez) {
  delete stato.annullate[idLez];
  salva();
}

export function segnaPresenza(idLez, idCliente, presente) {
  (stato.presenze[idLez] ||= {})[idCliente] = presente;
  salva();
}

/** Greta o Elisa registrano un pacchetto pagato in studio. */
export function caricaPacchetto(idCliente, idPacchetto, metodo) {
  const pacchetto = PACCHETTI.find((p) => p.id === idPacchetto);
  const c = stato.clienti[idCliente];
  c.ingressi += pacchetto.ingressi;
  c.nuova = false;
  const mesi = pacchetto.validita ? parseInt(pacchetto.validita, 10) : 1;
  const scadenza = new Date(adesso()); scadenza.setMonth(scadenza.getMonth() + mesi);
  c.scadenza = scadenza.toISOString();
  stato.movimenti.unshift({ cliente: idCliente, pacchetto: idPacchetto, metodo, quando: adesso().toISOString() });
  notifica(idCliente, `Abbiamo caricato il tuo ${pacchetto.nome.toLowerCase()}: ora hai ${c.ingressi} lezioni disponibili.`);
  salva();
}

export const movimentiDi = (idCliente) => stato.movimenti.filter((m) => m.cliente === idCliente);
export const movimenti = () => stato.movimenti;

export function pubblicaAvviso(testo, da) {
  stato.avvisi.unshift({ id: `a${Date.now()}`, testo, da, quando: adesso().toISOString() });
  salva();
}
export const avvisi = () => stato.avvisi;

// ------------------------------------------------------------ dati d'esempio
function datiEsempio() {
  // Un generatore pseudo-casuale con seme fisso: i dati d'esempio vengono
  // uguali ogni volta, così il video è sempre lo stesso.
  let seme = 20261007;
  const caso = () => ((seme = (seme * 1103515245 + 12345) % 2147483648) / 2147483648);

  const nomi = [
    ["sofia", "Sofia", "Marini"], ["chiara", "Chiara", "Rinaldi"], ["martina", "Martina", "Ferri"],
    ["laura", "Laura", "De Santis"], ["valentina", "Valentina", "Greco"], ["francesca", "Francesca", "Lombardi"],
    ["alessia", "Alessia", "Conti"], ["giorgia", "Giorgia", "Fabbri"], ["federica", "Federica", "Moretti"],
    ["silvia", "Silvia", "Galli"], ["paola", "Paola", "Testa"], ["roberta", "Roberta", "Villa"],
    ["serena", "Serena", "Bruno"], ["elena", "Elena", "Pace"], ["marta", "Marta", "Leone"],
    ["anna", "Anna", "Caruso"],
  ];
  const s = {
    versione: 1, io: null, clienti: {}, prenotazioni: {}, attesa: {}, titoli: {},
    annullate: {}, presenze: {}, notifiche: {}, letti: {}, avvisi: [], movimenti: [],
  };
  const ora = adesso();
  for (const [id, nome, cognome] of nomi) {
    const scadenza = new Date(ora); scadenza.setDate(scadenza.getDate() + 20 + Math.floor(caso() * 60));
    s.clienti[id] = {
      id, nome, cognome,
      telefono: `3${Math.floor(caso() * 9e8 + 1e8)}`.replace(/^(\d{3})(\d{3})(\d{4})$/, "$1 $2 $3"),
      email: `${nome.toLowerCase()}.${cognome.toLowerCase().replace(/\s/g, "")}@example.com`,
      ingressi: 2 + Math.floor(caso() * 8),
      scadenza: scadenza.toISOString(),
      iscrittaIl: new Date(ora.getTime() - (10 + caso() * 200) * 86400000).toISOString(),
    };
  }
  s.clienti.paola.ingressi = 0;
  s.clienti.roberta.ingressi = 1;
  s.clienti.sofia.ingressi = 6;

  const titoliPossibili = ["Reformer · Principianti", "Reformer · Postura e schiena", "Reformer · Total body", "Reformer · Core e addome"];
  const altre = Object.keys(s.clienti).filter((id) => id !== "sofia");
  const pesca = (escluse) => {
    const libere = altre.filter((x) => !escluse.includes(x));
    return libere[Math.floor(caso() * libere.length)];
  };

  // Un mese indietro e due settimane avanti, piene più o meno come uno studio vero.
  const inizio = new Date(ora); inizio.setDate(inizio.getDate() - 30);
  const elenco = [];
  const d = new Date(inizio); d.setHours(0, 0, 0, 0);
  for (let i = 0; i < 45; i++, d.setDate(d.getDate() + 1)) {
    for (const o of ORARIO[d.getDay()] || []) elenco.push({ id: idLezione(d, o), inizio: new Date(`${chiaveGiorno(d)}T${o}:00`) });
  }
  for (const { id, inizio: quando } of elenco) {
    const futura = quando > ora;
    const giorniAvanti = (quando - ora) / 86400000;
    // Più è vicina, più è piena.
    const quante = futura
      ? Math.min(POSTI, Math.floor(caso() * 4 + (giorniAvanti < 4 ? 1.2 : 0)))
      : 2 + Math.floor(caso() * 2);
    const iscritte = [];
    for (let k = 0; k < quante; k++) iscritte.push(pesca(iscritte));
    s.prenotazioni[id] = iscritte;
    if (futura && iscritte.length === POSTI && caso() < 0.5) s.attesa[id] = [pesca(iscritte)];
    if (caso() < 0.35) s.titoli[id] = titoliPossibili[Math.floor(caso() * titoliPossibili.length)];
    if (!futura) s.presenze[id] = Object.fromEntries(iscritte.map((x) => [x, caso() > 0.08]));
  }

  // Sofia, la cliente del prototipo: due lezioni in programma, qualcuna fatta.
  const future = elenco.filter((l) => l.inizio > ora);
  const passate = elenco.filter((l) => l.inizio <= ora);
  const metti = (l) => {
    const lista = s.prenotazioni[l.id];
    if (!lista.includes("sofia")) {
      if (lista.length >= POSTI) lista.pop();
      lista.push("sofia");
    }
  };
  if (future[0]) metti(future[0]);
  if (future[7]) metti(future[7]);
  for (const l of passate.slice(-12).filter((_, i) => i % 4 === 0)) {
    metti(l);
    (s.presenze[l.id] ||= {}).sofia = true;
  }
  // Una lezione piena domani o dopodomani, per far vedere la lista d'attesa.
  const piena = future.find((l, i) => i >= 3 && !s.prenotazioni[l.id].includes("sofia"));
  if (piena) {
    const lista = s.prenotazioni[piena.id];
    while (lista.length < POSTI) lista.push(pesca(lista));
    s.attesa[piena.id] = [];
  }

  s.avvisi = [
    {
      id: "a1",
      testo: "Benvenute nella nuova app! Da oggi le lezioni si prenotano da qui. Per qualsiasi dubbio scriveteci su WhatsApp.",
      da: "Greta ed Elisa",
      quando: new Date(ora.getTime() - 2 * 3600000).toISOString(),
    },
  ];
  s.movimenti = altre.slice(0, 6).map((id, i) => ({
    cliente: id,
    pacchetto: i % 3 === 0 ? "p5" : "p10",
    metodo: i % 2 ? "POS" : "contanti",
    quando: new Date(ora.getTime() - (i * 3 + 1) * 86400000).toISOString(),
  }));
  return s;
}

salva();
