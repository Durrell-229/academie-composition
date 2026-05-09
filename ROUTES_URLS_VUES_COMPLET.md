# 📋 ROUTES, URLS ET VUES COMPLETES DU PROJET

## 🎯 URLs PRINCIPALES

### 1. Système QCM Béninois
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/qcm/` | `views.start_qcm` | `qcm/start.html` | Page démarrage QCM standard |
| `/qcm/take/` | `views.take_qcm` | `qcm/take.html` | Passer le QCM |
| `/qcm/submit/` | `views.submit_qcm` | - | Soumettre QCM |
| `/qcm/bulletin/<uuid>/` | `views.download_qcm_bulletin` | - | Télécharger bulletin QCM |
| `/qcm/benin/start/` | `views_benin.start_qcm_benin` | `qcm/start_benin.html` | Démarrer QCM béninois |
| `/qcm/benin/take/<int:session_id>/` | `views_benin.take_qcm_benin` | `qcm/take_benin.html` | Passer QCM béninois |
| `/qcm/benin/submit/<int:session_id>/` | `views_benin.submit_qcm_benin` | - | Soumettre QCM béninois |

**Fichiers:**
- `qcm/urls.py` - URLs principales QCM
- `qcm/urls_benin.py` - URLs QCM béninois
- `qcm/views.py` - Vues standard
- `qcm/views_benin.py` - Vues béninoises
- `qcm/models_benin.py` - Modèles QCMBeninConfig, QuestionBenin, ChoixBenin

---

### 2. Système Corrections & Corrigés Types
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/corrections/dashboard/` | `views.correction_dashboard` | `corrections/dashboard.html` | Dashboard corrections |
| `/corrections/corrige-types/` | `views.corrige_types_list` | `corrections/corrige_types_list.html` | Liste corrigés types |
| `/corrections/corrige-types/<int:id>/` | `views.corrige_type_detail` | `corrections/corrige_type_detail.html` | Détail corrigé type |
| `/corrections/corrige-types/upload/` | `views.upload_corrige_type` | `corrections/upload_corrige_type.html` | Upload corrigé type |
| `/corrections/baremes/` | `views.baremes_list` | `corrections/baremes_list.html` | Liste barèmes |

**Fichiers:**
- `corrections/urls.py` - URLs corrections
- `corrections/views.py` - Vues corrections
- `corrections/corrige_type_service.py` - Service gestion corrigés types
- `corrections/correction_with_corrige_type.py` - Service correction avec corrigés
- `corrections/baremes_service.py` - Service barèmes IA
- `corrections/integrated_correction_service.py` - Service correction intégré

---

### 3. Système Temps Réel (WebSocket)
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/realtime/dashboard/` | `views.realtime_dashboard` | `realtime/dashboard.html` | Dashboard temps réel |
| `/realtime/notifications/` | `views.realtime_notifications` | `realtime/notifications.html` | Notifications temps réel |
| `/realtime/bulletins/` | `views.realtime_bulletins` | `realtime/bulletins.html` | Bulletins temps réel |
| `/realtime/exam/<int:exam_id>/status/` | `views.exam_room_status` | - | Statut salle d'examen (JSON) |

**WebSocket Routes:**
| WebSocket URL | Consumer | Description |
|---------------|----------|-------------|
| `ws://host/ws/exam/<exam_id>/` | `ExamRoomConsumer` | Salle d'examen en temps réel |
| `ws://host/ws/notifications/` | `NotificationConsumer` | Notifications push |
| `ws://host/ws/bulletin/` | `BulletinUpdateConsumer` | Mises à jour bulletins |

**Fichiers:**
- `realtime/urls.py` - URLs HTTP temps réel
- `realtime/routing.py` - Routing WebSocket
- `realtime/views.py` - Vues temps réel
- `realtime/consumers.py` - Consumers WebSocket
- `realtime/services.py` - Service temps réel
- `academie_numerique/asgi.py` - Configuration ASGI

---

### 4. Service NVIDIA OCR
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/ocr/test/` | `ocr_views.test_ocr` | `ai_engine/test_ocr.html` | Test OCR NVIDIA |
| `/ocr/upload/` | `ocr_views.upload_for_ocr` | - | Upload fichier pour OCR (JSON) |

**Fichiers:**
- `ai_engine/urls.py` - URLs OCR
- `ai_engine/views.py` - Vues OCR
- `ai_engine/nvidia_ocr.py` - Service NVIDIA OCR (endpoint: `ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v1`)

---

### 5. Système d'Examens
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/exams/` | `views.exam_list_view` | `exams/exam_list.html` | Liste des examens |
| `/exams/create/` | `views.exam_create_view` | `exams/exam_form.html` | Créer un examen |
| `/exams/<int:pk>/` | `views.exam_detail_view` | `exams/exam_detail.html` | Détail examen |
| `/exams/<int:exam_id>/download/<str:type>/` | `views.download_exam_file` | - | Télécharger fichier examen |
| `/examens-nationaux/` | - | - | Examens nationaux Bénin |

**Fichiers:**
- `exams/urls.py` - URLs examens
- `exams/views.py` - Vues examens
- `exams/models.py` - Modèles Exam, ExamFile, ExamAssignment

---

### 6. Système de Compositions
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/compositions/` | `views.composition_list` | `compositions/list.html` | Liste compositions |
| `/compositions/<int:exam_id>/room/` | `views.composition_room` | `compositions/room.html` | Salle de composition |
| `/compositions/<int:exam_id>/submit/` | `views.submit_composition` | - | Soumettre composition |

**Fichiers:**
- `compositions/urls.py` - URLs compositions
- `compositions/views.py` - Vues compositions
- `compositions/tasks.py` - Tâches asynchrones correction

---

### 7. Système de Bulletins
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/bulletins/` | `views.bulletin_list` | `bulletins/list.html` | Liste bulletins |
| `/bulletins/<int:id>/` | `views.bulletin_detail` | `bulletins/detail.html` | Détail bulletin |
| `/bulletins/<int:id>/download/` | `views.download_bulletin` | - | Télécharger bulletin PDF |
| `/bulletins/generate/` | `views.generate_bulletin` | - | Générer bulletin |

**Fichiers:**
- `bulletins/urls.py` - URLs bulletins
- `bulletins/views.py` - Vues bulletins
- `bulletins/bulletin_auto_generator.py` - Génération automatique

---

### 8. Système d'Authentification
| Route | Vue | Template | Description |
|-------|-----|----------|-------------|
| `/accounts/register/` | `views.register_view` | `accounts/register.html` | Inscription |
| `/accounts/login/` | `views.login_view` | `accounts/login.html` | Connexion |
| `/accounts/logout/` | `views.logout_view` | - | Déconnexion |
| `/accounts/profile/` | `views.profile_view` | `accounts/profile.html` | Profil utilisateur |
| `/accounts/dashboard/` | `views.dashboard_view` | `accounts/dashboard.html` | Dashboard utilisateur |

**Fichiers:**
- `accounts/urls.py` - URLs authentification
- `accounts/views.py` - Vues authentification
- `accounts/models.py` - Modèle User personnalisé

---

### 9. API REST
| Route | Description |
|-------|-------------|
| `/api/v1/` | API REST principale |
| `/api/core/` | API Core |

**Fichiers:**
- `api/v1/router.py` - Router API v1
- `core/api_urls.py` - URLs API core

---

### 10. Autres Modules
| Route | Module | Description |
|-------|--------|-------------|
| `/cours/` | Cours | Gestion des cours |
| `/devoirs/` | Devoirs | Gestion des devoirs |
| `/correction/` | Correction | Système de correction (legacy) |
| `/certificates/` | Certifications | Certificats |
| `/plagiat/` | Plagiat | Détection plagiat |
| `/gamification/` | Gamification | XP, badges, classements |
| `/audit/` | Audit Trail | Logs d'audit |
| `/webhooks/` | Webhooks | Intégrations externes |
| `/subscriptions/` | Subscriptions | Abonnements |
| `/notifications/` | Notifications | Notifications standard |

---

## 🔧 CONFIGURATION

### Settings.py (Modifications du jour)
```python
THIRD_PARTY_APPS = [
    'ninja',
    'corsheaders',
    'storages',
    'channels',  # AJOUTÉ
]

LOCAL_APPS = [
    'accounts',
    'core',
    'exams',
    'compositions',
    'correction',
    'bulletins',
    'notifications',
    'ai_engine',
    'certifications',
    'qcm',
    'plagiat',
    'gamification',
    'audittrail',
    'webhooks',
    'subscriptions',
    'realtime',      # AJOUTÉ
    'corrections',   # AJOUTÉ
    'cours',
    'devoirs',
]
```

### URLs Principales (academie_numerique/urls.py)
```python
urlpatterns = [
    path('', promo_video_view, name='promo'),
    path('accueil/', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('api/v1/', v1_api.urls),
    path('api/core/', core_api.urls),
    path('accounts/', include('accounts.urls')),
    path('exams/', include('exams.urls')),
    path('compositions/', include('compositions.urls')),
    path('notifications/', include('notifications.urls')),
    path('correction/', include('correction.urls')),
    path('bulletins/', include('bulletins.urls')),
    path('certificates/', include('certifications.urls')),
    path('qcm/', include('qcm.urls')),          # INCLUT qcm/urls_benin.py
    path('plagiat/', include('plagiat.urls')),
    path('gamification/', include('gamification.urls')),
    path('audit/', include('audittrail.urls')),
    path('webhooks/', include('webhooks.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('cours/', include('cours.urls')),
    path('devoirs/', include('devoirs.urls')),
    path('examens-nationaux/', include('exams.examens_nationaux_urls')),
    path('realtime/', include('realtime.urls')),      # AJOUTÉ
    path('corrections/', include('corrections.urls')), # AJOUTÉ
    path('ocr/', include('ai_engine.urls')),          # AJOUTÉ
]
```

---

## 📁 FICHIERS CRÉÉS/MODIFIÉS AUJOURD'HUI

### Nouveaux fichiers
- `realtime/__init__.py`
- `realtime/apps.py`
- `realtime/models.py`
- `realtime/admin.py`
- `realtime/views.py`
- `realtime/urls.py`
- `realtime/routing.py`
- `realtime/consumers.py`
- `realtime/services.py`
- `corrections/__init__.py`
- `corrections/views.py`
- `corrections/urls.py`
- `ai_engine/views.py`
- `ai_engine/urls.py`
- `templates/realtime/dashboard.html`
- `templates/realtime/notifications.html`
- `templates/realtime/bulletins.html`
- `templates/corrections/dashboard.html`
- `templates/corrections/corrige_types_list.html`
- `templates/ai_engine/test_ocr.html`
- `academie_numerique/asgi.py`
- `install_realtime.py`
- `test_nvidia_api.py`
- `test_nvidia_api_v2.py`
- `test_nvidia_api_v3.py`
- `test_nemotron_ocr_v1.py`
- `test_nemotron_ocr_v1_correct.py`
- `test_nemotron_parse.py`
- `test_separation_stricte.py`
- `test_all_integrations.py`
- `fix_correction_types.py`
- `implement_realtime_system.py`
- `integrate_all_components.py`
- `REALTIME_DOCUMENTATION.md`

### Fichiers modifiés
- `academie_numerique/settings.py` - Ajout channels, realtime, corrections
- `academie_numerique/urls.py` - Ajout routes realtime, corrections, ocr
- `qcm/urls.py` - Ajout include urls_benin
- `qcm/models_benin.py` - Correction syntaxe apostrophe
- `ai_engine/nvidia_ocr.py` - Configuration Nemotron OCR v1
- `requirements.txt` - Ajout channels, redis, daphne

---

## 🚀 SERVICES IA OPÉRATIONNELS

| Service | Fichier | Status | Description |
|---------|---------|--------|-------------|
| NVIDIA OCR | `ai_engine/nvidia_ocr.py` | ✅ OK | OCR avec Nemotron v1 |
| Multi-IA | `ai_engine/multi_ai.py` | ✅ OK | Groq/Gemini/Mistral/DeepSeek |
| Corrigés Types | `corrections/corrige_type_service.py` | ✅ OK | Gestion corrigés types |
| Correction IA | `corrections/correction_with_corrige_type.py` | ✅ OK | Correction avec corrigés |
| Barèmes IA | `corrections/baremes_service.py` | ✅ OK | Génération barèmes |
| Bulletins Auto | `bulletins/bulletin_auto_generator.py` | ✅ OK | Génération automatique |
| Temps Réel | `realtime/services.py` | ✅ OK | WebSocket temps réel |
| QCM Bénin | `qcm/views_benin.py` | ✅ OK | QCM adapté Bénin |

---

## 🎯 ACCÈS FRONTEND - RÉCAPITULATIF

### Pages Principales
- **Accueil** : `/`
- **Dashboard** : `/accounts/dashboard/`
- **Admin** : `/admin/`

### Examens & Compositions
- **Liste examens** : `/exams/`
- **Créer examen** : `/exams/create/`
- **Salle composition** : `/compositions/<exam_id>/room/`

### QCM
- **QCM Standard** : `/qcm/start/`
- **QCM Bénin** : `/qcm/benin/start/`

### Corrections
- **Dashboard corrections** : `/corrections/dashboard/`
- **Corrigés types** : `/corrections/corrige-types/`
- **Barèmes** : `/corrections/baremes/`

### Temps Réel
- **Dashboard temps réel** : `/realtime/dashboard/`
- **Notifications temps réel** : `/realtime/notifications/`
- **Bulletins temps réel** : `/realtime/bulletins/`

### OCR & IA
- **Test OCR** : `/ocr/test/`

### Bulletins
- **Liste bulletins** : `/bulletins/`

---

*Document généré le 9 mai 2026 - Toutes les routes, URLs et vues du projet*
