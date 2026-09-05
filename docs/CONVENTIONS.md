# KONVENCIJE

Pravila po kojima se piše kod u ovom projektu. Važe za svakoga ko ga dodiruje —
čoveka ili asistenta.

Ovaj fajl **ide u git** (ADR-020). `CLAUDE.md` ne ide — on je uputstvo asistentu
i upućuje ovamo. Sve što bi važilo i bez asistenta stoji ovde.

Kod, komentari, imena i commit poruke su na **engleskom**. Dokumentacija i
korisnički interfejs su na **srpskom**.

---

## 1. Namena i hijerarhija dokumenata

### Ko odgovara na koje pitanje

| Dokument | Pitanje |
|---|---|
| `docs/PROJECT.md` | šta pravimo i zašto |
| `docs/DECISIONS.md` | zašto je nešto odlučeno baš tako |
| `docs/PROTOCOL.md` | kako server i klijent razgovaraju |
| `docs/CONVENTIONS.md` | kako se piše kod |
| `docs/ROADMAP.md` | šta je sledeće i gde smo stali |
| `docs/WORKFLOW.md` | kako izgleda jedna radna sesija |
| `docs/POJMOVNIK.md` | šta znače termini |

### Hijerarhija kad se dokumenti ne slažu

ADR-030 propisuje:

```
DECISIONS.md  >  PROTOCOL.md  >  PROJECT.md  >  ROADMAP.md
```

**ADR-032** proširuje tu listu, jer `CONVENTIONS.md` i `POJMOVNIK.md` u trenutku
ADR-030 nisu postojali. Puna hijerarhija:

```
DECISIONS.md > PROTOCOL.md > CONVENTIONS.md > PROJECT.md > ROADMAP.md > POJMOVNIK.md
```

- **`CONVENTIONS.md`** obavezuje kod, ali ne sme da protivreči protokolu.
  Protokol je ugovor sa spoljnim svetom; konvencije su unutrašnja stvar.
- **`POJMOVNIK.md`** nema autoritet. On objašnjava, ne propisuje. Ako se ne
  slaže sa bilo čim iznad sebe, POJMOVNIK je taj koji se ispravlja.

### Odeljak koji čita alat nosi rečenicu koja to kaže

Kad tekst iz `docs/` čita alat ili test, taj odeljak nosi rečenicu koja imenuje **šta ga
čita**. To je obaveštenje čitaocu i dijagnoza kad provera padne — **nije kapija**: nju samu
ništa ne proverava, i njeno odsustvo ne obara nijedan test. Ko menja takav odeljak mora da
zna da nešto puca; ko gleda pad mora da zna odakle je krenuo.

| Odeljak | Čita ga |
|---|---|
| §2, tabela dozvoljenih uvoza | `tools/layer_check.py`, i kao `tests/test_layers.py` (ADR-033, ADR-037) |
| `PROTOCOL.md` §5, prva kolona tabele kodova greške | `tests/client/test_i18n.py` (ADR-041) |
| `THIRD-PARTY.txt`, blok putanja | `tests/test_assets.py` (ADR-042) |

### Pravilo propagacije (ADR-030)

> Kad ADR obori nešto napisano u `PROJECT.md`, `PROTOCOL.md`, `ROADMAP.md` ili
> `CONVENTIONS.md`, ispravka tih dokumenata ide u **istom commitu** kao i ADR.
> Bez izuzetka.
>
> Obrazloženje: dokument koji zaostaje za odlukama je gori od dokumenta koji ne
> postoji, jer mu se veruje.

**Proširenje.** Pravilo važi za **svaki** fajl u `docs/`, uključujući
`POJMOVNIK.md` i `WORKFLOW.md`. ADR-030 ih nije naveo samo zato što tada nisu
postojali.

**Unutar `DECISIONS.md`** (ADR-032). Isto važi i kad novi ADR obori stariji. Stari ADR se
**ne briše** — dobija ⚠️ oznaku na vrhu koja pokazuje na novi. Fajl je
append-only i istorija odluka se čuva cela.

### Kad se piše ADR

Piše se kad odluka:

- menja strukturu ili smer zavisnosti
- menja protokol
- uvodi ili odbija zavisnost
- bira između dva pristupa gde je izbor mogao ići drugačije

Ne piše se za imena promenljivih, redosled funkcija ni sitne refaktore.

Format je uvek isti: **Kontekst** → **Odluka** → **Posledice**, gde posledice
navode i **šta smo izgubili**, ne samo šta smo dobili.

---

## 2. Slojevi i smer uvoza

Smer zavisnosti (ADR-002):

```
client  ─┐
server  ─┼─▶  protocol  ─▶  core  ─▶  stdlib
tools   ─┘
```

Strelica se **nikad ne obrće.** `core` ne zna da protokol postoji.

### Tabela dozvoljenih uvoza

| Modul | Sme da uvozi | Ne sme |
|---|---|---|
| `*/__init__.py` | **samo stdlib** | bilo šta iz projekta (ADR-037.3) |
| `core/*` | **samo stdlib** | bilo šta iz projekta van `core` |
| `protocol/*` | stdlib, `core` | `server`, `client` |
| `server/*` | stdlib, `core`, `protocol` | `client`, `pygame` |
| `client/net.py` | stdlib, `protocol` | `pygame`, `core.movegen` i sl. |
| `client/state.py` | stdlib, `protocol`, `core.types`, `core.fen` | `pygame` |
| `client/i18n.py` | stdlib | `pygame` |
| `client/render.py` | sve gore + `pygame` | `core.movegen`, `attacks`, `rules`, `game` |
| `client/scenes/*` | sve gore + `pygame` | isto |
| `tools/*` | sve | — |
| `tests/*` | sve | — |

Kako se bira red: **tačan red za fajl → red `*/__init__.py` → najduži prefiks.**
Zato `server/transport/tcp.py` pada pod `server/*`, a `tests/core/__init__.py` pod
`*/__init__.py`, ne pod `tests/*`.

„Sve gore" znači: sve što smeju `client` redovi **iznad**, plus ti moduli sami. Uvoz
unutar istog sloja je dozvoljen (`core` → `core`, `server` → `server`), ali unutar
`client/` ide **samo naniže**: `i18n` ← `state` ← `render` ← `scenes`. Kad bi
`state.py` smeo da uveze `render.py`, posredno bi povukao `pygame` i prestao da bude
prevodiv 1:1 (ADR-004).

Četiri posledice koje se lako previde:

1. **`core` uvozi samo standardnu biblioteku.** Ni `pygame`, ni bilo šta sa
   PyPI-ja. Ovo je uslov da `core` preživi prelazak na veb bez izmene.
2. **pygame tipovi ne izlaze iz `render.py` i `scenes/`.** `Surface`, `Rect`,
   `event` ne smeju da se pojave u potpisu funkcije koju zove `state.py`.
   Koordinate koje prelaze tu granicu su `Square`, nikad pikseli.
3. **`net.py` i `state.py` se pišu bez pygame-a namerno** (ADR-004) — u fazi 4
   se prevode 1:1 u JavaScript. Sve što u njima nije prevodivo je greška u
   dizajnu, ne u prevodu.
4. **`__init__.py` ne uvozi ništa iz projekta** — ni relativno. Fasada
   (`from chess.core import Piece` u `core/__init__.py`) pravi ivicu u grafu
   zavisnosti koju nijedan red tabele ne opisuje. Uvoz je uvek pun:
   `from chess.core.types import Piece` (ADR-037.3).

### Provera

Pravilo se proverava automatski, alatom u gitu — ne skillom (ADR-033):

```
python tools/layer_check.py
```

Alat parsira `import` naredbe kroz `ast` i prijavljuje svaki uvoz koji tabela ne
dozvoljava. Pokreće se i kao test (`tests/test_layers.py`), pa checkpoint faze 0
pada ako se pravilo prekrši.

- izlazni kod: `0` čisto, `1` ima nalaza; svaki nalaz nosi fajl, liniju i razlog
- **fajl koji tabela ne pokriva je nalaz**, ne izuzetak i ne tišina — nov modul
  traži nov red u tabeli, u istom commitu (ADR-037.2)
- uvoz sakriven u telu funkcije i relativni uvoz hvataju se isto kao uvoz na vrhu
- **dinamički uvoz se ne vidi** — `importlib.import_module("pygame")` ne može da
  uhvati nijedan `ast` alat; to je granica alata, ne rupa u pravilu
- pravila u alatu su prepis ove tabele; test veže imena redova, pa dodat red bez
  pravila (i obrnuto) pada. U sukobu je **tabela** u pravu (ADR-037.1, §1)

---

## 3. Šta klijent sme, a šta ne

Ovo je granica koju je najlakše pogrešno pročitati, pa stoji zapisana doslovno
(ADR-024):

> Granica je između **čitanja pozicije** i **odlučivanja o legalnosti**.

| | Klijent |
|---|---|
| parsiranje FEN-a, crtanje table | ✅ dozvoljeno |
| računanje kuda figura sme | ❌ zabranjeno |

> Konkretno: pygame klijent sme da uvozi **samo** `core/types.py` i
> `core/fen.py`. Nikad `movegen`, `attacks`, `rules` ni `game`.
>
> Veb klijent u fazi 4 reimplementira parsiranje FEN-a u JavaScriptu — takođe
> dozvoljeno po istoj logici. **Parsiranje nije rasuđivanje.**

### Šta ovo znači u praksi

| Situacija | Ko odlučuje |
|---|---|
| gde stoje figure | FEN iz `STATE`, klijent parsira |
| kuda pešak sme | `legal_moves` iz `STATE` |
| da li je ovo uzimanje | polje `capture` iz `STATE` (ADR-034) |
| da li treba dijalog za promociju | polje `promotion` iz `STATE` |
| da li je potez legalan | server, uvek |
| koliko je vremena ostalo | `clocks` iz `STATE` je izvor istine |
| da li je pala zastavica | server |

Klijent sme da odbrojava sat lokalno radi glatkoće prikaza, ali se **uvek
sinhronizuje** na vrednost iz `STATE` i nikad sam ne proglašava pad zastavice.

Klijent sme da odbije drag & drop na polje koje nije u `legal_moves` — to nije
odlučivanje, to je korišćenje serverovog odgovora.

---

## 4. Imenovanje, tipovi i komentari

### Imena

| Šta | Kako | Primer |
|---|---|---|
| fajl, folder | `snake_case` | `movegen.py` |
| klasa, enum | `PascalCase` | `CastlingRights` |
| funkcija, metoda, promenljiva | `snake_case` | `is_square_attacked` |
| konstanta | `UPPER_SNAKE_CASE` | `STARTING_FEN` |
| interno (nije javni API modula) | vodeća donja crta | `_rook_path_clear` |
| član enuma | `UPPER_SNAKE_CASE` | `Color.WHITE`, `MoveKind.EN_PASSANT` |

Boolean funkcija počinje sa `is_`, `has_` ili `can_`. Funkcija koja menja stanje
je glagol (`make_move`), funkcija koja vraća vrednost je imenica ili `get_`.

### Tipovi

Type hints se pišu **svuda** — u potpisima funkcija, na poljima dataclass-a, na
modulskim konstantama gde tip nije očigledan.

**Ali tipovi se ne proveravaju alatom** (ADR-031). `ruff` ih ne gleda, mypy ne
koristimo. Znači:

- hint je dokumentacija za čitaoca i IDE, ne garancija
- `Square` je **običan alias** `Square = int`, ne `NewType`. Bez type checkera
  `NewType` ne daje ništa osim lepšeg imena.
- svaka funkcija koja prima `Square` mora to reći **u potpisu i u docstringu**,
  uz opseg: `0–63, a1 = 0, h8 = 63`

Revidira se u fazi 4, kad `core` bude stabilan.

### Dataclass-ovi

- vrednosni objekti (`Move`, `Piece`, `CastlingRights`, `TimeControl`) su
  `frozen=True, slots=True`
- poruke protokola su `frozen=True`
- `Board` je **mutabilan** — na tome počiva `make`/`unmake` (ADR-006)

Nikad mutabilan podrazumevani argument. Ako treba prazna lista, `field(default_factory=list)`.

### Bez stanja i bez hijerarhije

- **Nema globalnog stanja ni singletona.** Tabla i stanje partije se **prosleđuju** kao
  argument. Modul koji pamti nešto između poziva ne može da radi neizmenjen u serveru,
  botu i testu koji ga zove hiljadu puta — a to je uslov iz `PROJECT.md` §6.
- **Komanda ≠ upit.** Funkcija koja odgovara na pitanje ne sme ništa da promeni:
  `is_legal()`, `is_in_check()` i `generate_moves()` ostavljaju tablu kakvu su je našle.
  Ono što menja stanje nosi ime glagola („Imena" iznad).
- **Figura je podatak, ne klasa u hijerarhiji.** `Color` i `PieceType` su `Enum` — nikad
  string ni go broj — a `Piece` je `frozen=True, slots=True`. `class Pawn(Piece)` ne
  postoji: kretanje je stvar generatora poteza, ne figure.

### Komentari i docstringovi

Docstring dobija svaka javna funkcija u `core/` i `protocol/`. Format:

```python
def is_square_attacked(board: Board, square: Square, by: Color) -> bool:
    """Return True if `square` (0-63) is attacked by any `by` piece.

    Does not care whether the attacking move would be legal - a pinned
    piece still attacks. Used by check detection and castling rules.
    """
```

Komentar objašnjava **zašto**, nikad **šta**. Ako je potrebno objasniti šta kod
radi, kod treba prepraviti, ne komentarisati.

Izuzetak gde je komentar obavezan: svako mesto gde je izabrana neočigledna
varijanta. Tada komentar nosi broj ADR-a.

```python
# EP square enters the key only when a capture is actually available (ADR-027).
```

### Dužina i oblik

- linija do 100 znakova (`ruff` to sprovodi)
- funkcija koja ne staje na ekran je kandidat za razdvajanje
- rani `return` umesto ugnježdenih `if`-ova
- apstrakcija se ne uvodi pre nego što je zatražena ili pre nego što postoji
  drugi pozivalac — sloj bez drugog korisnika je trošak bez pokrića

---

## 5. Testovi

### Raspored

`tests/` preslikava `src/chess/`. Svaki podfolder ima `__init__.py` da bi ga
`unittest discover` našao.

```
tests/
├── __init__.py
├── client/
│   ├── __init__.py
│   └── test_i18n.py      sr.json, t(), i spona sa PROTOCOL §5 (ADR-040, ADR-041)
├── core/
│   ├── __init__.py
│   ├── test_board.py
│   ├── test_movegen.py
│   ├── test_perft.py
│   └── test_fen.py
├── protocol/
├── server/
├── test_assets.py        sha1 tuđeg materijala + .gitattributes (ADR-039);
│                         od 0.6 i lanac licenci — LICENSE, THIRD-PARTY.txt i
│                         pyproject.toml (ADR-042, ADR-043)
└── test_layers.py        poziva tools/layer_check.py
```

### Pokretanje

```bash
python -m unittest discover -s tests          # podrazumevano
CHESS_SLOW_TESTS=1 python -m unittest discover -s tests
```

Prva komanda radi tek posle `pip install -e ".[dev]"` — `src/` raspored znači da
paket nije na `sys.path` bez instalacije (ADR-029), a bez `[dev]` nema `ruff`-a
(ADR-036).

### Imenovanje

`test_<šta>_<uslov>_<očekivano>`:

```python
def test_castling_rejected_when_king_passes_attacked_square(self): ...
def test_en_passant_capture_removes_pawn_behind_target(self): ...
```

Ime testa treba da bude čitljivo kao rečenica u izveštaju o padu.

### Tabelarni testovi

Kroz `subTest()`, da jedan pad ne sakrije ostale:

```python
for fen, depth, expected in PERFT_CASES:
    with self.subTest(fen=fen, depth=depth):
        self.assertEqual(perft(Board.from_fen(fen), depth), expected)
```

### Perft

Skup pozicija i podela dubina su u ADR-026. Podrazumevani suite ostaje ispod
~300.000 čvorova da bi se stvarno pokretao; dublje ide iza `CHESS_SLOW_TESTS=1`.

```python
@unittest.skipUnless(os.environ.get("CHESS_SLOW_TESTS"), "slow")
```

> **FEN-ovi i referentni brojevi se prepisuju sa Chess Programming Wiki.**
> Nikad iz sećanja — ni čovekovog ni modelovog. Svaka konstanta nosi komentar sa
> izvorom. Ako referenca nije potvrđena, to se kaže umesto da se pretpostavi.

### Determinizam

Test koji ne daje isti rezultat pri svakom pokretanju je pokvaren test.

- Zobrist tabela se generiše sa **fiksnim seed-om** (ADR-027)
- nema `random` bez seed-a, nema oslanjanja na `time.time()`
- nema oslanjanja na redosled `set`-a ili `dict`-a gde redosled nije garantovan

### Izolacija

- test **ne piše na disk** izvan `tempfile`. **Čitanje** fajlova iz repozitorijuma
  je dozvoljeno kad je predmet testa upravo sadržaj repozitorijuma:
  `tests/test_layers.py` obilazi stablo od 0.2b, a `tests/test_assets.py` čita
  `assets/` i `.gitattributes` od 0.4 (ADR-039), pa `LICENSE`, `THIRD-PARTY.txt` i
  `pyproject.toml` od 0.6 (ADR-042). Pravilo je od početka ciljalo na
  pisanje — formulacija „ne dira disk" bila je šira od namere i nije opisivala ono
  što projekat već radi.
  Od 0.6 `test_assets.py` čita i **sopstveni izvor**, da bi tvrdio da je čist ASCII.
  To nije izuzetak od pravila nego njegov najuži slučaj: provera ne sme da deli
  sudbinu sa kvarom od kog štiti (ADR-042).
- test **ne otvara socket** — server se testira kroz `Player` interfejs sa
  lažnom implementacijom, ne kroz mrežu
- test ne zavisi od drugog testa ni od redosleda izvršavanja

### Redosled

> **Test se piše pre implementacije, a bag prvo dobije test koji pada.**

Implementacija koja postoji pre testa određuje šta će test proveravati: test tada opisuje
ono što kod radi, umesto onoga što se od koda traži. Ispravka bez testa koji ju je
zahtevao ne dokazuje ništa — ne zna se ni da je bag reprodukovan, ni da se neće vratiti.
Redosled kod bagova je: test koji pada iz istog razloga iz kog je bag prijavljen, pa
ispravka, pa isti test prolazi.

Pravilo obavezuje kod u `src/` i `tools/`. Task koji menja samo `docs/` ili fajlove van
gita nema šta da testira; njegove kapije su ostale stavke iz §9.

### Pravilo koje se ne krši

> **Test se nikad ne menja da bi prošao.**

Ako test pada, greška je u kodu dok se ne dokaže suprotno. Ako je test zaista
pogrešan, to je **zaseban commit** sa obrazloženjem zašto je očekivanje bilo
pogrešno — nikad tiha izmena u istom commitu sa implementacijom.

---

## 6. Greške i izuzeci

### Hijerarhija

```python
class ChessError(Exception):          # core/types.py
class IllegalMoveError(ChessError):
class InvalidFenError(ChessError):
class InvalidSanError(ChessError):

class ProtocolError(Exception):       # protocol/codec.py
```

`core` baca samo `ChessError` potomke. `protocol` baca `ProtocolError` na
neispravan ulaz. Server hvata i pretvara u `ERROR` poruku sa kodom iz
`PROTOCOL.md`.

### Pravila

- **nikad goli `except:`** — uvek konkretan tip
- `except Exception` je dozvoljen samo na **granici procesa** (glavna petlja
  servera), i mora da loguje i nastavi ili da ponovo baci
- izuzetak nosi poruku na **engleskom**, dovoljno konkretnu za debug:
  `f"no piece on {to_algebraic(sq)}"`, ne `"invalid"`
- izuzetak **nikad ne nosi tekst za korisnika** — korisnički tekst ide kroz
  `message_key` i `sr.json` (ADR-010)
- `core` ne štampa ništa i ne loguje — vraća vrednost ili baca

### Validacija na granici

Sve što dolazi spolja proverava se u `protocol/codec.py`, jednom, na ulazu.
Posle te tačke kod radi sa proverenim `dataclass`-om i ne proverava ponovo.

Potez iz spoljnog sveta se **traži u listi generisanih legalnih poteza**, nikad
ne izvršava direktno (ADR-022). `Move.from_uci()` ne može da odredi `kind` bez
table — to nije nedostatak nego zaštita.

---

## 7. Ulaz/izlaz i enkodiranje

Razvija se na Windows-u, gde je podrazumevano enkodiranje `open()`-a lokalno, a
ne UTF-8. To je izvor grešaka koje se ne vide kod tebe dok ne pukne kod drugoga.

### Pravila

```python
# uvek, bez izuzetka
with path.open(encoding="utf-8") as f: ...

# JSON sa dijakritikom
json.dump(data, f, ensure_ascii=False, indent=2)
```

- **svaki `open()` ide sa `encoding="utf-8"` eksplicitno**
- putanje su `pathlib.Path`, nikad spojeni stringovi
- putanja do resursa se računa od modula, nikad od radnog direktorijuma:

```python
# broj .parent zavisi od dubine modula - broji se do korena, jedan po nivou
ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"          # src/chess/<modul>.py

# prepisano iz src/chess/client/i18n.py: i18n.py -> client -> chess -> src -> koren
CATALOG = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "i18n" / "sr.json"
```

- konfiguracija ide kroz promenljivu okruženja sa razumnim podrazumevanim:
  `os.environ.get("CHESS_DB_PATH", "chess.db")`

### Logovanje

- kroz `logging`, nikad `print()` u kodu biblioteke
- log poruke na **engleskom i bez dijakritika** — Windows konzola ume da pukne
  na č ć š ž đ (ADR-010)
- `DEBUG` za tok poruka, `INFO` za životni ciklus partije, `WARNING` za
  odbijene poteze i neispravne poruke, `ERROR` za neočekivano
- `print()` je dozvoljen samo u `tools/` i u ulaznim tačkama (`__main__.py`)

### Font i tekst

Nijedan tekst vidljiv korisniku ne stoji u kodu. Sve ide kroz ključ u
`assets/i18n/sr.json`. Font koji se pakuje mora da podržava č ć š ž đ —
DejaVu Sans, ne podrazumevani pygame font.

Šahovska notacija se **ne prevodi**: `e4`, `Nf3`, `O-O`, `1-0`, FEN, PGN su međunarodni
standard i ostaju kakvi jesu.

### Ključevi: `oblast.stvar`

Malim slovima, tačno jedna tačka: `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`.

Dve vrste ključeva, i pravilo **nije isto** za obe:

| Vrsta | Odakle ime | Primer |
|---|---|---|
| **izveden** | mehanički iz zatvorenog skupa u `PROTOCOL.md` (ADR-041) | `error.illegal_move` iz koda `ILLEGAL_MOVE`; `termination.checkmate` iz `"checkmate"` |
| **slobodan** | izmišljen kad tekst nastane | `menu.play` |

Izveden ključ se **ne izmišlja i ne preimenuje** — dobija se pravilom
(`"error." + kod malim slovima`), a `tests/client/test_i18n.py` poredi oba spiska u oba
smera. Slobodan ključ bira onaj ko piše tekst.

Kad se dodaje ključ, prvo se pogleda kojoj vrsti pripada. Za `menu.play` niko ne pita;
za `error.*` i `termination.*` protokol je već odlučio.

### Ugovor `t()` (ADR-040)

`t(key, params=None) -> str`. Puni tekst odluke je u ADR-040; ovde stoji ono što obavezuje
kod:

- **`t()` ne baca na loš podatak.** Nepostojeći ključ vraća se kao sam ključ, a parametar
  koji nije prosleđen ostaje vidljiv kao `{{ime}}`. Oba uz WARNING — koji je **drugi kanal
  pored simptoma na ekranu, nikad jedini.**
- **Baca na pogrešan poziv:** `RuntimeError` ako `load()` nije pozvan, `TypeError` ako
  parametar nije `str`.
- **`load()` odbija loš podatak glasno** — `ValueError` na BOM, neispravan JSON i duplirani
  ključ. Poruka je engleska i namenjena programeru (§6); korisnički tekst nikad ne izlazi iz
  izuzetka.
- Zamena je `{{ime}}`, ne `str.format` — funkcija se u 4.7 prevodi 1:1 u JavaScript.
  **Parametri su stringovi; `t()` ne poziva `str()`** (`str(1.0)` je `"1.0"`, `String(1.0)`
  je `"1"`). Broj se formatira na pozivnom mestu.

### Ton korisničkog teksta

> Tekst za korisnika je bezličan: bez drugog lica, bez prefiksa „Greška:", bez pripisivanja
> krivice. Poruka koju je izazvala radnja igrača opisuje stanje. Poruka koju je izazvao kvar
> imenuje šta se pokvarilo i šta sledi, nikad ono što je igrač uradio.

```
DA   Sada je protivnik na potezu.
NE   Greška: niste vi na potezu!

DA   Program je poslao neispravnu poruku. Veza je prekinuta.
NE   Poslali ste neispravnu poruku.
```

---

## 8. Git

### Grane

- `main` je uvek u stanju koje prolazi checkpoint
- rad ide na grani po fazi: `faza-1`, `faza-2`, …
- merge nazad u `main` sa `--no-ff`, da faza ostane vidljiva u istoriji

### Commit

Jedan task = jedan commit. Poruka na engleskom, u imperativu, po standardu
**Conventional Commits**:

```
<tip>: <šta, malim slovom, bez tačke>

<opciono telo: zašto, ne šta>
```

Tipovi: `feat` · `fix` · `docs` · `test` · `refactor` · `chore`

```
feat: add castling generation with five-condition check
fix: restore en passant square in unmake
docs: protocol v2, glossary, ADR-022 to ADR-031
test: add Position 3 and Position 4 perft cases
```

Telo se piše kad odluka nije očigledna iz diffa. Ako commit prati ADR, broj ADR-a
ide u telo.

### Šta nikad ne ulazi u commit

```
.claude/          CLAUDE.md         __pycache__/      *.pyc
.venv/            .idea/            chess.db          *.log
```

Repozitorijum je javan i u gitu se **ništa ne briše** — što uđe u commit, ostaje
u istoriji zauvek. Zato `.gitignore` postoji pre prvog commita (ADR-012).

### Provera da ništa ignorisano nije već ušlo u istoriju

Pokreće se **pre `push`-a**, i posle svake izmene `.gitignore`. `git status` za ovo
ne vredi — on gleda radno stablo i ne kaže šta je ušlo u commit prošle nedelje.

```bash
git rev-list --objects --all \
  | awk 'NF>1 { $1=""; sub(/^ /,""); print }' | sort -u \
  | git check-ignore --no-index --verbose --stdin
```

`git rev-list --objects --all` daje svaku putanju iz svakog stabla svakog commita,
dakle i preimenovane i kasnije obrisane fajlove. `--no-index` je obavezan: bez njega
`git check-ignore` **preskače praćene fajlove**, a praćen fajl koji `.gitignore`
opisuje je tačno ono što se traži.

Izlazni kod je obrnut od očekivanog: **`1` = nijedna putanja nije pogođena = čisto**,
`0` = nešto je pogođeno = stati i ne pushovati.

**Granica ove provere.** Ona vidi samo ono što je bilo u stablu repozitorijuma. Postoje
fajlovi koji utiču na projekat a žive **izvan** njega — `.gitignore` ih ne opisuje,
`git rev-list` ih nikad nije video, i nijedna komanda iz ovog odeljka ne može da ih
prijavi. Izmeren slučaj: `MEMORY.md` i fajlovi uz njega, u Claude Code profilu korisnika.
Ovde se imenuju, ne rešavaju (ADR-044).

Dok commit stoji samo lokalno, istorija se sme prepisati. Posle `push`-a na `main`
ispravka traži `push --force`, koji je zabranjen — a kod tajne prepis ionako ne
pomaže, jer udaljeni server drži objekat dohvatljivim po SHA. Tajna se opoziva i
menja, ne briše.

### Zabranjeno

- `push --force` na `main`
- `reset --hard`, `rebase`, `clean -fd`, `checkout -- <putanja>`, `restore` bez izričitog
  odobrenja — sve to baca radno stablo, i nijedno ne pita
- commit koji meša implementaciju i ispravku testa
- commit koji nosi ADR bez propagacije iz §1

#### `checkout --` vraća iz indeksa, ne sa HEAD-a

`git checkout -- <putanja>` i `git restore <putanja>` vraćaju fajl **iz indeksa**, a šta to
znači zavisi od toga da li je fajl `add`-ovan. Izmereno:

| Stanje fajla | Šta se desi |
|---|---|
| nema unos u indeksu (nov u tasku) | **odbija**: `did not match any file(s) known to git`, izlaz `1`, fajl netaknut |
| praćen, izmenjen, **nije** `add`-ovan | tiho vrati HEAD verziju — **ceo task nestaje**, izlaz `0`, bez upozorenja |
| praćen, `add`-ovan pa izmenjen | vrati `add`-ovano stanje — nestaje samo ono posle `add`-a |

Opasan je srednji red: nov fajl git štiti greškom, a fajl koji je pre taska postojao odlazi
u tišini. Zato ritual namernih kvarova počinje sa `git add -A` — posle njega indeks nosi
tekući task, pa `checkout --` briše kvar, ne rad.

### Referenciranje za pregled

Kad se dokument šalje na pregled van projekta, link se zakucava na **commit SHA**,
nikad na `main` — `main` može biti keširan i ne kaže koju verziju je čitalac video.

```
https://raw.githubusercontent.com/<user>/<repo>/<SHA>/docs/PROTOCOL.md
```

---

## 9. Definicija gotovog taska

Task nije gotov dok svih sedam ne prođe:

- [ ] `python -m unittest discover -s tests` prolazi
- [ ] `ruff check .` i `ruff format --check .` čisti
- [ ] perft pokrenut ako je diran generator poteza (obavezno od 1.3)
- [ ] pročitan `git diff` — ceo, ne preleteo
- [ ] odgovoreno na pitanja iz koraka 4 ritma po tasku; pitanje i odgovor
      zapisani u `docs/faze/faza-N.md` (ADR-021)
- [ ] `ROADMAP.md` ažuriran; `DECISIONS.md` dopunjen ako je doneta odluka, uz
      propagaciju iz §1 u **istom commitu**
- [ ] commitovano

Poslednja stvarna provera nije na listi jer se ne može odštiklirati:

> **Mogu naglas da objasnim šta je urađeno i zašto baš tako.**

Ako to ne prolazi, ne prelazi se na sledeći task — pitaj da ti se objasni
drugačije, ili odnesi kod na claude.ai.

---

## 10. Alati

| Alat | Uloga | Zavisnost |
|---|---|---|
| `ruff` | linter i formatter | dev-only |
| `unittest` | testovi | stdlib |
| `tools/perft.py` | perft i `perft_divide` | u gitu (ADR-028) |
| `tools/cli_client.py` | CLI klijent za testiranje servera | u gitu (ADR-017) |
| `tools/layer_check.py` | provera uvoza iz §2 | u gitu (ADR-033) |
| `tools/rasterize_pieces.py` | SVG figure → PNG, dve veličine | u gitu (ADR-038) |

Konfiguracija `ruff`-a stoji u `pyproject.toml`: `line-length = 100`,
`target-version = "py311"`, `extend-exclude = ["docs"]`.

`docs/` je isključen jer `ruff format` ulazi i u Python blokove unutar Markdown
fajlova i prepravlja namerno zbijene primere (ADR-035). Dokumentacija nije kod.

Nova zavisnost se **ne dodaje bez odobrenja i bez ADR-a.** Trenutna lista je
`pygame` za klijenta i `ruff` za razvoj. To je sve.

`build-system.requires` u `pyproject.toml` **nije zavisnost projekta**, nego zahtev
okruženja u kom se paket gradi — a to okruženje `pip` stvara sam, izolovano, i posle
izgradnje ga briše. Podizanje njegove donje granice zato ne obara rečenicu iznad.
Trenutno stoji `setuptools>=77`, jer je 77 prvo izdanje koje prihvata `project.license`
kao SPDX izraz; 76.1.0 ga odbija `ValueError`-om (ADR-043).

Alat koji jednom generiše resurs čiji rezultat ide u git **nije zavisnost
projekta** (ADR-038). Piše se onim što već postoji; ako to ne ide, bira se između
nove zavisnosti i drugog puta — i taj izbor traži ADR, jer je mogao ići drugačije.
