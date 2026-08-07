// Accesso, registrazione e creazione del profilo: tutto ciò che accade
// prima di poter vedere la bacheca.

import { api } from "../api.js";
import { caricaProfilo, caricaZone, entra, stato } from "../stato.js";
import { LOGO, avviso, brindisi, el } from "../ui.js";

/** Schermata iniziale: entra o registrati. */
export function vistaAccesso(vaiAllApp) {
  const contenitore = el("div", { classe: "accesso" });

  const marchio = el("div", { classe: "marchio", html: LOGO });
  marchio.append(
    el("h1", { testo: "Portale Piscina" }),
    el("p", { testo: "Turni e sostituzioni per bagnini e strutture, a Roma." }),
  );

  const zonaModulo = el("div");
  contenitore.append(marchio, zonaModulo);

  const mostraAccesso = () => {
    zonaModulo.replaceChildren(moduloAccesso(vaiAllApp, mostraRegistrazione));
  };
  const mostraRegistrazione = () => {
    zonaModulo.replaceChildren(moduloRegistrazione(vaiAllApp, mostraAccesso));
  };

  mostraAccesso();
  return contenitore;
}

function moduloAccesso(vaiAllApp, vaiARegistrazione) {
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
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:16px" }, [
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
    el("button", { type: "submit", classe: "btn largo", testo: "Crea account" }),
    el("p", { classe: "sommesso", style: "text-align:center;margin-top:16px" }, [
      "Hai già un account? ",
      el("a", { href: "#", onclick: (e) => (e.preventDefault(), vaiAdAccesso()), testo: "Entra" }),
    ]),
  );
  return form;
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
    const zone = el("div", {
      style: "display:grid;grid-template-columns:1fr 1fr;gap:8px;max-height:180px;overflow-y:auto",
    });
    caricaZone().then((elenco) => {
      zone.replaceChildren(
        ...elenco.map((z) =>
          el("label", { style: "display:flex;gap:8px;align-items:center;font-size:14px" }, [
            el("input", { type: "checkbox", name: "zona", value: z.id, style: "width:20px;min-height:0" }),
            z.nome,
          ]),
        ),
      );
    });

    form.append(
      el("div", { classe: "riga-campi" }, [
        campo("Nome", el("input", { type: "text", name: "nome", required: true })),
        campo("Cognome", el("input", { type: "text", name: "cognome", required: true })),
      ]),
      el("div", { classe: "riga-campi" }, [
        campo("Data di nascita", el("input", { type: "date", name: "nascita" })),
        campo("Anni di esperienza", el("input", { type: "number", name: "esperienza", min: 0, max: 60, value: 0 })),
      ]),
      campo("Zone in cui puoi lavorare", zone),
    );
  } else {
    const zona = el("select", { name: "zona" }, [el("option", { value: "", testo: "—" })]);
    caricaZone().then((elenco) =>
      zona.append(...elenco.map((z) => el("option", { value: z.id, testo: z.nome }))),
    );

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
