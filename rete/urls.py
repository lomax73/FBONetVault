from django.urls import path

from . import views

urlpatterns = [
    path('', views.ProgettoListView.as_view(), name='progetto-list'),
    path('progetti/nuovo/', views.ProgettoCreateView.as_view(), name='progetto-create'),
    path('progetti/<int:pk>/', views.ProgettoDetailView.as_view(), name='progetto-detail'),
    path('progetti/<int:pk>/modifica/', views.ProgettoUpdateView.as_view(), name='progetto-update'),
    path('progetti/<int:pk>/elimina/', views.ProgettoDeleteView.as_view(), name='progetto-delete'),

    path('progetti/<int:progetto_pk>/sezioni/nuova/', views.SezioneCreateView.as_view(), name='sezione-create'),
    path('sezioni/<int:pk>/modifica/', views.SezioneUpdateView.as_view(), name='sezione-update'),
    path('sezioni/<int:pk>/elimina/', views.SezioneDeleteView.as_view(), name='sezione-delete'),

    path('progetti/<int:progetto_pk>/apparati/nuovo/', views.ApparatoCreateView.as_view(), name='apparato-create'),
    path('apparati/<int:pk>/', views.ApparatoDetailView.as_view(), name='apparato-detail'),
    path('apparati/<int:pk>/modifica/', views.ApparatoUpdateView.as_view(), name='apparato-update'),
    path('apparati/<int:pk>/elimina/', views.ApparatoDeleteView.as_view(), name='apparato-delete'),

    path(
        'apparati/<int:apparato_pk>/parametri/nuovo/',
        views.ParametroConfigCreateView.as_view(), name='parametro-create',
    ),
    path('parametri/<int:pk>/modifica/', views.ParametroConfigUpdateView.as_view(), name='parametro-update'),
    path('parametri/<int:pk>/elimina/', views.ParametroConfigDeleteView.as_view(), name='parametro-delete'),

    path(
        'apparati/<int:apparato_pk>/credenziali/nuova/',
        views.CredenzialeCreateView.as_view(), name='credenziale-create',
    ),
    path('credenziali/<int:pk>/modifica/', views.CredenzialeUpdateView.as_view(), name='credenziale-update'),
    path('credenziali/<int:pk>/elimina/', views.CredenzialeDeleteView.as_view(), name='credenziale-delete'),

    path('progetti/<int:progetto_pk>/rete/modifica/', views.ReteInfoUpdateView.as_view(), name='rete-info-update'),

    path('progetti/<int:progetto_pk>/vlan/nuova/', views.VlanCreateView.as_view(), name='vlan-create'),
    path('vlan/<int:pk>/modifica/', views.VlanUpdateView.as_view(), name='vlan-update'),
    path('vlan/<int:pk>/elimina/', views.VlanDeleteView.as_view(), name='vlan-delete'),

    path(
        'progetti/<int:progetto_pk>/wireless/nuova/',
        views.ReteWirelessCreateView.as_view(), name='wireless-create',
    ),
    path('wireless/<int:pk>/modifica/', views.ReteWirelessUpdateView.as_view(), name='wireless-update'),
    path('wireless/<int:pk>/elimina/', views.ReteWirelessDeleteView.as_view(), name='wireless-delete'),

    path('configurazione/', views.configurazione, name='configurazione'),
]
