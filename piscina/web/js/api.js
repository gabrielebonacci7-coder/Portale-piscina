// Unico punto di contatto con il backend. Se cambia l'indirizzo dell'API o il
// modo di autenticarsi, si tocca solo questo file.

export class ErroreApi extends Error {
  constructor(stato, dettaglio) {
    super(dettaglio);
    this.stato = stato;
    this.dettaglio = dettaglio;
  }
}

const CHIAVE_TOKEN = "piscina-staff-token";
let token = localStorage.getItem(CHIAVE_TOKEN) || null;

export function impostaToken(nuovo) {
  token = nuovo;
  if (nuovo) localStorage.setItem(CHIAVE_TOKEN, nuovo);
  else localStorage.removeItem(CHIAVE_TOKEN);
}

export const haToken = () => Boolean(token);

function messaggioLeggibile(stato, corpo) {
  // FastAPI mette la spiegazione in `detail`, che per gli errori di
  // validazione è una lista di oggetti: va ridotta a una frase sola.
  const d = corpo && corpo.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    const primo = d[0];
    const campo = Array.isArray(primo.loc) ? primo.loc[primo.loc.length - 1] : "";
    return campo ? `${campo}: ${primo.msg}` : primo.msg;
  }
  if (stato === 401) return "Sessione scaduta, accedi di nuovo";
  if (stato === 0) return "Sembra che non ci sia rete. Riprova.";
  if (stato >= 500) return "Il server non risponde. Riprova fra poco.";
  return "Qualcosa non ha funzionato";
}

async function chiama(percorso, opzioni = {}) {
  const intestazioni = { ...(opzioni.headers || {}) };
  if (opzioni.body !== undefined) intestazioni["Content-Type"] = "application/json";
  if (token) intestazioni["Authorization"] = `Bearer ${token}`;

  let risposta;
  try {
    risposta = await fetch(percorso, {
      ...opzioni,
      headers: intestazioni,
      body: opzioni.body === undefined ? undefined : JSON.stringify(opzioni.body),
    });
  } catch {
    throw new ErroreApi(0, messaggioLeggibile(0));
  }

  if (risposta.status === 204) return null;

  const testo = await risposta.text();
  let corpo = null;
  try {
    corpo = testo ? JSON.parse(testo) : null;
  } catch {
    corpo = null; // un 500 di uvicorn è testo semplice, non JSON
  }

  if (!risposta.ok) {
    if (risposta.status === 401) impostaToken(null);
    throw new ErroreApi(risposta.status, messaggioLeggibile(risposta.status, corpo));
  }
  return corpo;
}

const query = (parametri) => {
  const q = new URLSearchParams(
    Object.entries(parametri).filter(([, v]) => v !== undefined && v !== null && v !== "")
  ).toString();
  return q ? `?${q}` : "";
};

// --- Pubblico --------------------------------------------------------------
export const info = () => chiama("/api/info");
export const listino = () => chiama("/api/listino");
export const mappa = (giorno) => chiama(`/api/mappa${query({ giorno })}`);

export const prenota = (dati) => chiama("/api/prenotazioni", { method: "POST", body: dati });
export const ritrova = (codice, telefono) =>
  chiama(`/api/prenotazioni/${encodeURIComponent(codice)}${query({ telefono })}`);
export const annullaPrenotazione = (codice, telefono) =>
  chiama(`/api/prenotazioni/${encodeURIComponent(codice)}/annulla`, {
    method: "POST",
    body: { telefono },
  });

// --- Staff -----------------------------------------------------------------
export async function accessoStaff(email, password) {
  const dati = await chiama("/api/staff/accesso", { method: "POST", body: { email, password } });
  impostaToken(dati.token);
  return dati;
}

export const chiSono = () => chiama("/api/staff/io");
export const prenotazioniStaff = (giorno, cerca) =>
  chiama(`/api/staff/prenotazioni${query({ giorno, cerca })}`);
export const cambiaStato = (codice, stato) =>
  chiama(`/api/staff/prenotazioni/${encodeURIComponent(codice)}`, {
    method: "PATCH",
    body: { stato },
  });
export const postazioniStaff = () => chiama("/api/staff/postazioni");
export const modificaPostazione = (codice, dati) =>
  chiama(`/api/staff/postazioni/${encodeURIComponent(codice)}`, { method: "PATCH", body: dati });
export const urlCsv = (giorno) => `/api/staff/prenotazioni.csv${query({ giorno })}`;

export async function scaricaCsv(giorno) {
  // Il link non può portare l'intestazione con il token: si scarica via fetch
  // e si consegna al browser come file.
  const risposta = await fetch(urlCsv(giorno), { headers: { Authorization: `Bearer ${token}` } });
  if (!risposta.ok) throw new ErroreApi(risposta.status, messaggioLeggibile(risposta.status));
  const blob = await risposta.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `prenotazioni-${giorno}.csv`;
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
