# MealMate — Documento di Progetto Completo
> Documento di riferimento per Claude Code. Contiene tutto il necessario per costruire il progetto dall'inizio.

---

## 1. PANORAMICA

MealMate è una **Progressive Web App (PWA)** per la gestione della vita domestica familiare. Permette di gestire la dispensa di casa, la lista della spesa, le ricette e il calendario dei pasti.

### Obiettivi
- Gestione dispensa con stato presenza/assenza prodotti
- Lista della spesa intelligente con organizzazione per negozio e corsia
- Ricettario privato e pubblico condiviso tra utenti
- Calendario pasti con verifica automatica ingredienti in dispensa
- Condivisione in tempo reale tra membri della famiglia
- Notifiche push per scadenze, ingredienti mancanti, aggiornamenti
- Possibilità di commercializzazione con account separati per famiglia

---

## 2. STACK TECNOLOGICO

### Backend
- **Django 5.0** — framework principale
- **Django REST Framework** — API REST
- **Django Channels + Daphne** — WebSocket per real-time
- **PostgreSQL** — database principale
- **Redis** — channel layer per WebSocket + broker Celery
- **Celery + Celery Beat** — task asincroni e periodici
- **Simple JWT** — autenticazione JWT
- **Open Food Facts API** — dati prodotti da barcode (Python SDK ufficiale)

### Frontend
- **React 18** — UI
- **Vite + vite-plugin-pwa** — build tool e PWA support
- **Zustand** — state management
- **Axios** — HTTP client
- **@zxing/library** — barcode scanner via fotocamera
- **date-fns** — gestione date calendario
- **react-beautiful-dnd** — drag & drop per riordino corsie

### Infrastruttura
- **Railway** — hosting backend (Django + Celery + Redis + PostgreSQL)
- **Vercel** — hosting frontend React PWA
- **GitHub** — versionamento + CI/CD via GitHub Actions
- **AWS S3 o Railway Volumes** — storage immagini

---

## 3. STRUTTURA CARTELLE

```
mealmate/
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── accounts/
│   │   ├── families/
│   │   ├── products/
│   │   ├── stores/
│   │   ├── pantry/
│   │   ├── shopping/
│   │   ├── recipes/
│   │   ├── calendar/
│   │   ├── sharing/
│   │   └── notifications/
│   ├── core/
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── pagination.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── integrations/
│   │   ├── open_food_facts.py
│   │   └── recipe_importer.py
│   ├── channels/
│   │   ├── pantry.py
│   │   ├── shopping.py
│   │   ├── calendar.py
│   │   └── notifications.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── notifications.py
│   │   └── pantry.py
│   ├── manage.py
│   ├── requirements.txt
│   ├── Procfile
│   └── runtime.txt
├── frontend/
│   ├── public/
│   │   ├── manifest.json
│   │   └── sw.js
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── ws/
│   ├── package.json
│   └── vite.config.js
├── .github/
│   └── workflows/
│       ├── backend.yml
│       └── frontend.yml
├── .gitignore
├── README.md
└── docker-compose.yml
```

---

## 4. DATABASE — MODELLI

### Modello base (tutti i modelli ereditano da questo)
```python
# core/models.py
class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```

### accounts — Utenti
```
User
  - email (unique, usato come username)
  - name
  - avatar (immagine)
  - is_active
  - is_staff
  - created_at, updated_at
```

### families — Famiglie e Membri
```
Family
  - name
  - invite_code (unique, generato automaticamente)
  - created_by (FK User)

FamilyMember
  - family (FK Family)
  - user (FK User, nullable — null se membro senza account es. figlio)
  - name (usato se user è null)
  - avatar
  - birth_date (opzionale)
  - role (admin | member)
  - is_registered (bool)
  - joined_at
```

### products — Prodotti globali
```
ProductCategory
  - name
  - icon (opzionale)
  - order

Product
  - name
  - brand (opzionale)
  - barcode (opzionale, unique)
  - category (FK ProductCategory)
  - type (food | medicine | cleaning | bathroom | other)
  - default_unit (FK UnitOfMeasure)
  - image_url (opzionale, da Open Food Facts)
  - nutriscore (opzionale)
  - off_id (ID Open Food Facts, opzionale)
  - source (manual | open_food_facts | import)
  - created_by (FK User)

UnitOfMeasure
  - name (es. grammi, kg, ml, litri, pezzi, cucchiai, q.b.)
  - abbreviation (es. g, kg, ml, l, pz)
  - is_custom (bool — unità create da utenti)
```

### stores — Negozi
```
StoreCategory
  - name (supermercato | farmacia | polleria | pescheria | panetteria | macelleria | mercato | altro)
  - icon

Store
  - family (FK Family)
  - name (es. "Lidl Via Roma", "Farmacia Centrale")
  - store_category (FK StoreCategory)
  - is_default (bool — negozio predefinito per quella categoria)

StoreAisle
  - store (FK Store)
  - name (es. "Latticini", "Surgelati", "Carne")
  - order (intero, per drag & drop)

ProductStore
  - product (FK Product)
  - store (FK Store)
  - store_aisle (FK StoreAisle, opzionale)
  - preferred (bool — negozio preferito per questo prodotto)
```

### pantry — Dispensa
```
PantryItem
  - family (FK Family)
  - product (FK Product)
  - status (present | finished)
  - expiry_date (opzionale)
  - note (opzionale)
  - updated_by (FK User)

PantryHistory
  - pantry_item (FK PantryItem)
  - action (added | finished | updated)
  - performed_by (FK User)
  - timestamp
```

### shopping — Lista della spesa
```
ShoppingItem
  - family (FK Family)
  - product (FK Product)
  - quantity (opzionale — solo per la spesa, non per la dispensa)
  - unit (FK UnitOfMeasure, opzionale)
  - store (FK Store, opzionale)
  - store_aisle (FK StoreAisle, opzionale)
  - checked (bool)
  - unavailable (bool — non disponibile al negozio oggi)
  - added_by (FK User)
  - added_automatically (bool — aggiunto da calendario o dispensa)
  - source_recipe (FK Recipe, opzionale — da quale ricetta è stato aggiunto)
  - source_meal_date (date, opzionale — per quale data pasto)
  - note (opzionale)

ShoppingHistory
  - family (FK Family)
  - completed_at
  - completed_by (FK User)
  - items (JSON snapshot degli items al momento del completamento)
```

### recipes — Ricette
```
RecipeCategory
  - name
  - level (1 | 2)
  - parent (FK self, nullable — per il secondo livello)
  - order
  # Livello 1: colazione, antipasti, primi, secondi, contorni, dolci, bevande
  # Livello 2 (figli di secondi): carne, pesce, vegetariano, vegano ecc.

Recipe
  - title
  - description (opzionale)
  - cover_image (opzionale)
  - external_link (opzionale)
  - servings (opzionale)
  - prep_time (minuti, opzionale)
  - cook_time (minuti, opzionale)
  - difficulty (easy | medium | hard)
  - category (FK RecipeCategory)
  - family (FK Family, nullable — null se ricetta pubblica dell'app)
  - created_by (FK User)
  - is_public (bool)
  - forked_from (FK self, nullable — se è una copia personalizzata)
  - is_draft (bool)
  - average_rating (float, calcolato)
  - ratings_count (int, calcolato)

RecipeIngredient
  - recipe (FK Recipe)
  - product (FK Product)
  - quantity (opzionale — approccio B: quantità solo per la spesa)
  - unit (FK UnitOfMeasure, opzionale)
  - is_optional (bool)
  - note (opzionale, es. "a piacere", "tritato finemente")
  - order

RecipeInstruction
  - recipe (FK Recipe)
  - step_number (intero)
  - text
  - image (opzionale)

RecipeRating
  - recipe (FK Recipe)
  - user (FK User)
  - score (1-5)
  - comment (opzionale)
  - image (opzionale — foto del piatto finito)
  - created_at
  # unique_together: (recipe, user)

RecipeReport
  - recipe (FK Recipe)
  - reported_by (FK User)
  - reason (wrong_content | spam | inappropriate)
  - status (pending | reviewed | resolved)
  - created_at
```

### calendar — Calendario pasti
```
MealCalendar
  - family (FK Family)
  - name (es. "Famiglia", "Alette", "Adulti")
  - color (hex)
  - created_by (FK User)

MealSlot
  - calendar (FK MealCalendar)
  - date (date)
  - meal_type (breakfast | lunch | dinner | snack)
  # unique_together: (calendar, date, meal_type)

MealEntry
  - slot (FK MealSlot)
  - recipe (FK Recipe, nullable)
  - note (testo libero, usato se recipe è null es. "Pizza fuori")
  - assigned_members (M2M FamilyMember)
  - added_by (FK User)
  # Un MealSlot può avere più MealEntry (es. primo + secondo)

MealCalendarShare
  - calendar (FK MealCalendar)
  - shared_with_family (FK Family, nullable)
  - shared_with_user (FK User, nullable)
  - permission (read | write)
```

### sharing — Condivisione risorse
```
SharedResource
  - resource_type (recipe | calendar | shopping | pantry)
  - resource_id (UUID — id della risorsa)
  - shared_by (FK User)
  - shared_with_user (FK User, nullable)
  - shared_with_family (FK Family, nullable)
  - permission (read | write)
  - status (pending | accepted | rejected)
  - created_at
```

### notifications — Notifiche
```
Notification
  - user (FK User)
  - type (expiry | missing_ingredient | shopping_updated | menu_today | member_joined | recipe_rated | recipe_shared)
  - title
  - message
  - read (bool)
  - related_type (opzionale — tipo oggetto correlato)
  - related_id (opzionale — UUID oggetto correlato)
  - created_at

PushSubscription
  - user (FK User)
  - endpoint
  - p256dh
  - auth
  - user_agent (opzionale)
  - created_at

NotificationSettings
  - user (FK User, unique)
  - expiry_enabled (bool, default True)
  - expiry_days_before (int, default 2)
  - missing_ingredient_enabled (bool, default True)
  - shopping_updated_enabled (bool, default True)
  - menu_today_enabled (bool, default True)
  - menu_today_time (time, default 08:00)
  - recipe_rated_enabled (bool, default True)
  - recipe_shared_enabled (bool, default True)
```

---

## 5. API ENDPOINTS

Base URL: `/api/v1/`
Autenticazione: `Authorization: Bearer <JWT>`
Formato: JSON

### Auth
```
POST   /auth/register/
POST   /auth/login/
POST   /auth/logout/
POST   /auth/token/refresh/
POST   /auth/password/reset/
POST   /auth/password/confirm/
GET    /auth/me/
PATCH  /auth/me/
DELETE /auth/me/
```

### Families
```
POST   /families/
GET    /families/{id}/
PATCH  /families/{id}/
DELETE /families/{id}/
GET    /families/{id}/members/
POST   /families/{id}/members/
PATCH  /families/{id}/members/{mid}/
DELETE /families/{id}/members/{mid}/
POST   /families/{id}/invite/
POST   /families/join/
POST   /families/{id}/invite/approve/
POST   /families/{id}/invite/reject/
POST   /families/{id}/leave/
POST   /families/{id}/transfer-admin/
```

### Products
```
GET    /products/
POST   /products/
GET    /products/{id}/
PATCH  /products/{id}/
GET    /products/barcode/{code}/
POST   /products/scan/              # chiama Open Food Facts se non trovato nel DB
GET    /products/categories/
POST   /products/categories/
GET    /products/units/
```

### Stores
```
GET    /families/{id}/stores/
POST   /families/{id}/stores/
GET    /families/{id}/stores/{sid}/
PATCH  /families/{id}/stores/{sid}/
DELETE /families/{id}/stores/{sid}/
GET    /families/{id}/stores/{sid}/aisles/
POST   /families/{id}/stores/{sid}/aisles/
PATCH  /families/{id}/stores/{sid}/aisles/{aid}/
DELETE /families/{id}/stores/{sid}/aisles/{aid}/
POST   /families/{id}/stores/{sid}/aisles/reorder/
GET    /store-categories/
```

### Pantry
```
GET    /families/{id}/pantry/
POST   /families/{id}/pantry/
GET    /families/{id}/pantry/{pid}/
PATCH  /families/{id}/pantry/{pid}/
DELETE /families/{id}/pantry/{pid}/
POST   /families/{id}/pantry/{pid}/finish/
GET    /families/{id}/pantry/expiring/
GET    /families/{id}/pantry/history/
```

### Shopping
```
GET    /families/{id}/shopping/
POST   /families/{id}/shopping/
GET    /families/{id}/shopping/{iid}/
PATCH  /families/{id}/shopping/{iid}/
DELETE /families/{id}/shopping/{iid}/
POST   /families/{id}/shopping/{iid}/check/
POST   /families/{id}/shopping/{iid}/uncheck/
POST   /families/{id}/shopping/{iid}/unavailable/
POST   /families/{id}/shopping/quick-add/
POST   /families/{id}/shopping/complete/
GET    /families/{id}/shopping/history/
GET    /families/{id}/shopping/history/{hid}/
POST   /families/{id}/shopping/history/{hid}/reuse/
```

### Recipes
```
GET    /recipes/
POST   /recipes/
GET    /recipes/{id}/
PATCH  /recipes/{id}/
DELETE /recipes/{id}/
POST   /recipes/import/
POST   /recipes/{id}/publish/
POST   /recipes/{id}/unpublish/
POST   /recipes/{id}/fork/
POST   /recipes/{id}/report/
GET    /recipes/{id}/ingredients/
POST   /recipes/{id}/ingredients/
PATCH  /recipes/{id}/ingredients/{iid}/
DELETE /recipes/{id}/ingredients/{iid}/
GET    /recipes/{id}/instructions/
POST   /recipes/{id}/instructions/
PATCH  /recipes/{id}/instructions/{sid}/
DELETE /recipes/{id}/instructions/{sid}/
POST   /recipes/{id}/instructions/reorder/
GET    /recipes/{id}/ratings/
POST   /recipes/{id}/ratings/
PATCH  /recipes/{id}/ratings/{rid}/
DELETE /recipes/{id}/ratings/{rid}/
GET    /recipes/categories/
GET    /recipes/suggestions/
```

### Calendar
```
GET    /families/{id}/calendars/
POST   /families/{id}/calendars/
GET    /families/{id}/calendars/{cid}/
PATCH  /families/{id}/calendars/{cid}/
DELETE /families/{id}/calendars/{cid}/
GET    /families/{id}/calendars/{cid}/slots/
POST   /families/{id}/calendars/{cid}/slots/
GET    /families/{id}/calendars/{cid}/slots/{sid}/
DELETE /families/{id}/calendars/{cid}/slots/{sid}/
GET    /families/{id}/calendars/{cid}/slots/{sid}/entries/
POST   /families/{id}/calendars/{cid}/slots/{sid}/entries/
PATCH  /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/
DELETE /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/
POST   /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/copy/
POST   /families/{id}/calendars/{cid}/slots/{sid}/entries/{eid}/move/
POST   /families/{id}/calendars/{cid}/plan-week/
GET    /families/{id}/calendars/{cid}/check-pantry/
```

### Sharing
```
GET    /shares/
POST   /shares/
GET    /shares/{id}/
PATCH  /shares/{id}/
DELETE /shares/{id}/
POST   /shares/{id}/accept/
POST   /shares/{id}/reject/
```

### Notifications
```
GET    /notifications/
PATCH  /notifications/{id}/read/
POST   /notifications/read-all/
DELETE /notifications/{id}/
GET    /notifications/settings/
PATCH  /notifications/settings/
POST   /notifications/push/register/
DELETE /notifications/push/unregister/
```

### WebSocket (Django Channels)
```
WS /ws/families/{id}/pantry/
WS /ws/families/{id}/shopping/
WS /ws/families/{id}/calendars/
WS /ws/notifications/
```

---

## 6. LOGICHE DI BUSINESS CRITICHE

### Verifica dispensa quando si pianifica un pasto
Quando viene aggiunta una `MealEntry` con una `Recipe`:
1. Recupera tutti i `RecipeIngredient` della ricetta (escludi `is_optional=True`)
2. Per ogni ingrediente, verifica se il `Product` è presente in `PantryItem` con `status=present`
3. Calcola percentuale fattibilità: `(ingredienti_presenti / totale_ingredienti) * 100`
4. Se mancano ingredienti → crea `ShoppingItem` per ognuno con:
   - `added_automatically=True`
   - `source_recipe=recipe`
   - `source_meal_date=slot.date`
   - `quantity` presa da `RecipeIngredient`
5. Restituisce nella response: lista ingredienti mancanti + percentuale fattibilità

### Quando si spunta un prodotto nella lista della spesa
1. `ShoppingItem.checked = True`
2. Cerca `PantryItem` esistente per `(family, product)`
3. Se esiste → aggiorna `status=present`
4. Se non esiste → crea nuovo `PantryItem` con `status=present`
5. Invia evento real-time via WebSocket a tutti i membri della famiglia
6. Crea `PantryHistory` con `action=added`

### Quando si segna un prodotto come terminato in dispensa
1. `PantryItem.status = finished`
2. Crea `PantryHistory` con `action=finished`
3. Invia evento real-time via WebSocket
4. Restituisce nella response: `{"suggest_shopping": true}` — il frontend chiede all'utente se aggiungere alla lista

### Eliminazione pasto pianificato con ingredienti in lista
Quando si elimina una `MealEntry`:
1. Trova tutti i `ShoppingItem` con `source_recipe=recipe` e `source_meal_date=slot.date`
2. Elimina solo quelli con `added_automatically=True` e `checked=False`
3. Non toccare quelli già spuntati o aggiunti manualmente

### Suggerimenti ricette dalla dispensa
```
GET /recipes/suggestions/?family_id={id}
```
1. Recupera tutti i prodotti presenti in dispensa (`status=present`)
2. Per ogni ricetta (pubblica + della famiglia):
   - Calcola `ingredienti_presenti / ingredienti_totali`
   - Escludi ingredienti `is_optional=True` dal calcolo
3. Ordina per percentuale decrescente
4. Raggruppa: 100%, 75-99%, 50-74%, sotto 50%
5. Restituisce lista con percentuale fattibilità per ogni ricetta

### Importazione ricetta da URL
```
POST /recipes/import/
Body: { "url": "https://..." }
```
1. Chiama `integrations/recipe_importer.py` con l'URL
2. Il modulo chiama l'API esterna (fornita in seguito)
3. Se successo → restituisce dati estratti come anteprima (NON salva ancora)
4. Frontend mostra anteprima modificabile
5. Utente conferma → `POST /recipes/` con i dati (eventualmente modificati)
6. Se fallimento parziale → restituisce dati parziali + campi mancanti
7. Se fallimento totale → restituisce `{"success": false, "url": url}`

### Scansione barcode — Open Food Facts
```
POST /products/scan/
Body: { "barcode": "8001120956705" }
```
1. Cerca barcode nel database locale (`Product.barcode`)
2. Se trovato → restituisce prodotto locale
3. Se non trovato → chiama Open Food Facts API
4. Se trovato su OFF → crea `Product` nel DB locale con `source=open_food_facts`
5. Restituisce prodotto con flag `{"source": "open_food_facts", "needs_confirmation": true}`
6. Se non trovato su OFF → restituisce `{"found": false}` → frontend apre form manuale

---

## 7. TASK PERIODICI (Celery Beat)

### Controllo scadenze — ogni mattina alle 07:00
```python
# tasks/pantry.py
def check_expiring_products():
    # Trova tutti i PantryItem con expiry_date entro N giorni (N da NotificationSettings)
    # Per ogni item, invia notifica push a tutti i membri della famiglia
```

### Controllo ingredienti mancanti — ogni sera alle 20:00
```python
# tasks/notifications.py
def check_missing_ingredients():
    # Trova tutti i MealEntry di domani
    # Per ogni entry con Recipe, verifica ingredienti in dispensa
    # Se mancano ingredienti, invia notifica push
```

### Promemoria menu del giorno — ogni mattina all'orario configurato (default 08:00)
```python
# tasks/notifications.py
def send_daily_menu():
    # Trova tutti i MealEntry di oggi
    # Raggruppa per famiglia
    # Invia notifica push con riepilogo pasti del giorno
```

---

## 8. WEBSOCKET — EVENTI

### Formato messaggi WebSocket
```json
{
  "type": "pantry.updated",
  "action": "item_finished",
  "data": {
    "item_id": "uuid",
    "product_name": "Latte",
    "updated_by": "Mario"
  }
}
```

### Canali e eventi

**`/ws/families/{id}/pantry/`**
- `pantry.item_added` — nuovo prodotto aggiunto
- `pantry.item_updated` — prodotto modificato
- `pantry.item_finished` — prodotto segnato come terminato
- `pantry.item_removed` — prodotto rimosso

**`/ws/families/{id}/shopping/`**
- `shopping.item_added` — prodotto aggiunto alla lista
- `shopping.item_checked` — prodotto spuntato
- `shopping.item_unchecked` — spunta rimossa
- `shopping.item_removed` — prodotto rimosso
- `shopping.list_completed` — spesa completata

**`/ws/families/{id}/calendars/`**
- `calendar.entry_added` — pasto pianificato
- `calendar.entry_updated` — pasto modificato
- `calendar.entry_removed` — pasto rimosso

**`/ws/notifications/`**
- `notification.new` — nuova notifica in arrivo

---

## 9. INTEGRAZIONE OPEN FOOD FACTS

```python
# integrations/open_food_facts.py

import openfoodfacts

def get_product_by_barcode(barcode: str) -> dict | None:
    """
    Cerca un prodotto su Open Food Facts per barcode.
    Restituisce un dict con i dati del prodotto o None se non trovato.
    """
    api = openfoodfacts.API(
        user_agent="MealMate/1.0 (mealmate@example.com)"
    )
    result = api.product.get(barcode)
    
    if result and result.get('status') == 1:
        product = result['product']
        return {
            'name': product.get('product_name', ''),
            'brand': product.get('brands', ''),
            'barcode': barcode,
            'off_id': barcode,
            'image_url': product.get('image_front_url', ''),
            'nutriscore': product.get('nutriscore_grade', '').upper() or None,
            'category_name': product.get('categories', '').split(',')[0].strip(),
            'source': 'open_food_facts',
        }
    return None
```

**Note importanti:**
- Usare sempre il staging di OFF durante lo sviluppo: `https://world.openfoodfacts.net`
- Rate limit: 100 req/min per prodotto
- Non richiedere autenticazione per operazioni in lettura
- Compilare il form di utilizzo API: https://docs.google.com/forms/d/e/1FAIpQLSdIE3D8qvjC_zRJw1W8OmuHhsWJ_NSckiiniAHlfaVwUZCziQ/viewform

---

## 10. CONFIGURAZIONE DJANGO

### requirements.txt
```
django==5.0
djangorestframework==3.15
django-cors-headers==4.3
djangorestframework-simplejwt==5.3
channels==4.0
channels-redis==4.2
daphne==4.1
psycopg2-binary==2.9
django-environ==0.11
celery==5.3
redis==5.0
django-celery-beat==2.6
django-storages==1.14
boto3==1.34
openfoodfacts==1.1
Pillow==10.2
django-filter==23.5
drf-spectacular==0.27
pywebpush==2.0
gunicorn==21.2
whitenoise==6.6
```

### config/settings/base.py (struttura)
```python
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    # Apps
    'apps.accounts',
    'apps.families',
    'apps.products',
    'apps.stores',
    'apps.pantry',
    'apps.shopping',
    'apps.recipes',
    'apps.calendar',
    'apps.sharing',
    'apps.notifications',
]

AUTH_USER_MODEL = 'accounts.User'

ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('redis', 6379)]},
    },
}

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

### Procfile (Railway)
```
web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
worker: celery -A config worker -l info
beat: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### docker-compose.yml (sviluppo locale)
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: mealmate
      POSTGRES_USER: mealmate
      POSTGRES_PASSWORD: mealmate
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - ./backend/.env

  celery:
    build: ./backend
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file:
      - ./backend/.env

  celery-beat:
    build: ./backend
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file:
      - ./backend/.env

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
```

---

## 11. VARIABILI D'AMBIENTE

### backend/.env (sviluppo)
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://mealmate:mealmate@db:5432/mealmate
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Railway (produzione)
```
DEBUG=False
SECRET_KEY=<generata>
DATABASE_URL=<da Railway PostgreSQL plugin>
REDIS_URL=<da Railway Redis plugin>
ALLOWED_HOSTS=<dominio Railway>
CORS_ALLOWED_ORIGINS=<dominio Vercel>
AWS_ACCESS_KEY_ID=<opzionale per S3>
AWS_SECRET_ACCESS_KEY=<opzionale per S3>
AWS_STORAGE_BUCKET_NAME=<opzionale per S3>
```

---

## 12. ORDINE DI SVILUPPO CONSIGLIATO

### Backend
1. Setup progetto Django + docker-compose funzionante
2. `core` — modello base, permessi, paginazione
3. `accounts` — modello User custom + JWT auth
4. `families` — famiglie, membri, inviti
5. `products` — database prodotti + integrazione Open Food Facts
6. `stores` — negozi, corsie, drag & drop ordine
7. `pantry` — dispensa + WebSocket real-time
8. `shopping` — lista spesa + WebSocket real-time
9. `recipes` — ricette, ingredienti, istruzioni, rating, importazione URL
10. `calendar` — calendario, slot, pasti + verifica dispensa
11. `sharing` — condivisione risorse
12. `notifications` — notifiche push + Celery tasks
13. Deploy Railway + configurazione GitHub Actions

### Frontend
1. Setup React + Vite + PWA manifest + Service Worker
2. Autenticazione (login, registrazione, JWT refresh)
3. Gestione famiglia
4. Dispensa
5. Lista della spesa (con filtro per negozio)
6. Ricette (lista, dettaglio, creazione, importazione)
7. Calendario pasti
8. Barcode scanner
9. Notifiche push
10. Deploy Vercel

---

## 13. NOTE IMPORTANTI PER CLAUDE CODE

- **Tutti i modelli** estendono `TimeStampedModel` con UUID come PK
- **Autenticazione** sempre JWT, nessuna sessione Django
- **Permessi**: un utente può accedere solo ai dati della propria famiglia. Implementare permission class `IsFamilyMember` e `IsFamilyAdmin`
- **Real-time**: ogni modifica a dispensa, lista spesa e calendario deve inviare un evento WebSocket al gruppo della famiglia
- **Dispensa**: NO quantità, solo presenza/assenza. Le quantità esistono solo su `RecipeIngredient` e `ShoppingItem`
- **Lista spesa**: una sola lista attiva per famiglia (non multiple liste contemporanee). Storico separato
- **Ricette**: public = visibili a tutti gli utenti. Private = visibili solo alla famiglia
- **Open Food Facts**: usare staging durante sviluppo. Caching dei risultati nel DB locale obbligatorio
- **Notifiche push**: usare Web Push API con pywebpush. Il service worker React deve gestire le notifiche in background
- **Importazione ricette**: l'API esterna verrà fornita successivamente. Implementare il modulo con un'interfaccia chiara (`def import_from_url(url: str) -> dict`) da poter collegare facilmente
- **Barcode**: gestire normalizzazione barcode (EAN-8, EAN-13, UPC-A) — Open Food Facts ha documentazione su questo
