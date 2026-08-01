from dataclasses import dataclass

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from . import portal_client
from .forms import (
    ApparatoForm,
    CredenzialeForm,
    ParametroConfigForm,
    ReteInfoForm,
    ReteWirelessForm,
    SezioneForm,
    TipoApparatoFormSet,
    VlanForm,
)
from .models import Apparato, Credenziale, ParametroConfig, ReteInfo, ReteWireless, Sezione, TipoApparato, Vlan


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


def _get_cliente(cliente_id):
    try:
        dati = portal_client.get_cliente(cliente_id)
    except portal_client.PortalUnavailableError:
        return ClienteInfo(id=str(cliente_id), ragione_sociale='Portale non raggiungibile')
    if dati is None:
        return ClienteInfo(id=str(cliente_id), ragione_sociale='Cliente non disponibile')
    return ClienteInfo(**dati)


# --- Clienti --------------------------------------------------------------

class ClienteListView(LoginRequiredMixin, ListView):
    """Elenco clienti dell'anagrafica condivisa del Portale: punto di
    ingresso per raggiungere la scheda di configurazione di ciascuno."""

    template_name = 'rete/cliente_list.html'

    def get(self, request, *args, **kwargs):
        errore = None
        try:
            clienti = [ClienteInfo(**c) for c in portal_client.list_clienti()]
        except portal_client.PortalUnavailableError as exc:
            clienti = []
            errore = str(exc)
        return render(request, self.template_name, {'clienti': clienti, 'errore_portale': errore})


class ClienteDetailView(LoginRequiredMixin, DetailView):
    """Scheda cliente: dashboard con sezioni, apparati, VLAN, reti wireless
    e descrizione della rete."""

    template_name = 'rete/cliente_detail.html'

    def get(self, request, *args, **kwargs):
        cliente_id = kwargs['cliente_id']
        cliente = _get_cliente(cliente_id)
        rete_info, _ = ReteInfo.objects.get_or_create(cliente_id=cliente_id)
        context = {
            'cliente': cliente,
            'cliente_id': cliente_id,
            'sezioni': Sezione.objects.filter(cliente_id=cliente_id),
            'apparati': Apparato.objects.filter(cliente_id=cliente_id).select_related('sezione', 'tipo'),
            'vlan_list': Vlan.objects.filter(cliente_id=cliente_id),
            'reti_wireless': ReteWireless.objects.filter(cliente_id=cliente_id).select_related('sezione', 'vlan'),
            'rete_info': rete_info,
        }
        return render(request, self.template_name, context)


class ClienteScopedCreateMixin:
    """Aggiunge cliente_id (dall'URL) ai form kwargs e al contesto template,
    per i CreateView di oggetti che appartengono a un cliente."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente_id'] = self.kwargs['cliente_id']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cliente_id'] = self.kwargs['cliente_id']
        return context

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.kwargs['cliente_id']])


# --- Sezioni ---------------------------------------------------------------

class SezioneCreateView(LoginRequiredMixin, ClienteScopedCreateMixin, CreateView):
    model = Sezione
    form_class = SezioneForm
    template_name = 'rete/sezione_form.html'


class SezioneUpdateView(LoginRequiredMixin, UpdateView):
    model = Sezione
    form_class = SezioneForm
    template_name = 'rete/sezione_form.html'

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


class SezioneDeleteView(LoginRequiredMixin, DeleteView):
    model = Sezione
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'sezione'}

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


# --- Apparati ----------------------------------------------------------

class ApparatoCreateView(LoginRequiredMixin, ClienteScopedCreateMixin, CreateView):
    model = Apparato
    form_class = ApparatoForm
    template_name = 'rete/apparato_form.html'

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.pk])


class ApparatoUpdateView(LoginRequiredMixin, UpdateView):
    model = Apparato
    form_class = ApparatoForm

    template_name = 'rete/apparato_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente_id'] = self.object.cliente_id
        return kwargs

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.object.pk])


class ApparatoDeleteView(LoginRequiredMixin, DeleteView):
    model = Apparato
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'apparato'}

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


class ApparatoDetailView(LoginRequiredMixin, DetailView):
    model = Apparato
    template_name = 'rete/apparato_detail.html'
    context_object_name = 'apparato'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parametri'] = self.object.parametri.all()
        context['credenziali'] = self.object.credenziali.all()
        return context


# --- Parametri configurazione -----------------------------------------

class ParametroConfigCreateView(LoginRequiredMixin, CreateView):
    model = ParametroConfig
    form_class = ParametroConfigForm
    template_name = 'rete/parametro_form.html'

    def form_valid(self, form):
        form.instance.apparato_id = self.kwargs['apparato_pk']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apparato_pk'] = self.kwargs['apparato_pk']
        return context

    def get_success_url(self):
        return reverse('apparato-detail', args=[self.kwargs['apparato_pk']])


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


# --- Rete (descrizione topologia + VLAN) --------------------------------

class ReteInfoUpdateView(LoginRequiredMixin, UpdateView):
    model = ReteInfo
    form_class = ReteInfoForm
    template_name = 'rete/rete_info_form.html'

    def get_object(self, queryset=None):
        rete_info, _ = ReteInfo.objects.get_or_create(cliente_id=self.kwargs['cliente_id'])
        return rete_info

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.kwargs['cliente_id']])


class VlanCreateView(LoginRequiredMixin, ClienteScopedCreateMixin, CreateView):
    model = Vlan
    form_class = VlanForm
    template_name = 'rete/vlan_form.html'


class VlanUpdateView(LoginRequiredMixin, UpdateView):
    model = Vlan
    form_class = VlanForm
    template_name = 'rete/vlan_form.html'

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


class VlanDeleteView(LoginRequiredMixin, DeleteView):
    model = Vlan
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'VLAN'}

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


# --- Reti wireless -------------------------------------------------------

class ReteWirelessCreateView(LoginRequiredMixin, ClienteScopedCreateMixin, CreateView):
    model = ReteWireless
    form_class = ReteWirelessForm
    template_name = 'rete/wireless_form.html'


class ReteWirelessUpdateView(LoginRequiredMixin, UpdateView):
    model = ReteWireless
    form_class = ReteWirelessForm
    template_name = 'rete/wireless_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente_id'] = self.object.cliente_id
        return kwargs

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


class ReteWirelessDeleteView(LoginRequiredMixin, DeleteView):
    model = ReteWireless
    template_name = 'rete/confirm_delete.html'
    extra_context = {'titolo': 'rete wireless'}

    def get_success_url(self):
        return reverse('cliente-detail', args=[self.object.cliente_id])


# --- Configurazione (tipi apparato) ---------------------------------------

@login_required
def configurazione(request):
    if request.method == 'POST':
        formset = TipoApparatoFormSet(request.POST, prefix='tipoapparato', queryset=TipoApparato.objects.all())
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Configurazione aggiornata.')
            return redirect('configurazione')
    else:
        formset = TipoApparatoFormSet(prefix='tipoapparato', queryset=TipoApparato.objects.all())
    return render(request, 'rete/configurazione.html', {'formset': formset})
