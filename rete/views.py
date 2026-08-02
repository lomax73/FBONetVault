from dataclasses import dataclass

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.formsets import DELETION_FIELD_NAME
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from . import portal_client
from .forms import (
    ApparatoAllegatoForm,
    ApparatoForm,
    CredenzialeForm,
    ParametroConfigForm,
    ParametroDisponibileFormSet,
    ProgettoForm,
    ReteInfoForm,
    ReteWirelessForm,
    SezioneForm,
    TipoApparatoFormSet,
    VlanForm,
)
from .models import (
    Apparato,
    ApparatoAllegato,
    Credenziale,
    ParametroConfig,
    ParametroDisponibile,
    Progetto,
    ReteInfo,
    ReteWireless,
    Sezione,
    TipoApparato,
    Vlan,
)


@dataclass
class ClienteInfo:
    """Dati del cliente risolti dall'anagrafica condivisa nel Portale."""

    id: str = ''
    ragione_sociale: str = ''
    indirizzo: str = ''
    cap: str = ''
    citta: str = ''
    provincia: str = ''
    piva: str = ''
    email: str = ''
    telefono: str = ''
    note: str = ''

    def __str__(self):
        return self.ragione_sociale


def _attach_clienti(progetti):
    """Risolve cliente_id -> dati cliente per una lista di progetti con UNA
    sola chiamata al Portale (non una per riga). Se il Portale non risponde
    o il cliente non esiste più, fallback esplicito invece di un errore."""
    progetti = list(progetti)
    try:
        by_id = {c['id']: c for c in portal_client.list_clienti()}
    except portal_client.PortalUnavailableError:
        by_id = {}
    for progetto in progetti:
        dati = by_id.get(str(progetto.cliente_id))
        progetto.cliente = ClienteInfo(**dati) if dati else ClienteInfo(ragione_sociale='Cliente non disponibile')
    return progetti


# --- Progetti ---------------------------------------------------------

class ProgettoListView(LoginRequiredMixin, ListView):
    model = Progetto
    template_name = 'rete/progetto_list.html'
    context_object_name = 'progetti'

    def get_queryset(self):
        return _attach_clienti(super().get_queryset())


class ProgettoDetailView(LoginRequiredMixin, DetailView):
    """Scheda progetto: dashboard con sezioni, apparati, VLAN, reti
    wireless e descrizione della rete."""

    model = Progetto
    template_name = 'rete/progetto_detail.html'
    context_object_name = 'progetto'

    def get_object(self, queryset=None):
        progetto = super().get_object(queryset)
        _attach_clienti([progetto])
        return progetto

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rete_info, _ = ReteInfo.objects.get_or_create(progetto=self.object)
        context['sezioni'] = self.object.sezioni.all()
        context['apparati'] = self.object.apparati.select_related('sezione', 'tipo')
        context['vlan_list'] = self.object.vlan_set.all()
        context['reti_wireless'] = self.object.reti_wireless.select_related('sezione', 'vlan')
        context['rete_info'] = rete_info
        return context


class ProgettoCreateView(LoginRequiredMixin, CreateView):
    model = Progetto
    form_class = ProgettoForm
    template_name = 'rete/progetto_form.html'

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.pk])


class ProgettoUpdateView(LoginRequiredMixin, UpdateView):
    model = Progetto
    form_class = ProgettoForm
    template_name = 'rete/progetto_form.html'

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.pk])


class ProgettoDeleteView(LoginRequiredMixin, DeleteView):
    model = Progetto
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'progetto'}
    success_url = '/'


# --- Sezioni ---------------------------------------------------------------

class ProgettoScopedCreateMixin:
    """Aggiunge progetto_pk (dall'URL) al contesto template e imposta la FK
    progetto sull'istanza salvata, per i CreateView di oggetti che
    appartengono a un progetto."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progetto_pk'] = self.kwargs['progetto_pk']
        return context

    def form_valid(self, form):
        form.instance.progetto_id = self.kwargs['progetto_pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.kwargs['progetto_pk']])


class SezioneCreateView(LoginRequiredMixin, ProgettoScopedCreateMixin, CreateView):
    model = Sezione
    form_class = SezioneForm
    template_name = 'rete/sezione_form.html'


class SezioneUpdateView(LoginRequiredMixin, UpdateView):
    model = Sezione
    form_class = SezioneForm
    template_name = 'rete/sezione_form.html'

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


class SezioneDeleteView(LoginRequiredMixin, DeleteView):
    model = Sezione
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'sezione'}

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


# --- Apparati ----------------------------------------------------------

class ApparatoCreateView(LoginRequiredMixin, ProgettoScopedCreateMixin, CreateView):
    model = Apparato
    form_class = ApparatoForm
    template_name = 'rete/apparato_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['progetto'] = Progetto.objects.get(pk=self.kwargs['progetto_pk'])
        return kwargs

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.pk])


class ApparatoUpdateView(LoginRequiredMixin, UpdateView):
    model = Apparato
    form_class = ApparatoForm
    template_name = 'rete/apparato_form.html'

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.pk])


class ApparatoDeleteView(LoginRequiredMixin, DeleteView):
    model = Apparato
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'apparato'}

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


class ApparatoDetailView(LoginRequiredMixin, DetailView):
    model = Apparato
    template_name = 'rete/apparato_detail.html'
    context_object_name = 'apparato'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parametri'] = self.object.parametri.select_related('definizione')
        context['credenziali'] = self.object.credenziali.all()
        context['allegati'] = self.object.allegati.all()
        context['allegato_form'] = ApparatoAllegatoForm()
        return context


# --- Parametri configurazione -----------------------------------------
# Quali parametri esistono per un apparato si sceglie nel form apparato
# (spuntandoli dal catalogo ParametroDisponibile, gestito in
# Configurazione): qui si modifica solo il valore di un parametro già
# selezionato.

class ParametroConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = ParametroConfig
    form_class = ParametroConfigForm
    template_name = 'rete/parametro_form.html'

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.apparato_id])


class ParametroConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = ParametroConfig
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'parametro'}

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.apparato_id])


# --- Credenziali ---------------------------------------------------------

class CredenzialeCreateView(LoginRequiredMixin, CreateView):
    model = Credenziale
    form_class = CredenzialeForm
    template_name = 'rete/credenziale_form.html'

    def form_valid(self, form):
        form.instance.apparato_id = self.kwargs['apparato_pk']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apparato_pk'] = self.kwargs['apparato_pk']
        return context

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.kwargs['apparato_pk']])


class CredenzialeUpdateView(LoginRequiredMixin, UpdateView):
    model = Credenziale
    form_class = CredenzialeForm
    template_name = 'rete/credenziale_form.html'

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.apparato_id])


class CredenzialeDeleteView(LoginRequiredMixin, DeleteView):
    model = Credenziale
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'credenziale'}

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.apparato_id])


# --- Allegati (backup / note di configurazione) ---------------------------

class ApparatoAllegatoCreateView(LoginRequiredMixin, CreateView):
    model = ApparatoAllegato
    form_class = ApparatoAllegatoForm
    template_name = 'rete/allegato_form.html'

    def form_valid(self, form):
        form.instance.apparato_id = self.kwargs['apparato_pk']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apparato_pk'] = self.kwargs['apparato_pk']
        return context

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.kwargs['apparato_pk']])


class ApparatoAllegatoDeleteView(LoginRequiredMixin, DeleteView):
    model = ApparatoAllegato
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'allegato'}

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.apparato_id])


# --- Rete (descrizione topologia + VLAN) --------------------------------

class ReteInfoUpdateView(LoginRequiredMixin, UpdateView):
    model = ReteInfo
    form_class = ReteInfoForm
    template_name = 'rete/rete_info_form.html'

    def get_object(self, queryset=None):
        rete_info, _ = ReteInfo.objects.get_or_create(progetto_id=self.kwargs['progetto_pk'])
        return rete_info

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.kwargs['progetto_pk']])


class VlanCreateView(LoginRequiredMixin, ProgettoScopedCreateMixin, CreateView):
    model = Vlan
    form_class = VlanForm
    template_name = 'rete/vlan_form.html'


class VlanUpdateView(LoginRequiredMixin, UpdateView):
    model = Vlan
    form_class = VlanForm
    template_name = 'rete/vlan_form.html'

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


class VlanDeleteView(LoginRequiredMixin, DeleteView):
    model = Vlan
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'VLAN'}

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


# --- Reti wireless -------------------------------------------------------

class ReteWirelessCreateView(LoginRequiredMixin, ProgettoScopedCreateMixin, CreateView):
    model = ReteWireless
    form_class = ReteWirelessForm
    template_name = 'rete/wireless_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['progetto'] = Progetto.objects.get(pk=self.kwargs['progetto_pk'])
        return kwargs


class ReteWirelessUpdateView(LoginRequiredMixin, UpdateView):
    model = ReteWireless
    form_class = ReteWirelessForm
    template_name = 'rete/wireless_form.html'

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


class ReteWirelessDeleteView(LoginRequiredMixin, DeleteView):
    model = ReteWireless
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'rete wireless'}

    def get_success_url(self):
        return reverse('progetto-detail', args=[self.object.progetto_id])


# --- Configurazione (tipi apparato) ---------------------------------------

@login_required
def configurazione(request):
    if request.method == 'POST':
        tipo_formset = TipoApparatoFormSet(request.POST, prefix='tipoapparato', queryset=TipoApparato.objects.all())
        parametro_formset = ParametroDisponibileFormSet(
            request.POST, prefix='parametrodisponibile', queryset=ParametroDisponibile.objects.all(),
        )
        if tipo_formset.is_valid() and parametro_formset.is_valid():
            protetti = []
            for form in parametro_formset.deleted_forms:
                definizione = form.instance
                if definizione.pk and definizione.tipi_apparato.exists():
                    protetti.append(definizione.nome)
                    form.cleaned_data[DELETION_FIELD_NAME] = False
            if protetti:
                # deleted_forms è una cached_property: senza invalidarla,
                # save() userebbe comunque la lista calcolata sopra, prima
                # della correzione di cleaned_data appena fatta.
                del parametro_formset._deleted_form_indexes
            tipo_formset.save()
            parametro_formset.save()
            for apparato in Apparato.objects.select_related('tipo'):
                apparato.sync_parametri()
            if protetti:
                messages.error(
                    request,
                    'Non eliminabili perché usati in almeno una tipologia di apparato: '
                    + ', '.join(protetti) + '. Rimuovili prima dalla tipologia.',
                )
            messages.success(request, 'Configurazione aggiornata.')
            return redirect('configurazione')
    else:
        tipo_formset = TipoApparatoFormSet(prefix='tipoapparato', queryset=TipoApparato.objects.all())
        parametro_formset = ParametroDisponibileFormSet(
            prefix='parametrodisponibile', queryset=ParametroDisponibile.objects.all(),
        )
    return render(request, 'rete/configurazione.html', {
        'tipo_formset': tipo_formset,
        'parametro_formset': parametro_formset,
    })
