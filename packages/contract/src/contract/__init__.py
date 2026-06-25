"""contract — the boundary every block crosses.

Owns the ``expression_de_besoin`` artifact (its schema + the closed type vocabulary, a
deliberately temporary hand-curated scaffold) and the append-only ``trace``. The other
blocks depend ONLY on this package, never on each other.

Status: brique 1 (active). Glossary: docs/dictionnaire-metier.md.
"""
