"""
Coefficients officiels du système éducatif béninois — Baccalauréat
Référence: Arrêté interministériel N°016-2003/MESRS/MEPS/METFP
"""

COEFFICIENTS_BENIN = {
    # ═══ PREMIER CYCLE — BEPC ═══
    "bepc": {
        "description": "Classes de 6ème à 3ème — Examen : BEPC",
        "matieres": {
            "Français": 4,
            "Communication Écrite": 4,
            "Mathématiques": 4,
            "SVT": 2,
            "Sciences de la Vie et de la Terre": 2,
            "PCT": 2,
            "Physique-Chimie-Technologie": 2,
            "Histoire-Géographie": 2,
            "Anglais": 2,
            "Espagnol": 1,
            "Allemand": 1,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
        }
    },

    # ═══ SECOND CYCLE — SÉRIES LITTÉRAIRES ═══
    "A1": {
        "intitule": "Lettres - Langues",
        "filiere": "Littéraire",
        "matieres": {
            "Français": 5,
            "Philosophie": 3,
            "Histoire-Géographie": 3,
            "Anglais": 5,
            "Espagnol": 4,
            "Allemand": 4,
            "Mathématiques": 2,
            "SVT": 1,
            "Sciences de la Vie et de la Terre": 1,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
            "Langue Nationale": 1,
        }
    },

    "A2": {
        "intitule": "Lettres - Sciences Humaines",
        "filiere": "Littéraire",
        "matieres": {
            "Français": 5,
            "Philosophie": 4,
            "Histoire-Géographie": 5,
            "Anglais": 3,
            "Espagnol": 2,
            "Allemand": 2,
            "Mathématiques": 2,
            "SVT": 1,
            "Sciences de la Vie et de la Terre": 1,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
            "Langue Nationale": 1,
        }
    },

    "B": {
        "intitule": "Lettres - Sciences Sociales",
        "filiere": "Littéraire / Sciences Sociales",
        "matieres": {
            "Français": 4,
            "Philosophie": 3,
            "Histoire-Géographie": 3,
            "Économie": 4,
            "Mathématiques Appliquées": 3,
            "Anglais": 3,
            "Espagnol": 2,
            "Allemand": 2,
            "SVT": 1,
            "Sciences de la Vie et de la Terre": 1,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
            "Langue Nationale": 1,
        }
    },

    # ═══ SECOND CYCLE — SÉRIES SCIENTIFIQUES ═══
    "C": {
        "intitule": "Sciences et Techniques (Mathématiques)",
        "filiere": "Scientifique",
        "matieres": {
            "Mathématiques": 7,
            "PCT": 5,
            "Physique-Chimie-Technologie": 5,
            "SVT": 2,
            "Sciences de la Vie et de la Terre": 2,
            "Français": 3,
            "Philosophie": 2,
            "Histoire-Géographie": 2,
            "Anglais": 2,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
            "Langue Nationale": 1,
        }
    },

    "D": {
        "intitule": "Biologie - Géologie",
        "filiere": "Scientifique",
        "matieres": {
            "SVT": 6,
            "Sciences de la Vie et de la Terre": 6,
            "Mathématiques": 4,
            "PCT": 4,
            "Physique-Chimie-Technologie": 4,
            "Français": 3,
            "Philosophie": 2,
            "Histoire-Géographie": 2,
            "Anglais": 2,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
            "Langue Nationale": 1,
        }
    },

    "E": {
        "intitule": "Mathématiques et Techniques",
        "filiere": "Technique",
        "matieres": {
            "Mathématiques": 6,
            "PCT": 5,
            "Physique-Chimie-Technologie": 5,
            "Technologie Industrielle": 4,
            "Français": 3,
            "Philosophie": 2,
            "Anglais": 2,
            "Histoire-Géographie": 1,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
        }
    },

    # ═══ SECOND CYCLE — SÉRIES GESTION ═══
    "G1": {
        "intitule": "Techniques Administratives",
        "filiere": "Commerciale / Gestion",
        "matieres": {
            "TBS": 5,
            "Techniques de Base de Secrétariat": 5,
            "Économie": 4,
            "Droit": 3,
            "Mathématiques Appliquées": 3,
            "Français": 3,
            "Anglais": 3,
            "Histoire-Géographie": 2,
            "Philosophie": 2,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
        }
    },

    "G2": {
        "intitule": "Techniques Quantitatives de Gestion",
        "filiere": "Commerciale / Gestion",
        "matieres": {
            "Étude de Cas": 5,
            "Comptabilité": 5,
            "Gestion": 5,
            "Mathématiques Appliquées": 4,
            "Économie": 4,
            "Droit": 3,
            "Français": 3,
            "Anglais": 2,
            "Histoire-Géographie": 2,
            "Philosophie": 2,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
        }
    },

    "G3": {
        "intitule": "Techniques Commerciales",
        "filiere": "Commerciale / Gestion",
        "matieres": {
            "Techniques Commerciales": 5,
            "Économie": 4,
            "Mathématiques Appliquées": 3,
            "Droit": 3,
            "Français": 3,
            "Anglais": 3,
            "Histoire-Géographie": 2,
            "Philosophie": 2,
            "EPS": 1,
            "Éducation Physique et Sportive": 1,
        }
    },
}


def get_coefficient(matiere, serie="bepc"):
    """
    Retourne le coefficient d'une matière pour une série donnée.
    Si la série n'est pas trouvée, utilise BEPC par défaut.
    Si la matière n'est pas trouvée, retourne 1.
    """
    # Normaliser la série (uppercase pour les séries littéraires/scientifiques)
    serie_key = serie.upper() if serie and len(serie) <= 3 else serie.lower() if serie else "bepc"
    
    # Mapping des clés de série
    serie_map = {
        "BEP": "bepc",
        "BEPC": "bepc",
        "A1": "A1",
        "A2": "A2",
        "B": "B",
        "C": "C",
        "D": "D",
        "E": "E",
        "G1": "G1",
        "G2": "G2",
        "G3": "G3",
    }
    
    serie_key = serie_map.get(serie_key, "bepc")
    serie_data = COEFFICIENTS_BENIN.get(serie_key, COEFFICIENTS_BENIN["bepc"])
    matieres = serie_data.get("matieres", {})
    
    # Recherche exacte
    if matiere in matieres:
        return matieres[matiere]
    
    # Recherche partielle (case-insensitive)
    matiere_lower = matiere.lower()
    for key, coeff in matieres.items():
        if key.lower() == matiere_lower:
            return coeff
    
    # Recherche par mots-clés
    keywords = {
        "math": ["Mathématiques", "Math"],
        "francais": ["Français", "Communication Écrite"],
        "philo": ["Philosophie"],
        "histoire": ["Histoire-Géographie"],
        "anglais": ["Anglais"],
        "espagnol": ["Espagnol"],
        "allemand": ["Allemand"],
        "svt": ["SVT", "Sciences de la Vie et de la Terre"],
        "pct": ["PCT", "Physique-Chimie-Technologie"],
        "eco": ["Économie", "Economie"],
        "droit": ["Droit"],
        "eps": ["EPS", "Éducation Physique et Sportive", "Education Physique et Sportive"],
        "techno": ["Technologie Industrielle", "Techniques Commerciales", "TBS", "Techniques de Base de Secrétariat"],
        "langue": ["Langue Nationale"],
        "secretaire": ["TBS", "Techniques de Base de Secrétariat"],
        "etude": ["Étude de Cas", "Etude de Cas"],
        "compta": ["Comptabilité", "Etude de Cas"],
        "gestion": ["Gestion", "Étude de Cas"],
    }
    
    for keyword, matiere_names in keywords.items():
        if keyword in matiere_lower:
            for name in matiere_names:
                if name in matieres:
                    return matieres[name]
    
    return 1  # Coefficient par défaut


def get_all_coefficients(serie="bepc"):
    """Retourne tous les coefficients d'une série."""
    serie_data = COEFFICIENTS_BENIN.get(serie, COEFFICIENTS_BENIN["bepc"])
    return serie_data.get("matieres", {})


def get serie_info(serie="bepc"):
    """Retourne les informations d'une série."""
    serie_data = COEFFICIENTS_BENIN.get(serie, COEFFICIENTS_BENIN["bepc"])
    return {
        "intitule": serie_data.get("intitule", "BEPC"),
        "filiere": serie_data.get("filiere", "Général"),
        "matieres": serie_data.get("matieres", {}),
    }
