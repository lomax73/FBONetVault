"""Parsing dell'output XML di nmap (nmap -oX) per l'import guidato degli
apparati in un progetto. Vedi rete/views.apparato_import. Usa defusedxml
invece di xml.etree diretto perché il file arriva da upload utente."""

import defusedxml.ElementTree as ET


class NmapImportError(Exception):
    pass


def parse_nmap_xml(fileobj):
    """Ritorna una lista di dict {ip, mac, vendor, hostname} per ogni host
    con stato 'up' trovato nel file."""
    try:
        root = ET.parse(fileobj).getroot()
    except Exception as exc:
        raise NmapImportError('file XML non valido o non leggibile') from exc
    if root.tag != 'nmaprun':
        raise NmapImportError("non sembra un output di 'nmap -oX'")

    risultati = []
    for host in root.findall('host'):
        status = host.find('status')
        if status is not None and status.get('state') != 'up':
            continue
        ip = mac = vendor = hostname = ''
        for address in host.findall('address'):
            addrtype = address.get('addrtype')
            if addrtype in ('ipv4', 'ipv6'):
                ip = address.get('addr', '')
            elif addrtype == 'mac':
                mac = address.get('addr', '')
                vendor = address.get('vendor', '')
        hostnames = host.find('hostnames')
        if hostnames is not None:
            hostname_el = hostnames.find('hostname')
            if hostname_el is not None:
                hostname = hostname_el.get('name', '')
        if ip:
            risultati.append({'ip': ip, 'mac': mac, 'vendor': vendor, 'hostname': hostname})
    return risultati
