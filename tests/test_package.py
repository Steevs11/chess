"""Smoke test for the editable install (ADR-029).

Nothing here tests chess. It proves the precondition every later test relies on:
`pip install -e ".[dev]"` produced an importable, installed distribution.
"""

import importlib
import unittest
from importlib import metadata

# Mirrors src/chess/; every package here must have an __init__.py (CONVENTIONS 5).
SUBPACKAGES = (
    "chess",
    "chess.core",
    "chess.protocol",
    "chess.server",
    "chess.server.transport",
    "chess.client",
    "chess.client.scenes",
)


class PackageInstallTest(unittest.TestCase):
    def test_every_subpackage_is_importable(self) -> None:
        for name in SUBPACKAGES:
            with self.subTest(package=name):  # one failure must not hide the rest
                module = importlib.import_module(name)
                self.assertTrue(module.__doc__, f"{name} has no module docstring")

    def test_distribution_metadata_is_present_after_editable_install(self) -> None:
        """Import can succeed from sys.path alone; metadata proves pip installed it.

        Asserts that metadata exists, not what it says. Pinning the version here
        would mean editing the test on every version bump - exactly the change
        CONVENTIONS 5 forbids.
        """
        # Raises PackageNotFoundError - not just returns empty - when pip never ran.
        self.assertTrue(metadata.version("chess"))
