from django.contrib import admin
from .models import Devoir, DevoirMatiere, DevoirComposition, DevoirReponseEleve, BulletinDevoir, BulletinDevoirLigne, Certificat


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display = ('titre', 'annee_scolaire', 'date_debut', 'date_fin', 'statut', 'createur')
    list_filter = ('statut', 'annee_scolaire')
    search_fields = ('titre', 'description')
    filter_horizontal = ('classes', 'matieres')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DevoirMatiere)
class DevoirMatiereAdmin(admin.ModelAdmin):
    list_display = ('devoir', 'matiere', 'statut', 'soumis_par', 'submitted_at')
    list_filter = ('statut', 'matiere')
    search_fields = ('devoir__titre', 'matiere__nom')


@admin.register(DevoirComposition)
class DevoirCompositionAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'devoir', 'statut', 'moyenne_generale', 'rang', 'resultat')
    list_filter = ('statut', 'resultat', 'devoir')
    search_fields = ('eleve__email', 'devoir__titre')


@admin.register(DevoirReponseEleve)
class DevoirReponseEleveAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'devoir_matiere', 'statut', 'note_ia', 'note_finale', 'created_at')
    list_filter = ('statut', 'devoir_matiere__devoir')
    search_fields = ('eleve__email', 'devoir_matiere__matiere__nom')
    readonly_fields = ('note_ia', 'appreciation_ia', 'feedback_ia', 'corrige_at')


@admin.register(BulletinDevoir)
class BulletinDevoirAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'devoir', 'moyenne_generale', 'rang', 'statut', 'approuve_par', 'created_at')
    list_filter = ('statut', 'devoir')
    search_fields = ('eleve__email', 'devoir__titre')
    readonly_fields = ('verification_token', 'moyenne_generale', 'rang', 'created_at')


@admin.register(BulletinDevoirLigne)
class BulletinDevoirLigneAdmin(admin.ModelAdmin):
    list_display = ('bulletin', 'matiere', 'coefficient', 'moyenne', 'rang')
    list_filter = ('bulletin__devoir',)
    search_fields = ('matiere', 'bulletin__eleve__email')


@admin.register(Certificat)
class CertificatAdmin(admin.ModelAdmin):
    list_display = ('numero_certificat', 'eleve', 'type_certificat', 'moyenne_obtenue', 'date_delivrance')
    list_filter = ('type_certificat', 'date_delivrance')
    search_fields = ('numero_certificat', 'eleve__email', 'eleve__first_name', 'eleve__last_name')
    readonly_fields = ('numero_certificat', 'verification_token', 'created_at')
