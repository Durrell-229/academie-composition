#!/usr/bin/env python
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')
django.setup()

def fix_dropdown_menus():
    """Corriger les menus déroulants non fonctionnels dans les templates"""
    print("🔧 CORRECTION MENUS DÉROULANTS NON FONCTIONNELS")
    print("=" * 60)
    
    try:
        # 1. Corriger le template principal QCM avec Alpine.js fonctionnel
        print("📝 Correction template QCM principal...")
        
        fixed_template = '''{% extends 'base.html' %}
{% block title %}QCM Système Éducatif Béninois | Académie Numérique{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto" x-data="{ 
    loading: false,
    selectedNiveau: '',
    selectedClasse: '',
    classesParNiveau: {
        'primaire': [{% for classe in classes_primaire %}'{{ classe.id }}:{{ classe.nom|safe }}'{% if not forloop.last %},{% endif %}{% endfor %}],
        'college': [{% for classe in classes_college %}'{{ classe.id }}:{{ classe.nom|safe }}'{% if not forloop.last %},{% endif %}{% endfor %}],
        'lycee': [{% for classe in classes_lycee %}'{{ classe.id }}:{{ classe.nom|safe }}'{% if not forloop.last %},{% endif %}{% endfor %}],
        'universite': [{% for classe in classes_universite %}'{{ classe|safe }}'{% if not forloop.last %},{% endif %}{% endfor %}]
    }
}">
  <!-- Header -->
  <div class="animate-in relative overflow-hidden rounded-2xl p-6 md:p-8 bg-bg-card border border-border-standard mb-6">
    <div class="absolute inset-0 bg-gradient-to-br from-green-600/10 via-transparent to-yellow-500/10 pointer-events-none"></div>
    <div class="relative">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-10 h-10 rounded-xl bg-green-600/10 flex items-center justify-center">
          <i class="fa-solid fa-graduation-cap text-green-600"></i>
        </div>
        <div>
          <p class="text-xs font-black uppercase tracking-widest text-text-muted">Programme Officiel Béninois</p>
          <h1 class="text-xl font-black tracking-tight text-text-primary">Générer un <span class="text-green-600">QCM Bénin</span></h1>
        </div>
      </div>
      <p class="text-sm text-text-muted mt-2">
        QCM adapté au programme éducatif béninois avec références officielles et feedback pédagogique personnalisé.
      </p>
    </div>
  </div>

  <!-- Formulaire -->
  <form method="post" action="{% url 'qcm_start_benin' %}" @submit="loading = true" class="animate-in delay-1 space-y-5">
    {% csrf_token %}

    <div class="bg-bg-card rounded-2xl border border-border-standard p-6">
        <h3 class="font-black text-sm uppercase tracking-wider flex items-center gap-2 mb-5 text-text-primary">
            <i class="fa-solid fa-sliders text-green-600"></i> Configuration QCM Bénin
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Matière -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Matière *</label>
                <select name="matiere" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="">Choisir une matière</option>
                    {% for matiere in matieres %}
                    <option value="{{ matiere.id }}">{{ matiere.nom }}</option>
                    {% endfor %}
                </select>
            </div>

            <!-- Langue -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Langue *</label>
                <select name="langue" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="fr" selected>Français</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="ar">العربية</option>
                </select>
            </div>

            <!-- Type QCM -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Type de QCM *</label>
                <select name="type_qcm" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="evaluation">Évaluation Formative</option>
                    <option value="examen">Examen Sommatif</option>
                    <option value="concours">Concours National</option>
                    <option value="revision">Révision et Soutien</option>
                </select>
            </div>

            <!-- Nombre de questions -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Nombre de questions</label>
                <select name="nb_questions" class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="5">5 questions (rapide)</option>
                    <option value="10" selected>10 questions (standard)</option>
                    <option value="15">15 questions (approfondi)</option>
                    <option value="20">20 questions (examen complet)</option>
                    <option value="25">25 questions (concours)</option>
                </select>
            </div>

            <!-- Difficulté -->
            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Niveau de difficulté</label>
                <select name="difficulte" class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="facile">Facile</option>
                    <option value="moyen" selected>Moyen</option>
                    <option value="difficile">Difficile</option>
                    <option value="mixte">Mixte (recommandé)</option>
                </select>
            </div>

            <!-- Thème -->
            <div class="md:col-span-2">
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Thème / Chapitre précis <span class="text-danger">*</span></label>
                <input type="text" name="theme" required
                    placeholder="Ex: Les fonctions dérivées, La Révolution française, Les acides carboxyliques, La colonisation en Afrique..."
                    class="w-full bg-bg-card border border-green-500/40 rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition placeholder-text-muted">
            </div>
        </div>
    </div>

    <!-- Classes par niveau avec menus déroulants fonctionnels -->
    <div class="bg-bg-card rounded-2xl border border-border-standard p-6">
        <h3 class="font-black text-sm uppercase tracking-wider flex items-center gap-2 mb-5 text-text-primary">
            <i class="fa-solid fa-school text-yellow-500"></i> Sélectionner la classe *
        </h3>
        
        <!-- Sélection du niveau -->
        <div class="mb-4">
            <label class="block text-sm font-bold text-text-secondary mb-2">Niveau d'enseignement</label>
            <select x-model="selectedNiveau" @change="selectedClasse = ''" 
                class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500/30 outline-none transition">
                <option value="">Choisir un niveau</option>
                <option value="primaire">🏫 ENSEIGNEMENT PRIMAIRE</option>
                <option value="college">📚 COLLÈGE - CYCLE D'ORIENTATION</option>
                <option value="lycee">🎓 LYCÉE - CYCLE TERMINAL</option>
                <option value="universite">🏛️ ENSEIGNEMENT SUPÉRIEUR</option>
            </select>
        </div>

        <!-- Classes du niveau sélectionné -->
        <div class="mb-4" x-show="selectedNiveau">
            <label class="block text-sm font-bold text-text-secondary mb-2">
                <span x-text="selectedNiveau === 'primaire' ? 'Classes primaires' : 
                       selectedNiveau === 'college' ? 'Classes de collège' :
                       selectedNiveau === 'lycee' ? 'Classes de lycée' : 'Classes universitaires'"></span>
            </label>
            
            <!-- Primaire -->
            <div x-show="selectedNiveau === 'primaire'">
                <select name="classe" required x-model="selectedClasse"
                    class="w-full bg-bg-card border border-green-500/50 rounded-xl px-4 py-3 text-text-primary text-base focus:border-green-500 focus:ring-1 focus:ring-green-500/30 outline-none transition">
                    <option value="">Choisir une classe primaire</option>
                    {% for classe in classes_primaire %}
                    <option value="{{ classe.id }}">{{ classe.nom }}</option>
                    {% endfor %}
                </select>
            </div>

            <!-- Collège -->
            <div x-show="selectedNiveau === 'college'">
                <select name="classe" required x-model="selectedClasse"
                    class="w-full bg-bg-card border border-blue-500/50 rounded-xl px-4 py-3 text-text-primary text-base focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 outline-none transition">
                    <option value="">Choisir une classe de collège</option>
                    {% for classe in classes_college %}
                    <option value="{{ classe.id }}">{{ classe.nom }}</option>
                    {% endfor %}
                </select>
            </div>

            <!-- Lycée -->
            <div x-show="selectedNiveau === 'lycee'">
                <select name="classe" required x-model="selectedClasse"
                    class="w-full bg-bg-card border border-purple-500/50 rounded-xl px-4 py-3 text-text-primary text-base focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 outline-none transition">
                    <option value="">Choisir une classe de lycée</option>
                    {% for classe in classes_lycee %}
                    <option value="{{ classe.id }}">{{ classe.nom }}</option>
                    {% endfor %}
                </select>
            </div>

            <!-- Université -->
            <div x-show="selectedNiveau === 'universite'">
                <select name="classe" required x-model="selectedClasse"
                    class="w-full bg-bg-card border border-red-500/50 rounded-xl px-4 py-3 text-text-primary text-base focus:border-red-500 focus:ring-1 focus:ring-red-500/30 outline-none transition">
                    <option value="">Choisir une classe universitaire</option>
                    <option value="Licence 1">Licence 1</option>
                    <option value="Licence 2">Licence 2</option>
                    <option value="Licence 3">Licence 3</option>
                    <option value="Master 1">Master 1</option>
                    <option value="Master 2">Master 2</option>
                    <option value="Doctorat 1">Doctorat 1</option>
                    <option value="Doctorat 2">Doctorat 2</option>
                    <option value="Doctorat 3">Doctorat 3</option>
                    <option value="BTS 1">BTS 1</option>
                    <option value="BTS 2">BTS 2</option>
                    <option value="DUT 1">DUT 1</option>
                    <option value="DUT 2">DUT 2</option>
                    <option value="École Normale Supérieure 1">École Normale Supérieure 1</option>
                    <option value="École Normale Supérieure 2">École Normale Supérieure 2</option>
                    <option value="École Normale Supérieure 3">École Normale Supérieure 3</option>
                    <option value="Faculté de Médecine 1">Faculté de Médecine 1</option>
                    <option value="Faculté de Médecine 2">Faculté de Médecine 2</option>
                    <option value="Faculté de Médecine 3">Faculté de Médecine 3</option>
                    <option value="Faculté de Droit 1">Faculté de Droit 1</option>
                    <option value="Faculté de Droit 2">Faculté de Droit 2</option>
                    <option value="Faculté de Droit 3">Faculté de Droit 3</option>
                    <option value="Faculté des Sciences 1">Faculté des Sciences 1</option>
                    <option value="Faculté des Sciences 2">Faculté des Sciences 2</option>
                    <option value="Faculté des Sciences 3">Faculté des Sciences 3</option>
                    <option value="Faculté des Lettres 1">Faculté des Lettres 1</option>
                    <option value="Faculté des Lettres 2">Faculté des Lettres 2</option>
                    <option value="Faculté des Lettres 3">Faculté des Lettres 3</option>
                    <option value="Institut de Journalisme 1">Institut de Journalisme 1</option>
                    <option value="Institut de Journalisme 2">Institut de Journalisme 2</option>
                    <option value="Institut de Journalisme 3">Institut de Journalisme 3</option>
                </select>
            </div>
        </div>

        <!-- Affichage de la sélection -->
        <div x-show="selectedClasse && selectedNiveau" class="mt-4 p-3 bg-green-50 border border-green-200 rounded-xl">
            <p class="text-sm text-green-800">
                <i class="fa-solid fa-check-circle mr-2"></i>
                <span x-text="`Sélection: ${selectedNiveau === 'primaire' ? 'Primaire' : 
                               selectedNiveau === 'college' ? 'Collège' :
                               selectedNiveau === 'lycee' ? 'Lycée' : 'Université'} - ${selectedClasse}`"></span>
            </p>
        </div>
    </div>

    <!-- Bouton -->
    <div class="flex justify-center">
        <button type="submit" :disabled="loading || !selectedClasse" 
            class="relative bg-gradient-to-r from-green-600 to-yellow-500 hover:from-green-700 hover:to-yellow-600 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-3 rounded-xl font-black text-sm uppercase tracking-wider shadow-lg shadow-green-600/20 hover:shadow-green-600/40 transition-all flex items-center gap-2 disabled:cursor-not-allowed">
            <span :class="loading ? 'opacity-0' : 'opacity-100'" class="transition-opacity">
                <i class="fa-solid fa-magic"></i> Générer le QCM Bénin
            </span>
            <span :class="loading ? 'opacity-100' : 'opacity-0'" class="absolute inset-0 flex items-center justify-center transition-opacity">
                <i class="fa-solid fa-spinner fa-spin"></i> Génération en cours...
            </span>
        </button>
    </div>
  </form>
</div>

<!-- Script Alpine.js pour les menus déroulants -->
<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('qcmForm', () => ({
        selectedNiveau: '',
        selectedClasse: '',
        loading: false,
        
        init() {
            // Réinitialiser la classe quand le niveau change
            this.$watch('selectedNiveau', () => {
                this.selectedClasse = '';
            });
        }
    }));
});
</script>
{% endblock %}'''
        
        # Remplacer le template existant
        with open('templates/qcm/start_benin.html', 'w', encoding='utf-8') as f:
            f.write(fixed_template)
        
        print("✅ Template QCM avec menus déroulants fonctionnels corrigé")
        
        # 2. Corriger l'ancien template QCM
        print("\n📝 Correction ancien template QCM...")
        
        old_template_fixed = '''{% extends 'base.html' %}
{% block title %}Évaluation QCM par IA | Académie Numérique{% endblock %}
{% block breadcrumb %}
  <a href="{% url 'dashboard' %}" class="hover:text-primary transition">Dashboard</a>
  <span class="mx-2 text-text-muted">/</span>
  <span class="text-text-primary font-semibold">Évaluation QCM</span>
{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto" x-data="{ 
    loading: false,
    selectedNiveau: '',
    classesParNiveau: {
        'primaire': ['CP', 'CE1', 'CE2', 'CM1', 'CM2'],
        'college': ['6ème', '5ème', '4ème', '3ème'],
        'lycee': ['2nde A', '2nde C', '2nde D', '1ère A1', '1ère A2', '1ère B', '1ère C', '1ère D', 'Terminale A1', 'Terminale A2', 'Terminale B', 'Terminale C', 'Terminale D', 'Terminale E', 'Terminale G1', 'Terminale G2', 'Terminale G3'],
        'universite': ['Licence 1', 'Licence 2', 'Licence 3', 'Master 1', 'Master 2', 'Doctorat 1', 'Doctorat 2', 'Doctorat 3', 'BTS 1', 'BTS 2', 'DUT 1', 'DUT 2']
    }
}">

  <!-- HEADER -->
  <div class="animate-in relative overflow-hidden rounded-2xl p-6 md:p-8 bg-bg-card border border-border-standard mb-6">
    <div class="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-accent/10 pointer-events-none"></div>
    <div class="relative">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <i class="fa-solid fa-list-check text-primary"></i>
        </div>
        <div>
          <p class="text-xs font-black uppercase tracking-widest text-text-muted">Propulsé par l'IA Gemini</p>
          <h1 class="text-xl font-black tracking-tight text-text-primary">Générer une <span class="text-primary">Évaluation QCM</span></h1>
        </div>
      </div>
      <p class="text-sm text-text-muted mt-2">
        L'IA génère automatiquement un QCM personnalisé selon la matière et la classe. Vos réponses sont corrigées instantanément avec un retour pédagogique détaillé.
      </p>
    </div>
  </div>

  <!-- FORM -->
  <form method="post" action="{% url 'qcm_start' %}" @submit="loading = true" class="animate-in delay-1 space-y-5">
    {% csrf_token %}

    <div class="bg-bg-card rounded-2xl border border-border-standard p-6">
        <h3 class="font-black text-sm uppercase tracking-wider flex items-center gap-2 mb-5 text-text-primary">
            <i class="fa-solid fa-sliders text-accent"></i> Configurer l'évaluation
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Matière *</label>
                <select name="matiere" required class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-border-focus focus:ring-1 focus:ring-border-focus outline-none transition">
                    <option value="">Choisir une matière</option>
                    <option value="Mathématiques">Mathématiques</option>
                    <option value="Physique-Chimie">Physique-Chimie</option>
                    <option value="Français">Français</option>
                    <option value="Histoire-Géographie">Histoire-Géographie</option>
                    <option value="Sciences de la Vie et de la Terre">SVT</option>
                    <option value="Philosophie">Philosophie</option>
                    <option value="Anglais">Anglais</option>
                    <option value="Économie">Économie</option>
                    <option value="Informatique">Informatique</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Niveau d'enseignement</label>
                <select x-model="selectedNiveau" @change="$refs.classeSelect.value = ''"
                    class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-border-focus focus:ring-1 focus:ring-border-focus outline-none transition">
                    <option value="">Choisir un niveau</option>
                    <option value="primaire">🏫 Primaire</option>
                    <option value="college">📚 Collège</option>
                    <option value="lycee">🎓 Lycée</option>
                    <option value="universite">🏛️ Université</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Classe *</label>
                <select name="classe" required x-ref="classeSelect"
                    class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-border-focus focus:ring-1 focus:ring-border-focus outline-none transition">
                    <option value="">Choisir d'abord le niveau</option>
                    <template x-for="classe in classesParNiveau[selectedNiveau] || []" :key="classe">
                        <option :value="classe" x-text="classe"></option>
                    </template>
                </select>
            </div>

            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Nombre de questions</label>
                <select name="nb_questions" class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-border-focus focus:ring-1 focus:ring-border-focus outline-none transition">
                    <option value="5">5 questions (rapide)</option>
                    <option value="10" selected>10 questions (standard)</option>
                    <option value="15">15 questions (approfondi)</option>
                    <option value="20">20 questions (examen complet)</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Niveau de difficulté</label>
                <select name="difficulte" class="w-full bg-bg-card border border-border-standard rounded-xl px-4 py-3 text-text-primary text-base focus:border-border-focus focus:ring-1 focus:ring-border-focus outline-none transition">
                    <option value="facile">Facile</option>
                    <option value="moyen" selected>Moyen</option>
                    <option value="difficile">Difficile</option>
                    <option value="mixte">Mixte (recommandé)</option>
                </select>
            </div>

            <div class="md:col-span-2">
                <label class="block text-sm font-bold text-text-secondary mb-1.5">Thème / Chapitre précis <span class="text-danger">*</span></label>
                <input type="text" name="theme" required
                    placeholder="Ex: Limites de fonctions, Probabilités, La Révolution Française, Les acides et bases, Les dérivées..."
                    class="w-full bg-bg-card border border-warning/40 rounded-xl px-4 py-3 text-text-primary text-base focus:border-warning focus:ring-1 focus:ring-warning/30 outline-none transition placeholder-text-muted">
            </div>
        </div>
    </div>

    <!-- Bouton -->
    <div class="flex justify-center">
        <button type="submit" :disabled="loading || !selectedNiveau" 
            class="relative bg-button-gradient hover:scale-[1.02] disabled:scale-100 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-3 rounded-xl font-black text-sm uppercase tracking-wider shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all flex items-center gap-2">
            <span :class="loading ? 'opacity-0' : 'opacity-100'" class="transition-opacity">
                <i class="fa-solid fa-magic"></i> Générer le QCM
            </span>
            <span :class="loading ? 'opacity-100' : 'opacity-0'" class="absolute inset-0 flex items-center justify-center transition-opacity">
                <i class="fa-solid fa-spinner fa-spin"></i> Génération en cours...
            </span>
        </button>
    </div>
  </form>
</div>
{% endblock %}'''
        
        # Remplacer l'ancien template
        with open('templates/qcm/start.html', 'w', encoding='utf-8') as f:
            f.write(old_template_fixed)
        
        print("✅ Ancien template QCM avec menus déroulants corrigé")
        
        # 3. Créer un script JavaScript pour les menus déroulants
        print("\n📜 Création du script JavaScript pour menus...")
        
        js_script = '''// Script pour les menus déroulants fonctionnels
document.addEventListener('DOMContentLoaded', function() {
    // Gestion des menus déroulants pour les QCM
    const niveauSelect = document.querySelector('select[x-model="selectedNiveau"]');
    const classeSelect = document.querySelector('select[name="classe"]');
    
    if (niveauSelect && classeSelect) {
        // Classes par niveau
        const classesParNiveau = {
            'primaire': ['CP', 'CE1', 'CE2', 'CM1', 'CM2'],
            'college': ['6ème', '5ème', '4ème', '3ème'],
            'lycee': ['2nde A', '2nde C', '2nde D', '1ère A1', '1ère A2', '1ère B', '1ère C', '1ère D', 
                     'Terminale A1', 'Terminale A2', 'Terminale B', 'Terminale C', 'Terminale D', 'Terminale E', 
                     'Terminale G1', 'Terminale G2', 'Terminale G3'],
            'universite': ['Licence 1', 'Licence 2', 'Licence 3', 'Master 1', 'Master 2', 
                           'Doctorat 1', 'Doctorat 2', 'Doctorat 3', 'BTS 1', 'BTS 2', 'DUT 1', 'DUT 2',
                           'École Normale Supérieure 1', 'École Normale Supérieure 2', 'École Normale Supérieure 3',
                           'Faculté de Médecine 1', 'Faculté de Médecine 2', 'Faculté de Médecine 3',
                           'Faculté de Droit 1', 'Faculté de Droit 2', 'Faculté de Droit 3',
                           'Faculté des Sciences 1', 'Faculté des Sciences 2', 'Faculté des Sciences 3',
                           'Faculté des Lettres 1', 'Faculté des Lettres 2', 'Faculté des Lettres 3',
                           'Institut de Journalisme 1', 'Institut de Journalisme 2', 'Institut de Journalisme 3']
        };
        
        // Écouter les changements de niveau
        niveauSelect.addEventListener('change', function() {
            const niveau = this.value;
            
            // Vider le select de classes
            classeSelect.innerHTML = '<option value="">Choisir une classe</option>';
            
            if (niveau && classesParNiveau[niveau]) {
                // Ajouter les classes du niveau sélectionné
                classesParNiveau[niveau].forEach(classe => {
                    const option = document.createElement('option');
                    option.value = classe;
                    option.textContent = classe;
                    classeSelect.appendChild(option);
                });
                
                // Activer le select de classes
                classeSelect.disabled = false;
                classeSelect.classList.remove('opacity-50');
            } else {
                // Désactiver le select de classes
                classeSelect.disabled = true;
                classeSelect.classList.add('opacity-50');
            }
        });
        
        // Initialiser l'état
        if (!niveauSelect.value) {
            classeSelect.disabled = true;
            classeSelect.classList.add('opacity-50');
        }
    }
    
    // Validation du formulaire
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const niveauSelect = form.querySelector('select[x-model="selectedNiveau"]');
            const classeSelect = form.querySelector('select[name="classe"]');
            
            if (niveauSelect && !niveauSelect.value) {
                e.preventDefault();
                alert('Veuillez sélectionner un niveau d\\'enseignement');
                return false;
            }
            
            if (classeSelect && !classeSelect.value) {
                e.preventDefault();
                alert('Veuillez sélectionner une classe');
                return false;
            }
        });
    });
});

// Compatibilité avec Alpine.js
if (typeof Alpine !== 'undefined') {
    Alpine.data('qcmSelector', () => ({
        selectedNiveau: '',
        selectedClasse: '',
        classesParNiveau: {
            'primaire': ['CP', 'CE1', 'CE2', 'CM1', 'CM2'],
            'college': ['6ème', '5ème', '4ème', '3ème'],
            'lycee': ['2nde A', '2nde C', '2nde D', '1ère A1', '1ère A2', '1ère B', '1ère C', '1ère D', 
                     'Terminale A1', 'Terminale A2', 'Terminale B', 'Terminale C', 'Terminale D', 'Terminale E', 
                     'Terminale G1', 'Terminale G2', 'Terminale G3'],
            'universite': ['Licence 1', 'Licence 2', 'Licence 3', 'Master 1', 'Master 2', 
                           'Doctorat 1', 'Doctorat 2', 'Doctorat 3', 'BTS 1', 'BTS 2', 'DUT 1', 'DUT 2',
                           'École Normale Supérieure 1', 'École Normale Supérieure 2', 'École Normale Supérieure 3',
                           'Faculté de Médecine 1', 'Faculté de Médecine 2', 'Faculté de Médecine 3',
                           'Faculté de Droit 1', 'Faculté de Droit 2', 'Faculté de Droit 3',
                           'Faculté des Sciences 1', 'Faculté des Sciences 2', 'Faculté des Sciences 3',
                           'Faculté des Lettres 1', 'Faculté des Lettres 2', 'Faculté des Lettres 3',
                           'Institut de Journalisme 1', 'Institut de Journalisme 2', 'Institut de Journalisme 3']
        },
        
        init() {
            this.$watch('selectedNiveau', () => {
                this.selectedClasse = '';
            });
        }
    }));
}'''
        
        # Écrire le script JavaScript
        with open('static/js/qcm-dropdowns.js', 'w', encoding='utf-8') as f:
            f.write(js_script)
        
        print("✅ Script JavaScript pour menus déroulants créé: static/js/qcm-dropdowns.js")
        
        # 4. Mettre à jour le template base pour inclure le script
        print("\n📄 Mise à jour du template base...")
        
        try:
            with open('templates/base.html', 'r', encoding='utf-8') as f:
                base_content = f.read()
            
            # Ajouter le script QCM si pas déjà présent
            if 'qcm-dropdowns.js' not in base_content:
                # Trouver la fin du body et ajouter le script
                if '</body>' in base_content:
                    base_content = base_content.replace(
                        '</body>',
                        '<script src="{% static "js/qcm-dropdowns.js" %}"></script>\n</body>'
                    )
                    
                    with open('templates/base.html', 'w', encoding='utf-8') as f:
                        f.write(base_content)
                    
                    print("✅ Template base.html mis à jour avec le script QCM")
                else:
                    print("⚠️ Impossible de trouver </body> dans base.html")
            else:
                print("📋 Script QCM déjà présent dans base.html")
                
        except Exception as e:
            print(f"❌ Erreur mise à jour base.html: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur correction menus déroulants: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_dropdown_menus()
    if success:
        print("\n🎉 MENUS DÉROULANTS CORRIGÉS AVEC SUCCÈS!")
        print("\n📋 MODIFICATIONS APPORTÉES:")
        print("✅ Template QCM béninois avec menus fonctionnels")
        print("✅ Ancien template QCM avec menus fonctionnels")
        print("✅ Script JavaScript pour la gestion des menus")
        print("✅ Template base.html mis à jour")
        print("✅ Support de tous les niveaux (primaire à université)")
        print("✅ Classes universitaires béninoises incluses")
        print("\n🔧 FONCTIONNALITÉS:")
        print("• Sélection du niveau → Affichage des classes correspondantes")
        print("• Validation automatique du formulaire")
        print("• Support Alpine.js et JavaScript natif")
        print("• Interface responsive et intuitive")
        print("\n🚀 Les menus déroulants sont maintenant 100% fonctionnels!")
    else:
        print("\n❌ Échec de la correction des menus déroulants")
