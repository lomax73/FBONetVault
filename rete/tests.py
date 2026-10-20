from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    Apparato,
    Credenziale,
    CredenzialeCondivisa,
    CredenzialeDisponibile,
    ParametroDisponibile,
    Progetto,
    TipoApparato,
)


class ApparatoSchedaUnicaTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user('tecnico', password='x'))
        self.progetto = Progetto.objects.create(nome='Cliente test', cliente_id='00000000-0000-0000-0000-000000000001')
        self.admin_cliente = CredenzialeDisponibile.objects.create(
            etichetta='Admin cliente', titolare='cliente', tipo_accesso='https',
        )
        self.tecnico = CredenzialeDisponibile.objects.create(
            etichetta='Tecnico SSH', titolare='tecnico', tipo_accesso='ssh', ordine=1,
        )
        self.ip_wan = ParametroDisponibile.objects.create(nome='IP WAN')
        self.router = TipoApparato.objects.create(nome='Router')
        self.router.credenziali.set([self.admin_cliente, self.tecnico])
        self.router.parametri.set([self.ip_wan])
        self.switch = TipoApparato.objects.create(nome='Switch')

    def _dati_base(self, **extra):
        dati = {
            'nome': 'Router sede', 'tipo': self.router.pk, 'stato': 'attivo', 'ordine': 0,
            'parametri-TOTAL_FORMS': 0, 'parametri-INITIAL_FORMS': 0,
            'credenziali-TOTAL_FORMS': 0, 'credenziali-INITIAL_FORMS': 0,
        }
        dati.update(extra)
        return dati

    def test_sync_crea_credenziali_vuote_dal_tipo(self):
        apparato = Apparato.objects.create(progetto=self.progetto, nome='R1', tipo=self.router)
        self.assertEqual(apparato.sync_credenziali(), 2)
        self.assertEqual(apparato.sync_credenziali(), 0)
        cliente = apparato.credenziali.get(definizione=self.admin_cliente)
        self.assertEqual((cliente.etichetta, cliente.titolare, cliente.tipo_accesso), ('Admin cliente', 'cliente', 'https'))
        self.assertEqual(apparato.credenziali.get(definizione=self.tecnico).titolare, 'tecnico')

    def test_sync_non_cancella_credenziali_se_il_tipo_cambia(self):
        apparato = Apparato.objects.create(progetto=self.progetto, nome='R1', tipo=self.router)
        apparato.sync_tipo()
        apparato.credenziali.filter(definizione=self.tecnico).update(username='tech')
        apparato.tipo = self.switch
        apparato.save()
        apparato.sync_tipo()
        self.assertEqual(apparato.credenziali.count(), 2)
        self.assertEqual(apparato.parametri.count(), 0)

    def test_creazione_salva_credenziale_aggiunta_e_porta_a_modifica(self):
        risposta = self.client.post(
            reverse('apparato-create', args=[self.progetto.pk]),
            self._dati_base(**{
                'credenziali-TOTAL_FORMS': 1,
                'credenziali-0-titolare': 'cliente', 'credenziali-0-tipo_accesso': 'ssh',
                'credenziali-0-username': 'root', 'credenziali-0-password': 'segreta',
            }),
        )
        apparato = Apparato.objects.get(nome='Router sede')
        self.assertEqual(apparato.progetto, self.progetto)
        self.assertRedirects(risposta, reverse('apparato-update', args=[apparato.pk]))
        self.assertEqual(apparato.credenziali.count(), 3)
        self.assertEqual(apparato.credenziali.get(username='root').password, 'segreta')
        self.assertEqual(apparato.parametri.count(), 1)

    def test_modifica_compila_parametri_e_credenziali_insieme(self):
        apparato = Apparato.objects.create(progetto=self.progetto, nome='R1', tipo=self.router)
        apparato.sync_tipo()
        parametro = apparato.parametri.get()
        cred = apparato.credenziali.get(definizione=self.tecnico)
        risposta = self.client.get(reverse('apparato-update', args=[apparato.pk]))
        self.assertContains(risposta, 'IP WAN')
        self.assertContains(risposta, 'Tecnico SSH')
        dati = self._dati_base(**{
            'parametri-TOTAL_FORMS': 1, 'parametri-INITIAL_FORMS': 1,
            'parametri-0-id': parametro.pk, 'parametri-0-apparato': apparato.pk,
            'parametri-0-valore': '1.2.3.4', 'parametri-0-note': '',
            'credenziali-TOTAL_FORMS': 2, 'credenziali-INITIAL_FORMS': 1,
            'credenziali-0-id': cred.pk, 'credenziali-0-apparato': apparato.pk,
            'credenziali-0-etichetta': 'Tecnico SSH', 'credenziali-0-titolare': 'tecnico',
            'credenziali-0-tipo_accesso': 'ssh', 'credenziali-0-username': 'admin-fbo',
            'credenziali-0-password': 'pw-tecnico',
            'credenziali-1-titolare': 'cliente', 'credenziali-1-tipo_accesso': 'ssh',
        })
        dati['nome'] = 'R1'
        risposta = self.client.post(reverse('apparato-update', args=[apparato.pk]), dati)
        self.assertRedirects(risposta, reverse('apparato-detail', args=[apparato.pk]))
        parametro.refresh_from_db()
        cred.refresh_from_db()
        self.assertEqual(parametro.valore, '1.2.3.4')
        self.assertEqual((cred.username, cred.password), ('admin-fbo', 'pw-tecnico'))
        self.assertEqual(apparato.credenziali.count(), 2)  # la riga vuota in più viene ignorata
        dettaglio = self.client.get(reverse('apparato-detail', args=[apparato.pk]))
        self.assertContains(dettaglio, 'pw-tecnico')
        self.assertContains(dettaglio, 'Tecnico')

    def test_cambio_tipo_in_modifica_rimuove_parametri_senza_ricrearli(self):
        apparato = Apparato.objects.create(progetto=self.progetto, nome='R1', tipo=self.router)
        apparato.sync_tipo()
        parametro = apparato.parametri.get()
        dati = self._dati_base(**{
            'tipo': self.switch.pk,
            'parametri-TOTAL_FORMS': 1, 'parametri-INITIAL_FORMS': 1,
            'parametri-0-id': parametro.pk, 'parametri-0-apparato': apparato.pk,
            'parametri-0-valore': 'x', 'parametri-0-note': '',
        })
        dati['nome'] = 'R1'
        self.client.post(reverse('apparato-update', args=[apparato.pk]), dati)
        self.assertEqual(apparato.parametri.count(), 0)

    def test_credenziale_catalogo_eliminata_lascia_le_credenziali(self):
        apparato = Apparato.objects.create(progetto=self.progetto, nome='R1', tipo=self.router)
        apparato.sync_tipo()
        self.tecnico.delete()
        self.assertEqual(apparato.credenziali.count(), 2)
        self.assertEqual(Credenziale.objects.filter(apparato=apparato, definizione=None).count(), 1)

    def test_pagine_configurazione(self):
        risposta = self.client.get(reverse('configurazione'))
        self.assertContains(risposta, 'Credenziali disponibili')
        self.assertContains(risposta, 'Tecnico SSH (Tecnico di gestione)')
        url = reverse('tipo-apparato-parametri', args=[self.switch.pk])
        self.assertContains(self.client.get(url), 'Credenziali previste')
        apparato = Apparato.objects.create(progetto=self.progetto, nome='S1', tipo=self.switch)
        self.client.post(url, {'parametri': [], 'credenziali': [self.tecnico.pk]})
        self.assertEqual(apparato.credenziali.get().etichetta, 'Tecnico SSH')


class CredenzialiCondiviseTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user('tecnico', password='x'))
        self.progetto = Progetto.objects.create(nome='Cliente test', cliente_id='00000000-0000-0000-0000-000000000001')
        self.altro = Progetto.objects.create(nome='Altro', cliente_id='00000000-0000-0000-0000-000000000002')
        self.web = CredenzialeCondivisa.objects.create(
            progetto=self.progetto, etichetta='Tecnico web', titolare='tecnico', username='fbo', password='pw-web',
        )
        self.ssh = CredenzialeCondivisa.objects.create(
            progetto=self.progetto, etichetta='Tecnico SSH', titolare='tecnico', username='fbo', password='pw-ssh',
        )
        self.a1 = Apparato.objects.create(progetto=self.progetto, nome='R1')
        self.a2 = Apparato.objects.create(progetto=self.progetto, nome='R2')

    def _form_credenziale(self, **extra):
        dati = {'titolare': 'cliente', 'tipo_accesso': 'https', 'ordine': 0}
        dati.update(extra)
        return dati

    def test_servizi_diversi_usano_password_diverse_e_si_aggiornano_insieme(self):
        for apparato in (self.a1, self.a2):
            Credenziale.objects.create(apparato=apparato, tipo_accesso='https', condivisa=self.web)
            Credenziale.objects.create(apparato=apparato, tipo_accesso='ssh', condivisa=self.ssh)
        self.web.password = 'nuova'
        self.web.save()
        https = self.a2.credenziali.get(tipo_accesso='https')
        ssh = self.a2.credenziali.get(tipo_accesso='ssh')
        self.assertEqual((https.password_effettiva, ssh.password_effettiva), ('nuova', 'pw-ssh'))

    def test_form_con_condivisa_scarta_valori_propri_e_prende_titolare(self):
        risposta = self.client.post(
            reverse('credenziale-create', args=[self.a1.pk]),
            self._form_credenziale(condivisa=self.web.pk, username='x', password='y'),
        )
        self.assertRedirects(risposta, reverse('apparato-detail', args=[self.a1.pk]))
        credenziale = self.a1.credenziali.get()
        self.assertEqual((credenziale.username, credenziale.password, credenziale.titolare), ('', '', 'tecnico'))
        self.assertEqual(credenziale.password_effettiva, 'pw-web')
        dettaglio = self.client.get(reverse('apparato-detail', args=[self.a1.pk]))
        self.assertContains(dettaglio, 'data-pwd="pw-web"')
        self.assertNotContains(dettaglio, '>pw-web<')  # mai in chiaro nel testo visibile

    def test_non_si_puo_scegliere_la_condivisa_di_un_altro_progetto(self):
        estranea = CredenzialeCondivisa.objects.create(progetto=self.altro, etichetta='Estranea')
        risposta = self.client.post(
            reverse('credenziale-create', args=[self.a1.pk]), self._form_credenziale(condivisa=estranea.pk),
        )
        self.assertEqual(risposta.status_code, 200)
        self.assertFalse(self.a1.credenziali.exists())

    def test_eliminare_la_condivisa_copia_i_valori_nelle_righe(self):
        credenziale = Credenziale.objects.create(apparato=self.a1, tipo_accesso='https', condivisa=self.web)
        self.client.post(reverse('credenziale-condivisa-delete', args=[self.web.pk]))
        credenziale.refresh_from_db()
        self.assertIsNone(credenziale.condivisa)
        self.assertEqual((credenziale.username, credenziale.password), ('fbo', 'pw-web'))

    def test_scheda_apparato_offre_solo_le_condivise_del_progetto(self):
        CredenzialeCondivisa.objects.create(progetto=self.altro, etichetta='Estranea')
        risposta = self.client.get(reverse('apparato-update', args=[self.a1.pk]))
        self.assertContains(risposta, 'Tecnico web')
        self.assertNotContains(risposta, 'Estranea')
        nuovo = self.client.get(reverse('apparato-create', args=[self.progetto.pk]))
        self.assertContains(nuovo, 'Tecnico SSH')

    def test_pagina_progetto_elenca_le_condivise_con_uso(self):
        Credenziale.objects.create(apparato=self.a1, tipo_accesso='https', condivisa=self.web)
        risposta = self.client.get(reverse('progetto-detail', args=[self.progetto.pk]))
        self.assertContains(risposta, 'Tecnico web')
        self.assertContains(risposta, '1 credenziale')
