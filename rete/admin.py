from django.contrib import admin

from .models import (
    Apparato,
    Credenziale,
    ParametroConfig,
    Progetto,
    ReteInfo,
    ReteWireless,
    Sezione,
    TipoApparato,
    Vlan,
)


@admin.register(Progetto)
class ProgettoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente_id', 'indirizzo', 'creato_il')
    search_fields = ('nome', 'indirizzo')


@admin.register(Sezione)
class SezioneAdmin(admin.ModelAdmin):
    list_display = ('nome', 'progetto', 'ordine')
    search_fields = ('nome',)


@admin.register(TipoApparato)
class TipoApparatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordine')


class ParametroConfigInline(admin.TabularInline):
    model = ParametroConfig
    extra = 0


class CredenzialeInline(admin.TabularInline):
    model = Credenziale
    extra = 0


@admin.register(Apparato)
class ApparatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'progetto', 'sezione', 'tipo', 'indirizzo_ip')
    list_filter = ('tipo',)
    search_fields = ('nome', 'indirizzo_ip', 'marca_modello')
    inlines = [ParametroConfigInline, CredenzialeInline]


@admin.register(ReteInfo)
class ReteInfoAdmin(admin.ModelAdmin):
    list_display = ('progetto', 'aggiornato_il')


@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nome', 'progetto', 'subnet')
    search_fields = ('nome', 'subnet')


@admin.register(ReteWireless)
class ReteWirelessAdmin(admin.ModelAdmin):
    list_display = ('ssid', 'progetto', 'tipo_sicurezza', 'banda')
    search_fields = ('ssid',)
