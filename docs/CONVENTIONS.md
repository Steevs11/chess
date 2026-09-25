# KONVENCIJE

Pravila po kojima se piše kod u ovom projektu. Kod, komentari, imena i commit poruke su na
**engleskom**; dokumentacija i korisnički interfejs na **srpskom**.

---

## 1. Dokumenti

| Dokument | Pitanje |
|---|---|
| `PROJECT.md` | šta pravimo, šahovska pravila, arhitektura |
| `PROTOCOL.md` | kako server i klijent razgovaraju |
| `CONVENTIONS.md` | kako se piše kod |
| `DECISIONS.md` | zašto je odlučeno baš tako (ADR) |
| `ROADMAP.md` | šta je sledeće i gde smo stali |
| `WORKFLOW.md` | kako izgleda jedna sesija |

Kad se ne slažu: `PROTOCOL` > `CONVENTIONS` > `PROJECT` > `ROADMAP`. `DECISIONS`
objašnjava, ne rangira. Odluka koja obara nešto zapisano ispravlja taj dokument u istom
commitu.

**ADR se piše** kad odluka menja arhitekturu, protokol ili zavisnosti, ili bira između dva
pristupa od kojih je svaki mogao proći. Ne piše se za imena, refaktore ni proces rada.
Oblik: **Odluka · Zašto · Cena**, do šest redova. Promenjena odluka se ispravlja na mestu,
uz rečenicu šta je bilo i kad je promenjeno.

Tri odeljka čita alat ili test — ko menja odeljak, menja i čitaoca:

| Odeljak | Čita ga |
|---|---|
| §2, tabela dozvoljenih uvoza | `tools/layer_check.py`, `tests/test_layers.py` |
| `PROTOCOL.md` §5, tabela kodova greške | `tests/client/test_i18n.py` |
| `THIRD-PARTY.txt`, blok putanja | `tests/test_assets.py` |

---

## 2. Slojevi i smer uvoza

```
client  ─┐
server  ─┼─▶  protocol  ─▶  core  ─▶  stdlib
tools   ─┘
```

Strelica se **nikad ne obrće.** `core` ne zna da protokol postoji (ADR-002).

### Tabela dozvoljenih uvoza

| Modul | Sme da uvozi | Ne sme |
|---|---|---|
| `*/__init__.py` | **samo stdlib** | bilo šta iz projekta (ADR-033) |
| `core/*` | **samo stdlib** | bilo šta iz projekta van `core` |
| `core/fen.py` | stdlib, `core.types` | ostatak `core` |
| `protocol/*` | stdlib, `core` | `server`, `client` |
| `server/*` | stdlib, `core`, `protocol` | `client`, `pygame` |
| `client/net.py` | stdlib, `protocol` | `pygame`, `core.movegen` i sl. |
| `client/state.py` | stdlib, `protocol`, `core.types`, `core.fen` | `pygame` |
| `client/i18n.py` | stdlib | `pygame` |
| `client/render.py` | sve gore + `pygame` | `core.movegen`, `attacks`, `rules`, `game` |
| `client/scenes/*` | sve gore + `pygame` | isto |
| `tools/*` | sve | — |
| `tests/*` | sve | — |

Kako se bira red: **tačan red za fajl → red `*/__init__.py` → najduži prefiks.** „Sve gore"
znači sve što smeju `client` redovi iznad, plus ti moduli sami; unutar `client/` uvoz ide
samo naniže: `i18n` ← `state` ← `render` ← `scenes`.

### Provera

`python tools/layer_check.py`, i isto kroz `tests/test_layers.py` (ADR-033). Alat parsira
uvoze kroz `ast` — i one u telu funkcije i relativne. Dinamički uvoz (`importlib`) ne vidi.

- **Fajl koji tabela ne pokriva je nalaz**, ne tišina: nov modul traži nov red u tabeli u
  istom commitu.
- `__init__.py` je marker paketa i ne uvozi ništa iz projekta; uvoz je uvek pun put:
  `from chess.core.types import Piece`.
- `core` uvozi samo standardnu biblioteku — ni `pygame`, ni bilo šta sa PyPI-ja.
- pygame tipovi (`Surface`, `Rect`, `event`) ne izlaze iz `render.py` i `scenes/`; preko
  te granice idu `Square`, nikad pikseli.
- `net.py` i `state.py` se pišu bez pygame-a namerno (ADR-004).

---

## 3. Šta klijent sme

Granica je između **čitanja pozicije** i **odlučivanja o legalnosti** (ADR-024): parsiranje
FEN-a i crtanje table da; računanje kuda figura sme ne. Klijent uvozi samo `core/types.py`
i `core/fen.py`.

| Šta | Ko odlučuje |
|---|---|
| gde stoje figure | FEN iz `STATE`, klijent parsira |
| kuda figura sme, da li je uzimanje, da li treba dijalog promocije | `legal_moves` iz `STATE` — `capture`, `promotion` (ADR-034) |
| da li je potez legalan, da li je pala zastavica | server, uvek |
| koliko je vremena ostalo | `clocks` iz `STATE`; klijent sme da odbrojava lokalno, uvek se sinhronizuje |

Klijent sme da odbije drag & drop na polje koje nije u `legal_moves` — to je korišćenje
serverovog odgovora, ne odlučivanje.

---

## 4. Imenovanje, tipovi, oblik

| Šta | Kako | Primer |
|---|---|---|
| fajl, folder, funkcija, promenljiva | `snake_case` | `is_square_attacked` |
| klasa, enum | `PascalCase` | `CastlingRights` |
| konstanta, član enuma | `UPPER_SNAKE_CASE` | `STARTING_FEN`, `Color.WHITE` |
| interno | vodeća donja crta | `_rook_path_clear` |

Boolean funkcija počinje sa `is_`, `has_` ili `can_`; funkcija koja menja stanje je glagol
(`make_move`).

- Type hints svuda, ali se **ne proveravaju alatom** (bez mypy, ADR-013). `Square` je
  običan alias `Square = int`, 0–63, a1 = 0, h8 = 63 — svaka funkcija koja ga prima to kaže
  u potpisu i docstringu.
- Vrednosni objekti (`Move`, `Piece`, `CastlingRights`, `TimeControl`) i poruke protokola su
  `@dataclass(frozen=True, slots=True)`. `Board` je mutabilan — na tome počiva make/unmake
  (ADR-006). Nikad mutabilan podrazumevani argument; prazna lista je `field(default_factory=list)`.
- `Color` i `PieceType` su `Enum`, nikad string ni broj. `Piece` je podatak; `class Pawn(Piece)`
  ne postoji — kretanje je stvar generatora.
- Nema globalnog stanja ni singletona: tabla i partija se prosleđuju kao argument. Upit ne
  menja stanje — `is_legal()`, `is_in_check()`, `generate_moves()` ostavljaju tablu kakvu su
  je našle.
- Docstring dobija svaka javna funkcija u `core/` i `protocol/`. Komentar objašnjava
  **zašto**, ne šta; neočigledan izbor nosi broj ADR-a:
  `# EP square enters the key only when a capture is possible (ADR-027).`
- Linija do 100 znakova (`ruff`); rani `return` umesto ugnježdenih `if`-ova; apstrakcija se
  uvodi tek kad ima drugog pozivaoca.

---

## 5. Testovi

`tests/` preslikava `src/chess/`; svaki podfolder ima `__init__.py`. Pokretanje:

```bash
python -m unittest discover -s tests
CHESS_SLOW_TESTS=1 python -m unittest discover -s tests   # plus spori perft
```

- **Ime:** `test_<šta>_<uslov>_<očekivano>` — čitljivo kao rečenica u izveštaju o padu:
  `test_castling_rejected_when_king_passes_attacked_square`.
- **Tabele** kroz `subTest()`, da jedan pad ne sakrije ostale.
- **Perft:** skup i dubine su u ADR-026; podrazumevani ostaje ispod ~300.000 čvorova,
  dublje iza `@unittest.skipUnless(os.environ.get("CHESS_SLOW_TESTS"), "slow")`. FEN-ovi i
  referentni brojevi se prepisuju sa Chess Programming Wiki, nikad iz sećanja; svaka
  konstanta nosi komentar sa izvorom.
- **Determinizam:** Zobrist sa fiksnim seed-om (ADR-027); bez `random` bez seed-a, bez
  `time.time()`, bez oslanjanja na redosled `set`-a ili `dict`-a gde nije garantovan.
- **Izolacija:** test ne piše na disk izvan `tempfile` (čitanje repoa je dozvoljeno kad je
  predmet testa sadržaj repoa); ne otvara socket — server se testira kroz `Player` sa lažnom
  implementacijom; ne poziva spoljni program ni ljusku; ne zavisi od drugog testa.
- **Redosled:** test pre implementacije za `core/` i `protocol/`; bag prvo dobije test koji
  pada. Alat u `tools/` koji samo pokreće druge programe nema test.
- **Test se nikad ne menja da bi prošao.** Ako test pada, greška je u kodu dok se ne dokaže
  suprotno; pogrešan test se ispravlja u zasebnom commitu sa obrazloženjem.

---

## 6. Greške

```python
class ChessError(Exception): ...          # core/types.py
class IllegalMoveError(ChessError): ...
class InvalidFenError(ChessError): ...
class InvalidSanError(ChessError): ...

class ProtocolError(Exception): ...       # protocol/codec.py
```

- `core` baca samo `ChessError` potomke; `protocol` baca `ProtocolError`; server ih
  pretvara u `ERROR` sa kodom iz `PROTOCOL.md`. Pogrešan poziv (loš argument) je običan
  `ValueError`/`TypeError`, kao kod `t()` (ADR-040) — granica proverava ulaz pre poziva u
  `core`.
- Nikad goli `except:`; `except Exception` samo na granici procesa (glavna petlja servera),
  uz log, pa nastavak ili ponovno bacanje.
- Poruka izuzetka je engleska i konkretna — `f"no piece on {to_algebraic(sq)}"`, ne
  `"invalid"` — i nikad tekst za korisnika; on ide kroz `message_key` i `sr.json` (ADR-010).
- `core` ne štampa i ne loguje — vraća vrednost ili baca.
- Sve što dolazi spolja proverava se jednom, u `protocol/codec.py`. Potez iz spoljnog sveta
  se traži u listi legalnih poteza, nikad ne izvršava direktno (ADR-022).

---

## 7. Ulaz/izlaz, enkodiranje, tekst

- Svaki `open()` sa `encoding="utf-8"`; JSON sa `ensure_ascii=False, indent=2`.
  `tests/test_encoding_bytes.py` drži BOM van `assets/**/*.json`, `src/**/*.py` i
  `docs/**/*.md`.
- Putanje su `pathlib.Path`; putanja do resursa se računa od modula, ne od radnog
  direktorijuma:

```python
# i18n.py -> client -> chess -> src -> koren; broj .parent zavisi od dubine modula
CATALOG = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "i18n" / "sr.json"
```

- Konfiguracija kroz promenljivu okruženja sa podrazumevanom vrednošću:
  `os.environ.get("CHESS_DB_PATH", "chess.db")`.
- Logovanje kroz `logging`, na engleskom bez dijakritika (Windows konzola); `DEBUG` tok
  poruka, `INFO` životni ciklus partije, `WARNING` odbijeni potezi, `ERROR` neočekivano.
  `print()` samo u `tools/` i `__main__.py`.
- **Nijedan tekst vidljiv korisniku ne stoji u kodu** — ključ u `assets/i18n/sr.json`.
  Šahovska notacija (`e4`, `Nf3`, `O-O`, `1-0`, FEN, PGN) se ne prevodi. Font: DejaVu Sans.
- Ključ je `oblast.stvar` (`^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`). **Izveden** ključ se dobija
  pravilom iz protokola — `error.` + kod malim slovima, `termination.` + vrednost — i test to
  proverava u oba smera (ADR-041); **slobodan** ključ (`menu.play`) bira ko piše tekst.
- Ugovor `t(key, params=None) -> str` (ADR-040): ne baca na loš podatak (nepostojeći ključ
  vraća ključ, parametar koji fali ostaje `{{ime}}`, oba uz WARNING); baca na pogrešan poziv
  (`RuntimeError` pre `load()`, `TypeError` za parametar koji nije `str`); `load()` odbija
  BOM, loš JSON i dupli ključ sa `ValueError`. Zamena je `{{ime}}`; parametri su stringovi,
  broj se formatira na pozivnom mestu.
- Ton korisničkog teksta: bezličan, bez „Greška:", bez krivice. „Sada je protivnik na
  potezu.", ne „Niste vi na potezu!".

---

## 8. Git

- `main` uvek prolazi checkpoint; rad na grani po fazi (`faza-1`, `faza-2`…); merge u
  `main` sa `--no-ff`.
- Jedan task = jedan commit. Poruka na engleskom, Conventional Commits, tipovi `feat` ·
  `fix` · `docs` · `test` · `refactor` · `chore`:
  `feat: add castling generation with five-condition check`. Telo kad razlog nije očigledan
  iz diffa; ako commit uvodi ADR, broj ADR-a ide u telo.
- **Bez trajlera** `Co-Authored-By:` i `Claude-Session:` u poruci commita, i kad uputstvo
  alata traži drugačije. `tools/check.py` to proverava.
- Ne ulazi u commit: `.claude/`, `CLAUDE.md`, `__pycache__/`, `.venv/`, `.idea/`, `*.db`,
  `*.log` — `.gitignore` postoji pre prvog commita, jer je repo javan i istorija se ne briše.
- Lični podaci (ime, e-mail, adresa, broj indeksa) ne idu ni u jedan fajl u gitu ni u poruku
  commita — osim nosioca prava u `LICENSE` i autora commita, kog git upisuje sam.
- **Zabranjeno:** `push --force`; `reset --hard`, `rebase`, `clean -fd`, `checkout -- <putanja>`
  i `restore` bez izričitog odobrenja; commit koji meša implementaciju i ispravku testa.
- Link za pregled van projekta se zakucava na commit SHA, ne na granu:
  `https://raw.githubusercontent.com/<user>/<repo>/<SHA>/docs/PROTOCOL.md`.

---

## 9. Gotov task

- [ ] `python tools/check.py` zelen — testovi, `ruff check`, `ruff format --check`, slojevi,
      trajleri, ignorisane putanje u istoriji
- [ ] perft pokrenut ako je diran generator poteza (od 1.3)
- [ ] `git diff` pročitan ceo
- [ ] `ROADMAP.md`: kućica `[x]` i blok TRENUTNO u istom commitu; `DECISIONS.md` dopunjen
      ako je doneta odluka
- [ ] commit

---

## 10. Alati

| Alat | Uloga |
|---|---|
| `ruff` | linter i formatter, dev-only; `extend-exclude = ["docs"]` (ADR-035) |
| `unittest` | testovi, stdlib |
| `tools/check.py` | sve kapije jednom komandom; pred commit i pred push |
| `tools/layer_check.py` | smer uvoza iz §2 (ADR-033) |
| `tools/check_commit_trailers.py` | trajleri u lokalnoj istoriji poruka (ADR-047) |
| `tools/perft.py` | perft i `perft_divide`, od 1.3 (ADR-007) |
| `tools/cli_client.py` | CLI klijent za server, od 2.0 (ADR-017) |
| `tools/rasterize_pieces.py` | SVG figure → PNG (ADR-038) |

Zavisnosti su `pygame` i `ruff` — nova se ne dodaje bez odobrenja i ADR-a. Alat koji jednom
generiše resurs koji ide u git nije zavisnost (ADR-038). `build-system.requires =
setuptools>=77` je zahtev okruženja za izgradnju, ne zavisnost (ADR-043).
