// Sessione e dati condivisi fra le viste.

import { api, impostaToken, haToken } from "./api.js";

export const stato = {
  utente: null, // l'account autenticato
  profilo: null, // ProfiloBagnino o ProfiloPiscina
  zone: [],
  nonLetti: 0,
};

export const eBagnino = () => stato.utente?.tipo === "bagnino";
export const ePiscina = () => stato.utente?.tipo === "piscina";
export const haProfilo = () => Boolean(stato.profilo);
// Il permesso di gestione è indipendente dal tipo di account: chi lo ha vede
// una scheda in più, per il resto usa l'app come tutti gli altri.
export const eStaff = () => stato.utente?.ruolo === "staff";

export async function caricaSessione() {
  if (!haToken()) return false;
  try {
    stato.utente = await api.io();
  } catch {
    // Token vecchio o non valido: si riparte dall'accesso.
    esci();
    return false;
  }
  await Promise.all([caricaProfilo(), caricaZone(), aggiornaNonLetti()]);
  return true;
}

export async function caricaProfilo() {
  if (!stato.utente) return null;
  try {
    stato.profilo = eBagnino() ? await api.mioProfiloBagnino() : await api.mioProfiloPiscina();
  } catch (e) {
    // 409 = account creato ma profilo non ancora compilato: è previsto.
    if (e.stato !== 409 && e.stato !== 404) throw e;
    stato.profilo = null;
  }
  return stato.profilo;
}

export async function caricaZone() {
  if (stato.zone.length) return stato.zone;
  stato.zone = await api.zone();
  return stato.zone;
}

export async function aggiornaNonLetti() {
  if (!stato.utente) return 0;
  try {
    const r = await api.nonLetti();
    stato.nonLetti = r.non_letti;
  } catch {
    stato.nonLetti = 0;
  }
  return stato.nonLetti;
}

export async function entra(email, password) {
  const r = await api.accedi(email, password);
  impostaToken(r.access_token);
  stato.utente = r.utente;
  await Promise.all([caricaProfilo(), caricaZone(), aggiornaNonLetti()]);
  return stato.utente;
}

export function esci() {
  impostaToken(null);
  stato.utente = null;
  stato.profilo = null;
  stato.nonLetti = 0;
}
