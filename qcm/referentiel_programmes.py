"""
Référentiel des programmes scolaires béninois pour la génération de QCM par l'IA.
L'IA doit TOUJOURS se baser sur ces chapitres pour générer des questions.
"""

REFERENTIEL_BENIN = {
    "PRIMAIRE": {
        "CI": {
            "Français": ["Découverte et apprentissage de l'alphabet", "Sons simples et syllabes", "Lecture de mots courants", "Comptines et chansons simples"],
            "Mathématiques": ["Dénombrement jusqu'à 10", "Comparaison de quantités", "Formes géométriques simples", "Additions simples jusqu'à 10"],
            "Éveil": ["Le corps humain", "L'environnement immédiat", "Les animaux domestiques du Bénin", "Les fruits et légumes locaux"],
        },
        "CP": {
            "Français": ["Sons complexes et syllabes complexes", "Lecture de phrases simples", "Compréhension de textes courts", "Production de phrases simples", "Dictée de mots simples", "Vocabulaire du quotidien béninois"],
            "Mathématiques": ["Numération de 0 à 100", "Addition de nombres à 2 chiffres", "Soustraction simple", "Mesure de longueurs", "Introduction à la monnaie (franc CFA)"],
            "Éveil": ["La famille et la communauté au Bénin", "Les saisons", "L'eau : utilisation et importance", "Les plantes cultivées au Bénin"],
        },
        "CE1": {
            "Français": ["Lecture courante et expression orale", "Grammaire : la phrase, le nom, le verbe", "Conjugaison : présent de l'indicatif", "Orthographe : accord en genre et en nombre", "Vocabulaire : synonymes et antonymes", "Production de textes courts"],
            "Mathématiques": ["Numération jusqu'à 1000", "Addition et soustraction à 3 chiffres", "Multiplication (tables de 1 à 5)", "Mesure : longueur, masse, capacité", "Introduction aux fractions simples", "Géométrie : figures planes"],
            "Sciences": ["Les êtres vivants et non vivants", "La croissance des plantes", "Les animaux du Bénin", "L'alimentation et la santé", "Le sol et ses constituants"],
            "Histoire-Géographie": ["Ma localité, mon département", "Les grandes régions naturelles du Bénin", "Histoire du Bénin : les royaumes"],
        },
        "CE2": {
            "Français": ["Lecture et compréhension de textes", "Grammaire : nature et fonction des mots", "Conjugaison : passé composé, imparfait, futur", "Orthographe d'usage et grammaticale", "Rédaction : lettre simple, récit", "Vocabulaire thématique"],
            "Mathématiques": ["Numération jusqu'à 10 000", "Multiplication (tables complètes)", "Division euclidienne", "Fractions ordinaires", "Périmètre et aire des figures simples", "Problèmes à étapes"],
            "Sciences": ["La digestion et la nutrition", "La reproduction des êtres vivants", "Le cycle de l'eau", "L'air et le vent", "L'hygiène corporelle et la santé"],
            "Histoire-Géographie": ["Le Bénin : carte, frontières, voisins", "Population et ethnies du Bénin", "La colonisation française au Bénin", "L'indépendance du Bénin (1960)"],
        },
        "CM1": {
            "Français": ["Lecture et analyse de textes variés", "Grammaire : propositions, types de phrases", "Conjugaison : tous les temps de l'indicatif", "Orthographe : accord du participe passé", "Rédaction : narration, description", "Vocabulaire : dérivation, composition"],
            "Mathématiques": ["Numération décimale", "Opérations sur les fractions", "Nombres décimaux", "Proportionnalité et pourcentages", "Géométrie : triangles, quadrilatères", "Volume du cube et du parallélépipède", "Problèmes de la vie courante"],
            "Sciences": ["La respiration et la circulation sanguine", "Les maladies courantes au Bénin", "L'électricité : notions de base", "Les ressources naturelles du Bénin", "La pollution et l'environnement"],
            "Histoire-Géographie": ["Les grands royaumes africains précoloniaux", "La traite négrière et son impact au Bénin", "Géographie physique du Bénin", "L'économie du Bénin"],
        },
        "CM2": {
            "Français": ["Lecture et commentaire de textes", "Grammaire complète du primaire", "Conjugaison : subjonctif présent, conditionnel", "Orthographe : révision complète", "Rédaction : lettre administrative, exposé", "Révisions CEP"],
            "Mathématiques": ["Révision de toutes les opérations", "Problèmes de proportionnalité", "Statistiques simples", "Géométrie dans l'espace", "Révisions CEP"],
            "Sciences": ["Le corps humain : révision complète", "L'écosystème et la chaîne alimentaire", "Les énergies renouvelables au Bénin", "Prévention des maladies et hygiène publique"],
            "Histoire-Géographie": ["L'Afrique de l'Ouest : géographie régionale", "L'histoire du Bénin de 1960 à nos jours", "La CEDEAO et l'intégration africaine", "Les activités économiques du Bénin"],
        },
    },

    "SECONDAIRE_1ER_CYCLE": {
        "6eme": {
            "Français": ["Lecture et compréhension de textes narratifs", "Grammaire : classes grammaticales", "Conjugaison : présent, imparfait, passé composé, futur", "Orthographe grammaticale", "Figures de style : comparaison, métaphore", "Rédaction : récit d'expérience vécue", "Expression orale"],
            "Mathématiques": ["Ensembles de nombres : N, Z, D, Q", "Opérations sur les entiers et les décimaux", "Fractions : simplification, addition, soustraction", "Proportionnalité et tableaux de proportionnalité", "Géométrie : angles, triangles, cercle", "Symétrie axiale", "Périmètre et aire", "Statistiques : lecture de tableaux et graphiques"],
            "SVT": ["La cellule : unité du vivant", "Classification des êtres vivants", "La nutrition chez les végétaux (photosynthèse)", "La nutrition chez les animaux", "La reproduction chez les végétaux", "La reproduction chez les animaux", "Les champignons et les microbes", "La biodiversité au Bénin"],
            "PCT": ["Sécurité au laboratoire", "La matière : états et changements d'état", "Mélanges homogènes et hétérogènes", "Dissolution et saturation", "La lumière : propagation rectiligne", "Ombres et pénombres", "Introduction aux circuits électriques simples"],
            "Histoire-Géographie": ["Géographie : les grands milieux naturels africains", "Géographie du Bénin : relief, fleuves, côtes", "Histoire : les premières civilisations humaines", "Les grands royaumes africains (Mali, Songhaï, Dahomey)", "La traite atlantique et ses conséquences", "La colonisation de l'Afrique"],
            "Anglais": ["Greetings and introductions", "The verb 'to be' and 'to have'", "Present Simple tense", "Numbers, dates, time", "Describing people and places", "Family and daily routine", "School vocabulary", "Benin and Africa (basic description)"],
            "Espagnol": ["Saludos y presentaciones", "El verbo 'ser' y 'tener'", "Presente simple", "Números, fechas, hora", "Descripción de personas y lugares", "Familia y rutina diaria", "Vocabulario escolar"],
        },
        "5eme": {
            "Français": ["Textes descriptifs et explicatifs", "Grammaire : fonctions syntaxiques (sujet, COD, COI)", "Conjugaison : plus-que-parfait, futur antérieur", "Discours direct et indirect", "Figures de style : métonymie, hyperbole", "Rédaction : portrait, description de lieu", "Initiation à la poésie"],
            "Mathématiques": ["Nombres relatifs : opérations", "Puissances de 10", "Calcul littéral : expressions algébriques", "Équations du 1er degré à une inconnue", "Proportionnalité : vitesse, taux", "Géométrie : quadrilatères, polygones réguliers", "Théorème de Thalès (introduction)", "Statistiques : moyenne, médiane"],
            "SVT": ["La digestion et l'absorption intestinale", "La respiration chez les êtres vivants", "La circulation sanguine", "Les systèmes immunitaires et les maladies", "Paludisme : cause, vecteur, prévention au Bénin", "VIH/SIDA : prévention", "La reproduction humaine", "La géologie : roches et minéraux du Bénin"],
            "PCT": ["Atomes et molécules", "Corps purs et mélanges", "Réactions chimiques : combustion", "L'air et ses constituants", "La pression atmosphérique", "L'électricité : loi d'Ohm, circuits en série et parallèle", "La chaleur et les changements d'état"],
            "Histoire-Géographie": ["La révolution industrielle et ses impacts en Afrique", "L'impérialisme colonial en Afrique de l'Ouest", "Le Bénin colonial : Dahomey sous la France", "Géographie : population et villes du Bénin", "Les ressources économiques de l'Afrique de l'Ouest", "Introduction à la géographie mondiale"],
            "Anglais": ["Past Simple tense", "Present Continuous", "Comparatives and superlatives", "Modal verbs (can, must, should)", "Health and environment vocabulary", "African history in English", "Reading comprehension"],
            "Espagnol": ["Pretérito indefinido (Past Simple)", "Presente continuo", "Comparativos y superlativos", "Verbos modales (poder, deber)", "Vocabulario de salud y medio ambiente", "Historia africana en español", "Comprensión lectora"],
        },
        "4eme": {
            "Français": ["Textes argumentatifs", "Grammaire : propositions subordonnées", "Conjugaison : subjonctif, conditionnel", "Étude de textes littéraires africains", "Rédaction : dissertation simple, lettre formelle", "Figures de rhétorique"],
            "Mathématiques": ["Factorisation et développement", "Systèmes d'équations à 2 inconnues", "Inéquations du 1er degré", "Fonctions linéaires et affines", "Théorème de Pythagore", "Trigonométrie dans le triangle rectangle", "Translations et homothéties", "Probabilités : notion de base"],
            "SVT": ["La génétique et l'hérédité", "La division cellulaire (mitose, méiose)", "Les groupes sanguins et transfusion", "Le système nerveux", "Les organes des sens", "L'environnement et les écosystèmes", "La déforestation et ses conséquences au Bénin"],
            "PCT": ["Les solutions aqueuses et pH", "Réactions acido-basiques", "Oxydation et corrosion", "Les métaux et leurs propriétés", "Électrolyse", "Loi de Coulomb", "Les ondes : son et lumière", "La radioactivité (introduction)"],
            "Histoire-Géographie": ["Les deux guerres mondiales", "La décolonisation africaine", "L'indépendance du Bénin et les régimes politiques (1960-1990)", "La Conférence Nationale de 1990", "Géographie : Afrique et monde en développement", "Les migrations et l'urbanisation au Bénin"],
            "Anglais": ["Present Perfect tense", "Passive voice", "Conditional sentences (type 1 and 2)", "Environment and development", "African literature in English", "Debate and opinion expression"],
            "Espagnol": ["Pretérito perfecto", "Voz pasiva", "Oraciones condicionales (tipo 1 y 2)", "Medio ambiente y desarrollo", "Literatura africana en español", "Debate y expresión de opiniones"],
        },
        "3eme": {
            "Français": ["Révision complète de la grammaire", "Textes littéraires et non-littéraires", "Rédaction : commentaire, résumé, synthèse", "Littérature africaine et béninoise", "Révision orthographe BEPC", "Expression écrite et orale — préparation BEPC"],
            "Mathématiques": ["Révision algèbre : équations, inéquations", "Fonctions : représentation graphique", "Statistiques et probabilités", "Géométrie dans l'espace (sphère, cône, cylindre)", "Trigonométrie", "Arithmétique : PGCD, PPCM", "Préparation BEPC"],
            "SVT": ["La reproduction sexuée et asexuée", "L'évolution des espèces", "La santé publique au Bénin (maladies endémiques)", "L'immunologie et les vaccins", "Les biotechnologies", "Géologie : séismes, volcans, tectonique", "Révision BEPC"],
            "PCT": ["Chimie organique : hydrocarbures", "Réactions chimiques quantitatives", "Énergie électrique et puissance", "Optique géométrique : lentilles", "Mécanique : forces et mouvement", "Révision BEPC"],
            "Histoire-Géographie": ["Le monde depuis 1990 : mondialisation", "La démocratie au Bénin depuis 1990", "Les organisations internationales (ONU, UA, CEDEAO)", "Développement durable et enjeux climatiques en Afrique", "Géopolitique de l'Afrique de l'Ouest", "Révision BEPC"],
            "Anglais": ["Full grammar revision", "Argumentative essay writing", "Reading comprehension on African topics", "Oral expression", "BEPC preparation"],
        },
    },

    "SECONDAIRE_2ND_CYCLE": {
        "Seconde": {
            "Français": ["Lecture analytique de textes littéraires", "Grammaire de texte", "Argumentation et dissertation", "Genres littéraires : roman, poésie, théâtre", "La littérature africaine et béninoise francophone", "Rédaction : commentaire composé"],
            "Mathématiques": ["Ensembles et logique", "Fonctions réelles : généralités", "Fonctions affines et quadratiques", "Suites numériques", "Trigonométrie : cercle trigonométrique", "Géométrie analytique : vecteurs", "Statistiques descriptives", "Probabilités"],
            "SVT": ["La cellule eucaryote et procaryote", "La photosynthèse", "La respiration cellulaire", "La génétique mendélienne", "Les mutations génétiques", "La biodiversité : espèces végétales et animales du Bénin", "L'écologie et les écosystèmes"],
            "PCT": ["Structure de l'atome", "Classification périodique des éléments", "Liaisons chimiques", "Oxydoréduction", "Cinétique chimique", "Mécanique : lois de Newton", "Électricité : circuits en régime continu", "Optique : réfraction et lentilles"],
            "Histoire-Géographie": ["Les grandes découvertes géographiques", "La Renaissance et les Lumières", "La révolution industrielle", "La géographie économique mondiale", "L'Afrique dans le monde contemporain", "Le Bénin et la CEDEAO"],
            "Philosophie": ["Introduction à la philosophie", "La connaissance et la vérité", "Le sujet et la conscience", "La société et la politique", "La morale et les valeurs"],
            "Anglais": ["Advanced grammar revision", "Reading comprehension (texts on Africa and the world)", "Essay writing", "Current affairs vocabulary", "Science and technology in English", "Debates and oral presentations"],
        },
        "Premiere_A1_A2": {
            "Français": ["Analyse littéraire approfondie", "Genres littéraires du monde africain", "Rédaction : dissertation littéraire", "La stylistique", "Œuvres au programme : littérature béninoise et africaine", "Langue française : syntaxe avancée"],
            "Philosophie": ["La conscience et l'inconscient", "La perception et le langage", "La raison et l'expérience", "Le désir et la liberté", "La technique et le travail"],
            "Histoire-Géographie": ["La Première Guerre mondiale", "La révolution russe", "La décolonisation en Afrique", "Géographie humaine et économique", "Le Bénin dans les relations internationales"],
            "Mathématiques": ["Fonctions : limites et dérivées", "Suites arithmétiques et géométriques", "Statistiques et probabilités avancées", "Trigonométrie"],
            "Anglais": ["Literature in English (African authors)", "Grammar : advanced structures", "Essay and argumentative writing", "African politics and society in English"],
            "SVT": ["La génétique et les maladies héréditaires", "La reproduction humaine", "Les maladies infectieuses au Bénin"],
        },
        "Premiere_B": {
            "Économie": ["Les agents économiques", "Les marchés et la formation des prix", "Le circuit économique", "La monnaie et le système bancaire", "Les échanges internationaux", "L'économie béninoise : agriculture, commerce, secteur informel"],
            "Mathématiques Appliquées": ["Statistiques : séries statistiques, représentations", "Calcul financier : intérêts, annuités", "Probabilités appliquées", "Fonctions économiques"],
            "Français": ["Textes économiques et sociaux", "Dissertation économique", "Communication professionnelle"],
        },
        "Premiere_C": {
            "Mathématiques": ["Fonctions : dérivation, étude de fonctions", "Suites numériques", "Trigonométrie avancée", "Nombres complexes (introduction)", "Géométrie vectorielle", "Probabilités : loi binomiale"],
            "PCT": ["Équilibres chimiques", "Électrochimie", "Thermodynamique chimique", "Mécanique : dynamique newtonienne", "Ondes mécaniques et lumineuses", "Électricité : courants alternatifs"],
            "SVT": ["La génétique moléculaire (ADN, ARN)", "La synthèse des protéines", "L'immunologie", "La neurophysiologie"],
        },
        "Premiere_D": {
            "SVT": ["La génétique moléculaire (ADN, ARN, protéines)", "Les mutations et maladies génétiques", "La physiologie de la reproduction", "L'immunologie : défenses de l'organisme", "La neurophysiologie : système nerveux", "Écologie : biomes et écosystèmes tropicaux", "La géologie structurale du Bénin"],
            "PCT": ["Chimie organique : alcanes, alcools, acides", "Réactions d'estérification", "La photosynthèse (aspect chimique)", "Mécanique newtonienne", "Optique géométrique"],
            "Mathématiques": ["Dérivation et applications", "Fonctions logarithme et exponentielle", "Statistiques et probabilités", "Suites numériques"],
        },
        "Premiere_G1_G2_G3": {
            "Économie": ["La production et les facteurs de production", "La consommation et les ménages", "L'État et les politiques économiques", "La croissance économique", "Le développement au Bénin"],
            "Droit": ["Introduction au droit", "Les personnes juridiques", "Les contrats commerciaux", "Le droit du travail au Bénin", "Le droit des sociétés"],
            "Comptabilité": ["Le bilan comptable", "Le compte de résultat", "La comptabilité générale (Plan Comptable SYSCOA)", "Les opérations d'achat et de vente", "L'inventaire et les amortissements"],
            "Techniques Commerciales": ["Le commerce et ses formes", "La mercatique (marketing)", "La distribution et la vente", "Le commerce international", "Les techniques de négociation"],
            "Mathématiques Appliquées": ["Arithmétique commerciale", "Les pourcentages et les remises", "Le calcul financier", "Les tableaux et graphiques statistiques"],
        },
        "Terminale_A1_A2": {
            "Français": ["Dissertation littéraire approfondie", "Commentaire composé", "Œuvres intégrales au programme (BAC)", "La littérature africaine et caribéenne", "Stylistique et rhétorique", "Révision BAC"],
            "Philosophie": ["La vérité et la raison", "L'art et la beauté", "La morale et la politique", "La religion et la foi", "Le bonheur et le sens de la vie", "La liberté et la responsabilité", "Révision BAC"],
            "Histoire-Géographie": ["La Seconde Guerre mondiale", "La Guerre Froide", "La mondialisation", "L'Afrique dans les relations internationales", "Géographie de développement", "Révision BAC"],
            "Anglais": ["African literature in English (Achebe, Soyinka...)", "Global issues : poverty, climate, democracy", "Advanced grammar", "Oral and written production", "Revision BAC"],
            "Espagnol": ["Grammaire avancée", "Textes littéraires", "Civilisation du pays (Espagne, Allemagne)", "Thèmes d'actualité", "Révision BAC"],
        },
        "Terminale_B": {
            "Économie": ["Les théories économiques (libéralisme, keynésianisme)", "La mondialisation économique", "Les déséquilibres économiques (chômage, inflation)", "L'économie béninoise dans l'espace UEMOA", "Le financement du développement en Afrique", "Révision BAC"],
            "Mathématiques Appliquées": ["Calcul financier avancé", "Statistiques inférentielles", "Probabilités", "Recherche opérationnelle", "Révision BAC"],
        },
        "Terminale_C": {
            "Mathématiques": ["Fonctions : limites, continuité, dérivabilité", "Étude complète de fonctions", "Intégration (primitives, intégrales)", "Équations différentielles", "Nombres complexes", "Géométrie dans l'espace", "Dénombrement et probabilités", "Révision BAC"],
            "PCT": ["Chimie : cinétique et équilibres", "Électrochimie et piles", "Chimie organique : polymères, biomolécules", "Thermodynamique", "Mécanique : lois de Newton, travail, énergie", "Électricité : régimes transitoires, courant alternatif", "Optique : interférences", "Physique nucléaire", "Révision BAC"],
            "SVT": ["L'expression des gènes", "La régulation hormonale", "L'immunologie avancée", "Les biotechnologies modernes", "Révision BAC"],
            "Français": ["Dissertation et commentaire BAC", "Littérature francophone africaine", "Révision BAC"],
            "Philosophie": ["La science et la vérité", "La technique et le progrès", "L'éthique scientifique", "Révision BAC"],
        },
        "Terminale_D": {
            "SVT": ["La régulation du milieu intérieur (homéostasie)", "La régulation hormonale et nerveuse", "L'immunologie : réactions immunitaires spécifiques", "Les vaccins et sérums", "La génétique des populations", "L'évolution et la sélection naturelle", "La géologie : formation des roches et orogenèse", "Les ressources géologiques du Bénin", "Révision BAC"],
            "PCT": ["Chimie organique avancée : acides aminés, glucides, lipides", "Les réactions enzymatiques", "Électricité et biologie : courants ioniques", "Optique : microscope, instruments d'optique", "Mécanique", "Révision BAC"],
            "Mathématiques": ["Fonctions et intégrales", "Statistiques et probabilités", "Suites et séries", "Révision BAC"],
        },
        "Terminale_G1": {
            "Techniques de Base de Secrétariat": ["La rédaction administrative (lettres, notes, rapports)", "Le classement et l'archivage", "L'accueil et la communication professionnelle", "La bureautique et l'informatique de gestion", "Organisation d'une réunion et compte-rendu", "Révision BAC"],
            "Économie": ["Les politiques économiques", "Le marché du travail", "Les finances publiques du Bénin", "Révision BAC"],
            "Droit": ["Le droit administratif", "Les marchés publics au Bénin", "Le droit du travail : contrats, licenciement", "La protection sociale", "Révision BAC"],
        },
        "Terminale_G2": {
            "Étude de Cas / Comptabilité": ["Les états financiers annuels", "L'analyse financière", "Les provisions et dépréciations", "La comptabilité des sociétés", "La TVA et les impôts au Bénin", "Révision BAC"],
            "Mathématiques Appliquées": ["Calcul financier : emprunts, amortissements", "Statistiques : régression, corrélation", "Probabilités et décision", "Révision BAC"],
        },
        "Terminale_G3": {
            "Techniques Commerciales": ["Le plan de marchéage (marketing mix)", "La gestion des stocks", "Le commerce électronique", "La négociation commerciale", "Le commerce international : Incoterms, douanes", "Révision BAC"],
        },
    },
}

# Mapping des niveaux de classe vers les clés du référentiel
CLASSE_TO_KEY = {
    "CI": "CI", "CP": "CP", "CE1": "CE1", "CE2": "CE2", "CM1": "CM1", "CM2": "CM2",
    "6ème": "6eme", "6eme": "6eme", "5ème": "5eme", "5eme": "5eme",
    "4ème": "4eme", "4eme": "4eme", "3ème": "3eme", "3eme": "3eme",
    "Seconde": "Seconde", "2nde": "Seconde",
    "Première A1": "Premiere_A1_A2", "Première A2": "Premiere_A1_A2",
    "Première B": "Premiere_B", "Première C": "Premiere_C", "Première D": "Premiere_D",
    "Première E": "Premiere_C",
    "Première G1": "Premiere_G1_G2_G3", "Première G2": "Premiere_G1_G2_G3", "Première G3": "Premiere_G1_G2_G3",
    "Terminale A1": "Terminale_A1_A2", "Terminale A2": "Terminale_A1_A2",
    "Terminale B": "Terminale_B", "Terminale C": "Terminale_C", "Terminale D": "Terminale_D",
    "Terminale E": "Terminale_C",
    "Terminale G1": "Terminale_G1", "Terminale G2": "Terminale_G2", "Terminale G3": "Terminale_G3",
}

# Mapping des matières vers les langues
MATIERE_LANGUES = {
    "anglais": "en", "anglais lv1": "en", "anglais lv2": "en", "english": "en",
    "espagnol": "es", "espagnol lv2": "es", "español": "es", "allemand": "de", "allemand lv2": "de",
}


def get_chapitres(classe: str, matiere: str) -> list:
    """
    Retourne la liste des chapitres officiels pour une classe et une matière données.
    Si non trouvé, retourne une liste vide.
    """
    # Normaliser la classe
    classe_key = CLASSE_TO_KEY.get(classe)
    if not classe_key:
        # Recherche approximative
        for key, val in CLASSE_TO_KEY.items():
            if key.lower() in classe.lower() or classe.lower() in key.lower():
                classe_key = val
                break
    
    if not classe_key:
        return []

    # Trouver le niveau (primaire, 1er cycle, 2nd cycle)
    for niveau_key, niveau_data in REFERENTIEL_BENIN.items():
        if classe_key in niveau_data:
            matieres = niveau_data[classe_key]
            # Recherche exacte de la matière
            if matiere in matieres:
                return matieres[matiere]
            # Recherche approximative
            for mat_key, chapitres in matieres.items():
                if mat_key.lower() == matiere.lower():
                    return chapitres
                if matiere.lower() in mat_key.lower() or mat_key.lower() in matiere.lower():
                    return chapitres
    
    return []


def get_all_matieres_for_classe(classe: str) -> dict:
    """Retourne toutes les matières et leurs chapitres pour une classe."""
    classe_key = CLASSE_TO_KEY.get(classe)
    if not classe_key:
        for key, val in CLASSE_TO_KEY.items():
            if key.lower() in classe.lower() or classe.lower() in key.lower():
                classe_key = val
                break
    
    if not classe_key:
        return {}

    for niveau_key, niveau_data in REFERENTIEL_BENIN.items():
        if classe_key in niveau_data:
            return niveau_data[classe_key]
    
    return {}


def get_langue_for_matiere(matiere: str) -> str:
    """Retourne le code langue pour une matière ('fr', 'en', 'es', 'de')."""
    matiere_lower = matiere.lower().strip()
    return MATIERE_LANGUES.get(matiere_lower, 'fr')


def get_referentiel_context(classe: str, matiere: str) -> str:
    """
    Génère un contexte formaté pour l'IA avec les chapitres officiels.
    Ce texte sera injecté dans le prompt de génération QCM.
    """
    chapitres = get_chapitres(classe, matiere)
    langue = get_langue_for_matiere(matiere)
    
    if not chapitres:
        return ""
    
    chapitres_str = "\n".join(f"  - {chap}" for chap in chapitres)
    
    langue_instruction = ""
    if langue == "en":
        langue_instruction = "CRITICAL: ALL questions, answer choices, and explanations MUST be written EXCLUSIVELY IN ENGLISH. Do NOT use any French."
    elif langue == "es":
        langue_instruction = "CRÍTICO: TODAS las preguntas, opciones y explicaciones deben estar escritas EXCLUSIVAMENTE EN ESPAÑOL. NO uses francés."
    elif langue == "de":
        langue_instruction = "KRITISCH: ALLE Fragen, Antwortmöglichkeiten und Erklärungen müssen AUSSCHLIEßLICH AUF DEUTSCH verfasst werden. Verwende KEIN Französisch."
    else:
        langue_instruction = "CRITIQUE : TOUTES les questions, choix de réponses et explications doivent être rédigés EXCLUSIVEMENT EN FRANÇAIS."
    
    return f"""PROGRAMME OFFICIEL BÉNINOIS — {classe} / {matiere}

CHAPITRES AUTORISÉS POUR CE QCM (ne JAMAIS sortir de cette liste) :
{chapitres_str}

{langue_instruction}

RÈGLE ABSOLUE : Tu ne dois générer des questions que sur UN ou PLUSIEURS de ces chapitres. Ne JAMAIS inventer de chapitres ou de notions hors-programme."""
