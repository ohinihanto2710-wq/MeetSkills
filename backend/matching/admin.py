from django.contrib import admin
from .models import Competence, Disponibilite, Annonce, Match

@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'domaine', 'transversale']
    search_fields = ['nom', 'domaine']

@admin.register(Disponibilite)
class DisponibiliteAdmin(admin.ModelAdmin):
    list_display = ['jour', 'heure_debut', 'heure_fin']

@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ['auteur', 'type_annonce', 'domaine_etudes', 'niveau', 'active', 'date_creation']
    list_filter = ['type_annonce', 'active']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['annonce_offre', 'annonce_demande', 'score', 'date_creation']
    ordering = ['-score']
