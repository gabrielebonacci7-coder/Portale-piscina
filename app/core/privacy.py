"""Costanti dell'informativa privacy e della cancellazione dell'account.

Stanno qui e non sparse nel codice perché sono valori che si controllano: la
versione dell'informativa va cambiata **ogni volta che il testo cambia in modo
sostanziale**, altrimenti la data di accettazione salvata sugli account non
dimostra più niente — direbbe che hanno accettato un testo che non è quello che
hanno letto.
"""

# Data dell'ultima revisione di `web/privacy.html`. Si salva su ogni account al
# momento dell'iscrizione, insieme alla data di accettazione.
VERSIONE_INFORMATIVA = "2026-08-10"

# Dominio degli indirizzi lasciati al posto di quelli cancellati. `.invalid` è
# riservato dallo standard (RFC 2606): non è di nessuno e non lo sarà mai,
# quindi nessuna email finirà mai per sbaglio a una persona vera.
DOMINIO_ANONIMO = "guardlink.invalid"

# Come compare chi ha cancellato l'account nelle conversazioni e nelle
# recensioni che restano agli altri.
NOME_ANONIMO = "Utente cancellato"
