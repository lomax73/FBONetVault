# Deploy sul VPS

Stesso pattern già in uso per MKRemote, il Portale, Collaudi Fibra,
FBOPreventivi e Report Rack (repo separato, utente di sistema dedicato,
venv proprio). Al momento nessun dominio è configurato sul VPS: si usa
l'IP nudo su una porta dedicata (vedi
`nginx-netvault-ip-provisional.conf`), da sostituire con un sottodominio
(`nginx-netvault.conf`) quando ci sarà un dominio reale.

## Provisioning iniziale (una tantum)

```
# da root sul VPS
adduser --system --group --home /opt/netvault netvault
mkdir -p /opt/netvault/app
chown netvault:netvault /opt/netvault/app

sudo -u netvault git clone https://github.com/lomax73/FBONetVault.git /opt/netvault/app
cd /opt/netvault/app
sudo -u netvault python3 -m venv venv
sudo -u netvault venv/bin/pip install -r requirements.txt

cp .env.example .env   # poi valorizzare DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, INTERNAL_API_TOKEN,
                        # MASTER_ENCRYPTION_KEY, PORTAL_INTERNAL_BASE_URL=https://127.0.0.1:8443,
                        # PORTAL_API_TOKEN, PORTAL_PUBLIC_URL
                        # DJANGO_DEBUG=false — .env.example lo lascia a "true", NON dimenticarlo:
                        # con DEBUG=True qualunque eccezione espone MASTER_ENCRYPTION_KEY in
                        # chiaro, con cui si decifrano le credenziali di TUTTI gli apparati clienti
sudo -u netvault venv/bin/python manage.py migrate
sudo -u netvault venv/bin/python manage.py collectstatic --noinput
sudo -u netvault venv/bin/python manage.py createsuperuser
mkdir -p /opt/netvault/app/media && chown netvault:netvault /opt/netvault/app/media

cp deploy/netvault-web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now netvault-web.service

# Certificato self-signed (IP nudo, nessun dominio):
mkdir -p /etc/ssl/netvault
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/ssl/netvault/selfsigned.key \
    -out /etc/ssl/netvault/selfsigned.crt \
    -subj "/CN=94.177.161.127"

cp deploy/nginx-netvault-ip-provisional.conf /etc/nginx/sites-available/netvault
ln -s /etc/nginx/sites-available/netvault /etc/nginx/sites-enabled/netvault
nginx -t && systemctl reload nginx
ufw allow 8447/tcp comment 'FBONetVault HTTPS'
```

Ricorda anche: `chmod 751 /opt/netvault` (come per le altre app) perché
Nginx/www-data possa attraversare la home e servire `staticfiles/`.

## Chiave di cifratura delle credenziali

`MASTER_ENCRYPTION_KEY` cifra a riposo (Fernet) le password degli
apparati e delle reti wireless (vedi `rete/fields.py`). **Non va mai
rigenerata dopo il primo avvio**: le credenziali già salvate
diventerebbero illeggibili. Farne un backup separato dal DB (es. gestore
password del team), non solo nel `.env` sul VPS.

## API interna di gestione utenti (per il Portale)

Come per le altre app, questa app espone `accounts/` sotto
`api/internal/` per permettere al Portale FBO di creare/modificare/
eliminare utenti da remoto. **Va esposta solo in locale**, mai
pubblicamente — il location block dedicato è già incluso in
`nginx-netvault-ip-provisional.conf`, prima di quello generico
`location /`.

1. `INTERNAL_API_TOKEN` va già valorizzato in `.env` (vedi sopra).
2. `systemctl restart netvault-web.service` dopo aver aggiornato `.env`.
3. Configurare lo stesso token nel Portale (admin → AppLink → nuovo
   record "FBONetVault", campo "API token"), insieme a
   `internal_base_url = https://127.0.0.1:8447`.

## Anagrafica clienti condivisa (dal Portale)

Sezioni, apparati, VLAN e reti wireless salvano solo `cliente_id` (UUID)
e si risolvono in tempo reale chiamando l'API di sola lettura del
Portale (`clienti/api/internal/clienti/`), stesso schema HTTP della
gestione utenti sopra ma in direzione opposta (qui è questa app a
chiamare il Portale). Configurare in `.env`:
- `PORTAL_INTERNAL_BASE_URL` (es. `https://127.0.0.1:8443`, l'URL
  loopback del Portale, non quello pubblico)
- `PORTAL_API_TOKEN` (stesso valore di `INTERNAL_API_TOKEN` nel `.env`
  del Portale)
- `PORTAL_PUBLIC_URL` (solo per il link "Clienti (Portale)" in sidebar)

Se il Portale non risponde, l'elenco clienti mostra un errore invece di
bloccarsi.

## Deploy di un aggiornamento

```
ssh mkremote-vps
cd /opt/netvault/app
sudo -u netvault git pull origin main
sudo -u netvault venv/bin/pip install -r requirements.txt
sudo -u netvault venv/bin/python manage.py migrate
sudo -u netvault venv/bin/python manage.py collectstatic --noinput
systemctl restart netvault-web.service
```
