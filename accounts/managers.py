from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        
        # Validation de l'email
        email = self.normalize_email(email)
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValueError('Adresse email invalide')
        
        # Validation du mot de passe
        if password and len(password) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, first_name, last_name, password, **extra_fields)
