// Service worker: rende l'app installabile e apribile anche con poca rete.
//
// Regola importante: il guscio (HTML, CSS, JS) si mette in cache, le risposte
// dell'API mai. La mappa di oggi cambia ogni minuto, e mostrare una mappa di
// ieri farebbe scegliere un posto già occupato.

const VERSIONE = "piscina-v1";

const GUSCIO = [
  "/",
  "/index.html",
  "/css/stile.css",
  "/js/app.js",
  "/js/api.js",
  "/js/ui.js",
  "/js/mappa.js",
  "/js/omino.js",
  "/js/prezzi.js",
  "/js/viste/prenota.js",
  "/js/viste/listino.js",
  "/js/viste/dove.js",
  "/js/viste/prenotazione.js",
  "/js/viste/staff.js",
  "/manifest.webmanifest",
  "/icone/icona.svg",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(VERSIONE).then((cache) => cache.addAll(GUSCIO)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((chiavi) => Promise.all(chiavi.filter((k) => k !== VERSIONE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const richiesta = evento.request;
  if (richiesta.method !== "GET") return;

  const url = new URL(richiesta.url);
  if (url.origin !== location.origin) return;
  // Niente cache per i dati: né la mappa, né le prenotazioni, né il gestionale.
  if (url.pathname.startsWith("/api/")) return;

  evento.respondWith(
    caches.match(richiesta).then((salvata) => {
      const dallaRete = fetch(richiesta)
        .then((risposta) => {
          if (risposta.ok) {
            const copia = risposta.clone();
            caches.open(VERSIONE).then((cache) => cache.put(richiesta, copia));
          }
          return risposta;
        })
        .catch(() => salvata || caches.match("/index.html"));
      // Prima quello che c'è, intanto si aggiorna: l'app si apre subito.
      return salvata || dallaRete;
    })
  );
});
