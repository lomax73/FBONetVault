from django import forms
from django.forms import modelformset_factory

from . import portal_client
from .models import Apparato, Credenziale, ParametroConfig, Progetto, ReteInfo, ReteWireless, Sezione, TipoApparato, Vlan


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
        fields = ['nome', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 3})}


class ApparatoForm(forms.ModelForm):
    class Meta:
        model = Apparato
        fields = ['sezione', 'tipo', 'nome', 'marca_modello', 'indirizzo_ip', 'indirizzo_mac', 'note', 'ordine']
        widgets = {'note': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, progetto=None, **kwargs):
        super().__init__(*args, **kwargs)
        progetto = progetto or getattr(self.instance, 'progetto', None)
        if progetto:
            self.fields['sezione'].queryset = Sezione.objects.filter(progetto=progetto)


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


TipoApparatoFormSet = modelformset_factory(
    TipoApparato,
    fields=['nome', 'ordine'],
    extra=1,
    can_delete=True,
)
