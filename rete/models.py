from django.db import models

from .fields import EncryptedCharField


class Progetto(models.Model):
    """Un progetto di configurazione presso un cliente: raggruppa sezioni,
    apparati, schema di rete e reti wireless di un sito/intervento
    specifico. cliente_id fa riferimento all'anagrafica condivisa nel
    Portale FBO (nessuna FK cross-database, risolto a runtime via
    portal_client.py)."""

    nome = models.CharField(max_length=255)
    cliente_id = models.UUIDField(
        help_text="Riferimento al cliente nell'anagrafica condivisa del Portale.",
    )
    indirizzo = models.CharField(
        'Indirizzo / sede', max_length=255, blank=True,
        help_text='Dove si trova fisicamente il sito configurato, se diverso dalla sede del cliente in anagrafica.',
    )
    descrizione = models.TextField(blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creato_il']

    def __str__(self):
        return self.nome


class Sezione(models.Model):
    """Raggruppamento logico/fisico degli apparati di un progetto, es. "Sede
    Milano", "Sala CED", "Piano 2"."""

    progetto = models.ForeignKey(Progetto, on_delete=models.CASCADE, related_name='sezioni')
    nome = models.CharField(max_length=255)
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']

    def __str__(self):
        return self.nome


class TipoApparato(models.Model):
    """Voce configurabile per il menu a discesa 'Tipo apparato' (pagina di
    configurazione), es. Router, Switch, Firewall, Access Point, Server."""

    nome = models.CharField(max_length=100, unique=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']

    def __str__(self):
        return self.nome


class Apparato(models.Model):
    progetto = models.ForeignKey(Progetto, on_delete=models.CASCADE, related_name='apparati')
    sezione = models.ForeignKey(
        Sezione, verbose_name='Sezione', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='apparati',
    )
    tipo = models.ForeignKey(
        TipoApparato, verbose_name='Tipo apparato', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='apparati',
    )
    nome = models.CharField(max_length=255, help_text='Nome identificativo, es. "Switch core piano 1".')
    marca_modello = models.CharField('Marca / modello', max_length=255, blank=True)
    indirizzo_ip = models.CharField('Indirizzo IP', max_length=100, blank=True)
    indirizzo_mac = models.CharField('Indirizzo MAC', max_length=100, blank=True)
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordine', 'nome']

    def __str__(self):
        return self.nome


class ParametroConfig(models.Model):
    """Parametro di configurazione libero (chiave/valore) di un apparato:
    copre tutti i parametri specifici del dispositivo senza dover
    modellare uno schema diverso per ogni tipo di apparato."""

    apparato = models.ForeignKey(Apparato, on_delete=models.CASCADE, related_name='parametri')
    chiave = models.CharField(max_length=255)
    valore = models.TextField(blank=True)
    note = models.CharField(max_length=255, blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'chiave']

    def __str__(self):
        return self.chiave


class Credenziale(models.Model):
    ACCESSO_SSH = 'ssh'
    ACCESSO_HTTPS = 'https'
    ACCESSO_HTTP = 'http'
    ACCESSO_TELNET = 'telnet'
    ACCESSO_CONSOLE = 'console'
    ACCESSO_ALTRO = 'altro'
    ACCESSO_CHOICES = [
        (ACCESSO_SSH, 'SSH'),
        (ACCESSO_HTTPS, 'HTTPS'),
        (ACCESSO_HTTP, 'HTTP'),
        (ACCESSO_TELNET, 'Telnet'),
        (ACCESSO_CONSOLE, 'Console'),
        (ACCESSO_ALTRO, 'Altro'),
    ]

    apparato = models.ForeignKey(Apparato, on_delete=models.CASCADE, related_name='credenziali')
    tipo_accesso = models.CharField('Tipo accesso', max_length=20, choices=ACCESSO_CHOICES, default=ACCESSO_SSH)
    url_porta = models.CharField(
        'URL / porta', max_length=255, blank=True,
        help_text='Es. "https://10.0.0.1:8443" oppure "22".',
    )
    username = models.CharField(max_length=255, blank=True)
    password = EncryptedCharField(blank=True, null=True)
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'id']
        verbose_name_plural = 'credenziali'

    def __str__(self):
        return f'{self.get_tipo_accesso_display()} — {self.username or "?"}'


class ReteInfo(models.Model):
    """Descrizione libera di come è strutturata la rete di un progetto
    (topologia, criteri di indirizzamento, note). Una sola voce per
    progetto."""

    progetto = models.OneToOneField(Progetto, on_delete=models.CASCADE, related_name='rete_info')
    descrizione = models.TextField(blank=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Rete — {self.progetto}'


class Vlan(models.Model):
    progetto = models.ForeignKey(Progetto, on_delete=models.CASCADE, related_name='vlan_set')
    numero = models.PositiveIntegerField('VLAN ID')
    nome = models.CharField(max_length=255, blank=True)
    subnet = models.CharField(max_length=100, blank=True, help_text='Es. "10.0.10.0/24".')
    gateway = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'numero']
        verbose_name = 'VLAN'
        verbose_name_plural = 'VLAN'

    def __str__(self):
        return f'VLAN {self.numero}' + (f' — {self.nome}' if self.nome else '')


class ReteWireless(models.Model):
    BANDA_24 = '2.4'
    BANDA_5 = '5'
    BANDA_6 = '6'
    BANDA_DUAL = 'dual'
    BANDA_CHOICES = [
        (BANDA_24, '2.4 GHz'),
        (BANDA_5, '5 GHz'),
        (BANDA_6, '6 GHz'),
        (BANDA_DUAL, 'Dual band'),
    ]

    SICUREZZA_WPA2_PERSONAL = 'wpa2_personal'
    SICUREZZA_WPA2_ENTERPRISE = 'wpa2_enterprise'
    SICUREZZA_WPA3 = 'wpa3'
    SICUREZZA_APERTA = 'aperta'
    SICUREZZA_CHOICES = [
        (SICUREZZA_WPA2_PERSONAL, 'WPA2 Personal'),
        (SICUREZZA_WPA2_ENTERPRISE, 'WPA2 Enterprise'),
        (SICUREZZA_WPA3, 'WPA3'),
        (SICUREZZA_APERTA, 'Aperta'),
    ]

    progetto = models.ForeignKey(Progetto, on_delete=models.CASCADE, related_name='reti_wireless')
    sezione = models.ForeignKey(
        Sezione, verbose_name='Sezione', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reti_wireless',
    )
    vlan = models.ForeignKey(
        Vlan, verbose_name='VLAN', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reti_wireless',
    )
    ssid = models.CharField('SSID', max_length=255)
    tipo_sicurezza = models.CharField(
        'Sicurezza', max_length=20, choices=SICUREZZA_CHOICES, default=SICUREZZA_WPA2_PERSONAL,
    )
    password = EncryptedCharField(blank=True, null=True)
    banda = models.CharField(max_length=10, choices=BANDA_CHOICES, blank=True)
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'ssid']
        verbose_name = 'rete wireless'
        verbose_name_plural = 'reti wireless'

    def __str__(self):
        return self.ssid
