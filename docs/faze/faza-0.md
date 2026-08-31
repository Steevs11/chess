# Faza 0 — Skelet

Beleške nastale tokom rada na fazi 0. Fajl se dopunjuje posle **svakog** taska:
dva reda po ADR-021 — postavljeno pitanje i da li sam znao odgovor.

Prepričavanje cele faze svojim rečima dolazi na kraju faze, kao poslednji odeljak.

**Checkpoint faze:** `pip install -e ".[dev]"` pa
`python -m unittest discover -s tests` prolazi (uključujući `test_layers.py`),
`ruff check .` i `ruff format --check .` čisti.

> `ruff format --check .` je u checkpoint ušao u 0.2. Do tada je bio neupotrebljiv
> kao uslov — padao je na dokumentaciji, ne na kodu (ADR-035). Gate koji ne može
> da prođe se ne štiklira, nego se popravi ili ukloni.

---

## 0.1 — Struktura foldera

Napravljena je struktura paketa iz `PROJECT.md` §5: `src/chess/` sa šest
podpaketa, `tests/` koji je preslikava, plus `tools/` i `assets/`. Samo
`__init__.py` fajlovi — nijedan prazan modul; `types.py`, `board.py` i ostali
nastaju svaki u svom tasku.

### Otvoreno — gate iz CONVENTIONS §9 nije zatvoren na 0.1

> ✅ **Zatvoreno u 0.2** kroz `extend-exclude = ["docs"]` u `pyproject.toml`
> (ADR-035). Tekst ispod ostaje kako je zapisan — kako je problem otkriven i
> zašto tri druga rešenja nisu prošla vredi više od zaključka.

`ruff check .` je čist. **`ruff format --check .` pada**, i to ne na kodu:

```
unformatted: File would be reformatted
   --> docs\CONVENTIONS.md:381:39
```

`ruff` 0.16.5 po defaultu formatira i Python blokove unutar Markdown fajlova.
U `CONVENTIONS.md` §7 stoji namerno zbijen primer, koji `ruff` hoće da razlomi
na dva reda:

```
# napisano u dokumentaciji, u jednom redu
with path.open(encoding="utf-8") as f: ...

# ruff hoce da razlomi na dva reda
with path.open(encoding="utf-8") as f:
    ...
```

To je dokumentacija, ne kod, i ne sme da se prepravlja da bi alat ćutao.

> Ovaj blok namerno **nije** označen kao ` ```python `. Prvi put jeste bio, pa ga
> je `ruff` prepravio i time izjednačio „napisano" i „ruff hoće" — primer je sam
> sebe pojeo. To je najjasniji mogući dokaz da problem postoji.

**Rešenje pripada tasku 0.2**, jer je to konfiguracija `ruff`-a, a `pyproject.toml`
je njegov predmet: dodaje se isključivanje Markdown fajlova (`extend-exclude`)
i tek tada `ruff format --check .` postaje upotrebljiv kao gate. Do tada se
`ruff format --check .` čita ručno — kod prolazi, prijava se odnosi samo na
`docs/`.

Nije rešeno prekidačem u komandnoj liniji niti sužavanjem komande na
`src/ tests/`: gate glasi `ruff format --check .`, sa tačkom. Komanda koja se
suzi dok ne prođe više ništa ne dokazuje.

### Pitanja

Pitanja su rekonstruisana naknadno, u sesiji posle commita `ec3e754`, jer u trenutku
commita nisu bila zapisana. Na 2 i 3 sam prvo odgovorio pogrešno; tačan odgovor je
došao tek posle objašnjenja na claude.ai.

**1. Zašto `src/chess/`, a ne `chess/` u korenu, kad to traži `pip install -e .`?**
Znao — delimično. Pogodio sam organizaciju koda, promašio mehanizam.
Python stavlja trenutni folder na početak `sys.path`, pa kod flat layouta `import
chess` nađe `./chess/` prosto zato što stojim u njemu — instalacija se nikad ne
proveri. Greška u `pyproject.toml` se tako ne vidi: testovi prolaze uvozeći mimo
instalacije, a puca kod druge osobe posle `git clone`. Sa `src/` u korenu nema
foldera `chess`, pa uvoz mora kroz ono što je `pip` upisao — testira se ono što se
stvarno instalira. Kod `-e` su fajlovi isti, ali put do njih ide kroz zapis koji je
`pip` napravio čitajući `pyproject.toml`, pa greška u tom fajlu pada odmah (ADR-029).

**2. Zašto `tests/` dobija `__init__.py`, a `tools/` i `assets/` samo `.gitkeep`,
kad su sva tri fajla prazna?**
Nisam znao. Prvi odgovor je bio da `__init__.py` omogućava uvoz standardnih
biblioteka — netačno; `import json` radi bez ijednog `__init__.py`.
Oba fajla drže folder u gitu, jer git prati fajlove a ne foldere, ali govore
različitim alatima. `.gitkeep` govori samo gitu. `__init__.py` govori i Pythonu:
„ovo je paket, sme se uvesti kao `tests.core`". Ako obrišem `tests/core/__init__.py`,
`unittest discover` u Pythonu 3.11 taj folder **tiho preskoči** — bez greške, bez
poruke. Vidim `OK` i mislim da je prošlo, a pola testova se nije ni pokrenulo.
Tišina je opasnija od greške. `tools/` ga nema jer se `layer_check.py` pokreće kao
skripta i nikad se ne uvozi; `assets/` uopšte nema Python fajlova.

**3. Zašto granica stoji i u docstringu `__init__.py`, kad već stoji u
`CONVENTIONS §2` i kad će je `layer_check.py` mašinski proveravati?**
Nisam znao. Prvi odgovor je opisao hijerarhiju dokumenata (ADR-030/ADR-032) — tačno,
ali odgovor na drugo pitanje.
Tri mesta hvataju istu grešku u tri različita trenutka. `CONVENTIONS.md` pre pisanja,
ali samo ako ga otvorim. `layer_check.py` posle pisanja, kad pokrenem testove.
Docstring **dok** pišem, jer stoji u fajlu pored onog koji uređujem. Alat kaže
„zabranjeno" i ništa više; docstring kaže **zašto** — `core` ostaje čist da bi
preživeo prelazak na veb bez izmene. Sa razlogom znam i kad pravilo ne važi; bez
razloga ga samo zaobilazim.

---

## 0.2 — `pyproject.toml` i prvi test

Task je bio manji nego što izgleda: `pyproject.toml` je skoro ceo napisan još u
0.1 — `pygame` kao zavisnost, `line-length = 100`, `select` lista pravila,
zabrana `pickle`-a, `where = ["src"]`. Ovde je dodat **jedan red**,
`extend-exclude = ["docs"]`. Sve ostalo u tasku je bilo zatvaranje četiri stvari
koje 0.1 nije zatvorio, i pisanje prvog testa.

### Šta je urađeno

| Šta | Gde |
|---|---|
| `extend-exclude = ["docs"]` | `pyproject.toml`, `[tool.ruff]` (ADR-035) |
| `pip install -e ".[dev]"` kao tačna komanda | ADR-036 + propagacija u 4 fajla |
| prvi test | `tests/test_package.py` |
| permission obrasci za stvarne komande | `.claude/settings.json` |
| hook obrisan, ne vraćen | `.claude/settings.json` |
| tri `.claude/` fajla koji su protivrečili ADR-ovima | `.claude/rules/`, `.claude/skills/` |

### `extend-exclude` — zašto baš `["docs"]`

Obrasci su **izmereni**, ne pretpostavljeni. `"docs"`, `"docs/*.md"` i
`"docs/**/*.md"` daju exit 0. `"*.md"` **ne radi** — `ruff` 0.16.5 obrazac bez
kose crte ne primeni. `"**/*.md"` je bio gori nego ništa: uvukao je i fajlove
koje `.gitignore` isključuje, pa je prijavio dva fajla umesto jednog.

Izabran je `"docs"` jer posle njega `ruff check . --show-files` izlista tačno
11 `.py` fajlova projekta i `pyproject.toml`, i ništa više — najuži ishod od sva
tri koja rade.

Cena je zapisana u ADR-035: Python blokovi u dokumentaciji od sada nemaju nikakvu
mašinsku proveru. Primer sa sintaksnom greškom proći će nezapaženo.

### `pip install -e .` nije bilo dovoljno

`ruff` stoji u `[project.optional-dependencies] dev`, pa ga `pip install -e .`
ne instalira. `PROJECT.md` §4 je tvrdio „jedna komanda, to je sve", a checkpoint
svake faze traži `ruff check .` — komande koje posle te instalacije nema.

Netačnost je stajala od prvog dana i primetila se tek kad je gate stvarno
pokrenut. Komanda je sada `pip install -e ".[dev]"`; navodnici su deo komande jer
i `bash` i PowerShell drugačije čitaju gole uglaste zagrade.

`ruff` **nije** premešten u `dependencies` — igraču šaha linter ne treba.

### Prvi test

`tests/test_package.py`, dva testa. Ne testiraju šah, nego preduslov na koji se
svi kasniji testovi oslanjaju:

1. **svih sedam podpaketa se uvozi** i svaki ima docstring — kroz `subTest()`, da
   jedan pad ne sakrije ostale (CONVENTIONS §5)
2. **metapodaci distribucije postoje** — `importlib.metadata.version("chess")`

Drugi test razlikuje „uvezlo se" od „instalirano je": uvoz može uspeti i preko
`sys.path`, a metapodaci postoje samo ako je `pip` pročitao `pyproject.toml`.

Prva verzija je poredila sa `"0.1.0"`. To je odbačeno: test bi pucao pri svakoj
promeni verzije, a jedina ispravka bila bi prepravka testa da prođe — tačno ono
što CONVENTIONS §5 zabranjuje. Test sada tvrdi da metapodaci **postoje**, ne koja
im je vrednost. Dokaz je isti — bez `pip`-a `metadata.version()` baca
`PackageNotFoundError`, ne vraća prazan string.

`unittest discover` više ne javlja `Ran 0 tests`.

### Zašto hook u `.claude/settings.json` ostaje ugašen

Blok `_hooks_disabled` je pokretao `ruff format` i `ruff check --fix` posle svakog
`Edit`/`Write`. **Obrisan je, ne vraćen.** Četiri razloga, po težini:

1. **Ne bi ni radio.** Komanda glasi `ruff format $CLAUDE_FILE_PATHS`, a `ruff`
   nije na `PATH`-u — Bash alat startuje shell bez aktiviranog venv-a. Uz
   `2>/dev/null; exit 0` hook nikad ne prijavi grešku. Dobili bismo alat koji
   izgleda da radi a ne radi ništa — gore od nepostojećeg alata, po istoj logici
   kojom `CLAUDE.md` brani zaostalu dokumentaciju.
2. **`--fix` menja kod tiho, posle mene.** CONVENTIONS §9 traži pročitan
   `git diff` — ceo. Auto-fix koji izbaci uvoz ili prepiše izraz pravi diff koji
   nisam video da nastaje, u projektu čiji je cilj da svaku liniju branim usmeno
   (ADR-021).
3. **Gate već postoji.** `ruff check .` i `ruff format --check .` iz CONVENTIONS
   §9 hvataju isto, ali na kraju taska i vidljivo.
4. **Mrtav ključ je treća vrsta laži.** `_hooks_disabled` liči na konfiguraciju a
   nije; sledeći čitalac mora da poznaje Claude Code interno da bi to znao.

Iz istog razloga je iz allow liste izbačen i `ruff format` bez `--check`:
formatiranje koje menja fajlove ostaje ručna komanda koja se odobrava kad zatreba.

Ako se ikad poželi automatsko formatiranje: samo `ruff format` (bez `--fix`), sa
punom putanjom do `.venv/Scripts/ruff.exe`, bez gutanja grešaka, i uz
`force-exclude = true` u `pyproject.toml` — jer tada `ruff` dobija eksplicitne
putanje, na koje se `extend-exclude` inače ne primenjuje.

### `.claude/` je bio treći izvor istine

Provera je pokazala da je 80–85% od ~378 redova u `.claude/rules/` i
`.claude/skills/` prepričavanje `CONVENTIONS.md`, `PROJECT.md`, `POJMOVNIK.md` i
ADR-ova. To samo po sebi nije greška, ali `.claude/` nije u hijerarhiji dokumenata
(CONVENTIONS §1) i nije pokriven pravilom propagacije (ADR-030/032) — pa mu ADR-i
prolaze iznad glave. Tri puta jesu:

| Fajl | Šta je tvrdio | Šta ga obara |
|---|---|---|
| `rules/core-purity.md` | `frozen=True` dataclass za `Square` | ADR-013 se zove „`Square` je `int`, ne dataclass"; ADR-031 precizira |
| `skills/layer-check/SKILL.md` | 67 redova ručnih `grep` provera, bez pomena `tools/layer_check.py` | ADR-033 i CONVENTIONS §2: „ne skillom" |
| `skills/perft/SKILL.md` | `tests.test_perft`, samo 2 pozicije, bez `CHESS_SLOW_TESTS` | CONVENTIONS §5 (`tests.core.test_perft`), ADR-026 (4 pozicije), ADR-028 |

Sva tri su ispravljena. Prvi je bio najopasniji: učitava se automatski na svaki
dodir `src/chess/core/**`, pa bi obarao task 1.1 baš u trenutku kad se `Square`
piše.

Duplirani ali **tačan** sadržaj nije diran. Svođenje `.claude/` na pokazivače je
zaseban posao i ne pripada tasku o `pyproject.toml`-u.

### Sadržaj iz `.claude/` koji po ADR-028 pripada gitu

*„Ako nešto radi i bez asistenta, ide u git."* Šest stavki ispunjava taj uslov, a
živi samo u folderu koji CONVENTIONS §8 zabranjuje da uđe u commit. Ne sele se
sada — svaka stiže u task u kom se koristi i tada je razumljiva. Lista postoji da
se ne izgubi:

| Šta | Živi u | Seli se u |
|---|---|---|
| „Socket u svojoj niti; pygame se nikad ne dira iz mrežne niti" | `rules/client-boundaries.md` | **3.2** → CONVENTIONS §3 |
| „`BotScene` u fazi 6 mora biti nov fajl, ne prepravka postojećih" | `rules/client-boundaries.md` | **6.7** → ROADMAP ili ADR |
| Konvencija i18n ključeva `oblast.stvar` | `rules/i18n.md` | **0.5** → CONVENTIONS §7 |
| `t()` vraća ključ kad prevoda nema, ne baca | `rules/i18n.md` | **0.5** → CONVENTIONS §7 (kandidat za ADR — izbor je mogao ići drugačije) |
| Kiwipete FEN + brojevi d1–d3 · tabela simptom→uzrok | `skills/perft/SKILL.md` | **1.3** → `tests/core/test_perft.py` uz komentar o izvoru, odnosno docstring `tools/perft.py` |
| „`b1`/`b8` mora biti prazno, ali sme biti napadnuto" | `skills/chess-rules/SKILL.md` | **1.4** → `PROJECT.md` §7 |

### Pitanja

**1. Zašto je `extend-exclude` u `[tool.ruff]`, a ne u `[tool.ruff.format]`, kad
je izmereno da `ruff check` Markdown uopšte ne čita?**
Znao. `[tool.ruff]` važi za ceo alat — i za `check` i za `format`. To da `check`
danas ne čita Markdown je stanje verzije 0.16.5, ne garancija; ako `ruff` sutra
dobije pravilo koje čita blokove u dokumentaciji, isključenje u `[tool.ruff.format]`
ga ne bi pokrivalo i problem bi se vratio na druga vrata. Šira sekcija izražava
**nameru** — „`docs/` nije kod, `ruff` ga ne dira" — umesto da opisuje trenutno
ponašanje jednog potkomandnog alata.

**2. Šta `metadata.version("chess")` dokazuje, a `import chess` ne može?**
Znao. Uvoz može uspeti a da `pip` nikad nije pokrenut: Python stavlja trenutni
folder na početak `sys.path`, pa bi `import chess` prošao i da se paket zatekne
negde na putanji, bez ijedne instalacije. Prvi test dakle dokazuje samo da je kod
**dohvatljiv**. `importlib.metadata` čita metapodatke distribucije, a njih pravi
isključivo `pip` kad pročita `pyproject.toml`; bez instalacije baca
`PackageNotFoundError`. Prvi test tvrdi „uvezlo se", drugi „instalirano je" — dve
različite tvrdnje, a ADR-029 se oslanja na drugu.

**3. Zašto je pogrešna tvrdnja u `core-purity.md` opasnija od komande u
`perft/SKILL.md` koja uopšte ne radi?**
Znao, i preko onoga što je pitano. Kvar koji puca sam sebe prijavljuje: pokreneš
`tests.test_perft`, dobiješ grešku da modul ne postoji, ispraviš za minut, šteta
je nula. Tvrdnja da je `Square` `frozen` dataclass **radi savršeno** — kod bi se
napisao, testovi bi prolazili, ništa ne bi puklo. Otkrilo bi se tek kad perft na
dubini 5 alocira desetine miliona objekata i postane neupotrebljivo spor, a tada
bi trebalo prepraviti `board.py`, `movegen.py` i sve što `Square` dodiruje. Uz to
se `core-purity.md` učitava automatski na svaki dodir `src/chess/core/**` — dakle
baš u tasku 1.1, gde se `Square` piše. Tiha greška u pravom trenutku je skuplja od
glasne greške u pogrešnom.

---

## 0.2b — `layer_check.py` i `test_layers.py`

Tabela iz `CONVENTIONS.md` §2 je do sada bila pravilo koje niko ne sprovodi. Sada je
sprovodi alat od 254 reda, koji parsira svaki `.py` fajl kroz `ast` i poredi svaki uvoz
sa redom tabele, i 15 testova koji proveravaju **alat**, ne samo kod.

| Šta | Gde |
|---|---|
| alat, `RULES` + prepis tabele u docstringu | `tools/layer_check.py` |
| 15 testova, `ALLOWED` (21) i `FORBIDDEN` (21) | `tests/test_layers.py` |
| red `*/__init__.py`, redosled biranja reda, značenje „sve gore" | `CONVENTIONS.md` §2 |
| ADR-037 sa tri citljive tačke | `DECISIONS.md` |

### Tri pitanja koja je otvorilo pisanje alata

**1. Kako test uvozi alat kad `tools/` nije paket?** Kroz `importlib.util`, po putanji
izračunatoj od `__file__` (§7). `tools/` ostaje folder sa skriptama, kako je i zapisano
u 0.1. Odbačeni su `sys.path.insert` — menja globalno stanje procesa i uvodi zavisnost
od redosleda testova — i `subprocess`, koji bi testirao CLI omotač umesto pravila i pri
padu dao samo izlazni kod, bez fajla i linije.

> Zamka koja se videla tek pri pokretanju: `@dataclass` razrešava anotacije modula sa
> `from __future__ import annotations` kroz `sys.modules[cls.__module__]`. Za modul koji
> nije registrovan to je `None`, pa alat pukne pri učitavanju. Red
> `sys.modules[_spec.name] = layer_check` **pre** `exec_module` nije stilska sitnica nego
> uslov da se modul uopšte učita.

**2. Šta sa fajlom koji tabela ne opisuje?** Prijavljuje se kao nalaz (ADR-037.2).
Preskakanje bi značilo da nov paket dobija nula provere a da to niko ne vidi — isti oblik
kvara kao obrisan `tests/core/__init__.py` iz pitanja 2 u tasku 0.1. Posledica: u fazi
3.1 `client/__main__.py` neće proći dok mu se ne doda red u §2.

**3. Kako tabela dolazi do koda a da ne nastane drugi izvor istine?** Prepisom u `RULES`
plus testom koji veže **imena redova** sa pipe-tabelom iz `CONVENTIONS.md`. Alat koji bi
sam parsirao tabelu tražio bi da ćelije budu gramatika — „sve gore + `pygame`" i „sve"
to nisu — pa bi se tabela prepisala u strogi oblik i dokument bi počeo da služi alatu.

Prepisivanje je nateralo da se dvosmislena ćelija dovrši: „sve gore" sada u §2 znači i
smer unutar `client/` (`i18n` ← `state` ← `render` ← `scenes`), jer bi `state.py` koji
sme `render.py` posredno povukao pygame i prestao da bude prevodiv 1:1 (ADR-004).

### Dokaz da test nije prazan

Sa privremenim `import pygame` u `core/__init__.py` i praznim `src/chess/ai/engine.py`:

```
src/chess/ai/engine.py:0: not covered by the import table (CONVENTIONS 2) - add a row for it
src/chess/core/__init__.py:3: may not import third-party pygame (CONVENTIONS 2)
2 violation(s) of the import table in CONVENTIONS 2   exit=1
```

Testovi su pali na dva mesta, alat vratio 1. Posle vraćanja: `14 files`, `Ran 15 tests OK`.

### Pitanja

**1. Zašto `check_source()` prima tekst, a ne `Path`, kad alat u radu uvek čita fajlove
sa diska?**
Znao. Zbog testova: sa `Path`-om bi svaki od 42 slučaja iz `ALLOWED` i `FORBIDDEN` morao
da napravi fajl, a test ne dira disk izvan `tempfile` (§5). Uz to razdvaja dve
odgovornosti — `check_source` presuđuje, `check_tree` čita disk. Da su spojene,
presuđivanje se ne bi moglo testirati bez čitanja.

**2. Test „stablo je čisto" prošao bi i da alat ne vidi nijedan uvoz. Šta to sprečava, i
zašto moraju oba testa?**
Znao. `test_forbidden_imports_are_reported` sa 21 slučajem koji **mora** da da nalaz —
alat koji oslepi pada odmah. Oba su potrebna jer tvrde suprotne stvari: prvi „nema lažnih
uzbuna", drugi „nema propuštenih". Alat koji sve prijavljuje prolazi drugi a pada prvi;
alat koji ćuti prolazi prvi a pada drugi. Tek zajedno znače da presuđuje.

**3. Koja izmena u alatu ne bi oborila nijedan test?**
Znao, uz samoispravku u toku odgovora. Prvi primer — dodati `"server"` u red `protocol/*`
— zapravo pada, jer `FORBIDDEN` sadrži `protocol/codec.py` koji uvozi `chess.server`.
Ali klasa problema je tačna: spona proverava imena redova, ne sadržaj ćelije, pa proširenje
pravila prolazi svuda gde negativan slučaj ne postoji. Konkretno je to bio `client/i18n.py`,
koji je imao samo `import pygame` kao zabranjen slučaj — dodat mu je i `chess.core.types`,
pa red više nije neproveren. Opšta odbrana ostaje čitanje diffa; zato tabela stoji doslovno
prepisana u docstringu tik iznad `RULES`, i zato je taj gubitak zapisan u ADR-037.1.

---
