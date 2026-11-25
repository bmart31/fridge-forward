"""SR-2.3: time recipe suggestions against a large recipe database.

    python manage.py benchmark_suggestions [--recipes 1000] [--runs 5]

Adds dummy recipes, times makeable_recipes() and a full render of the home
page, then rolls everything back so your database is left as it was.
"""
import platform
import statistics
import time

import django
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext

from pantry.benchmark import create_dummy_recipes
from pantry.models import Recipe
from pantry.services import makeable_recipes
from pantry.views import home

LIMIT_SECONDS = 2.0


class Rollback(Exception):
    pass


class Command(BaseCommand):
    help = "Time recipe suggestions with ~1,000 dummy recipes (SR-2.3). Leaves the database unchanged."

    def add_arguments(self, parser):
        parser.add_argument("--recipes", type=int, default=1000)
        parser.add_argument("--runs", type=int, default=5)

    def handle(self, *args, recipes, runs, **options):
        try:
            with transaction.atomic():
                self.run(recipes, runs)
                raise Rollback
        except Rollback:
            self.stdout.write("Dummy data rolled back.")

    def run(self, count, runs):
        makeable = create_dummy_recipes(count)
        total = Recipe.objects.count()

        request = RequestFactory().get("/")
        match_times, page_times = [], []
        for _ in range(runs):
            start = time.perf_counter()
            matched = makeable_recipes()
            match_times.append(time.perf_counter() - start)

            with CaptureQueriesContext(connection) as queries:
                start = time.perf_counter()
                response = home(request)
                page_times.append(time.perf_counter() - start)

        worst = max(page_times)
        self.stdout.write(
            f"Recipes in database:    {total} ({count} dummy, {makeable} of them makeable)\n"
            f"Suggestions returned:   {len(matched)}\n"
            f"makeable_recipes():     median {statistics.median(match_times) * 1000:.1f} ms, "
            f"worst {max(match_times) * 1000:.1f} ms over {runs} runs\n"
            f"Home page (view+render): median {statistics.median(page_times) * 1000:.1f} ms, "
            f"worst {worst * 1000:.1f} ms, {len(queries)} queries, "
            f"{len(response.content) // 1024} KB\n"
            f"Environment:            Python {platform.python_version()}, Django {django.get_version()}, "
            f"{connection.vendor}, {platform.system()} {platform.machine()}"
        )
        if worst < LIMIT_SECONDS:
            self.stdout.write(self.style.SUCCESS(f"PASS: under {LIMIT_SECONDS:.0f} s"))
        else:
            self.stdout.write(self.style.ERROR(f"FAIL: {worst:.2f} s is over {LIMIT_SECONDS:.0f} s"))
