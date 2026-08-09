// Unico punto di contatto con il backend FastAPI.
// Tutte le viste passano da qui: se cambia l'indirizzo dell'API o il modo di
// autenticarsi, si tocca solo questo file.

const BASE = ""; // stessa origine: l'API serve anche i file statici

export class ErroreApi extends Error {
  constructor(stato, dettaglio) {
    super(dettaglio);
    this.stato = stato;
    this.dettaglio = dettaglio;
  }
}

let token = localStorage.getItem("token") || null;
let alScadere = null; // richiamata quando il token non vale più

export function impostaToken(nuovo) {
  token = nuovo;
  if (nuovo) localStorage.setItem("token", nuovo);
  else localStorage.removeItem("token");
}

export function haToken() {
  return Boolean(token);
}

export function quandoScade(richiamata) {
  alScadere = richiamata;
}

function messaggioLeggibile(stato, corpo) {
  // FastAPI mette la spiegazione in `detail`, che però per gli errori di
  // validazione è una lista di oggetti: va ridotta a una frase.
  const d = corpo && corpo.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    const primo = d[0];
    const campo = Array.isArray(primo.loc) ? primo.loc[primo.loc.length - 1] : "";
    return campo ? `${campo}: ${primo.msg}` : primo.msg;
  }
  if (stato === 401) return "Sessione scaduta, accedi di nuovo";
  if (stato >= 500) return "Il server non risponde. Riprova fra poco.";
  return "Qualcosa non ha funzionato";
}

/** Legge il corpo della risposta.

    Non tutto quello che arriva è JSON: un errore 500 di uvicorn è testo
    semplice ("Internal Server Error"), e un proxy può rispondere HTML.
    Passarli a JSON.parse farebbe fallire il client con un errore
    incomprensibile invece di mostrare il guasto vero. */
async function leggiCorpo(risposta) {
  const testo = await risposta.text();
  if (!testo) return null;
  try {
    return JSON.parse(testo);
  } catch {
    return null;
  }
}

/** Caricamento di un file: multipart, senza Content-Type impostato a mano
    (il browser deve aggiungere da sé il "boundary"). */
async function invioFile(metodo, percorso, file, campi = {}) {
  const modulo = new FormData();
  modulo.append("file", file);
  for (const [k, v] of Object.entries(campi)) {
    if (v !== undefined && v !== null && v !== "") modulo.append(k, v);
  }

  let risposta;
  try {
    risposta = await fetch(new URL(BASE + percorso, location.origin), {
      method: metodo,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: modulo,
    });
  } catch {
    throw new ErroreApi(0, "Nessuna connessione. Controlla la rete.");
  }

  const dati = await leggiCorpo(risposta);
  if (!risposta.ok) {
    if (risposta.status === 401 && alScadere) alScadere();
    throw new ErroreApi(risposta.status, messaggioLeggibile(risposta.status, dati));
  }
  return dati;
}

async function richiesta(metodo, percorso, { corpo, parametri } = {}) {
  const url = new URL(BASE + percorso, location.origin);
  if (parametri) {
    for (const [k, v] of Object.entries(parametri)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    }
  }

  const intestazioni = {};
  if (corpo !== undefined) intestazioni["Content-Type"] = "application/json";
  if (token) intestazioni["Authorization"] = `Bearer ${token}`;

  let risposta;
  try {
    risposta = await fetch(url, {
      method: metodo,
      headers: intestazioni,
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
    });
  } catch {
    throw new ErroreApi(0, "Nessuna connessione. Controlla la rete.");
  }

  if (risposta.status === 204) return null;

  const dati = await leggiCorpo(risposta);

  if (!risposta.ok) {
    if (risposta.status === 401 && alScadere) alScadere();
    throw new ErroreApi(risposta.status, messaggioLeggibile(risposta.status, dati));
  }
  return dati;
}

const get = (p, parametri) => richiesta("GET", p, { parametri });
const post = (p, corpo, parametri) => richiesta("POST", p, { corpo, parametri });
const patch = (p, corpo) => richiesta("PATCH", p, { corpo });
const elimina = (p) => richiesta("DELETE", p);

export const api = {
  // --- Autenticazione ---
  registrazione: (dati) => post("/auth/registrazione", dati),
  accedi: (email, password) => post("/auth/login", { email, password }),
  io: () => get("/auth/me"),
  cambioPassword: (dati) => post("/auth/cambio-password", dati),
  recuperoPassword: (email) => post("/auth/recupero-password", { email }),
  reimpostaPassword: (codice, passwordNuova) =>
    post("/auth/reimposta-password", { codice, password_nuova: passwordNuova }),
  verificaEmail: (codice) => post("/auth/verifica-email", { codice }),
  inviaVerifica: () => post("/auth/invia-verifica"),

  // --- Anagrafiche ---
  zone: () => get("/zone"),

  // --- Bagnini ---
  creaProfiloBagnino: (dati) => post("/bagnini", dati),
  mioProfiloBagnino: () => get("/bagnini/me"),
  aggiornaProfiloBagnino: (dati) => patch("/bagnini/me", dati),
  bagnini: (filtri) => get("/bagnini", filtri),
  bagnino: (id) => get(`/bagnini/${id}`),
  caricaFotoBagnino: (file) => invioFile("PUT", "/bagnini/me/foto", file),
  rimuoviFotoBagnino: () => elimina("/bagnini/me/foto"),
  aggiungiBrevetto: (dati) => post("/bagnini/me/brevetti", dati),
  eliminaBrevetto: (id) => elimina(`/bagnini/me/brevetti/${id}`),
  aggiungiEsperienza: (dati) => post("/bagnini/me/esperienze", dati),
  eliminaEsperienza: (id) => elimina(`/bagnini/me/esperienze/${id}`),
  aggiungiDisponibilita: (dati) => post("/bagnini/me/disponibilita", dati),
  eliminaDisponibilita: (id) => elimina(`/bagnini/me/disponibilita/${id}`),

  // --- Piscine ---
  creaProfiloPiscina: (dati) => post("/piscine", dati),
  mioProfiloPiscina: () => get("/piscine/me"),
  aggiornaProfiloPiscina: (dati) => patch("/piscine/me", dati),
  piscine: (filtri) => get("/piscine", filtri),
  caricaFotoPiscina: (file, tipo, didascalia) =>
    invioFile("POST", "/piscine/me/foto", file, { tipo, didascalia }),
  eliminaFotoPiscina: (id) => elimina(`/piscine/me/foto/${id}`),
  piscina: (id) => get(`/piscine/${id}`),

  // --- Annunci ---
  bacheca: (filtri) => get("/annunci", filtri),
  annuncio: (id) => get(`/annunci/${id}`),
  pubblica: (dati) => post("/annunci", dati),
  modificaAnnuncio: (id, dati) => patch(`/annunci/${id}`, dati),
  eliminaAnnuncio: (id) => elimina(`/annunci/${id}`),
  mieiAnnunci: (filtri) => get("/annunci/miei", filtri),
  chiudiAnnuncio: (id) => post(`/annunci/${id}/chiudi`),

  // --- Candidature ---
  candidati: (annuncioId, dati) => post(`/annunci/${annuncioId}/candidature`, dati),
  candidature: (annuncioId) => get(`/annunci/${annuncioId}/candidature`),
  accettaCandidatura: (annuncioId, id) =>
    post(`/annunci/${annuncioId}/candidature/${id}/accetta`),
  rifiutaCandidatura: (annuncioId, id) =>
    post(`/annunci/${annuncioId}/candidature/${id}/rifiuta`),
  mieCandidature: () => get("/candidature/mie"),
  ritiraCandidatura: (id) => elimina(`/candidature/${id}`),

  // --- Messaggi ---
  conversazioni: () => get("/conversazioni"),
  nonLetti: () => get("/conversazioni/non-letti"),
  messaggi: (id) => get(`/conversazioni/${id}/messaggi`),
  scriviNuova: (dati) => post("/conversazioni", dati),
  rispondi: (id, testo) => post(`/conversazioni/${id}/messaggi`, { testo }),
  blocca: (utenteId, motivo) => post(`/blocchi/${utenteId}`, { motivo }),
  sblocca: (utenteId) => elimina(`/blocchi/${utenteId}`),
  blocchi: () => get("/blocchi"),

  // --- Recensioni ---
  recensisci: (dati) => post("/recensioni", dati),
  recensioni: (utenteId) => get(`/utenti/${utenteId}/recensioni`),

  // --- Gestione (solo staff) ---
  staffRiepilogo: () => get("/staff/riepilogo"),
  staffUtenti: (filtri) => get("/staff/utenti", filtri),
  staffBrevetti: (filtri) => get("/staff/brevetti", filtri),
  staffVerificaBrevetto: (id, valore, motivo) =>
    post(`/staff/brevetti/${id}/verifica`, { valore, motivo }),
  staffVerificaUtente: (id, valore, motivo) =>
    post(`/staff/utenti/${id}/verifica`, { valore, motivo }),
  staffStatoUtente: (id, attivo, motivo) =>
    post(`/staff/utenti/${id}/stato`, { attivo, motivo }),
  staffRegistro: (filtri) => get("/staff/registro", filtri),
};
