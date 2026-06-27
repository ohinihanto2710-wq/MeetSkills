from rest_framework import serializers
from .models import Competence, Disponibilite, Annonce, Match


class CompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competence
        fields = ['id', 'nom', 'domaine', 'transversale']


class DisponibiliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilite
        fields = ['id', 'jour', 'heure_debut', 'heure_fin']


class AnnonceSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.SerializerMethodField()
    competences = CompetenceSerializer(many=True, read_only=True)
    competences_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Competence.objects.all(),
        write_only=True, source='competences'
    )
    disponibilites = DisponibiliteSerializer(many=True, read_only=True)
    disponibilites_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Disponibilite.objects.all(),
        write_only=True, source='disponibilites', required=False
    )

    class Meta:
        model = Annonce
        fields = [
            'id', 'auteur', 'auteur_nom', 'type_annonce',
            'competences', 'competences_ids',
            'domaine_etudes', 'niveau', 'description',
            'disponibilites', 'disponibilites_ids',
            'active', 'date_creation',
        ]
        read_only_fields = ['auteur', 'date_creation']

    def get_auteur_nom(self, obj):
        return f"{obj.auteur.prenom} {obj.auteur.nom}"

    def create(self, validated_data):
        competences = validated_data.pop('competences', [])
        disponibilites = validated_data.pop('disponibilites', [])
        annonce = Annonce.objects.create(**validated_data)
        annonce.competences.set(competences)
        annonce.disponibilites.set(disponibilites)
        return annonce


class MatchSerializer(serializers.ModelSerializer):
    annonce_offre = AnnonceSerializer(read_only=True)
    annonce_demande = AnnonceSerializer(read_only=True)
    competences_communes = CompetenceSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'annonce_offre', 'annonce_demande',
            'score', 'competences_communes', 'date_creation',
        ]