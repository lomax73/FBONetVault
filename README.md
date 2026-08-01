# FBONetVault

App della famiglia FBO per raccogliere in un unico posto tutti i
parametri di configurazione della rete e dei server dei clienti presso
cui si interviene. Il lavoro è organizzato per **progetti**: ogni
progetto ha un nome, un indirizzo/sede, una descrizione ed è collegato a
un cliente dell'anagrafica condivisa del Portale FBO. All'interno di un
progetto si gestiscono apparati (router, switch, firewall, access
point, server, ...) organizzati per sezione e tipo, i relativi
parametri di configurazione e credenziali di accesso, la struttura
della rete (VLAN e descrizione della topologia) e le reti wireless con
le relative credenziali.

## Sviluppo locale

```
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env   # valorizzare almeno MASTER_ENCRYPTION_KEY (vedi commento nel file)
venv/bin/python manage.py migrate
venv/bin/python manage.py createsuperuser
venv/bin/python manage.py runserver
```

Il picker cliente nel form progetto dipende dall'anagrafica clienti
condivisa nel Portale FBO — serve un'istanza del Portale raggiungibile
(vedi `PORTAL_INTERNAL_BASE_URL` in `.env.example`). Senza Portale
configurato, l'app parte comunque ma la creazione di un progetto mostra
un errore nel picker cliente.

## Flusso

1. Da "Progetti" crea un nuovo progetto: nome, indirizzo/sede,
   descrizione e cliente (dall'anagrafica del Portale).
2. Nella scheda progetto crea le sezioni (sedi/aree interne, es. "Sala
   CED").
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
