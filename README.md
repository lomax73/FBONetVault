# FBONetVault

App della famiglia FBO per raccogliere in un unico posto tutti i
parametri di configurazione della rete e dei server dei clienti presso
cui si interviene: apparati (router, switch, firewall, access point,
server, ...) organizzati per sezione e tipo, i relativi parametri di
configurazione e credenziali di accesso, la struttura della rete (VLAN
e descrizione della topologia) e le reti wireless con le relative
credenziali.

## Sviluppo locale

```
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env   # valorizzare almeno MASTER_ENCRYPTION_KEY (vedi commento nel file)
venv/bin/python manage.py migrate
venv/bin/python manage.py createsuperuser
venv/bin/python manage.py runserver
```

Il picker cliente (elenco in home, dettaglio cliente) dipende
dall'anagrafica clienti condivisa nel Portale FBO — serve un'istanza del
Portale raggiungibile (vedi `PORTAL_INTERNAL_BASE_URL` in
`.env.example`). Senza Portale configurato, l'app parte comunque ma
l'elenco clienti mostra un errore.

## Flusso

1. Da "Clienti" scegli il cliente (anagrafica condivisa del Portale).
2. Nella scheda cliente crea le sezioni (sedi/aree, es. "Sala CED").
3. Aggiungi gli apparati, assegnandoli a una sezione e a un tipo
   (configurabile in "Configurazione").
4. Nella scheda apparato aggiungi i parametri di configurazione liberi
   (chiave/valore) e le credenziali di accesso (SSH, HTTPS, ...).
5. In "Struttura della rete" documenta topologia e criteri di
   indirizzamento; in "VLAN" registra i segmenti di rete.
6. In "Reti wireless" registra SSID, sicurezza e password delle reti
   Wi-Fi generate presso il cliente.

Le password (credenziali apparati e reti wireless) sono cifrate a
riposo nel database (Fernet, vedi `rete/fields.py` e
`MASTER_ENCRYPTION_KEY` in `.env.example`).

## Deploy

Vedi `deploy/README.md`.
