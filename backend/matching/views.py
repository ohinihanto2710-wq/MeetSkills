from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Competence, Disponibilite, Annonce, Match
from .serializers import (
    CompetenceSerializer, DisponibiliteSerializer,
    AnnonceSerializer, MatchSerializer
)


class CompetenceViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste et détail des compétences (lecture seule)."""
    queryset = Competence.objects.all()
    serializer_class = CompetenceSerializer
    permission_classes = [permissions.IsAuthenticated]


class DisponibiliteViewSet(viewsets.ModelViewSet):
    """CRUD des disponibilités."""
    queryset = Disponibilite.objects.all()
    serializer_class = DisponibiliteSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnnonceViewSet(viewsets.ModelViewSet):
    """CRUD des annonces + matching automatique."""
    serializer_class = AnnonceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Annonce.objects.filter(active=True)
        type_annonce = self.request.query_params.get('type')
        domaine = self.request.query_params.get('domaine')
        if type_annonce:
            queryset = queryset.filter(type_annonce=type_annonce)
        if domaine:
            queryset = queryset.filter(domaine_etudes__icontains=domaine)
        return queryset

    def perform_create(self, serializer):
        annonce = serializer.save(auteur=self.request.user)
        # Déclenche le matching automatiquement après création
        self._calculer_matches(annonce)

    def _calculer_matches(self, annonce):
        """Calcule et enregistre les matches pour une annonce."""
        if annonce.type_annonce == 'offre':
            annonces_opposees = Annonce.objects.filter(
                type_annonce='demande', active=True
            ).exclude(auteur=annonce.auteur)
        else:
            annonces_opposees = Annonce.objects.filter(
                type_annonce='offre', active=True
            ).exclude(auteur=annonce.auteur)

        for autre in annonces_opposees:
            score, competences_communes = self._score(annonce, autre)
            if score > 0:
                offre = annonce if annonce.type_annonce == 'offre' else autre
                demande = annonce if annonce.type_annonce == 'demande' else autre
                match, created = Match.objects.get_or_create(
                    annonce_offre=offre,
                    annonce_demande=demande,
                    defaults={'score': score}
                )
                if created:
                    match.competences_communes.set(competences_communes)

    def _score(self, a1, a2):
        """Calcule le score de compatibilité entre deux annonces."""
        comp1 = set(a1.competences.values_list('id', flat=True))
        comp2 = set(a2.competences.values_list('id', flat=True))
        communes = comp1 & comp2
        if not communes:
            return 0, []

        # Score compétences (50 points max)
        score_comp = min(len(communes) * 25, 50)

        # Score disponibilités (30 points max)
        dispo1 = set(a1.disponibilites.values_list('id', flat=True))
        dispo2 = set(a2.disponibilites.values_list('id', flat=True))
        dispos_communes = dispo1 & dispo2
        score_dispo = min(len(dispos_communes) * 15, 30)

        # Score domaine (20 points max)
        score_domaine = 20 if a1.domaine_etudes.lower() == a2.domaine_etudes.lower() else 0

        score_total = score_comp + score_dispo + score_domaine
        competences_communes = list(
            a1.competences.filter(id__in=communes)
        )
        return score_total, competences_communes

    @action(detail=True, methods=['get'])
    def mes_matches(self, request, pk=None):
        """Retourne les matches d'une annonce triés par score."""
        annonce = self.get_object()
        if annonce.type_annonce == 'offre':
            matches = Match.objects.filter(
                annonce_offre=annonce
            ).order_by('-score')
        else:
            matches = Match.objects.filter(
                annonce_demande=annonce
            ).order_by('-score')
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste et détail des matches (lecture seule)."""
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            annonce_offre__auteur=user
        ) | Match.objects.filter(
            annonce_demande__auteur=user
        ).order_by('-score')
