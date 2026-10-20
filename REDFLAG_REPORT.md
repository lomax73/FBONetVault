## 2026-08-11 — sessione redflag

### Segnalazioni FBOFlag
- [Conclusa] "nei campi delle sezione ci deve essere il campo rack" (#39) — aggiunto campo `rack` (CharField, blank) al modello `Sezione` (`rete/models.py`), migration `rete/migrations/0002_sezione_rack.py`, esposto in `SezioneForm` (`rete/forms.py`) e colonna "Rack" in `templates/rete/progetto_detail.html`.
- [Approvata, da fare in seguito] "per trovare gli apparati possibilità di importare un file da un ip scan per poi deniminare ed assegnare gli apparati" (#38) — feature sostanziosa: serve definire formato file supportato (Nmap XML? CSV Angry IP Scanner?), parsing, e UI per mappare righe importate a nome/sezione/tipo prima di creare gli `Apparato`. Da progettare in una sessione dedicata.

### Verifica rapida del codice
- Nessun bug evidente trovato in `rete/models.py`, `rete/views.py`, `rete/forms.py` durante la verifica rapida legata alle pagine coinvolte nelle note (progetto/sezioni/apparati). Il pattern generale (LoginRequiredMixin, scoping per progetto via URL kwargs, sync_parametri su save apparato) è coerente col resto del progetto.

### Per chi riprende questo progetto
La #38 (import da IP scan) resta aperta e non banale: prima di implementarla, chiarire con l'utente quale tool di scan usa in pratica (per fissare il formato di import) e se l'assegnazione a sezione/tipo va proposta come step guidato post-import o lasciata manuale come oggi.

## 2026-08-11 — ripresa nota #38 (stessa sessione)

### Segnalazioni FBOFlag
- [Conclusa] "per trovare gli apparati possibilità di importare un file da un ip scan..." (#38) — implementato l'import guidato apparati da scan nmap:
  - `rete/nmap_import.py`: parsing dell'XML di `nmap -oX` con `defusedxml` (dipendenza aggiunta a `requirements.txt`), estrae ip/mac/vendor/hostname degli host con stato "up".
  - `rete/forms.py`: `ImportRigaForm` + `ImportRigaFormSet` per la tabella di revisione (checkbox "includi", nome editabile, sezione/tipo assegnabili, IP/MAC in campi nascosti).
  - `rete/views.py`: `apparato_import` (function-based view) — step 1 mostra il comando `nmap -sn -oX scan.xml <subnet>` (suggerito dalle VLAN del progetto se presenti, altrimenti placeholder generico); step 2 upload file XML e parsing; step 3 form di revisione, righe con IP già presente tra gli apparati del progetto deselezionate di default; conferma crea gli `Apparato` (con `sync_parametri()`) solo per le righe selezionate.
  - `rete/urls.py`: nuova route `progetti/<progetto_pk>/apparati/importa/` (`apparato-import`).
  - `templates/rete/apparato_import.html` (nuovo) + pulsante "Importa da scan" in `templates/rete/progetto_detail.html`.
  - Scelta architetturale: niente scanner lato server — NetVault gira su VPS remoto e non raggiunge la rete del cliente, quindi il comando nmap va eseguito in locale dal tecnico e solo il risultato XML viene caricato.
  - Testato end-to-end con `manage.py shell` + Django test `Client`: host già censito correttamente deselezionato di default, host "down" scartato dal parser, host nuovo importato con IP/MAC corretti.

### Per chi riprende questo progetto
Nessun'altra nota aperta al momento su NetVault. Possibili miglioramenti futuri non richiesti esplicitamente: supporto ad altri formati di import (CSV Angry IP Scanner) se in pratica si rivela più comodo di nmap; deduplica anche per MAC oltre che per IP.

## 2026-08-18 — sessione redflag

### Segnalazioni FBOFlag
- [In test, in attesa di conferma] (id 83) "DEBUG=True di default, impatto potenziale il più alto tra le app finora: MASTER_ENCRYPTION_KEY cifra le credenziali di ogni apparato di rete e le password Wi-Fi dei clienti" — verificato che in produzione `DJANGO_DEBUG=false` è già impostato correttamente (non era un rischio attivo). Aggiunto promemoria esplicito in `deploy/README.md`. Commit+push (`56ea416`), nessun deploy applicativo necessario (solo doc).
- [In test, in attesa di conferma] (id 84) "`rete/portal_client.py`, `verify=False` verso il Portale" — stesso identico fix già applicato a FBORackReport (id 94), FBOPreventivi (id 91), FBOFiberReport (id 78): pinning del certificato self-signed del Portale (`PORTAL_INTERNAL_CA_CERT`, `_PinnedCertAdapter`) invece di disattivare la verifica. Testato in produzione prima del commit. Deployato (commit `ea8cfbb`).

### Verifica rapida del codice
Nessun bug nuovo trovato oltre alle 2 note stesse, entrambe confermate nel codice prima di procedere.

### Per chi riprende questo progetto
Entrambe le note restano `testing` su FBOFlag finché l'utente non conferma di persona: per la 83 basta dare un'occhiata al commit (solo doc); per la 84 verificare che nome/indirizzo cliente (preso dal Portale) compaiano correttamente nell'app. Il pattern `verify=False` verso il Portale resta ancora da correggere solo in `mailer` — ultima app rimasta con questo problema (già fatto in rackreport, preventivi, fiberreport, netvault, portal).
