import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import Matiere, Classe


class Devoir(models.Model):
    """
    Calendrier d'évaluation programmé par l'administration.
    Couvre deux types : Devoir Surveillé (DS) et Composition Trimestrielle.

    Workflow :
      1. Admin crée le Devoir (type + trimestre + dates)
      2. Admin ajoute les DevoirMatiere avec horaires par matière
      3. Profs soumettent épreuve + corrigé type pour leur matière
      4. Admin valide les épreuves
      5. Admin publie le programme (PROGRAMME_PUBLIE)
      6. Séance de composition
      7. Correction IA + approbation admin
      8. Génération des bulletins
    """

    class TypeEvaluation(models.TextChoices):
        DEVOIR_SURVEILLE = 'devoir_surveille', _('Devoir Surveillé')
        COMPOSITION = 'composition', _('Composition Trimestrielle')

    class Trimestre(models.TextChoices):
        T1 = 'T1', _('1er Trimestre')
        T2 = 'T2', _('2ème Trimestre')
        T3 = 'T3', _('3ème Trimestre')

    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        PROGRAMME_PUBLIE = 'programme_publie', _('Programme publié')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True, default='')
    annee_scolaire = models.CharField(_('année scolaire'), max_length=20, default='2025-2026')
    type_evaluation = models.CharField(
        _('type d\'évaluation'), max_length=20,
        choices=TypeEvaluation.choices, default=TypeEvaluation.DEVOIR_SURVEILLE
    )
    trimestre = models.CharField(
        _('trimestre'), max_length=2, choices=Trimestre.choices, default=Trimestre.T1
    )
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'))
    coefficient_default = models.DecimalField(_('coefficient par défaut'), max_digits=4, decimal_places=2, default=1.00)
    classes = models.ManyToManyField(Classe, related_name='devoirs', verbose_name=_('classes concernées'))
    matieres = models.ManyToManyField(Matiere, related_name='devoirs_nationaux', verbose_name=_('matières concernées'))
    statut = models.CharField(_('statut'), max_length=30, choices=Statut.choices, default=Statut.BROUILLON)
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devoirs_crees')
    instructions = models.TextField(_('instructions'), blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('calendrier d\'évaluation')
        verbose_name_plural = _('calendriers d\'évaluation')
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.get_type_evaluation_display()} — {self.get_trimestre_display()} {self.annee_scolaire}"

    @property
    def is_active(self):
        now = timezone.now().date()
        return self.date_debut <= now <= self.date_fin and self.statut == self.Statut.EN_COURS


class DevoirMatiere(models.Model):
    """
    Entrée du calendrier par matière + épreuve soumise par le prof.

    L'admin crée d'abord cette entrée avec les horaires (date, heure, salle).
    Le prof soumet ensuite l'épreuve et le corrigé type.
    L'admin valide avant publication du programme.
    """

    class StatutEP(models.TextChoices):
        PROGRAMME = 'programme', _('Programmé (en attente de l\'épreuve)')
        SOUMIS = 'soumis', _('Épreuve soumise par le prof')
        VALIDE = 'valide', _('Validé par l\'admin')
        REJETE = 'rejete', _('Rejeté — à corriger')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='devoir_matieres')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='devoir_matieres')
    coefficient = models.DecimalField(_('coefficient'), max_digits=4, decimal_places=2, default=1.00)

    # ── Calendrier (saisi par l'admin) ──────────────────────────────────────
    date_epreuve = models.DateField(_('date de l\'épreuve'), null=True, blank=True)
    heure_debut = models.TimeField(_('heure de début'), null=True, blank=True)
    heure_fin = models.TimeField(_('heure de fin'), null=True, blank=True)
    salle = models.CharField(_('salle / lieu'), max_length=100, blank=True, default='')
    numero_ordre = models.PositiveSmallIntegerField(
        _('ordre dans le programme'), default=1,
        help_text='Numéro d\'ordre de passage de cette matière dans le programme'
    )

    # ── Épreuve (soumise par le prof, validée par l'admin) ──────────────────
    epreuve_file = models.FileField(
        _('épreuve'), upload_to='devoirs/epreuves/%Y/%m/', blank=True, null=True
    )
    corrige_type_file = models.FileField(
        _('corrigé type'), upload_to='devoirs/corriges/%Y/%m/', blank=True, null=True
    )
    epreuve_document_id = models.CharField(
        _('ID épreuve'), max_length=32, blank=True, editable=False,
        help_text='Identifiant unique pour le suivi IA'
    )
    corrige_document_id = models.CharField(
        _('ID corrigé'), max_length=32, blank=True, editable=False,
        help_text='Identifiant unique pour le suivi IA'
    )
    soumis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='devoirs_soumis'
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='devoirs_valides'
    )
    statut = models.CharField(_('statut'), max_length=20, choices=StatutEP.choices, default=StatutEP.PROGRAMME)
    commentaire_admin = models.TextField(_('commentaire admin'), blank=True, default='')
    submitted_at = models.DateTimeField(_('soumis le'), null=True, blank=True)
    validated_at = models.DateTimeField(_('validé le'), null=True, blank=True)
    created_at = models.DateTimeField(_('créé le'), default=timezone.now, editable=False)

    class Meta:
        verbose_name = _('programme de matière')
        verbose_name_plural = _('programmes par matière')
        unique_together = ['devoir', 'matiere']
        ordering = ['numero_ordre', 'date_epreuve', 'heure_debut']

    def __str__(self):
        return f"{self.devoir} — {self.matiere.nom} ({self.date_epreuve or 'date à fixer'})"

    def save(self, *args, **kwargs):
        if not self.epreuve_document_id:
            self.epreuve_document_id = f"EPREUVE-{self.devoir.id.hex[:8]}-{self.matiere.id.hex[:8]}".upper()
        if not self.corrige_document_id:
            self.corrige_document_id = f"CORRIGE-DEV-{self.devoir.id.hex[:8]}-{self.matiere.id.hex[:8]}".upper()
        super().save(*args, **kwargs)


class DevoirComposition(models.Model):
    """Participation d'un élève à un devoir national."""

    class StatutComp(models.TextChoices):
        INSCRIT = 'inscrit', _('Inscrit')
        ABSENT = 'absent', _('Absent')
        COMPOSE = 'compose', _('A composé')

    class Resultat(models.TextChoices):
        ADMIS = 'admis', _('Admis')
        AJOURNE = 'ajourne', _('Ajourné')
        REFUSE = 'refuse', _('Refusé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='compositions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devoir_compositions')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='devoir_compositions')
    statut = models.CharField(_('statut'), max_length=20, choices=StatutComp.choices, default=StatutComp.INSCRIT)
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0.00, null=True, blank=True)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    resultat = models.CharField(_('résultat'), max_length=20, choices=Resultat.choices, default=Resultat.ADMIS, null=True, blank=True)
    details_notes = models.JSONField(_('détails des notes'), default=dict, blank=True)
    composed_at = models.DateTimeField(_('date de composition'), null=True, blank=True)

    class Meta:
        verbose_name = _('composition devoir')
        verbose_name_plural = _('compositions devoirs')
        unique_together = ['devoir', 'eleve']
        ordering = ['rang', '-moyenne_generale']

    def __str__(self):
        return f"{self.eleve.full_name} — {self.devoir.titre}"


class Certificat(models.Model):
    """Certificat administratif généré pour un élève."""

    class TypeCertificat(models.TextChoices):
        ADMISSION = 'admission', _('Admission')
        EXCELLENCE = 'excellence', _('Excellence')
        PARTICIPATION = 'participation', _('Participation')
        FIN_ANNEE = 'fin_annee', _('Fin d\'année')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificats_devoirs')
    devoir = models.ForeignKey(Devoir, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificats')
    type_certificat = models.CharField(_('type'), max_length=20, choices=TypeCertificat.choices, default=TypeCertificat.ADMISSION)
    moyenne_obtenue = models.DecimalField(_('moyenne'), max_digits=5, decimal_places=2, default=0.00)
    mention = models.TextField(_('mention'), blank=True, default='')
    numero_certificat = models.CharField(_('numéro'), max_length=30, unique=True, blank=True)
    date_delivrance = models.DateField(_('date de délivrance'), auto_now_add=True)
    file_pdf = models.FileField(_('fichier PDF'), upload_to='certificats/%Y/%m/', blank=True, null=True)
    verification_token = models.UUIDField(_('token de vérification'), unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('certificat')
        verbose_name_plural = _('certificats')
        ordering = ['-created_at']

    def __str__(self):
        return f"Certificat {self.numero_certificat} — {self.eleve.full_name}"

    def save(self, *args, **kwargs):
        if not self.numero_certificat:
            year = timezone.now().year
            count = Certificat.objects.filter(date_delivrance__year=year).count() + 1
            self.numero_certificat = f"CERT-{year}-{count:05d}"
        super().save(*args, **kwargs)


class DevoirReponseEleve(models.Model):
    """Copie soumise par un élève pour une matière d'un devoir national."""

    class StatutReponse(models.TextChoices):
        SOUMIS = 'soumis', _('Soumis')
        EN_COURS_CORRECTION = 'en_cours_correction', _('En cours de correction IA')
        CORRIGE = 'corrige', _('Corrigé par IA')
        APPROUVE = 'approuve', _('Approuvé par admin')
        REJETE = 'rejete', _('Rejeté / à reprendre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir_matiere = models.ForeignKey(DevoirMatiere, on_delete=models.CASCADE, related_name='reponses')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devoir_reponses')
    copie_file = models.FileField(_('copie de l\'élève'), upload_to='devoirs/copies/%Y/%m/', blank=True, null=True)
    copie_text = models.TextField(_('texte de la copie'), blank=True, default='')
    copie_document_id = models.CharField(_('ID copie'), max_length=32, blank=True, editable=False,
                                         help_text='Identifiant unique pour le suivi IA')
    statut = models.CharField(_('statut'), max_length=30, choices=StatutReponse.choices, default=StatutReponse.SOUMIS)
    note_ia = models.DecimalField(_('note IA'), max_digits=5, decimal_places=2, null=True, blank=True)
    note_finale = models.DecimalField(_('note finale'), max_digits=5, decimal_places=2, null=True, blank=True)
    appreciation_ia = models.TextField(_('appréciation IA'), blank=True, default='')
    feedback_ia = models.JSONField(_('feedback détaillé IA'), default=dict, blank=True)
    soumis_par_admin = models.BooleanField(_('saisi par admin'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    corrige_at = models.DateTimeField(_('date de correction'), null=True, blank=True)
    approuve_at = models.DateTimeField(_('date d\'approbation'), null=True, blank=True)

    class Meta:
        verbose_name = _('réponse élève')
        verbose_name_plural = _('réponses élèves')
        unique_together = ['devoir_matiere', 'eleve']
        ordering = ['created_at']

    def __str__(self):
        return f"{self.eleve.full_name} — {self.devoir_matiere.matiere.nom}"

    def save(self, *args, **kwargs):
        if not self.copie_document_id:
            self.copie_document_id = f"COPIE-DEV-{self.devoir_matiere.id.hex[:8]}-{self.eleve.id.hex[:8]}".upper()
        super().save(*args, **kwargs)


class BulletinDevoir(models.Model):
    """
    Relevé de notes généré après un Devoir Surveillé ou une Composition Trimestrielle.

    Pour un Devoir Surveillé : affiche uniquement la note DS par matière.
    Pour une Composition : affiche moy_interros + note DS + note composition + moyenne trimestre.
    """

    class StatutBulletin(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente d\'approbation')
        APPROUVE = 'approuve', _('Approuvé')
        REJETE = 'rejete', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='bulletins')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bulletins_devoir')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='bulletins_devoir')

    # ── Résultats généraux ──────────────────────────────────────────────────
    moyenne_generale = models.DecimalField(_('moyenne générale'), max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(_('rang'), default=0)
    effectif_total = models.PositiveIntegerField(_('effectif total'), default=0)

    # ── Comportement & Absences (format bulletin béninois) ──────────────────
    absences_justifiees = models.PositiveSmallIntegerField(_('absences justifiées (h)'), default=0)
    absences_non_justifiees = models.PositiveSmallIntegerField(_('absences non justifiées (h)'), default=0)
    retards = models.PositiveSmallIntegerField(_('retards'), default=0)

    # ── Décision & Appréciation ─────────────────────────────────────────────
    decision_conseil = models.CharField(_('décision du conseil'), max_length=200, blank=True, default='')
    observation_prof_principal = models.TextField(_('observation du professeur principal'), blank=True, default='')
    appreciation_ia = models.TextField(_('synthèse IA'), blank=True, default='')

    # ── Workflow ────────────────────────────────────────────────────────────
    statut = models.CharField(_('statut'), max_length=20, choices=StatutBulletin.choices, default=StatutBulletin.EN_ATTENTE)
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bulletins_devoir_approuves'
    )
    file_pdf = models.FileField(_('fichier PDF'), upload_to='bulletins_devoirs/%Y/%m/', blank=True, null=True)
    verification_token = models.UUIDField(_('token de vérification'), unique=True, default=uuid.uuid4)
    prof_lu = models.BooleanField(_('lu par le professeur principal'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    approuve_at = models.DateTimeField(_('date d\'approbation'), null=True, blank=True)

    class Meta:
        verbose_name = _('bulletin d\'évaluation')
        verbose_name_plural = _('bulletins d\'évaluation')
        unique_together = ['devoir', 'eleve']
        ordering = ['rang', '-moyenne_generale']

    def __str__(self):
        return f"Bulletin {self.devoir} — {self.eleve.full_name}"


class BulletinDevoirLigne(models.Model):
    """
    Ligne par matière dans un bulletin d'évaluation — format bulletin béninois.

    Colonnes affichées selon le type de Devoir :
      DS  → Matière | Coeff | Note DS | Moy×C | Rang | Appréciation
      Compo → Matière | Coeff | Moy.Interros | Note DS | Note Compo | Moy. Trim | Moy×C | Rang | Appréciation
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulletin = models.ForeignKey(BulletinDevoir, on_delete=models.CASCADE, related_name='lignes')
    matiere = models.CharField(_('matière'), max_length=100)
    coefficient = models.DecimalField(_('coefficient'), max_digits=4, decimal_places=2, default=1.00)

    # ── Notes (selon le type d'évaluation) ─────────────────────────────────
    note_interro_moyenne = models.DecimalField(
        _('moy. interrogations'), max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Moyenne des interrogations du trimestre pour cette matière'
    )
    note_devoir = models.DecimalField(
        _('note devoir surveillé'), max_digits=5, decimal_places=2, null=True, blank=True
    )
    note_composition = models.DecimalField(
        _('note composition'), max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Note de la composition trimestrielle (examen de fin de trimestre)'
    )

    # ── Calculs ─────────────────────────────────────────────────────────────
    moyenne = models.DecimalField(_('moyenne du trimestre'), max_digits=5, decimal_places=2, default=0.00)
    note_moy_coeff = models.DecimalField(
        _('moy × coeff'), max_digits=6, decimal_places=2, default=0.00,
        help_text='Utilisé pour le calcul de la moyenne générale pondérée'
    )

    # ── Stats classe ────────────────────────────────────────────────────────
    moyenne_classe = models.DecimalField(_('moy. de la classe'), max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(_('rang dans la classe'), default=0)

    # ── Appréciation ────────────────────────────────────────────────────────
    appreciation = models.TextField(_('appréciation'), blank=True, default='')

    class Meta:
        verbose_name = _('ligne de bulletin')
        verbose_name_plural = _('lignes de bulletin')
        ordering = ['matiere']

    def __str__(self):
        return f"{self.matiere} — {self.moyenne}/20"


# ══════════════════════════════════════════════════════════════════════════
#  NOTES TRIMESTRIELLES CONSOLIDÉES
#  Stocke la synthèse des notes (interros + DS + composition) d'un élève
#  pour une matière donnée sur un trimestre.
#  Calcul selon la formule béninoise : Moy = (DS + 2×Compo) / 3
# ══════════════════════════════════════════════════════════════════════════

class NoteTrimestre(models.Model):
    """
    Consolidation des notes d'un élève pour une matière sur un trimestre.
    Utilisée pour construire le BulletinAnnuel.
    """

    class Trimestre(models.TextChoices):
        T1 = 'T1', _('1er Trimestre')
        T2 = 'T2', _('2ème Trimestre')
        T3 = 'T3', _('3ème Trimestre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    eleve        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notes_trimestre', verbose_name=_('élève'),
    )
    matiere_nom  = models.CharField(_('matière'), max_length=200)
    coefficient  = models.PositiveSmallIntegerField(_('coefficient'), default=1)
    classe       = models.ForeignKey(
        Classe, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notes_trimestre', verbose_name=_('classe'),
    )
    annee_scolaire = models.CharField(_('année scolaire'), max_length=20, default='2025-2026')
    trimestre    = models.CharField(_('trimestre'), max_length=2, choices=Trimestre.choices)

    # ── Notes brutes ──────────────────────────────────────────────────────
    moy_interrogations = models.DecimalField(
        _('moyenne interrogations'), max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text=_('Moyenne des interrogations du trimestre (/20)'),
    )
    note_devoir = models.DecimalField(
        _('note devoir surveillé (DS)'), max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text=_('Note du devoir surveillé (/20)'),
    )
    note_composition = models.DecimalField(
        _('note composition'), max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text=_('Note de la composition trimestrielle (/20)'),
    )

    # ── Calculs (remplis automatiquement via save()) ───────────────────────
    moyenne_trimestre = models.DecimalField(
        _('moyenne du trimestre'), max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text=_('Formule : (DS + 2×Composition) / 3'),
    )
    note_ponderee = models.DecimalField(
        _('note pondérée (moy × coeff)'), max_digits=6, decimal_places=2,
        null=True, blank=True,
    )

    # ── Classement ────────────────────────────────────────────────────────
    rang_classe     = models.PositiveIntegerField(_('rang'), null=True, blank=True)
    moyenne_classe  = models.DecimalField(
        _('moyenne de la classe'), max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    appreciation    = models.TextField(_('appréciation'), blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name         = _('note trimestrielle')
        verbose_name_plural  = _('notes trimestrielles')
        unique_together      = ['eleve', 'matiere_nom', 'trimestre', 'annee_scolaire']
        ordering             = ['matiere_nom', 'trimestre']

    def __str__(self):
        return f"{self.eleve} — {self.matiere_nom} {self.trimestre} : {self.moyenne_trimestre}/20"

    def calculer_moyenne(self):
        """
        Formule béninoise : Moy_trim = (Note_DS + 2 × Note_Composition) / 3
        Si la composition est absente, on utilise seulement le DS.
        Si ni DS ni composition, on utilise la moyenne des interros.
        """
        ds   = float(self.note_devoir or 0)
        comp = float(self.note_composition or 0)
        interro = float(self.moy_interrogations or 0)

        if self.note_devoir is not None and self.note_composition is not None:
            moy = (ds + 2 * comp) / 3
        elif self.note_composition is not None:
            moy = comp
        elif self.note_devoir is not None:
            moy = ds
        elif self.moy_interrogations is not None:
            moy = interro
        else:
            return None
        return round(moy, 2)

    def save(self, *args, **kwargs):
        moy = self.calculer_moyenne()
        if moy is not None:
            self.moyenne_trimestre = moy
            self.note_ponderee = round(moy * self.coefficient, 2)
        super().save(*args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════
#  BULLETIN ANNUEL
#  Synthèse annuelle complète d'un élève (3 trimestres × toutes matières)
#  Compatible avec le template bulletin_benin_template.html
# ══════════════════════════════════════════════════════════════════════════

class BulletinAnnuel(models.Model):
    """
    Bulletin scolaire annuel d'un élève.
    Consolide les NoteTrimestre des 3 trimestres pour générer
    le bulletin officiel format MEMP Bénin.
    """

    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        APPROUVE  = 'approuve',  _('Approuvé')
        PUBLIE    = 'publie',    _('Publié')

    class Mention(models.TextChoices):
        EXCELLENT       = 'Excellent',      _('Excellent')
        TRES_BIEN       = 'Très Bien',      _('Très Bien')
        BIEN            = 'Bien',           _('Bien')
        ASSEZ_BIEN      = 'Assez Bien',     _('Assez Bien')
        PASSABLE        = 'Passable',       _('Passable')
        INSUFFISANT     = 'Insuffisant',    _('Insuffisant')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    eleve          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bulletins_annuels', verbose_name=_('élève'),
    )
    classe         = models.ForeignKey(
        Classe, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bulletins_annuels', verbose_name=_('classe'),
    )
    annee_scolaire = models.CharField(_('année scolaire'), max_length=20, default='2025-2026')
    numero_ordre   = models.CharField(_('n° d\'ordre'), max_length=20, blank=True)

    # ── Synthèse annuelle ─────────────────────────────────────────────────
    moyenne_annuelle  = models.DecimalField(
        _('moyenne générale annuelle'), max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    rang_classe       = models.PositiveIntegerField(_('rang dans la classe'), null=True, blank=True)
    effectif_total    = models.PositiveIntegerField(_('effectif de la classe'), null=True, blank=True)

    # ── Appréciation & décision ───────────────────────────────────────────
    mention              = models.CharField(
        _('mention'), max_length=20, choices=Mention.choices, blank=True,
    )
    appreciation_generale = models.TextField(_('appréciation générale'), blank=True)
    decision_conseil     = models.CharField(_('décision du conseil de classe'), max_length=200, blank=True)
    observations_chef    = models.TextField(_('observations du chef d\'établissement'), blank=True)

    # ── Absences (totales sur l'année) ────────────────────────────────────
    absences_justifiees     = models.PositiveSmallIntegerField(_('absences justifiées (h)'), default=0)
    absences_non_justifiees = models.PositiveSmallIntegerField(_('absences non justifiées (h)'), default=0)
    retards                 = models.PositiveSmallIntegerField(_('retards'), default=0)

    @property
    def absences_total(self):
        return self.absences_justifiees + self.absences_non_justifiees

    # ── Examen final (BEPC / BAC / CEP) ──────────────────────────────────
    presente_examen  = models.BooleanField(_('présenté(e) à l\'examen'), default=False)
    resultat_examen  = models.CharField(_('résultat examen'), max_length=50, blank=True)
    mention_examen   = models.CharField(_('mention à l\'examen'), max_length=50, blank=True)

    # ── Lieu et date ──────────────────────────────────────────────────────
    fait_a        = models.CharField(_('fait à'), max_length=100, blank=True, default='Cotonou')
    date_emission = models.DateTimeField(_('date d\'émission'), null=True, blank=True)

    # ── PDF & statut ──────────────────────────────────────────────────────
    file_pdf = models.FileField(
        _('fichier PDF'), upload_to='bulletins_annuels/%Y/%m/', null=True, blank=True,
    )
    statut = models.CharField(
        _('statut'), max_length=20, choices=Statut.choices, default=Statut.BROUILLON,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name         = _('bulletin annuel')
        verbose_name_plural  = _('bulletins annuels')
        unique_together      = ['eleve', 'annee_scolaire']
        ordering             = ['-annee_scolaire', 'eleve']

    def __str__(self):
        return f"Bulletin annuel {self.eleve} — {self.annee_scolaire}"

    def get_mention_from_moyenne(self):
        """Calcule la mention selon la moyenne béninoise."""
        if self.moyenne_annuelle is None:
            return ''
        m = float(self.moyenne_annuelle)
        if m >= 18:  return self.Mention.EXCELLENT
        if m >= 16:  return self.Mention.TRES_BIEN
        if m >= 14:  return self.Mention.BIEN
        if m >= 12:  return self.Mention.ASSEZ_BIEN
        if m >= 10:  return self.Mention.PASSABLE
        return self.Mention.INSUFFISANT

    def calculer_moyenne_annuelle(self):
        """
        Calcule la moyenne annuelle pondérée à partir des BulletinAnnuelLigne.
        Formule : Σ(note_ponderee) / Σ(coefficient)
        """
        lignes = self.lignes.all()
        total_coeff = sum(int(l.coefficient) for l in lignes if l.coefficient)
        total_pts   = sum(float(l.note_ponderee_annuelle or 0) for l in lignes)
        if total_coeff:
            return round(total_pts / total_coeff, 2)
        return None

    def generer_depuis_notes_trimestre(self):
        """
        Génère (ou recrée) les lignes du bulletin à partir des NoteTrimestre
        de cet élève pour l'année scolaire en cours.
        """
        notes = NoteTrimestre.objects.filter(
            eleve=self.eleve,
            annee_scolaire=self.annee_scolaire,
        )
        matieres = notes.values_list('matiere_nom', flat=True).distinct()

        for matiere in matieres:
            notes_mat = notes.filter(matiere_nom=matiere)
            coeff = notes_mat.first().coefficient if notes_mat.exists() else 1

            ligne, _ = BulletinAnnuelLigne.objects.get_or_create(
                bulletin=self, matiere_nom=matiere,
                defaults={'coefficient': coeff},
            )

            for note in notes_mat:
                if note.trimestre == NoteTrimestre.Trimestre.T1:
                    ligne.t1_moy_interros   = note.moy_interrogations
                    ligne.t1_note_devoir    = note.note_devoir
                    ligne.t1_note_compo     = note.note_composition
                    ligne.t1_moyenne        = note.moyenne_trimestre
                elif note.trimestre == NoteTrimestre.Trimestre.T2:
                    ligne.t2_moy_interros   = note.moy_interrogations
                    ligne.t2_note_devoir    = note.note_devoir
                    ligne.t2_note_compo     = note.note_composition
                    ligne.t2_moyenne        = note.moyenne_trimestre
                elif note.trimestre == NoteTrimestre.Trimestre.T3:
                    ligne.t3_moy_interros   = note.moy_interrogations
                    ligne.t3_note_devoir    = note.note_devoir
                    ligne.t3_note_compo     = note.note_composition
                    ligne.t3_moyenne        = note.moyenne_trimestre

            ligne.coefficient = coeff
            ligne.save()

        # Recalcule la moyenne annuelle du bulletin
        self.moyenne_annuelle = self.calculer_moyenne_annuelle()
        if not self.mention:
            self.mention = self.get_mention_from_moyenne()
        self.save(update_fields=['moyenne_annuelle', 'mention'])


class BulletinAnnuelLigne(models.Model):
    """
    Une ligne du bulletin annuel = une matière avec ses notes sur 3 trimestres.
    Correspond exactement aux colonnes du template bulletin_benin_template.html.
    """

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulletin = models.ForeignKey(
        BulletinAnnuel, on_delete=models.CASCADE,
        related_name='lignes', verbose_name=_('bulletin annuel'),
    )
    matiere_nom  = models.CharField(_('matière'), max_length=200)
    coefficient  = models.PositiveSmallIntegerField(_('coefficient'), default=1)

    # ── Trimestre 1 ───────────────────────────────────────────────────────
    t1_moy_interros = models.DecimalField(_('T1 — moy. interros'), max_digits=5, decimal_places=2, null=True, blank=True)
    t1_note_devoir  = models.DecimalField(_('T1 — note DS'),       max_digits=5, decimal_places=2, null=True, blank=True)
    t1_note_compo   = models.DecimalField(_('T1 — note compo'),    max_digits=5, decimal_places=2, null=True, blank=True)
    t1_moyenne      = models.DecimalField(_('T1 — moyenne'),       max_digits=5, decimal_places=2, null=True, blank=True)

    # ── Trimestre 2 ───────────────────────────────────────────────────────
    t2_moy_interros = models.DecimalField(_('T2 — moy. interros'), max_digits=5, decimal_places=2, null=True, blank=True)
    t2_note_devoir  = models.DecimalField(_('T2 — note DS'),       max_digits=5, decimal_places=2, null=True, blank=True)
    t2_note_compo   = models.DecimalField(_('T2 — note compo'),    max_digits=5, decimal_places=2, null=True, blank=True)
    t2_moyenne      = models.DecimalField(_('T2 — moyenne'),       max_digits=5, decimal_places=2, null=True, blank=True)

    # ── Trimestre 3 ───────────────────────────────────────────────────────
    t3_moy_interros = models.DecimalField(_('T3 — moy. interros'), max_digits=5, decimal_places=2, null=True, blank=True)
    t3_note_devoir  = models.DecimalField(_('T3 — note DS'),       max_digits=5, decimal_places=2, null=True, blank=True)
    t3_note_compo   = models.DecimalField(_('T3 — note compo'),    max_digits=5, decimal_places=2, null=True, blank=True)
    t3_moyenne      = models.DecimalField(_('T3 — moyenne'),       max_digits=5, decimal_places=2, null=True, blank=True)

    # ── Synthèse annuelle ─────────────────────────────────────────────────
    moyenne_annuelle      = models.DecimalField(_('moyenne annuelle'), max_digits=5, decimal_places=2, null=True, blank=True)
    note_ponderee_annuelle = models.DecimalField(_('note pondérée'), max_digits=6, decimal_places=2, null=True, blank=True)
    rang_classe           = models.PositiveIntegerField(_('rang'), null=True, blank=True)
    appreciation          = models.TextField(_('appréciation'), blank=True, default='')

    class Meta:
        verbose_name         = _('ligne bulletin annuel')
        verbose_name_plural  = _('lignes bulletin annuel')
        unique_together      = ['bulletin', 'matiere_nom']
        ordering             = ['matiere_nom']

    def __str__(self):
        return f"{self.matiere_nom} — {self.moyenne_annuelle}/20"

    def save(self, *args, **kwargs):
        """Calcule automatiquement la moyenne annuelle et la note pondérée."""
        moyennes = [m for m in [self.t1_moyenne, self.t2_moyenne, self.t3_moyenne] if m is not None]
        if moyennes:
            moy = round(sum(float(m) for m in moyennes) / len(moyennes), 2)
            self.moyenne_annuelle = moy
            self.note_ponderee_annuelle = round(moy * self.coefficient, 2)
        super().save(*args, **kwargs)
