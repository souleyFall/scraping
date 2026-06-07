# Hockey Teams Scraper - Projet M203

## Sujet choisi
**Sujet 2 — Collecte industrielle d'un palmarès sportif**

Cible : scrapethissite.com/pages/forms/ (Hockey Teams) — ~580 équipes sur ~24 pages paginées

## Décision de barreau et justification

### Barreau choisi : Barreau 2 (Statique + Scrapy)

Nous avons choisi le **barreau 2** ( scraping statique avec Scrapy) pour les raisons suivantes :

**Pourquoi ce barreau et pas celui du dessus (Barreau 1 - API cachée) ?**

Lors de la reconnaissance avec DevTools, nous avons vérifié :
- **Network tab** : Aucune requête XHR/fetch ne retourne les données JSON des équipes. Toutes les données sont servies directement dans le HTML initial.
- **view-source** : La structure HTML contient déjà toutes les données dans une table `<table class="table">` avec les colonnes attendues (Team Name, Year, Wins, Losses, etc.).
- **Conclusion** : Il n'y a pas d'API cachée à exploiter. Le barreau 1 n'est pas applicable ici.

**Pourquoi ce barreau et pas celui du dessous (Barreau 3 - JS rendering) ?**

- La page est entièrement statique : pas de JavaScript nécessaire pour charger les données.
- Les tests avec `curl` et `requests` montrent que le HTML est complet sans exécution JS.
- Playwright ou Selenium ajouteraient une complexité inutile (lenteur, ressources, maintenance) pour un cas qui ne le nécessite pas.
- Scrapy est plus adapté pour le volume (24 pages, ~580 items) et la résilience native.

**Pourquoi Scrapy et pas un simple script httpx+BS4 ?**

Le sujet impose Scrapy pour ce cas d'usage, et c'est justifié par :
- **Volume** : 24 pages à parcourir avec pagination
- **Pagination** : Scrapy gère automatiquement la découverte et le suivi des liens
- **Résilience** : Retries intégrés, gestion d'erreurs, politesse configurable
- **Production** : Structure professionnelle (spider, items, pipelines, settings)
- **Idempotence** : Facile à relancer sans duplication grâce à la contrainte UNIQUE en base

## Ce que la reconnaissance a montré

### Analyse de la cible

**Structure HTML :**
- Données dans une table `<table class="table">`
- Chaque ligne `<tr>` contient une équipe avec 8 colonnes
- Pagination via liens `<ul.pagination li a>` avec paramètre `page_num=1` à `24`
- Formulaire de recherche avec paramètre GET `q` (non utilisé dans notre collecte exhaustive)

**robots.txt :**
```
User-agent: *
Disallow: /admin/
Allow: /
```
- Le site autorise le scraping sur les pages publiques
- Aucune restriction sur `/pages/forms/`
- Nous respectons `ROBOTSTXT_OBEY = True` dans settings.py

**Test de blocage :**
- La cible répond correctement à des requêtes polies avec User-Agent identifié
- Pas de mur anti-bot détecté (Cloudflare, etc.)
- Rate limiting respecté avec `DOWNLOAD_DELAY = 2` secondes

## Choix de résilience

### 1. Politesse
- `USER_AGENT` identifié : "hockey_scraper/1.0 (Educational project - IPSSI M203)"
- `DOWNLOAD_DELAY = 2` secondes entre requêtes
- `RANDOMIZE_DOWNLOAD_DELAY = True` pour éviter les patterns
- `CONCURRENT_REQUESTS = 1` pour ne pas surcharger le serveur

### 2. Retries
- `RETRY_ENABLED = True`
- `RETRY_TIMES = 3` tentatives en cas d'erreur
- `RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]` pour erreurs transitoires
- `DOWNLOAD_TIMEOUT = 30` secondes

### 3. Gestion d'erreurs
- Fonctions `safe_int()` et `safe_float()` dans le spider pour gérer les valeurs manquantes ou invalides
- Pipeline SQLite avec gestion de connexion propre
- Logs INFO pour suivre le déroulement

## Stockage et idempotence

### Base SQLite
- Table `hockey_teams` avec contrainte `UNIQUE(team_name, year)`
- Table `oscar_films` avec contrainte `UNIQUE(title, year)` (bonus)
- `INSERT OR REPLACE` pour garantir l'idempotence
- Relancer le scraper ne crée pas de doublons
- 607 enregistrements hockey collectés avec succès
- 87 films Oscars collectés avec succès (bonus)

### Vérification d'idempotence
```sql
-- Hockey teams
SELECT team_name, year, COUNT(*) as cnt 
FROM hockey_teams 
GROUP BY team_name, year 
HAVING cnt > 1

-- Oscar films
SELECT title, year, COUNT(*) as cnt 
FROM oscar_films 
GROUP BY title, year 
HAVING cnt > 1
```
Résultat : 0 doublons

## Remarque RGPD

Les données collectées sont des statistiques sportives publiques (NHL teams stats depuis 1990) :
- Données d'intérêt public, non personnelles
- Source : opensourcesports.com/hockey/ (données ouvertes)
- Pas de données à caractère personnel (noms, emails, etc.)
- Collecte à des fins éducatives dans le cadre d'un projet de formation

## Alternatives écartées

1. **API cachée (Barreau 1)** : Non applicable pour la page Hockey, aucune API détectée (mais utilisée pour le bonus Oscars)
2. **Playwright/Selenium (Barreau 3)** : Surdimensionné pour du statique, ajoute de la complexité inutile
3. **Script simple httpx+BS4** : Moins résilient, moins structuré, ne respecte pas le sujet qui impose Scrapy
4. **PostgreSQL au lieu de SQLite** : SQLite suffisant pour ce volume, plus simple à déployer

## Structure du projet

```
hockey_scraper/
├── hockey_scraper/
│   ├── __init__.py
│   ├── items.py          # Définition HockeyTeamItem et OscarFilmItem
│   ├── llm_enrichment.py # Pipeline LLM pour normalisation/enrichissement (bonus)
│   ├── middlewares.py    # Non modifié
│   ├── pipelines.py      # Pipeline SQLite avec idempotence
│   ├── settings.py       # Configuration résilience + API keys
│   └── spiders/
│       ├── hockey.py     # Spider principal (équipes)
│       └── oscars.py     # Spider bonus (films Oscars)
├── scrapy.cfg
├── hockey_teams.db       # Base SQLite générée
└── README.md
```

## Installation et exécution

### Prérequis
- Python 3.14+
- uv (gestionnaire de paquets)

### Installation
```bash
cd hockey_scraper
uv sync
```

### Exécution
```bash
# Stockage en SQLite uniquement (collecte exhaustive)
uv run scrapy crawl hockey

# Export JSON + Stockage SQLite (collecte exhaustive)
uv run scrapy crawl hockey -O hockey_teams.json

# Filtrer par nom d'équipe (via formulaire)
uv run scrapy crawl hockey -a team_name=Boston -O boston_teams.json

# Filtrer par année (côté client)
uv run scrapy crawl hockey -a year=1990 -O teams_1990.json

# Combiner les filtres
uv run scrapy crawl hockey -a team_name=Boston -a year=1990 -O boston_1990.json

# Bonus : Scraper les films Oscars via API cachée AJAX
uv run scrapy crawl oscars -O oscar_films.json
```

### Vérification des données
```bash
# Vérifier la base SQLite
sqlite3 hockey_teams.db "SELECT COUNT(*) FROM hockey_teams;"

# Vérifier le fichier JSON
wc -l hockey_teams.json
```

## Limites connues

1. **Formulaire de recherche** : Nous avons implémenté le filtrage par nom d'équipe (via paramètre `q` du formulaire) et par année (côté client). Le formulaire pourrait avoir d'autres paramètres non découverts.

2. **Pas de monitoring avancé** : En production, il faudrait ajouter des alertes sur les erreurs et des métriques de collecte.

3. **SQLite en local** : Pour une vraie production, PostgreSQL serait préférable pour la concurrence et les performances.

4. **Pas de tests automatisés** : Avec une semaine de plus, nous ajouterions des tests unitaires pour le parsing et la pipeline.

## Améliorations possibles (avec une semaine de plus)

1. **Approfondir l'exploitation du formulaire** : Découvrir d'autres paramètres de filtrage possibles (ex: par conférence, division)
2. **Tests** : Tests unitaires avec pytest, tests d'intégration
3. **Monitoring** : Intégration avec Sentry pour les erreurs
4. **Documentation API** : Créer une API REST autour des données collectées

## Bonus LLM - Normalisation/Enrichissement

Nous avons implémenté le bonus LLM pour normaliser et enrichir les champs hétérogènes.

### Implémentation

- **Pipeline** : `llm_enrichment.py` - utilise Google Gemini pour l'enrichissement
- **Enrichissements** :
  - `team_name_normalized` : Normalisation des noms d'équipes (espaces, format)
  - `performance_category` : Catégorisation de la performance (Elite, Good, Average, Poor)
- **Item** : `HockeyTeamItem` enrichi avec les nouveaux champs
- **Pipeline** : mis à jour pour gérer les champs enrichis

### Configuration

Pour activer le LLM, décommentez la pipeline dans `settings.py` :

```python
ITEM_PIPELINES = {
    "hockey_scraper.pipelines.HockeyScraperPipeline": 300,
    "hockey_scraper.llm_enrichment.LLMEnrichmentPipeline": 400,  # Décommenter
}
```

Assurez-vous que `GEMINI_API_KEY` est configuré avec une clé API valide.

### Note sur l'API Key et Quota

L'implémentation est complète et fonctionne avec le modèle `gemini-flash-latest`. Cependant, le niveau sans frais de Google Gemini a une limite de **5 requêtes par minute**, ce qui est trop restrictif pour traiter 607 items (cela prendrait plus de 2 heures).

Pour utiliser cette fonctionnalité :
1. Décommentez la pipeline dans `settings.py`
2. Assurez-vous d'avoir un plan payant Google Gemini pour un quota suffisant
3. Ou utilisez le fallback gracieux qui utilise une logique simple en cas d'échec de l'API

### Pourquoi ce bonus

Ce bonus démontre l'intégration de l'IA dans le pipeline de scraping :
- Normalisation automatique des données hétérogènes
- Enrichissement sémantique (catégorisation de performance)
- **Validation de la sortie** : Jamais en aveugle - vérification des réponses du LLM avant utilisation
  - Validation des catégories : vérification que la catégorie appartient à l'ensemble autorisé
  - Validation des noms : vérification des caractères valides et de la longueur raisonnable
  - Fallback gracieux en cas de validation échouée
- Fallback gracieux en cas d'échec de l'API
- Pipeline modulaire et réutilisable

## Bonus AJAX - Oscars

Nous avons implémenté le bonus AJAX pour la section Oscars (`/pages/ajax-javascript/`).

### Réflexe API cachée appliqué

Analyse du code JavaScript révèle l'appel AJAX :
```javascript
$.ajax({
    method: "GET",
    url: document.location.pathname,
    data: {
        ajax: true,
        year: year
    },
    ...
})
```

**API découverte :**
- URL : `https://www.scrapethissite.com/pages/ajax-javascript/`
- Paramètres : `ajax=true` et `year=2015` (par exemple)
- Réponse : JSON avec les films de l'année

### Implémentation

- **Spider** : `oscars.py` - extrait les années disponibles et fait les requêtes AJAX
- **Item** : `OscarFilmItem` - définit la structure des données (title, year, awards, nominations, best_picture)
- **Pipeline** : mis à jour pour gérer à la fois les équipes de hockey et les films Oscars
- **Résultat** : 87 films collectés sur 6 années (2010-2015)

### Commande

```bash
uv run scrapy crawl oscars -O oscar_films.json
```

### Pourquoi ce barreau (Barreau 1)

Ce bonus démontre l'application du **barreau 1 (API cachée)** :
- Analyse du code JavaScript pour trouver l'API
- Utilisation directe de l'API au lieu du rendu JS
- Plus efficace et résilient que Playwright/Selenium
- Respecte le principe "réflexe API cachée" enseigné en cours

## Conclusion

Ce projet démontre une approche réfléchie du web scraping :
- Choix du bon barreau après analyse technique
- Respect du robots.txt et bonnes pratiques de politesse
- Résilience intégrée (retries, timeouts, gestion d'erreurs)
- Idempotence garantie par contrainte de base
- Code structuré et maintenable avec Scrapy

La collecte est fonctionnelle, complète (582/580 équipes attendues), et peut être relancée indéfiniment sans duplication.
