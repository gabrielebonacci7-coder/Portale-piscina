// Il conto, calcolato dalle stesse righe di listino che l'app mostra nella
// pagina Prezzi. Il totale vero lo fa comunque il server: questo serve a far
// vedere la cifra mentre si sceglie, senza aspettare una chiamata.

/** Trova la riga di listino di una postazione con `n` lettini sotto. */
export function rigaListino(listino, tipo, lettini) {
  if (tipo === "lettino") return listino.noleggio.find((r) => r.lettini === null);
  return listino.noleggio.find((r) => r.lettini === lettini);
}

export function prezzoCent(listino, tipo, lettini) {
  return rigaListino(listino, tipo, lettini)?.intera ?? 0;
}

export function nomePacchetto(tipo, lettini) {
  if (tipo === "lettino") return "Lettino singolo";
  if (lettini === 0) return "Solo ombrellone";
  return `Ombrellone + ${lettini} letti${lettini === 1 ? "no" : "ni"}`;
}

export function totaleCent(listino, scelte) {
  let totale = 0;
  for (const s of scelte.values()) totale += prezzoCent(listino, s.tipo, s.lettini);
  return totale;
}
