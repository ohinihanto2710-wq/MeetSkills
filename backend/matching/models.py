from django.db import models
from django.conf import settings


class Competence(models.Model):
    """Référentiel partagé de matières/compétences."""
    nom = models.CharField(max_length=150, unique=True)
    domaine = models.CharField(max_length=150, blank=True)  # ex: Informatique, Droit, Médecine
    transversale = models.BooleanField(
        default=False,
        help_text="Matière transversale (maths, anglais, méthodologie...) : "
                   "le matching reste possible même entre domaines éloignés."
    )

    class Meta:
        verbose_name = "Compétence"
        verbose_name_plural = "Compétences"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Disponibilite(models.Model):
    """Créneau horaire réutilisable, associé à un utilisateur ou une annonce."""
    JOURS = [
        ('lundi', 'Lundi'), ('mardi', 'Mardi'), ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'), ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'), ('dimanche', 'Dimanche'),
    ]
    jour = models.CharField(max_length=10, choices=JOURS)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    class Meta:
        verbose_name = "Disponibilité"
        verbose_name_plural = "Disponibilités"

    def __str__(self):
        return f"{self.get_jour_display()} {self.heure_debut}-{self.heure_fin}"


class Annonce(models.Model):
    """Offre ou demande de mentorat publiée par un utilisateur."""
    TYPE_CHOICES = [
        ('offre', "J'offre du mentorat"),
        ('demande', "Je recherche de l'aide"),
    ]
    NIVEAU_CHOICES = [
        ('licence', 'Licence (L1-L3)'),
        ('master', 'Master (M1-M2)'),
        ('autre', 'Autre'),
    ]

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='annonces'
    )
    type_annonce = models.CharField(max_length=10, choices=TYPE_CHOICES)
    competences = models.ManyToManyField(Competence, related_name='annonces')
    domaine_etudes = models.CharField(max_length=150)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='licence')
    disponibilites = models.ManyToManyField(Disponibilite, related_name='annonces', blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_type_annonce_display()} — {self.auteur} ({self.domaine_etudes})"


class Match(models.Model):
    """Résultat du matching entre deux annonces, avec score de compatibilité."""
    annonce_offre = models.ForeignKey(
        Annonce, on_delete=models.CASCADE, related_name='matches_offre',
        limit_choices_to={'type_annonce': 'offre'}
    )
    annonce_demande = models.ForeignKey(
        Annonce, on_delete=models.CASCADE, related_name='matches_demande',
        limit_choices_to={'type_annonce': 'demande'}
    )
    score = models.PositiveSmallIntegerField(help_text="Score de compatibilité sur 100")
    competences_communes = models.ManyToManyField(Competence, related_name='matches', blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Match"
        verbose_name_plural = "Matches"
        ordering = ['-score']
        unique_together = ('annonce_offre', 'annonce_demande')

    def __str__(self):
        return f"Match {self.annonce_offre.auteur} ↔ {self.annonce_demande.auteur} ({self.score}%)"