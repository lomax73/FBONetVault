from django import forms
from django.forms import formset_factory, inlineformset_factory, modelformset_factory

from . import portal_client
from .models import (
    Apparato,
    ApparatoAllegato,
    Credenziale,
    CredenzialeCondivisa,
    CredenzialeDisponibile,
    ParametroConfig,
    ParametroDisponibile,
    Progetto,
    ReteInfo,
    ReteWireless,
    Sezione,
    TipoApparato,
    Vlan,
)


class ProgettoForm(forms.ModelForm):
    cliente = forms.ChoiceField(label='Cliente')

    class Meta:
        model = Progetto
        fields = ['nome', 'indirizzo', 'descrizione']
        widgets = {'descrizione': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', '— seleziona —')]
        try:
            clienti = portal_client.list_clienti()
        except portal_client.PortalUnavailableError as exc:
            self.fields['cliente'].help_text = (
                f"Impossibile contattare l'anagrafica clienti nel Portale: {exc}"
            )
        else:
            choices += [(c['id'], c['ragione_sociale']) for c in clienti]
        self.fields['cliente'].choices = choices
        if self.instance and self.instance.pk and self.instance.cliente_id:
            self.fields['cliente'].initial = str(self.instance.cliente_id)

    def clean_cliente(self):
        valore = self.cleaned_data['cliente']
        if not valore:
            raise forms.ValidationError('Seleziona un cliente.')
        return valore

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.cliente_id = self.cleaned_data['cliente']
        if commit:
            instance.save()
        return instance


class SezioneForm(forms.ModelForm):
    class Meta:
        model = Sezione
        fields = ['nome', 'rack', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 3})}


class ApparatoForm(forms.ModelForm):
    class Meta:
        model = Apparato
        fields = [
            'sezione', 'tipo', 'collegato_a', 'nome', 'hostname', 'marca_modello', 'numero_seriale', 'firmware',
            'indirizzo_ip', 'indirizzo_mac', 'stato', 'data_installazione', 'note', 'ordine',
        ]
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'data_installazione': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, progetto=None, **kwargs):
        super().__init__(*args, **kwargs)
        progetto = progetto or getattr(self.instance, 'progetto', None)
        if progetto:
            self.fields['sezione'].queryset = Sezione.objects.filter(progetto=progetto)
            # Un solo livello di collegamento (NVR → telecamere): si può
            # collegare solo a un apparato che non sia a sua volta collegato.
            self.fields['collegato_a'].queryset = Apparato.objects.filter(
                progetto=progetto, collegato_a=None,
            ).exclude(pk=self.instance.pk)

    def clean_collegato_a(self):
        padre = self.cleaned_data.get('collegato_a')
        if padre and self.instance.pk and self.instance.collegati.exists():
            raise forms.ValidationError('Questo apparato ha già apparati collegati: non può essere collegato a sua volta.')
        return padre

    nuove_righe = 0

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            self.nuove_righe = instance.sync_tipo()
        return instance


class TelecamereDefaultForm(forms.Form):
    """Valori comuni per l'aggiunta di più telecamere a un NVR (vedi
    views.telecamere_aggiungi): login condivisa o uguale per tutte, a meno
    che la singola riga non ne indichi una propria."""

    ACCESSO_CHOICES = [('http', 'HTTP'), ('https', 'HTTPS')]

    tipo_accesso = forms.ChoiceField(choices=ACCESSO_CHOICES, label='Interfaccia web')
    condivisa = forms.ModelChoiceField(
        queryset=CredenzialeCondivisa.objects.none(), required=False, label='Usa credenziale condivisa',
        help_text='Se scelta, vale per tutte le righe senza login propria.',
    )
    username = forms.CharField(max_length=255, required=False, label='Username per tutte')
    password = forms.CharField(max_length=255, required=False, label='Password per tutte', widget=forms.TextInput)

    def __init__(self, *args, progetto=None, **kwargs):
        super().__init__(*args, **kwargs)
        if progetto:
            self.fields['condivisa'].queryset = CredenzialeCondivisa.objects.filter(progetto=progetto)


class TelecameraRigaForm(forms.Form):
    nome = forms.CharField(max_length=255, required=False)
    indirizzo_ip = forms.CharField(max_length=100, required=False, label='IP')
    marca_modello = forms.CharField(max_length=255, required=False, label='Marca / modello')
    username = forms.CharField(max_length=255, required=False)
    password = forms.CharField(max_length=255, required=False, widget=forms.TextInput)

    def clean(self):
        dati = super().clean()
        if self.has_changed() and not (dati.get('nome') or dati.get('indirizzo_ip')):
            raise forms.ValidationError('Indica almeno il nome o l\'IP della telecamera.')
        return dati


TelecameraRigaFormSet = formset_factory(TelecameraRigaForm, extra=8)


class ParametroConfigForm(forms.ModelForm):
    class Meta:
        model = ParametroConfig
        fields = ['valore', 'note']
        widgets = {'valore': forms.Textarea(attrs={'rows': 2})}


class CredenzialeCondivisaForm(forms.ModelForm):
    class Meta:
        model = CredenzialeCondivisa
        fields = ['etichetta', 'titolare', 'username', 'password', 'note']
        widgets = {
            'password': forms.TextInput(),
            'note': forms.Textarea(attrs={'rows': 2}),
        }


class CredenzialeForm(forms.ModelForm):
    class Meta:
        model = Credenziale
        fields = [
            'etichetta', 'titolare', 'tipo_accesso', 'url_porta', 'condivisa', 'username', 'password', 'note',
            'ordine',
        ]
        widgets = {
            'password': forms.TextInput(),
            'note': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, progetto=None, **kwargs):
        super().__init__(*args, **kwargs)
        if progetto is None and self.instance.apparato_id:
            progetto = self.instance.apparato.progetto
        self.fields['condivisa'].queryset = (
            CredenzialeCondivisa.objects.filter(progetto=progetto) if progetto
            else CredenzialeCondivisa.objects.none()
        )

    def clean(self):
        dati = super().clean()
        condivisa = dati.get('condivisa')
        if condivisa:
            # Username e password stanno solo sulla credenziale condivisa:
            # non si tiene una copia che resterebbe vecchia al primo cambio.
            dati['username'] = ''
            dati['password'] = ''
            dati['titolare'] = condivisa.titolare
        return dati


# Parametri e credenziali di un apparato si compilano nella stessa pagina
# dei campi base (vedi views.ApparatoFormMixin).
ParametroConfigInlineFormSet = inlineformset_factory(
    Apparato, ParametroConfig, form=ParametroConfigForm, extra=0, can_delete=False,
)

CredenzialeInlineFormSet = inlineformset_factory(
    Apparato, Credenziale, form=CredenzialeForm,
    fields=['etichetta', 'titolare', 'tipo_accesso', 'url_porta', 'condivisa', 'username', 'password', 'note'],
    extra=1, can_delete=True,
)


class ApparatoAllegatoForm(forms.ModelForm):
    class Meta:
        model = ApparatoAllegato
        fields = ['tipo', 'file', 'descrizione']


class ReteInfoForm(forms.ModelForm):
    class Meta:
        model = ReteInfo
        fields = ['descrizione']
        widgets = {'descrizione': forms.Textarea(attrs={'rows': 14})}


class VlanForm(forms.ModelForm):
    class Meta:
        model = Vlan
        fields = ['numero', 'nome', 'subnet', 'gateway', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 2})}


class ReteWirelessForm(forms.ModelForm):
    class Meta:
        model = ReteWireless
        fields = ['sezione', 'vlan', 'ssid', 'tipo_sicurezza', 'password', 'banda', 'note', 'ordine']
        widgets = {
            'password': forms.TextInput(),
            'note': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, progetto=None, **kwargs):
        super().__init__(*args, **kwargs)
        progetto = progetto or getattr(self.instance, 'progetto', None)
        if progetto:
            self.fields['sezione'].queryset = Sezione.objects.filter(progetto=progetto)
            self.fields['vlan'].queryset = Vlan.objects.filter(progetto=progetto)


class ImportRigaForm(forms.Form):
    """Una riga della pagina di revisione import apparati (vedi
    views.apparato_import): un host trovato nello scan nmap, da confermare
    ed eventualmente assegnare a sezione/tipo prima di creare l'Apparato."""

    includi = forms.BooleanField(required=False, initial=True, label='Importa')
    nome = forms.CharField(max_length=255, required=False, label='Nome')
    indirizzo_ip = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput)
    indirizzo_mac = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput)
    sezione = forms.ModelChoiceField(queryset=Sezione.objects.none(), required=False, label='Sezione')
    tipo = forms.ModelChoiceField(queryset=TipoApparato.objects.all(), required=False, label='Tipo')

    def __init__(self, *args, progetto=None, **kwargs):
        super().__init__(*args, **kwargs)
        if progetto:
            self.fields['sezione'].queryset = Sezione.objects.filter(progetto=progetto)


ImportRigaFormSet = formset_factory(ImportRigaForm, extra=0)


class TipoApparatoParametriForm(forms.ModelForm):
    class Meta:
        model = TipoApparato
        fields = ['parametri', 'credenziali']
        widgets = {'parametri': forms.CheckboxSelectMultiple, 'credenziali': forms.CheckboxSelectMultiple}
        labels = {'parametri': '', 'credenziali': ''}


TipoApparatoFormSet = modelformset_factory(
    TipoApparato,
    fields=['nome', 'ordine'],
    extra=1,
    can_delete=True,
)

CredenzialeDisponibileFormSet = modelformset_factory(
    CredenzialeDisponibile,
    fields=['etichetta', 'titolare', 'tipo_accesso', 'ordine'],
    extra=1,
    can_delete=True,
)

ParametroDisponibileFormSet = modelformset_factory(
    ParametroDisponibile,
    fields=['nome', 'ordine'],
    extra=1,
    can_delete=True,
)
