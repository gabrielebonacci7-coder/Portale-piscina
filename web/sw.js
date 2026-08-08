// Service worker: rende l'app installabile e apribile anche senza rete.
//
// Regola importante: il guscio (HTML, CSS, JS) si mette in cache, i dati
// dell'API mai. Le risposte dell'API sono legate al token di chi le ha
// chieste: salvarle significherebbe mostrare a un utente i dati di un altro.

const VERSIONE = "guardlink-v1";

const GUSCIO = [
  "/",
  "/index.html",
  "/css/stile.css",
  "/js/app.js",
  "/js/api.js",
  "/js/stato.js",
  "/js/ui.js",
  "/js/viste/accesso.js",
  "/js/viste/bacheca.js",
  "/js/viste/bagnini.js",
  "/js/viste/candidature.js",
  "/js/viste/messaggi.js",
  "/js/viste/profilo.js",
  "/js/viste/pubblica.js",
  "/manifest.webmanifest",
  "/icone/icona.svg",
];

// Percorsi serviti dal backend: non vanno mai messi in cache.
const API = [
  "/auth",
  "/annunci",
  "/bagnini",
  "/piscine",
  "/candidature",
  "/conversazioni",
  "/blocchi",
  "/recensioni",
  "/utenti",
  "/zone",
  "/health",
  "/schema",
  "/docs",
  "/openapi.json",
];

const eApi = (url) => API.some((p) => url.pathname === p || url.pathname.startsWith(p + "/"));

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(VERSIONE).then((cache) => cache.addAll(GUSCIO)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((chiavi) =>
        Promise.all(chiavi.filter((k) => k !== VERSIONE).map((k) => caches.delete(k))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (evento) => {
  const richiesta = evento.request;
  if (richiesta.method !== "GET") return;

  const url = new URL(richiesta.url);
  if (url.origin !== location.origin) return;
  if (eApi(url)) return; // l'API passa sempre dalla rete

  // Navigazione: rete, e se manca si apre comunque il guscio salvato.
  if (richiesta.mode === "navigate") {
    evento.respondWith(fetch(richiesta).catch(() => caches.match("/index.html")));
    return;
  }

  // File statici: prima la cache, così l'avvio è immediato.
  evento.respondWith(
    caches.match(richiesta).then((salvata) => {
      if (salvata) return salvata;
      return fetch(richiesta).then((risposta) => {
        if (risposta.ok) {
          const copia = risposta.clone();
          caches.open(VERSIONE).then((cache) => cache.put(richiesta, copia));
        }
        return risposta;
      });
    }),
  );
});
