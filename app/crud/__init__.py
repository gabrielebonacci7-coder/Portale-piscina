"""Livello di accesso ai dati: query e regole di dominio, separate dai router.

I router si occupano di HTTP (status code, autenticazione, serializzazione),
qui invece sta il "cosa significa" — quali annunci sono visibili, chi può
recensire chi, come si filtra la bacheca.
"""
