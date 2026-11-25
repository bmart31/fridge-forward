# Fridge Forward

Tell Fridge Forward what's in your fridge and it tells you what you can cook with it, and only that.

> **Status: early MVP.** It is deliberately rough so that it can be improved step by step. There is only minimal styling, no user accounts and a dataset of 39 recipes. See [Known limitations & next steps](#known-limitations--next-steps).

---

## Contents

1. [What the app does](#what-the-app-does)
2. [Tech stack](#tech-stack)
3. [Getting started](#getting-started)
4. [Day-to-day commands](#day-to-day-commands)
5. [Project structure](#project-structure)
6. [How it works](#how-it-works)
7. [Managing recipes](#managing-recipes)
8. [Testing](#testing)
9. [Development workflow](#development-workflow)
10. [Troubleshooting](#troubleshooting)
11. [Known limitations & next steps](#known-limitations--next-steps)

---

## What the app does

Everything is on a single page (`/`):

1. **Your fridge.** Type ingredients into the box and press Enter. You can add several at once by separating them with commas (`eggs, milk, cheese`). Each ingredient has an **x** button to remove it.
2. **You can make.** This lists every recipe whose ingredients you *all* have, as a card showing the recipe name, its ingredients and a numbered method behind a **Show method** toggle. If nothing matches, it says *"No recipes match your ingredients."*

### Key User Requirements

The app is built against these requirements. Every change should keep them working.

| ID | Requirement | How it's met | Tested by |
|----|-------------|--------------|-----------|
| KUR-01 | The user shall be able to record the ingredients they currently have. | `PantryItem` model, plus the add and remove views | `AddIngredientTests` |
| KUR-02 | The user shall be able to receive recipe suggestions based on the ingredients they have recorded. | "You can make" section, filled by `makeable_recipes()` | `MatchingTests` |
| KUR-03 | Only recipes that can be made with the ingredients they have are offered. If none match, none are offered. | `makeable_recipes()` returns a recipe only if **every** one of its ingredients is in the pantry | `MatchingTests` (`test_sr_2_2_*`, `test_sr_3_1_*`) |
| KUR-04 | Ingredients can be added quickly and easily, with no instructions or training. | One autofocused text box, comma-separated entry, autocomplete from known ingredients, case and whitespace ignored | `test_add_comma_separated_and_normalised` |

---

## Tech stack

| Thing | Choice | Notes |
|-------|--------|-------|
| Language | Python 3.9+ | Developed on 3.9.6 |
| Framework | Django 4.2 (LTS) | Pinned in `requirements.txt`. 4.2 is the newest Django that supports Python 3.9. |
| Database | SQLite | A single file (`db.sqlite3`) created on first `migrate`. It is not committed to git. |
| Frontend | Plain Django templates | No JavaScript and no CSS framework yet |

The project uses **Django only**: there is no separate frontend framework or API layer. New features should stay inside that structure (models, views, templates, URLs).

---

## Getting started

### 1. Prerequisites

- **Python 3.9 or newer.** Check with `python3 --version` (on Windows: `py --version`).
- **Git**

Nothing else needs installing globally. Django is installed inside a project-local virtual environment.

### 2. Clone and set up (one time)

**macOS / Linux**

```bash
git clone https://github.com/bmart31/fridge-forward.git fridge-forward
cd fridge-forward

python3 -m venv .venv              # create an isolated Python environment
source .venv/bin/activate          # activate it (your prompt shows "(.venv)")
pip install -r requirements.txt    # install Django and python-dotenv
cp .env.example .env               # create your local settings file
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/bmart31/fridge-forward.git fridge-forward
cd fridge-forward

py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### 3. Add a secret key to `.env`

Django needs a secret key, and it is **not** stored in the repo. Generate one:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Open `.env` and paste the output after `DJANGO_SECRET_KEY=` (no quotes or spaces needed). Leave `DJANGO_DEBUG=True` for local development.

| Variable | Required | What it does |
|----------|----------|--------------|
| `DJANGO_SECRET_KEY` | Yes | Django's secret key. Everyone generates their own. Never share or commit it. |
| `DJANGO_DEBUG` | No (default `False`) | `True` shows detailed error pages. Only use it locally. |
| `DJANGO_ALLOWED_HOSTS` | No | Comma-separated hostnames, e.g. `example.com,www.example.com`. Can stay empty locally while debug is on. |

`.env` is git-ignored. Real environment variables take precedence over it, which is how a hosting service would supply these settings.

Then create the database and load the recipe dataset:

```bash
python manage.py migrate
python manage.py loaddata recipes
```

### 4. Run it

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Stop the server with `Ctrl+C`.

### 5. Quick check that everything works

1. Type `bread, cheese` and press Enter.
2. **Cheese toast** should appear under "You can make".
3. Remove `cheese`. The page should now say *"No recipes match your ingredients."*

### 6. (Optional) Admin access

To add or edit recipes through Django's built-in admin site:

```bash
python manage.py createsuperuser   # follow the prompts
```

Then go to **http://127.0.0.1:8000/admin/**.

> **Remember:** run `source .venv/bin/activate` (or the Windows equivalent) in every new terminal before using `python manage.py ...`. If you get `ModuleNotFoundError: No module named 'django'`, you skipped this step.

---

## Day-to-day commands

All of these assume the virtual environment is active.

| Task | Command |
|------|---------|
| Start the dev server | `python manage.py runserver` |
| Run on a different port | `python manage.py runserver 8080` |
| Run all tests | `python manage.py test` |
| Create migrations after changing `models.py` | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Create an admin user | `python manage.py createsuperuser` |
| Interactive shell with Django loaded | `python manage.py shell` |
| Load / refresh the recipe dataset | `python manage.py loaddata recipes` |
| Time suggestions with 1,000 dummy recipes | `python manage.py benchmark_suggestions` (add `--recipes 10000` for more). Leaves your data unchanged. |
| Reset the database completely | Delete `db.sqlite3`, then `python manage.py migrate` and `python manage.py loaddata recipes` |
| Add a new Python dependency | `pip install <pkg>`, then add it with a version range to `requirements.txt` |

---

## Project structure

```
fridge-forward/
├── manage.py                   # Django's command-line entry point
├── requirements.txt            # Python dependencies: keep this up to date
├── README.md
├── .gitignore                  # ignores .venv/, db.sqlite3, __pycache__, .env
├── .env.example                # template for your local .env (secret key, debug, hosts)
│
├── fridgeforward/              # Project configuration (not app logic)
│   ├── settings.py             # Installed apps, database, etc.
│   ├── urls.py                 # Root URLs: /admin/ and everything else → pantry
│   ├── wsgi.py / asgi.py       # Server entry points (used when deploying)
│
└── pantry/                     # The one app: all features live here
    ├── models.py               # Ingredient, PantryItem, Recipe
    ├── services.py             # makeable_recipes(): the matching logic
    ├── views.py                # home, add_ingredient, remove_ingredient
    ├── urls.py                 # URL routes for the views above
    ├── admin.py                # Registers models with the Django admin
    ├── benchmark.py            # Generates dummy recipes for performance checks
    ├── tests.py                # Tests, labelled with the KUR/SR they cover
    ├── management/commands/
    │   └── benchmark_suggestions.py # `manage.py benchmark_suggestions`
    ├── templates/pantry/
    │   ├── home.html           # The single page
    │   └── _recipe_card.html   # One suggested recipe (name, ingredients, method)
    ├── fixtures/
    │   └── recipes.json        # The recipe dataset (load with `loaddata recipes`)
    └── migrations/
        ├── 0001_initial.py     # Creates the tables
        ├── 0002_seed_recipes.py# Loads the 7 original starter recipes
        └── 0003_singular_ingredient_names.py # eggs→egg, tomatoes→tomato
```

### URLs

| URL | Method | View | What it does |
|-----|--------|------|--------------|
| `/` | GET | `home` | Shows the pantry, the add box and matching recipes |
| `/add/` | POST | `add_ingredient` | Adds one or more comma-separated ingredients, then redirects to `/` |
| `/remove/<id>/` | POST | `remove_ingredient` | Removes a pantry item, then redirects to `/` |
| `/admin/` | GET/POST | Django admin | Manage recipes and ingredients |

The add and remove routes use the standard *Post/Redirect/Get* pattern: they change data and then redirect, so refreshing the page never re-submits a form.

---

## How it works

### Data model

```
Ingredient                  PantryItem                    Recipe
──────────                  ──────────                    ──────
id                          id                            id
name (unique, lowercase) ◄──ingredient (one-to-one)       name
                            added_at                      instructions
         ▲                                                ingredients (many-to-many)
         └────────────────────────────────────────────────────┘
```

- **Ingredient** is the master list of ingredient names. It is shared by the pantry and recipes, which is what makes matching possible. Names are **normalised** (spaces trimmed, lowercased) whenever they are saved, so `" Eggs "` and `"eggs"` are the same ingredient.
- **PantryItem** is "the user has this ingredient right now". It is one-to-one with `Ingredient`, so an ingredient can't be in the pantry twice.
- **Recipe** has a name, free-text instructions, and the set of ingredients it needs.

### Matching logic (KUR-02 / KUR-03)

All of it is in `pantry/services.py`. It is a single database query:

```
for each recipe, count:
    needed  = how many ingredients it has
    matched = how many of those are in the pantry
keep it if needed > 0 and matched == needed
```

A recipe is offered **only** if every ingredient it needs is in the pantry. Recipes with no ingredients are never offered. Extra ingredients in the pantry don't matter. Results are sorted by name.

Only the matching recipes are fetched, and their ingredients are loaded with one `prefetch_related` query. `makeable_recipes()` therefore takes **at most 2 queries** and the home page **4 queries**, however many recipes there are. `PerformanceTests` checks this with `assertNumQueries`.

### Recipe cards (SR-2.4)

Each suggestion is rendered by `templates/pantry/_recipe_card.html`: the name as a heading, the ingredients as a list, and the method as numbered steps inside `<details><summary>Show method</summary>`. That keeps the page short, needs no JavaScript and works with screen readers. `Recipe.steps()` splits the free-text `instructions` into steps at line breaks and sentence ends (`.`, `!`, `?`). The page has a mobile viewport tag and a small inline stylesheet, so cards fit a phone-width screen.

### Performance (SR-2.3)

Requirement: suggestions return in under 2 seconds with a large recipe database. Measured with `python manage.py benchmark_suggestions` on 25 Nov 2026 (Python 3.9.6, Django 4.2, SQLite, Apple Silicon Mac):

| Recipes | `makeable_recipes()` (median) | Home page view + render (worst of runs) | Queries | Suggestions shown |
|---------|------------------------------|------------------------------------------|---------|-------------------|
| 1,039   | 6.0 ms                        | 22.6 ms                                  | 4       | 88                |
| 10,039  | 59.1 ms                       | 159.7 ms                                 | 4       | 950               |

Both are far below the 2-second limit. For comparison, the previous Python-loop version of `makeable_recipes()` took 50.5 ms on the same 1,000-recipe data, so the database query is about 8× faster. `test_sr_2_3_home_page_with_1000_recipes_under_2_seconds` checks the limit on every test run.

The command creates dummy recipes inside a transaction and rolls it back afterwards, so your database is left unchanged. It times the view directly, without the dev server or the browser, so real page loads add a little network and rendering time on top.

### Adding ingredients (KUR-04)

`add_ingredient` splits the input on commas, normalises each part, skips blanks, then uses `get_or_create` for both the `Ingredient` and the `PantryItem`. Adding something you already have does nothing. Adding a brand-new name creates it, even if no recipe uses it yet.

The input box offers autocomplete through an HTML `<datalist>` filled with every known ingredient. This needs no JavaScript.

---

## Managing recipes

There are two ways to add recipes.

**1. Django admin (quickest for trying things out).** Go to `/admin/` → Recipes → Add. Pick ingredients from the list, or add new ones with the `+` button. Recipes added this way exist only in your local database.

**2. The recipe fixture (so everyone gets them).** The shared dataset is `pantry/fixtures/recipes.json`. Load it, or reload it after pulling changes, with:

```bash
python manage.py loaddata recipes
```

Loading it twice is safe: it updates existing entries rather than duplicating them. The file has two kinds of entry:

```json
{ "model": "pantry.ingredient", "fields": { "name": "egg" } },
{ "model": "pantry.recipe", "pk": 8, "fields": {
    "name": "Boiled egg",
    "instructions": "Lower the egg into boiling water...",
    "ingredients": [["egg"]] } }
```

To add a recipe:
- Give it the next unused `pk`. Recipes are matched by `pk`, so reusing one overwrites that recipe.
- List ingredients by name, each wrapped in its own brackets: `[["egg"], ["milk"]]`. Every ingredient must also have its own `pantry.ingredient` entry in the file, or loading fails.
- Use **simple, singular, lowercase** names (`egg`, `tomato`, `onion`, not `2 large eggs`). Matching is exact, so reuse names already in the file wherever you can.

Run `python manage.py test` afterwards. `RecipeFixtureTests` checks that every recipe has a name, at least one ingredient and a method.

> **Note:** the fixture uses recipe `pk`s 1 and up, so loading it overwrites any recipe you created in admin with the same id.

The 7 original recipes were also seeded by `pantry/migrations/0002_seed_recipes.py`. The fixture contains the same recipes at `pk` 1–7, so the two agree.

---

## Testing

```bash
python manage.py test
```

Tests are in `pantry/tests.py`. Each test is labelled with the KUR or SR it covers (SR test names start with e.g. `test_sr_2_3_`). Django creates a throwaway test database, so your local data is never touched.

**Rule of thumb:** if you change behaviour connected to a KUR, add or update a test for it. KUR-03 matters most, because offering a recipe the user *can't* make is the main failure this app exists to avoid.

---

## Development workflow

- `main` is the main branch. Work on a feature branch and open a pull request into `main`.
- Before pushing: run `python manage.py test` and make sure it passes.
- If you changed `models.py`: run `makemigrations` and **commit the migration files** along with your change.
- If you added a dependency: update `requirements.txt` in the same commit.
- Never commit `db.sqlite3`, `.venv/`, or `.env` (they're already in `.gitignore`).
- If you add a new setting that differs between machines or holds a secret, read it from an environment variable in `settings.py` and add it, with no real value, to `.env.example`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'django'` | The virtual environment isn't active. Run `source .venv/bin/activate` (Windows: `.venv\Scripts\Activate.ps1`). |
| `ImproperlyConfigured: DJANGO_SECRET_KEY is not set` | You don't have a `.env` file, or its `DJANGO_SECRET_KEY=` line is empty. See [step 3 of Getting started](#3-add-a-secret-key-to-env). |
| `ModuleNotFoundError: No module named 'dotenv'` | Run `pip install -r requirements.txt` again: `python-dotenv` was added after you first set up. |
| `CommandError: You must set settings.ALLOWED_HOSTS if DEBUG is False.` | Set `DJANGO_DEBUG=True` in `.env` for local development. |
| `no such table: pantry_ingredient` | You haven't run `python manage.py migrate`. |
| `Error: That port is already in use.` | Another server is running. Stop it, or use `python manage.py runserver 8080`. |
| "You can make" is empty but I expected a recipe | You need *every* ingredient, spelled the same way. `egg` ≠ `eggs`. Check the recipe's ingredients in `/admin/`. |
| Windows: `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again. |
| `loaddata`: `Ingredient matching query does not exist` | A recipe uses an ingredient with no `pantry.ingredient` entry in `recipes.json`. Add one. |
| Something's badly broken locally | Delete `db.sqlite3`, then run `python manage.py migrate` and `python manage.py loaddata recipes` for a fresh start. |

---

## Known limitations & next steps

These are known gaps, not bugs. They are good first tasks for someone new to the project.

**Product**
- [ ] **Single shared pantry.** There are no user accounts, so everyone using the same server shares one fridge. *Next step: Django auth, and a `user` field on `PantryItem`.*
- [ ] **Exact-name matching.** `egg` vs `eggs` and `tomato` vs `tomatoes` count as different ingredients. *Next step: an alias or plural table, or always choosing from the known list.*
- [ ] **Staples count like any other ingredient.** If you didn't add `salt`, Scrambled eggs won't appear. *Next step: an "always have" flag for pantry staples.*
- [ ] **No quantities.** "Have eggs" is all-or-nothing.
- [x] ~~**Only 7 recipes.**~~ There are now 39 in `pantry/fixtures/recipes.json` (SCRUM-52).

**Technical**
- [ ] **Minimal styling.** There is only a small inline stylesheet so recipe cards fit a phone. *Next step: a proper CSS file in Django `static/`.*
- [x] ~~**Matching runs in Python** over all recipes.~~ It is now a single database query and stays well under 2 s with 10,000 recipes (SCRUM-54).
- [ ] **Not production-ready yet.** `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` now come from environment variables, but nothing else has been set up for deployment (static files, HTTPS settings, a production database). Note that the original generated key is still in git history, so it must never be used anywhere.
- [ ] **No CI.** Running `python manage.py test` on every PR would be cheap insurance.
