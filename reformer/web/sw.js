// Service worker: rende l'app installabile e veloce da riaprire.
//
// Il guscio (HTML, CSS, JS, immagini) si tiene in cache; le risposte
// dell'API mai: i posti liberi cambiano di minuto in minuto, e mostrare quelli
// di ieri farebbe prenotare una lezione già piena.
//
// **Dopo ogni modifica ai file di web/ si alza VERSIONE**, altrimenti i
// telefoni che hanno l'app installata continuano a usare la copia vecchia.

const VERSIONE = "reformer-v6";

const GUSCIO = [
  "/",
  "/index.html",
  "/privacy.html",
  "/css/stile.css",
  "/js/app.js",
  "/js/api.js",
  "/js/ui.js",
  "/js/tempo.js",
  "/js/avatar.js",
  "/js/viste/cliente.js",
  "/js/viste/studio.js",
  "/font/Fraunces.woff2",
  "/font/DMSans.woff2",
  "/immagini/marchio.png",
  "/immagini/greta.webp",
  "/immagini/elisa.webp",
  "/icone/icona-192.png",
  "/manifest.webmanifest",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(VERSIONE).then((c) => c.addAll(GUSCIO)));
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((chiavi) => Promise.all(chiavi.filter((k) => k !== VERSIONE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// L'app chiede di passare subito alla versione nuova quando la cliente tocca
// "Aggiorna" (vedi app.js).
self.addEventListener("message", (evento) => {
  if (evento.data === "aggiorna") self.skipWaiting();
});

self.addEventListener("fetch", (evento) => {
  const richiesta = evento.request;
  if (richiesta.method !== "GET") return;
  const url = new URL(richiesta.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname === "/health") return;

  evento.respondWith(
    caches.match(richiesta, { ignoreSearch: true }).then((salvata) => {
      const dallaRete = fetch(richiesta)
        .then((risposta) => {
          if (risposta.ok) {
            const copia = risposta.clone();
            caches.open(VERSIONE).then((c) => c.put(richiesta, copia));
          }
          return risposta;
        })
        .catch(() => salvata || caches.match("/index.html"));
      // Prima quello che c'è, intanto si aggiorna: l'app si apre subito.
      return salvata || dallaRete;
    })
  );
});
