// Unico punto di contatto con il server. Se cambia l'indirizzo dell'API o il
// modo di autenticarsi, si tocca solo questo file.

export class ErroreApi extends Error {
  constructor(stato, dettaglio) {
    super(dettaglio);
    this.stato = stato;
  }
}

const CHIAVE_TOKEN = "reformer-token";

function leggi() {
  try { return localStorage.getItem(CHIAVE_TOKEN); } catch { return null; }
}

let token = leggi();

export function impostaToken(nuovo) {
  token = nuovo || null;
  try {
    if (token) localStorage.setItem(CHIAVE_TOKEN, token);
    else localStorage.removeItem(CHIAVE_TOKEN);
  } catch { /* navigazione privata: resta dentro finché la pagina è aperta */ }
}

export const haToken = () => Boolean(token);

// Chi ascolta quando la sessione scade (l'app torna all'accesso).
let alScadere = () => {};
export const quandoScade = (f) => { alScadere = f; };

function messaggio(stato, corpo) {
  const d = corpo && corpo.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    const primo = d[0];
    const campo = Array.isArray(primo.loc) ? primo.loc[primo.loc.length - 1] : "";
    const nomi = { email: "Email", password: "Password", telefono: "Telefono", nome: "Nome", cognome: "Cognome" };
    if (campo === "password" && /at least/.test(primo.msg)) return "La password deve avere almeno 8 caratteri";
    if (campo === "email") return "Controlla l'indirizzo email";
    if (campo === "telefono") return "Controlla il numero di telefono";
    if (campo === "privacy") return "Serve accettare l'informativa sulla privacy";
    return nomi[campo] ? `${nomi[campo]}: controlla il campo` : "Controlla i dati inseriti";
  }
  if (stato === 401) return "Sessione scaduta, accedi di nuovo";
  if (stato === 429) return "Troppi tentativi: riprova fra un po'";
  if (stato === 0) return "Sembra che non ci sia rete. Riprova.";
  if (stato >= 500) return "Il server non risponde. Riprova fra poco.";
  return "Qualcosa non ha funzionato";
}

async function chiama(percorso, { metodo = "GET", corpo } = {}) {
  const intestazioni = {};
  if (corpo !== undefined) intestazioni["Content-Type"] = "application/json";
  if (token) intestazioni.Authorization = `Bearer ${token}`;
  let risposta;
  try {
    risposta = await fetch(percorso, {
      method: metodo,
      headers: intestazioni,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new ErroreApi(0, messaggio(0));
  }
  if (risposta.status === 204) return null;
  const testo = await risposta.text();
  let dati = null;
  try { dati = testo ? JSON.parse(testo) : null; } catch { dati = null; }
  if (!risposta.ok) {
    if (risposta.status === 401 && token) {
      impostaToken(null);
      alScadere();
    }
    throw new ErroreApi(risposta.status, messaggio(risposta.status, dati));
  }
  return dati;
}

const q = (p) => {
  const s = new URLSearchParams(Object.entries(p).filter(([, v]) => v !== undefined && v !== null && v !== "")).toString();
  return s ? `?${s}` : "";
};

// --- Pubblico e accesso ------------------------------------------------------
export const info = () => chiama("/api/info");

async function conSessione(promessa) {
  const dati = await promessa;
  impostaToken(dati.token);
  return dati.utente;
}

export const registrati = (dati) => conSessione(chiama("/api/auth/registrati", { metodo: "POST", corpo: dati }));
export const accedi = (email, password) =>
  conSessione(chiama("/api/auth/accedi", { metodo: "POST", corpo: { email, password } }));
export const conferma = (codice) => conSessione(chiama("/api/auth/conferma", { metodo: "POST", corpo: { codice } }));
export const reinviaConferma = () => chiama("/api/auth/reinvia-conferma", { metodo: "POST" });
export const recupero = (email) => chiama("/api/auth/recupero", { metodo: "POST", corpo: { email } });
export const nuovaPassword = (codice, password) =>
  conSessione(chiama("/api/auth/nuova-password", { metodo: "POST", corpo: { codice, password } }));
export const esci = () => impostaToken(null);

// --- Cliente -----------------------------------------------------------------
export const io = () => chiama("/api/io");
export const modificaIo = (dati) => chiama("/api/io", { metodo: "PATCH", corpo: dati });
export async function cambiaPassword(attuale, nuova) {
  const r = await chiama("/api/io/password", { metodo: "POST", corpo: { attuale, nuova } });
  impostaToken(r.token);
}
export const esporta = () => chiama("/api/io/esporta");
export const cancellaAccount = (password) => chiama("/api/io/cancella", { metodo: "POST", corpo: { password } });

export const lezioni = (da, giorni) => chiama(`/api/lezioni${q({ da, giorni })}`);
export const prenota = (id) => chiama(`/api/lezioni/${id}/prenota`, { metodo: "POST" });
export const disdici = (id) => chiama(`/api/lezioni/${id}/prenota`, { metodo: "DELETE" });
export const entraInAttesa = (id) => chiama(`/api/lezioni/${id}/attesa`, { metodo: "POST" });
export const esciDallAttesa = (id) => chiama(`/api/lezioni/${id}/attesa`, { metodo: "DELETE" });
export const mie = () => chiama("/api/mie");
export const pacchetto = () => chiama("/api/pacchetto");
export const notifiche = () => chiama("/api/notifiche");
export const segnaLette = () => chiama("/api/notifiche/lette", { metodo: "POST" });

// --- Staff -------------------------------------------------------------------
export const staffLezioni = (da, giorni) => chiama(`/api/staff/lezioni${q({ da, giorni })}`);
export const nuovaLezione = (giorno, ora, titolo) =>
  chiama("/api/staff/lezioni", { metodo: "POST", corpo: { giorno, ora, titolo } });
export const staffLezione = (id) => chiama(`/api/staff/lezioni/${id}`);
export const cambiaTitolo = (id, titolo, ogniSettimana = false) =>
  chiama(`/api/staff/lezioni/${id}`, { metodo: "PATCH", corpo: { titolo, ogni_settimana: ogniSettimana } });
export const annullaLezione = (id, motivo) =>
  chiama(`/api/staff/lezioni/${id}/annulla`, { metodo: "POST", corpo: { motivo } });
export const ripristinaLezione = (id) => chiama(`/api/staff/lezioni/${id}/ripristina`, { metodo: "POST" });
export const aggiungiIscritta = (id, clienteId) =>
  chiama(`/api/staff/lezioni/${id}/iscritte`, { metodo: "POST", corpo: { cliente_id: clienteId } });
export const togliIscritta = (id, clienteId) =>
  chiama(`/api/staff/lezioni/${id}/iscritte/${clienteId}`, { metodo: "DELETE" });
export const segnaPresenza = (id, clienteId, presente) =>
  chiama(`/api/staff/lezioni/${id}/presenze/${clienteId}`, { metodo: "PUT", corpo: { presente } });
export const clienti = (cerca) => chiama(`/api/staff/clienti${q({ cerca })}`);
export const scheda = (id) => chiama(`/api/staff/clienti/${id}`);
export const impostaSaldo = (id, dati) => chiama(`/api/staff/clienti/${id}/lezioni`, { metodo: "POST", corpo: dati });
export const avvisi = () => chiama("/api/staff/avvisi");
export const pubblicaAvviso = (testo) => chiama("/api/staff/avvisi", { metodo: "POST", corpo: { testo } });
export const togliAvviso = (id) => chiama(`/api/staff/avvisi/${id}`, { metodo: "DELETE" });
export const numeri = () => chiama("/api/staff/numeri");
