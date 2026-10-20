"""Icone (SVG inline, stile a tratto 24x24) per i tipi di apparato.

I tipi sono liberi (si creano in Configurazione), quindi l'icona si sceglie
dalle parole nel nome; per quelli non riconosciuti c'è un'icona generica."""

import re

ICONE = {
    'router': '<rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 17h.01M11 17h.01M7 14V9M17 14V9"/>',
    'switch': '<rect x="2" y="9" width="20" height="8" rx="1"/><path d="M6 13h.01M10 13h.01M14 13h.01M18 13h.01"/>',
    'firewall': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    'ap': '<path d="M5 12a10 10 0 0 1 14 0M8.5 15.5a5 5 0 0 1 7 0"/><circle cx="12" cy="19" r="1"/>',
    'server': '<rect x="3" y="3" width="18" height="7" rx="1"/><rect x="3" y="14" width="18" height="7" rx="1"/><path d="M7 6.5h.01M7 17.5h.01"/>',
    'nvr': '<rect x="2" y="6" width="20" height="12" rx="1"/><circle cx="7" cy="12" r="2"/><path d="M13 10h6M13 14h4"/>',
    'telecamera': '<rect x="2" y="7" width="13" height="10" rx="1"/><path d="M15 11l7-3v8l-7-3"/>',
    'nas': '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    'ups': '<rect x="2" y="8" width="18" height="9" rx="1"/><path d="M22 11v3M10 10l-2 3h4l-2 3"/>',
    'stampante': '<path d="M6 9V3h12v6M6 18H4v-7h16v7h-2"/><rect x="6" y="14" width="12" height="7"/>',
    'pc': '<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M8 20h8M12 16v4"/>',
    'telefono': '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    'generico': '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/>',
}

# Ordine significativo: la prima regola che corrisponde vince (es. "NVR"
# prima di "server", "telecamera" prima di "cam" generico).
REGOLE = [
    ('nvr', r'\b(nvr|dvr|videoregistrat)'),
    ('telecamera', r'telecam|camera|\bcam\b|videosorveglianza'),
    ('ap', r'access\s*point|\bap\b|wi-?fi|wireless'),
    ('firewall', r'firewall|\butm\b'),
    ('router', r'router|gateway|modem'),
    ('switch', r'switch'),
    ('nas', r'\bnas\b|storage|\bsan\b'),
    ('server', r'server|hypervisor|proxmox|\bvm\b|esx'),
    ('ups', r'\bups\b|continuit|batteria'),
    ('stampante', r'stampant|printer|plotter'),
    ('telefono', r'telefon|voip|pbx|centralino'),
    ('pc', r'\bpc\b|computer|workstation|desktop|notebook|laptop|client'),
]


def chiave_icona(nome_tipo):
    nome = (nome_tipo or '').lower()
    for chiave, pattern in REGOLE:
        if re.search(pattern, nome):
            return chiave
    return 'generico'
