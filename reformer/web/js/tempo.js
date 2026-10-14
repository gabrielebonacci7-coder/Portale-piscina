// Date e ore, scritte come le dice una persona: "domani alle 17:30".
//
// Il server manda istanti in UTC; qui si mostrano **sempre nell'ora di
// Roma**, anche se il telefono è impostato su un altro fuso (in vacanza, o un
// telefono comprato all'estero): la lezione delle 16:30 è alle 16:30.
//
// Il trucco: `data()` restituisce una Date i cui getter locali (getHours,
// getDate...) danno l'ora di Roma. Va usata solo per mostrare e confrontare
// date, mai per rimandarle al server.

export const GIORNI = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
export const GIORNI_CORTI = ["dom", "lun", "mar", "mer", "gio", "ven", "sab"];
export const MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
  "agosto", "settembre", "ottobre", "novembre", "dicembre"];

const due = (n) => String(n).padStart(2, "0");

const ROMA = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Rome", year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
});

function aRoma(istante) {
  const p = Object.fromEntries(ROMA.formatToParts(istante).map((x) => [x.type, x.value]));
  return new Date(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second);
}

export const data = (iso) => aRoma(new Date(iso));
/** Adesso, nell'ora di Roma. */
export const ora = () => aRoma(new Date());
export const chiaveGiorno = (d) => `${d.getFullYear()}-${due(d.getMonth() + 1)}-${due(d.getDate())}`;
export const oraDi = (d) => `${due(d.getHours())}:${due(d.getMinutes())}`;
export const dataLunga = (d) => `${GIORNI[d.getDay()]} ${d.getDate()} ${MESI[d.getMonth()]}`;
export const dataBreve = (d) => `${d.getDate()} ${MESI[d.getMonth()]}`;
export const cap = (t) => (t ? t[0].toUpperCase() + t.slice(1) : t);

export function oggi() {
  const d = ora();
  d.setHours(0, 0, 0, 0);
  return d;
}

export function piuGiorni(d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

/** Da "2026-10-14" a una data locale a mezzanotte (senza scivolare di fuso). */
export function daChiave(chiave) {
  const [a, m, g] = chiave.split("-").map(Number);
  return new Date(a, m - 1, g);
}

export function quandoRelativo(d) {
  const diff = Math.round((daChiave(chiaveGiorno(d)) - oggi()) / 86400000);
  if (diff === 0) return "oggi";
  if (diff === 1) return "domani";
  if (diff === -1) return "ieri";
  return dataLunga(d);
}

/** "oggi alle 16:30", "domani alle 17:30", "giovedì 16 ottobre alle 18:30" */
export const quando = (d) => `${quandoRelativo(d)} alle ${oraDi(d)}`;
