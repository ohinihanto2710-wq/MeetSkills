import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """Applique côté serveur les mêmes règles que le formulaire (inscription.html).

    Au moins une majuscule, une minuscule, un chiffre et un caractère spécial.
    La longueur minimale est déjà gérée par MinimumLengthValidator.
    """

    def validate(self, password, user=None):
        errors = []
        if not re.search(r'[A-Z]', password):
            errors.append(ValidationError(
                "Le mot de passe doit contenir au moins une majuscule.",
                code='password_no_upper',
            ))
        if not re.search(r'[a-z]', password):
            errors.append(ValidationError(
                "Le mot de passe doit contenir au moins une minuscule.",
                code='password_no_lower',
            ))
        if not re.search(r'[0-9]', password):
            errors.append(ValidationError(
                "Le mot de passe doit contenir au moins un chiffre.",
                code='password_no_digit',
            ))
        if not re.search(r'[^A-Za-z0-9]', password):
            errors.append(ValidationError(
                "Le mot de passe doit contenir au moins un caractère spécial (!@#$...).",
                code='password_no_special',
            ))
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "Votre mot de passe doit contenir au moins une majuscule, une minuscule, "
            "un chiffre et un caractère spécial."
        )
