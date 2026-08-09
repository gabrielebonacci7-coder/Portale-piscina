// Accesso, registrazione e creazione del profilo: tutto ciò che accade
// prima di poter vedere la bacheca.

import { api, impostaToken } from "../api.js";
import { caricaProfilo, caricaZone, entra, stato } from "../stato.js";
import { LOGO, avviso, brindisi, caselleZone, el, opzioniZone } from "../ui.js";

/** Schermata iniziale: entra o registrati. */
export function vistaAccesso(vaiAllApp) {
  const contenitore = el("div", { classe: "accesso" });

  const marchio = el("div", { classe: "marchio", html: LOGO });
  marchio.append(
    el("h1", { testo: "Guardlink" }),
    el("p", { testo: "Turni e sostituzioni per bagnini e strutture." }),
  );

  const zonaModulo = el("div");
  contenitore.append(marchio, zonaModulo);

  const mostraAccesso = () => {
    zonaModulo.replaceChildren(moduloAccesso(vaiAllApp, mostraRegistrazione, mostraRecupero));
  };
  const mostraRegistrazione = () => {
    zonaModulo.replaceChildren(moduloRegistrazione(vaiAllApp, mostraAccesso));
  };
  const mostraRecupero = () => {
    zonaModulo.replaceChildren(moduloRecupero(mostraAccesso));
  };

  mostraAccesso();
  return contenitore;
}

function moduloAccesso(vaiAllApp, vaiARegistrazione, vaiARecupero) {
  const errore = el("div");

  const form = el("form", {
    onsubmit: async (e) => {
      e.preventDefault();
      errore.replaceChildren();
      const invio = form.querySelector("button[type=submit]");
      invio.disabled = true;
      invio.textContent = "Accesso…";
      try {
        await entra(form.email.value.trim(), form.password.value);
        vaiAllApp();
      } catch (err) {
        errore.replaceChildren(avviso(err.dettaglio || "Accesso non riuscito"));
        invio.disabled = false;
        invio.textContent = "Entra";
      }
    },
  });

  form.append(
    errore,
    campo("Email", el("input", { type: "email", name: "email", required: true, autocomplete: "email" })),
    campo(
      "Password",
      el("input", {
        type: "password",
        name: "password",
        required: true,
        autocomplete: "current-password",
      }),
    ),
    el("button", { type: "submit", classe: "btn largo", testo: "Entra" }),
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:14px" }, [
      el("a", {
        href: "#",
        onclick: (e) => (e.preventDefault(), vaiARecupero()),
        testo: "Password dimenticata?",
      }),
    ]),
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:6px" }, [
      "Non hai un account? ",
      el("a", { href: "#", onclick: (e) => (e.preventDefault(), vaiARegistrazione()), testo: "Registrati" }),
    ]),
  );
  return form;
}

function moduloRegistrazione(vaiAllApp, vaiAdAccesso) {
  const errore = el("div");
  let tipoScelto = "bagnino";

  const scelta = el("div", { classe: "segmenti" });
  const bottoni = [
    ["bagnino", "Sono un bagnino"],
    ["piscina", "Sono una struttura"],
  ].map(([valore, testo]) =>
    el("button", {
      type: "button",
      testo,
      "aria-pressed": valore === tipoScelto,
      onclick: () => {
        tipoScelto = valore;
        bottoni.forEach((b) => b.setAttribute("aria-pressed", b.dataset.valore === valore));
      },
      "data-valore": valore,
    }),
  );
  scelta.append(...bottoni);

  const form = el("form", {
    onsubmit: async (e) => {
      e.preventDefault();
      errore.replaceChildren();
      const invio = form.querySelector("button[type=submit]");
      invio.disabled = true;
      invio.textContent = "Creazione…";
      const email = form.email.value.trim();
      const password = form.password.value;
      try {
        await api.registrazione({
          email,
          password,
          tipo: tipoScelto,
          telefono: form.telefono.value.trim() || null,
          accetta_privacy: form.privacy.checked,
        });
        await entra(email, password);
        vaiAllApp(); // l'app porterà alla creazione del profilo
      } catch (err) {
        errore.replaceChildren(avviso(err.dettaglio || "Registrazione non riuscita"));
        invio.disabled = false;
        invio.textContent = "Crea account";
      }
    },
  });

  form.append(
    errore,
    scelta,
    campo("Email", el("input", { type: "email", name: "email", required: true, autocomplete: "email" })),
    campo(
      "Password",
      el("input", {
        type: "password",
        name: "password",
        required: true,
        minlength: 8,
        autocomplete: "new-password",
      }),
      "Almeno 8 caratteri.",
    ),
    campo(
      "Telefono (facoltativo)",
      el("input", { type: "tel", name: "telefono", autocomplete: "tel" }),
    ),
    // `required` sulla casella: il browser non lascia inviare senza spunta, e
    // la spunta non è mai messa in partenza — una casella già segnata non è un
    // consenso. Il controllo vero resta comunque sul server.
    el("label", { classe: "interruttore consenso" }, [
      el("span", {}, [
        "Ho letto l'",
        el("a", { href: "/privacy.html", target: "_blank", testo: "informativa privacy" }),
        " e accetto il trattamento dei miei dati.",
      ]),
      el("input", { type: "checkbox", name: "privacy", required: true }),
    ]),
    el("button", { type: "submit", classe: "btn largo", testo: "Crea account" }),
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:16px" }, [
      "Hai già un account? ",
      el("a", { href: "#", onclick: (e) => (e.preventDefault(), vaiAdAccesso()), testo: "Entra" }),
    ]),
  );
  return form;
}

/** Chiede il link per reimpostare la password. */
function moduloRecupero(vaiAdAccesso) {
  const esito = el("div");

  const form = el("form", {
    onsubmit: async (e) => {
      e.preventDefault();
      const invio = form.querySelector("button[type=submit]");
      invio.disabled = true;
      invio.textContent = "Invio…";
      try {
        await api.recuperoPassword(form.email.value.trim());
      } catch {
        // Il server risponde uguale in ogni caso: nemmeno qui si deve poter
        // capire se quell'indirizzo è registrato.
      }
      // Messaggio volutamente vago, per lo stesso motivo.
      esito.replaceChildren(
        avviso(
          "Se l'indirizzo è registrato, fra poco arriva un'email con il link per " +
            "reimpostare la password. Controlla anche lo spam.",
          "ok",
        ),
      );
      form.querySelector(".campo").hidden = true;
      invio.hidden = true;
    },
  });

  form.append(
    esito,
    el("p", {
      classe: "sommesso",
      style: "margin-bottom:16px",
      testo: "Scrivi l'indirizzo con cui ti sei iscritto: ti mandiamo un link.",
    }),
    campo("Email", el("input", { type: "email", name: "email", required: true, autocomplete: "email" })),
    el("button", { type: "submit", classe: "btn largo", testo: "Mandami il link" }),
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:16px" }, [
      el("a", { href: "#", onclick: (e) => (e.preventDefault(), vaiAdAccesso()), testo: "Torna all'accesso" }),
    ]),
  );
  return form;
}

/** Schermata aperta dal link ricevuto per email: imposta la nuova password. */
export function vistaReimposta(codice, vaiAllApp, vaiAdAccesso) {
  const contenitore = el("div", { classe: "accesso" });
  const errore = el("div");

  contenitore.append(
    el("div", { classe: "marchio", html: LOGO }),
    el("h1", { style: "text-align:center", testo: "Nuova password" }),
  );

  const form = el("form", {
    onsubmit: async (e) => {
      e.preventDefault();
      errore.replaceChildren();
      const invio = form.querySelector("button[type=submit]");
      invio.disabled = true;
      try {
        const r = await api.reimpostaPassword(codice, form.password.value);
        impostaToken(r.access_token);
        brindisi("Password aggiornata");
        vaiAllApp();
      } catch (err) {
        errore.replaceChildren(avviso(err.dettaglio));
        invio.disabled = false;
      }
    },
  });

  form.append(
    errore,
    campo(
      "Nuova password",
      el("input", {
        type: "password",
        name: "password",
        required: true,
        minlength: 8,
        autocomplete: "new-password",
      }),
      "Almeno 8 caratteri.",
    ),
    el("button", { type: "submit", classe: "btn largo", testo: "Salva ed entra" }),
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:16px" }, [
      el("a", { href: "#", onclick: (e) => (e.preventDefault(), vaiAdAccesso()), testo: "Annulla" }),
    ]),
  );

  contenitore.append(form);
  return contenitore;
}

/** Creazione del profilo: obbligatoria prima di pubblicare o candidarsi. */
export function vistaCreaProfilo(fatto) {
  const contenitore = el("div", { classe: "accesso" });
  const errore = el("div");
  const bagnino = stato.utente.tipo === "bagnino";

  contenitore.append(
    el("div", { classe: "marchio" }, [
      el("h1", { testo: bagnino ? "Il tuo profilo" : "La tua struttura" }),
      el("p", {
        testo: bagnino
          ? "Servono per farti trovare dalle piscine. Puoi completarlo più avanti."
          : "Servono a farti riconoscere dai bagnini quando pubblichi un turno.",
      }),
    ]),
  );

  const form = el("form", {
    onsubmit: async (e) => {
      e.preventDefault();
      errore.replaceChildren();
      const invio = form.querySelector("button[type=submit]");
      invio.disabled = true;
      try {
        if (bagnino) {
          await api.creaProfiloBagnino({
            nome: form.nome.value.trim(),
            cognome: form.cognome.value.trim(),
            data_nascita: form.nascita.value || null,
            anni_esperienza: Number(form.esperienza.value || 0),
            zone_ids: [...form.querySelectorAll("input[name=zona]:checked")].map((i) =>
              Number(i.value),
            ),
          });
        } else {
          await api.creaProfiloPiscina({
            nome_struttura: form.struttura.value.trim(),
            tipo_struttura: form.tipoStruttura.value,
            zona_id: Number(form.zona.value) || null,
            indirizzo: form.indirizzo.value.trim() || null,
            referente_nome: form.referente.value.trim() || null,
          });
        }
        await caricaProfilo();
        brindisi("Profilo creato");
        fatto();
      } catch (err) {
        errore.replaceChildren(avviso(err.dettaglio || "Non è stato possibile salvare"));
        invio.disabled = false;
      }
    },
  });

  form.append(errore);

  if (bagnino) {
    const zone = el("div");
    caricaZone().then((elenco) => zone.replaceChildren(caselleZone(elenco)));

    form.append(
      el("div", { classe: "riga-campi" }, [
        campo("Nome", el("input", { type: "text", name: "nome", required: true })),
        campo("Cognome", el("input", { type: "text", name: "cognome", required: true })),
      ]),
      el("div", { classe: "riga-campi" }, [
        campo("Data di nascita", el("input", { type: "date", name: "nascita" })),
        campo("Anni di esperienza", el("input", { type: "number", name: "esperienza", min: 0, max: 60, value: 0 })),
      ]),
      campo(
        "Zone in cui puoi lavorare",
        zone,
        "Puoi sceglierne più di una, anche fuori Roma.",
      ),
    );
  } else {
    const zona = el("select", { name: "zona" }, [el("option", { value: "", testo: "—" })]);
    caricaZone().then((elenco) => zona.append(...opzioniZone(elenco)));

    form.append(
      campo("Nome della struttura", el("input", { type: "text", name: "struttura", required: true })),
      campo(
        "Tipo",
        el(
          "select",
          { name: "tipoStruttura" },
          Object.entries({
            comunale: "Piscina comunale",
            hotel: "Hotel",
            condominio: "Condominio",
            centro_sportivo: "Centro sportivo",
            palestra: "Palestra",
            parco_acquatico: "Parco acquatico",
            camping: "Camping",
            privata: "Privata",
            altro: "Altro",
          }).map(([v, t]) => el("option", { value: v, testo: t })),
        ),
      ),
      campo("Zona", zona),
      campo("Indirizzo", el("input", { type: "text", name: "indirizzo" })),
      campo("Chi pubblica gli annunci", el("input", { type: "text", name: "referente" })),
    );
  }

  form.append(el("button", { type: "submit", classe: "btn largo", testo: "Salva e continua" }));
  contenitore.append(form);
  return contenitore;
}

function campo(etichettaTesto, controllo, aiuto) {
  return el("div", { classe: "campo" }, [
    el("label", { testo: etichettaTesto }),
    controllo,
    aiuto && el("span", { classe: "aiuto", testo: aiuto }),
  ]);
}

export { campo };
