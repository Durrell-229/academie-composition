// Script pour les menus déroulants fonctionnels
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
                alert('Veuillez sélectionner un niveau d\'enseignement');
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
}