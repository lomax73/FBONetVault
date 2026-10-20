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
    rack = models.CharField(
        max_length=100, blank=True,
        help_text='Rack o armadio in cui si trova questa sezione, se pertinente (es. "Rack 1", "Armadio B").',
    )
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']

    def __str__(self):
        return self.nome


class TipoApparato(models.Model):
    """Voce configurabile per il menu a discesa 'Tipo apparato' (pagina di
    configurazione), es. Router, Switch, Firewall, Access Point, Server.
    Ogni tipo ha di default solo il nome: gli altri parametri di
    configurazione che un apparato di questo tipo dovrà avere si scelgono
    qui, dal catalogo ParametroDisponibile."""

    nome = models.CharField(max_length=100, unique=True)
    parametri = models.ManyToManyField(
        'ParametroDisponibile', blank=True, related_name='tipi_apparato',
        verbose_name='Parametri di configurazione',
        help_text='Un apparato di questo tipo avrà questi parametri (oltre ai campi base) nella sua scheda.',
    )
    credenziali = models.ManyToManyField(
        'CredenzialeDisponibile', blank=True, related_name='tipi_apparato',
        verbose_name='Credenziali previste',
        help_text='Un apparato di questo tipo avrà queste credenziali già pronte da compilare.',
    )
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
    STATO_ATTIVO = 'attivo'
    STATO_MANUTENZIONE = 'manutenzione'
    STATO_DISMESSO = 'dismesso'
    STATO_CHOICES = [
        (STATO_ATTIVO, 'Attivo'),
        (STATO_MANUTENZIONE, 'In manutenzione'),
        (STATO_DISMESSO, 'Dismesso'),
    ]

    nome = models.CharField(max_length=255, help_text='Nome identificativo, es. "Switch core piano 1".')
    hostname = models.CharField(max_length=255, blank=True)
    marca_modello = models.CharField('Marca / modello', max_length=255, blank=True)
    numero_seriale = models.CharField('Numero seriale', max_length=255, blank=True)
    firmware = models.CharField('Versione firmware', max_length=100, blank=True)
    indirizzo_ip = models.CharField('Indirizzo IP', max_length=100, blank=True)
    indirizzo_mac = models.CharField('Indirizzo MAC', max_length=100, blank=True)
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default=STATO_ATTIVO)
    data_installazione = models.DateField('Data installazione', null=True, blank=True)
    note = models.TextField(blank=True)
    ordine = models.PositiveIntegerField(default=0)
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordine', 'nome']

    def __str__(self):
        return self.nome

    def sync_parametri(self):
        """Allinea i ParametroConfig di questo apparato ai parametri
        previsti dal suo tipo (crea quelli mancanti, rimuove quelli non
        più previsti). Va richiamato ogni volta che l'apparato viene
        salvato o quando cambia l'elenco parametri del tipo. Restituisce
        quante righe ha creato."""
        attese = set(self.tipo.parametri.all()) if self.tipo_id else set()
        esistenti = {p.definizione: p for p in self.parametri.select_related('definizione')}
        for definizione in attese - esistenti.keys():
            self.parametri.create(definizione=definizione)
        for definizione in esistenti.keys() - attese:
            esistenti[definizione].delete()
        return len(attese - esistenti.keys())

    def sync_credenziali(self):
        """Crea le Credenziale (vuote, da compilare) previste dal tipo che
        l'apparato non ha ancora. A differenza dei parametri non toglie mai
        nulla: sono dati sensibili, quindi se il tipo smette di prevedere
        una credenziale quella già inserita resta. Restituisce quante righe
        ha creato."""
        if not self.tipo_id:
            return 0
        presenti = set(self.credenziali.exclude(definizione=None).values_list('definizione_id', flat=True))
        create = 0
        for definizione in self.tipo.credenziali.all():
            if definizione.pk in presenti:
                continue
            self.credenziali.create(
                definizione=definizione, etichetta=definizione.etichetta, titolare=definizione.titolare,
                tipo_accesso=definizione.tipo_accesso, ordine=definizione.ordine,
            )
            create += 1
        return create

    def sync_tipo(self):
        """Parametri e credenziali previsti dal tipo; restituisce quante
        righe nuove sono apparse da compilare."""
        return self.sync_parametri() + self.sync_credenziali()


class ParametroDisponibile(models.Model):
    """Catalogo dei parametri di configurazione aggiuntivi assegnabili a un
    tipo di apparato (es. "IP WAN", "Porta WAN", "N. porte switch
    integrato"), gestito in Configurazione. Un apparato eredita
    automaticamente i parametri del suo tipo: i campi base (hostname, IP,
    MAC, seriale, ...)
    restano invece sempre presenti come campi fissi di Apparato."""

    nome = models.CharField(max_length=255, unique=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'nome']
        verbose_name = 'parametro disponibile'
        verbose_name_plural = 'parametri disponibili'

    def __str__(self):
        return self.nome


class ParametroConfig(models.Model):
    """Valore di un parametro di configurazione aggiuntivo per un apparato
    specifico. Quali parametri sono presenti si sceglie nel form
    dell'apparato, spuntandoli dal catalogo ParametroDisponibile."""

    apparato = models.ForeignKey(Apparato, on_delete=models.CASCADE, related_name='parametri')
    definizione = models.ForeignKey(ParametroDisponibile, on_delete=models.CASCADE, related_name='usi')
    valore = models.TextField(blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['definizione__ordine', 'definizione__nome']
        unique_together = ['apparato', 'definizione']

    def __str__(self):
        return self.definizione.nome


TITOLARE_CLIENTE = 'cliente'
TITOLARE_TECNICO = 'tecnico'
TITOLARE_CHOICES = [
    (TITOLARE_CLIENTE, 'Cliente'),
    (TITOLARE_TECNICO, 'Tecnico di gestione'),
]


ACCESSO_SSH = 'ssh'
ACCESSO_HTTPS = 'https'
ACCESSO_HTTP = 'http'
ACCESSO_TELNET = 'telnet'
ACCESSO_CONSOLE = 'console'
ACCESSO_CLOUD = 'cloud'
ACCESSO_ALTRO = 'altro'
ACCESSO_CHOICES = [
    (ACCESSO_SSH, 'SSH'),
    (ACCESSO_HTTPS, 'HTTPS'),
    (ACCESSO_HTTP, 'HTTP'),
    (ACCESSO_TELNET, 'Telnet'),
    (ACCESSO_CONSOLE, 'Console'),
    (ACCESSO_CLOUD, 'Cloud'),
    (ACCESSO_ALTRO, 'Altro'),
]


class CredenzialeDisponibile(models.Model):
    """Catalogo delle credenziali previste per un tipo di apparato (es.
    "Admin cliente — HTTPS", "Tecnico — SSH"), gestito in Configurazione:
    un apparato eredita dal suo tipo una Credenziale vuota per ognuna."""

    etichetta = models.CharField(max_length=255, unique=True)
    titolare = models.CharField(
        max_length=20, choices=TITOLARE_CHOICES, default=TITOLARE_CLIENTE,
    )
    tipo_accesso = models.CharField('Tipo accesso', max_length=20, choices=ACCESSO_CHOICES, default='ssh')
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'etichetta']
        verbose_name = 'credenziale disponibile'
        verbose_name_plural = 'credenziali disponibili'

    def __str__(self):
        return self.etichetta


class CredenzialeCondivisa(models.Model):
    """Credenziale riusabile del progetto (es. "Tecnico FBO — web admin",
    "Cliente — SSH"): più righe Credenziale di apparati diversi possono
    collegarsi alla stessa, così la password si cambia in un punto solo.
    Servizi con password diverse sono voci diverse; una riga che non si
    collega a nessuna voce tiene username e password propri."""

    progetto = models.ForeignKey(Progetto, on_delete=models.CASCADE, related_name='credenziali_condivise')
    etichetta = models.CharField(max_length=255, help_text='Es. "Tecnico FBO — web admin".')
    titolare = models.CharField(max_length=20, choices=TITOLARE_CHOICES, default=TITOLARE_TECNICO)
    username = models.CharField(max_length=255, blank=True)
    password = EncryptedCharField(blank=True, null=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['titolare', 'etichetta']
        unique_together = ['progetto', 'etichetta']
        verbose_name = 'credenziale condivisa'
        verbose_name_plural = 'credenziali condivise'

    def __str__(self):
        return self.etichetta

    def delete(self, *args, **kwargs):
        """Prima di eliminarla scrive username e password nelle righe che
        la usavano, così nessun apparato resta senza credenziali."""
        for credenziale in self.usi.all():
            credenziale.username = self.username
            credenziale.password = self.password
            credenziale.save(update_fields=['username', 'password'])
        return super().delete(*args, **kwargs)


class Credenziale(models.Model):
    apparato = models.ForeignKey(Apparato, on_delete=models.CASCADE, related_name='credenziali')
    definizione = models.ForeignKey(
        CredenzialeDisponibile, null=True, blank=True, on_delete=models.SET_NULL, related_name='usi',
    )
    condivisa = models.ForeignKey(
        CredenzialeCondivisa, null=True, blank=True, on_delete=models.SET_NULL, related_name='usi',
        verbose_name='Usa credenziale condivisa',
        help_text='Se scelta, username e password sono quelli della credenziale condivisa del progetto.',
    )
    etichetta = models.CharField(max_length=255, blank=True, help_text='Es. "Admin cliente".')
    titolare = models.CharField(max_length=20, choices=TITOLARE_CHOICES, default=TITOLARE_CLIENTE)
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

    @property
    def username_effettivo(self):
        return self.condivisa.username if self.condivisa_id else self.username

    @property
    def password_effettiva(self):
        return self.condivisa.password if self.condivisa_id else self.password

    def __str__(self):
        return f'{self.etichetta or self.get_tipo_accesso_display()} — {self.username_effettivo or "?"}'


class ApparatoAllegato(models.Model):
    """File allegati a un apparato: backup della configurazione o note di
    configurazione libere (es. export, screenshot, PDF)."""

    TIPO_BACKUP = 'backup'
    TIPO_NOTE = 'note'
    TIPO_ALTRO = 'altro'
    TIPO_CHOICES = [
        (TIPO_BACKUP, 'Backup configurazione'),
        (TIPO_NOTE, 'Note di configurazione'),
        (TIPO_ALTRO, 'Altro'),
    ]

    apparato = models.ForeignKey(Apparato, on_delete=models.CASCADE, related_name='allegati')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_BACKUP)
    file = models.FileField(upload_to='apparato_allegati/%Y/%m/')
    descrizione = models.CharField(max_length=255, blank=True)
    caricato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-caricato_il']

    def __str__(self):
        return self.descrizione or self.file.name.rsplit('/', 1)[-1]


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
