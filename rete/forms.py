from django import forms
from django.forms import modelformset_factory

from . import portal_client
from .models import Apparato, Credenziale, ParametroConfig, ReteInfo, ReteWireless, Sezione, TipoApparato, Vlan


class ClienteScopedForm(forms.ModelForm):
    """Base per i form che appartengono a un cliente dell'anagrafica
    condivisa: il cliente non è scelto nel form (arriva dall'URL), viene
    impostato in save()."""

    def __init__(self, *args, cliente_id=None, **kwargs):
        self._cliente_id = cliente_id
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self._cliente_id:
            instance.cliente_id = self._cliente_id
        if commit:
            instance.save()
        return instance


class SezioneForm(ClienteScopedForm):
    class Meta:
        model = Sezione
        fields = ['nome', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 3})}


class ApparatoForm(ClienteScopedForm):
    class Meta:
        model = Apparato
        fields = ['sezione', 'tipo', 'nome', 'marca_modello', 'indirizzo_ip', 'indirizzo_mac', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, cliente_id=None, **kwargs):
        super().__init__(*args, cliente_id=cliente_id, **kwargs)
        if cliente_id:
            self.fields['sezione'].queryset = Sezione.objects.filter(cliente_id=cliente_id)


class ParametroConfigForm(forms.ModelForm):
    class Meta:
        model = ParametroConfig
        fields = ['chiave', 'valore', 'note', 'ordine']
        widgets = {'valore': forms.Textarea(attrs={'rows': 2})}


class CredenzialeForm(forms.ModelForm):
    class Meta:
        model = Credenziale
        fields = ['tipo_accesso', 'url_porta', 'username', 'password', 'note', 'ordine']
        widgets = {
            'password': forms.TextInput(),
            'note': forms.Textarea(attrs={'rows': 2}),
        }


class ReteInfoForm(forms.ModelForm):
    class Meta:
        model = ReteInfo
        fields = ['descrizione']
        widgets = {'descrizione': forms.Textarea(attrs={'rows': 14})}


class VlanForm(ClienteScopedForm):
    class Meta:
        model = Vlan
        fields = ['numero', 'nome', 'subnet', 'gateway', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 2})}


class ReteWirelessForm(ClienteScopedForm):
    class Meta:
        model = ReteWireless
        fields = ['sezione', 'vlan', 'ssid', 'tipo_sicurezza', 'password', 'banda', 'note', 'ordine']
        widgets = {
            'password': forms.TextInput(),
            'note': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, cliente_id=None, **kwargs):
        super().__init__(*args, cliente_id=cliente_id, **kwargs)
        if cliente_id:
            self.fields['sezione'].queryset = Sezione.objects.filter(cliente_id=cliente_id)
            self.fields['vlan'].queryset = Vlan.objects.filter(cliente_id=cliente_id)


TipoApparatoFormSet = modelformset_factory(
    TipoApparato,
    fields=['nome', 'ordine'],
    extra=1,
    can_delete=True,
)


def clienti_choices():
    """Lista (id, ragione_sociale) dei clienti dell'anagrafica condivisa,
    per popolare picker altrove. Solleva PortalUnavailableError se il
    Portale non risponde."""
    return [(c['id'], c['ragione_sociale']) for c in portal_client.list_clienti()]
