# Faza 0 — Skelet

**Checkpoint:** `pip install -e ".[dev]"` pa `python tools/check.py` (testovi, `ruff check`,
`ruff format --check`, slojevi, trajleri, ignorisane putanje u istoriji). Prošao na svežem
klonu: Windows 11, Python 3.11.9, 22. 9. 2026 — `Ran 58 tests → OK`, `ruff` čist.

## Šta je napravljeno

| Task | Rezultat |
|---|---|
| 0.1 | `src/chess/` sa paketima `core`, `protocol`, `server`, `client`; `tests/`, `docs/`, `assets/`, `tools/` |
| 0.2 | `pyproject.toml` (`pygame`, `ruff`, `line-length = 100`), `pip install -e ".[dev]"`, prvi test |
| 0.2b | `tools/layer_check.py` + `tests/test_layers.py` — smer uvoza se proverava kroz `ast` (ADR-033) |
| 0.3 | `.gitignore` pre prvog commita; provera da ništa ignorisano nije u istoriji |
| 0.4 | Cburnett figure (SVG + PNG 80/32 px), DejaVu Sans, dva `LICENSE.txt`, `.gitattributes`, `tests/test_assets.py` |
| 0.5 | `assets/i18n/sr.json` + `client/i18n.py` sa `t()`; spona `PROTOCOL.md` §5 ↔ `sr.json` u testu (ADR-040, ADR-041) |
| 0.6 | `LICENSE` (BSD-3-Clause), `THIRD-PARTY.txt`, SPDX oznaka u `pyproject.toml` (ADR-042, ADR-043) |
| 0.7–0.9 | uputstva asistentu svedena na pokazivače; `tests/test_encoding_bytes.py` (BOM), `tools/check_commit_trailers.py` |
| REZ 2 | procesna pravila posečena, `tools/check.py` kao jedna komanda za sve kapije (ADR-048) |

## Tri nalaza koja i dalje važe

- **Tuđi materijal se čuva bajt u bajt.** `core.autocrlf=true` na Windows-u menja prelaske
  reda pri kloniranju, pa `.gitattributes` drži `-text` za SVG i font licencu; bez toga
  `sha1` vrednosti iz `assets/pieces/LICENSE.txt` ne bi važile na svežem klonu (ADR-039).
- **nanosvg iz SDL_image-a ne skalira crtež na platno.** `tools/rasterize_pieces.py` zato
  sam skalira geometriju i poredi udeo neprovidnih piksela kroz veličine (ADR-038).
- **`pip install -e ".[dev]"`, ne `pip install -e .`** — bez `[dev]` nema `ruff`-a i
  checkpoint ne može da prođe (ADR-029).

## Istorija

Zapis task po task — merenja, tabele namernih kvarova, pitanja i odgovori — stoji u
istoriji ovog fajla do commita `4770159`. Komentari u `tests/` koji pominju odeljke
„0.1–0.9", „Checkpoint faze 0" i „R9" upućuju na tu verziju.
