from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompetenceViewSet, DisponibiliteViewSet,
    AnnonceViewSet, MatchViewSet
)

router = DefaultRouter()
router.register('competences', CompetenceViewSet)
router.register('disponibilites', DisponibiliteViewSet)
router.register('annonces', AnnonceViewSet, basename='annonce')
router.register('matches', MatchViewSet, basename='match')

urlpatterns = [
    path('', include(router.urls)),
]