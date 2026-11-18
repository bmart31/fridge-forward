# Fridge Forward

Tell Fridge Forward what's in your fridge and it tells you what you can cook with it, and only that.

> **Status: early MVP.** It is deliberately rough so that it can be improved step by step. There is no styling, no user accounts and only a small set of starter recipes. See [Known limitations & next steps](#known-limitations--next-steps).

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
2. **You can make.** This lists every recipe whose ingredients you *all* have. If nothing matches, it says *"No recipes match your ingredients."*

### Key User Requirements

The app is built against these requirements. Every change should keep them working.

| ID | Requirement | How it's met | Tested by |
|----|-------------|--------------|-----------|
| KUR-01 | The user shall be able to record the ingredients they currently have. | `PantryItem` model, plus the add and remove views | `AddIngredientTests` |
| KUR-02 | The user shall be able to receive recipe suggestions based on the ingredients they have recorded. | "You can make" section, filled by `makeable_recipes()` | `MatchingTests` |
| KUR-03 | Only recipes that can be made with the ingredients they have are offered. If none match, none are offered. | `makeable_recipes()` returns a recipe only if **every** one of its ingredients is in the pantry | `test_only_fully_makeable_recipes`, `test_no_match_returns_nothing` |
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
git clone <repo-url> fridge-forward
cd fridge-forward

python3 -m venv .venv              # create an isolated Python environment
source .venv/bin/activate          # activate it (your prompt shows "(.venv)")
pip install -r requirements.txt    # install Django
python manage.py migrate           # create the database and load the starter recipes
```

**Windows (PowerShell)**

```powershell
git clone <repo-url> fridge-forward
cd fridge-forward

py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
```

### 3. Run it

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Stop the server with `Ctrl+C`.

### 4. Quick check that everything works

1. Type `bread, cheese` and press Enter.
2. **Cheese toast** should appear under "You can make".
3. Remove `cheese`. The page should now say *"No recipes match your ingredients."*

### 5. (Optional) Admin access

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
| Reset the database completely | Delete `db.sqlite3`, then `python manage.py migrate` |
| Add a new Python dependency | `pip install <pkg>`, then add it with a version range to `requirements.txt` |

---

## Project structure

```
fridge-forward/
├── manage.py                   # Django's command-line entry point
├── requirements.txt            # Python dependencies: keep this up to date
├── README.md
├── .gitignore                  # ignores .venv/, db.sqlite3, __pycache__, .env
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
    ├── tests.py                # Tests, labelled with the KUR they cover
    ├── templates/pantry/
    │   └── home.html           # The single page
    └── migrations/
        ├── 0001_initial.py     # Creates the tables
        └── 0002_seed_recipes.py# Loads the 7 starter recipes
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

All of it is in `pantry/services.py`:

```python
have = set of ingredient ids in the pantry
for each recipe:
    needed = set of that recipe's ingredient ids
    if needed is not empty and needed ⊆ have:
        include it
```

A recipe is offered **only** if every ingredient it needs is in the pantry. Recipes with no ingredients are never offered. Extra ingredients in the pantry don't matter.

This runs in Python over every recipe. That is fine for hundreds of recipes. If the recipe list grows large it should move into a database query (see next steps).

### Adding ingredients (KUR-04)

`add_ingredient` splits the input on commas, normalises each part, skips blanks, then uses `get_or_create` for both the `Ingredient` and the `PantryItem`. Adding something you already have does nothing. Adding a brand-new name creates it, even if no recipe uses it yet.

The input box offers autocomplete through an HTML `<datalist>` filled with every known ingredient. This needs no JavaScript.

---

## Managing recipes

There are two ways to add recipes.

**1. Django admin (quickest for trying things out).** Go to `/admin/` → Recipes → Add. Pick ingredients from the list, or add new ones with the `+` button. Recipes added this way exist only in your local database.

**2. Data migration (so everyone gets them).** Starter recipes are in `pantry/migrations/0002_seed_recipes.py`. Because migrations that have already run won't run again, **don't edit 0002**. Create a new one instead:

```bash
python manage.py makemigrations pantry --empty -n more_recipes
```

Then copy the `seed`/`unseed` pattern from `0002_seed_recipes.py` into the new file. Use lowercase ingredient names: `apps.get_model` returns a "historical" model that skips the custom `save()`, so names are **not** normalised automatically inside migrations.

---

## Testing

```bash
python manage.py test
```

Tests are in `pantry/tests.py`. Each test is labelled with the KUR it covers. Django creates a throwaway test database, so your local data is never touched.

**Rule of thumb:** if you change behaviour connected to a KUR, add or update a test for it. KUR-03 matters most, because offering a recipe the user *can't* make is the main failure this app exists to avoid.

---

## Development workflow

- `main` is the main branch. Work on a feature branch and open a pull request into `main`.
- Before pushing: run `python manage.py test` and make sure it passes.
- If you changed `models.py`: run `makemigrations` and **commit the migration files** along with your change.
- If you added a dependency: update `requirements.txt` in the same commit.
- Never commit `db.sqlite3`, `.venv/`, or `.env` (they're already in `.gitignore`).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'django'` | The virtual environment isn't active. Run `source .venv/bin/activate` (Windows: `.venv\Scripts\Activate.ps1`). |
| `no such table: pantry_ingredient` | You haven't run `python manage.py migrate`. |
| `Error: That port is already in use.` | Another server is running. Stop it, or use `python manage.py runserver 8080`. |
| "You can make" is empty but I expected a recipe | You need *every* ingredient, spelled the same way. `egg` ≠ `eggs`. Check the recipe's ingredients in `/admin/`. |
| Windows: `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again. |
| Something's badly broken locally | Delete `db.sqlite3` and run `python manage.py migrate` for a fresh start. |

---

## Known limitations & next steps

These are known gaps, not bugs. They are good first tasks for someone new to the project.

**Product**
- [ ] **Single shared pantry.** There are no user accounts, so everyone using the same server shares one fridge. *Next step: Django auth, and a `user` field on `PantryItem`.*
- [ ] **Exact-name matching.** `egg` vs `eggs` and `tomato` vs `tomatoes` count as different ingredients. *Next step: an alias or plural table, or always choosing from the known list.*
- [ ] **Staples count like any other ingredient.** If you didn't add `salt`, Scrambled eggs won't appear. *Next step: an "always have" flag for pantry staples.*
- [ ] **No quantities.** "Have eggs" is all-or-nothing.
- [ ] **Only 7 recipes**, and they can only be added through admin or migrations.

**Technical**
- [ ] **No styling at all.** Add a CSS file (Django `static/`) and make it work on a phone.
- [ ] **Matching runs in Python** over all recipes. Move it to a database query if recipes reach the thousands.
- [ ] **Not production-ready.** `settings.py` still has the generated `SECRET_KEY` and `DEBUG = True`. Before deploying, load them from environment variables (a `.env` file is already git-ignored for this) and set `ALLOWED_HOSTS`.
- [ ] **No CI.** Running `python manage.py test` on every PR would be cheap insurance.
