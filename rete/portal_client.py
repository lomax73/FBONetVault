"""Client per l'anagrafica clienti condivisa, esposta dal Portale FBO
(clienti/api/internal/). L'app salva solo client_id (UUID) e risolve
nome/indirizzo chiamando questa API in tempo reale — nessuna FK
cross-database (vedi memoria project-multi-app-portal-architecture).
Stesso client usato in FBORackReport/cablaggio/portal_client.py e
FBOPreventivi/preventivi/portal_client.py.
"""

import requests
from django.conf import settings

TIMEOUT = 5


class PortalUnavailableError(Exception):
    """Il Portale non ha risposto correttamente (giù, token sbagliato,
    non configurato)."""


def _base_url():
    base = getattr(settings, 'PORTAL_INTERNAL_BASE_URL', '')
    if not base:
        raise PortalUnavailableError('PORTAL_INTERNAL_BASE_URL non configurato.')
    return base.rstrip('/') + '/api/internal/clienti/'


def _headers():
    return {'Authorization': f'Token {settings.PORTAL_API_TOKEN}'}


def list_clienti():
    """Tutti i clienti dell'anagrafica condivisa, come lista di dict."""
    try:
        resp = requests.get(_base_url(), headers=_headers(), timeout=TIMEOUT, verify=False)
    except requests.RequestException as exc:
        raise PortalUnavailableError(str(exc)) from exc
    if resp.status_code != 200:
        raise PortalUnavailableError(f'HTTP {resp.status_code}: {resp.text[:200]}')
    return resp.json().get('clienti', [])


def get_cliente(cliente_id):
    """Un cliente per id, o None se non esiste più nell'anagrafica."""
    try:
        resp = requests.get(f'{_base_url()}{cliente_id}/', headers=_headers(), timeout=TIMEOUT, verify=False)
    except requests.RequestException as exc:
        raise PortalUnavailableError(str(exc)) from exc
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise PortalUnavailableError(f'HTTP {resp.status_code}: {resp.text[:200]}')
    return resp.json()
