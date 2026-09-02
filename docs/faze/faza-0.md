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

*„Ako nešto radi i bez asistenta, ide u git."* Sedam stavki ispunjava taj uslov, a
živi samo u folderu koji CONVENTIONS §8 zabranjuje da uđe u commit. Ne sele se
sada — svaka stiže u task u kom se koristi i tada je razumljiva. Lista postoji da
se ne izgubi:

| Šta | Živi u | Seli se u |
|---|---|---|
| „Socket u svojoj niti; pygame se nikad ne dira iz mrežne niti" | `rules/client-boundaries.md` | **3.2** → CONVENTIONS §3 |
| „`BotScene` u fazi 6 mora biti nov fajl, ne prepravka postojećih" | `rules/client-boundaries.md` | **6.7** → ROADMAP ili ADR |
| ✅ Konvencija i18n ključeva `oblast.stvar` | `rules/i18n.md` | **preseljeno u 0.5** → CONVENTIONS §7 |
| ✅ `t()` vraća ključ kad prevoda nema, ne baca | `rules/i18n.md` | **preseljeno u 0.5** → CONVENTIONS §7 i ADR-040 (kandidat za ADR se ostvario) |
| ✅ Notacija se ne prevodi (`e4`, `Nf3`, `O-O`, `1-0`, FEN, PGN) | `rules/i18n.md` | **preseljeno u 0.5** → CONVENTIONS §7 |
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

## 0.3 — `.gitignore` proveren, commit, push

Task koji izgleda kao štikliranje, a nije: pet commita je čekalo push na javni
repozitorijum, a po ADR-012 u gitu se ništa ne briše. Push je jednosmerna vrata —
dok commit stoji lokalno istorija se sme prepisati, posle push-a na `main` ispravka
traži `push --force`, koji je zabranjen. Provera je zato morala da se obavi **pre**
push-a, i morala je da ima moć da ga zaustavi.

### Zašto `git status` nije provera

`git status` gleda radno stablo. Pitanje nije „šta je sad tu", nego „šta je ušlo u
commit pre tri dana i ostalo tamo zauvek". To su dva različita pitanja, a samo drugo
je važno posle push-a.

Provera ide kroz svaki objekat svakog commita:

```bash
git rev-list --objects --all \
  | awk 'NF>1 { $1=""; sub(/^ /,""); print }' | sort -u \
  | git check-ignore --no-index --verbose --stdin
```

Dve zamke, obe zapisane u CONVENTIONS §8 da se ne otkrivaju ponovo:

1. **`--no-index` je obavezan.** Bez njega `git check-ignore` preskače praćene
   fajlove — a praćen fajl koji `.gitignore` opisuje je tačno ono što se traži.
   Podrazumevano ponašanje bi na jedini zanimljiv slučaj odgovorilo ćutanjem.
2. **Izlazni kod je obrnut.** `1` = ništa nije pogođeno = čisto. `0` = uzbuna.
   Ko ga pročita kao običan alat, dobiće tačno pogrešan zaključak.

Uzet je `rev-list --objects`, a ne `log --diff-filter=A`, jer `A` ne vidi
preimenovanja (`R`), pa bi fajl dodat pa preimenovan mogao da promakne. Obe metode
su pokrenute; obe su dale isto.

### Rezultat

| Šta | Vrednost |
|---|---|
| commita u istoriji | 10 (5 pushovano, 5 čekalo) |
| jedinstvenih putanja ikad u stablu | 36 |
| pogođeno obrascima iz `.gitignore` | **0** (`exit 1`) |
| `git status --porcelain` | prazno |

Sve što je nastalo u 0.1–0.2b i ne sme u git — `.venv/`, `.ruff_cache/`, `.idea/`,
`.claude/`, `CLAUDE.md`, `src/chess.egg-info/` i 12 `__pycache__/` foldera — stoji
pod `!!` u `git status --ignored`: ignorisano i nikad praćeno. `src/chess.egg-info/`
hvata `*.egg-info/`, jer obrazac bez kose crte važi na svakoj dubini, ne samo u korenu.

### Nalaz: `*.log`

CONVENTIONS §8 nabraja osam stavki koje „nikad ne ulaze u commit". `.gitignore` je
pokrivao sedam. `*.log` je nedostajao.

Dodat je u `.gitignore`, nije izbačen iz CONVENTIONS: §8 je propis, `.gitignore` je
njegova implementacija, pa se dopunjuje implementacija. Ništa u projektu još ne piše
`.log`, ali server iz faze 2 loguje (§7) — pitanje je bilo kad, ne da li. A obrazac
koji nedostaje otkriva se tek kad je fajl već u commitu, dakle prekasno.

### Odgovor unapred — šta da je provera nešto našla

Zapisano pre pokretanja, jer posle push-a odgovor više nije isti:

- **nalaz samo u nepushovanim commitima** → prepis istorije (`git filter-repo`) je
  besplatan, jer `push --force` nije potreban za commite koje udaljeni repo nema;
- **nalaz u već pushovanim commitima** → prepis traži `push --force` na `main`,
  koji je zabranjen. Ako je tajna — opoziv i rotacija, ne brisanje, jer udaljeni
  server drži objekat dohvatljivim po SHA i posle prepisa. Ako je smeće —
  `git rm -r --cached` od tog commita nadalje, istorija ostaje kakva jeste, i to
  ide u ADR jer je odluka mogla ići drugačije;
- **nalaz samo u radnom stablu** → nije problem istorije, dopuni se `.gitignore`.

U sva tri slučaja push staje dok korisnik ne odluči.

### Pitanja

**1. Zašto je podrazumevano ponašanje `git check-ignore` — preskakanje praćenih fajlova
— pogrešno baš za ovu proveru?**
Znao. Alat je napravljen za suprotno pitanje: „zašto mi ovaj **nepraćeni** fajl ne ulazi
u commit". Za tu upotrebu preskakanje praćenih fajlova ima smisla, jer praćen fajl ulazi
bez obzira na `.gitignore`. Mi pitamo obrnuto — da li je nešto ušlo u istoriju iako ga
`.gitignore` opisuje — pa je praćen fajl koji obrazac pogađa **jedini nalaz koji nas
zanima**, i baš o njemu podrazumevano ponašanje ćuti. Bez `--no-index` provera bi uvek
vraćala „čisto", i to najglasnije kad bi trebalo da vrišti.

**2. Zašto `*.egg-info/` hvata `src/chess.egg-info/`, a `.venv/` ne bi uhvatio
`src/.venv/`?**
Znao, i oborio pitanje. Druga polovina pitanja je netačna: `.venv/` bi ga uhvatio.
Pravilo iz `gitignore(5)` gleda da li kosa crta stoji **na početku ili u sredini**
obrasca; crta na kraju znači samo „ovo je folder, ne fajl" i ne veže obrazac za koren.
Oba reda imaju crtu isključivo na kraju, pa oba važe na svakoj dubini stabla. Razlika
koju je pitanje tražilo postojala bi tek kod `/.venv/` — vodeća crta vezuje obrazac za
folder u kom `.gitignore` stoji. Takvog reda u našem `.gitignore` nema nijednog.

> Pitanje je postavljeno sa netačnom pretpostavkom, uz napomenu „nije očigledno" koja je
> gurala ka pogrešnom odgovoru. Zapisano je jer je oboreno pitanje jači dokaz razumevanja
> od tačnog odgovora — a i podsetnik da se `gitignore(5)` proverava, ne pamti.

**3. Zašto je `*.log` moralo odmah, kad nijedna linija koda još ne otvara `.log`, a
`tools/history_check.py` nije morao, iako bi proveru učinio mašinskom?**
Znao. Odlučuje cena kašnjenja, ne cena rada. Ako `*.log` fali u trenutku kad server prvi
put zaloguje, fajl uđe u commit i po ADR-012 ostaje tamo zauvek — kašnjenje je nepovratno,
a rad sada je jedan red. Ako alata nema, provera se otkuca ručno komandom iz §8; ništa se
ne gubi, kašnjenje košta nula. Uz to se dve provere razlikuju po ritmu: `layer_check`
gleda nešto što se menja svakim novim fajlom, a istorija se proverava pred `push` — desetak
puta u životu projekta.

---

## 0.4 — Figure, font i dva `LICENSE.txt`

Prvi task koji unosi **tuđi materijal** u javni repozitorijum. Težište nije bilo na
kodu nego na licencama, iz jednog razloga: po ADR-012 se u gitu ništa ne briše, a
netačna licenca — za razliku od tajne — nema opoziv. Ko uzme materijal oslanjajući
se na naš `LICENSE.txt` nasledi našu grešku u svoj repozitorijum, i mi za to nikad
ne saznamo.

Nijedan gate to ne hvata. `ruff`, `unittest` i `layer_check` prolaze nad savršeno
pogrešnom licencom. Zato je task imao **četiri tačke zaustavljanja** na kojima se
ne nastavlja bez čovekove potvrde.

| Šta | Gde |
|---|---|
| 12 SVG originala, `sha1` proveren nad preuzetim bajtovima | `assets/pieces/svg/` |
| 24 PNG rasterizacije, 80 px i 32 px | `assets/pieces/png/80/`, `/32/` |
| poreklo, autor, BSD-3, permalinkovi sa `oldid`, `sha1` | `assets/pieces/LICENSE.txt` |
| DejaVu Sans 2.37, licenca kopirana bajt u bajt | `assets/fonts/` |
| verzija, arhiva, `sha256` — naš dokument, ne njihov | `assets/fonts/PROVENANCE.txt` |
| rasterizator bez nove zavisnosti, sa samoproverom | `tools/rasterize_pieces.py` |
| provera `sha1` lanca | `tests/test_assets.py` |
| tuđi materijal se čuva bajt u bajt | `.gitattributes` |
| ADR-038 (odbijen `cairosvg`), ADR-039 (bajt u bajt) | `DECISIONS.md` |

### Ono što stranica tvrdi nije ono što je u fajlu

Opisi za `wk` i `bk` na Commons-u kažu „default size 64x64", dok ostalih deset kažu
45x45 — a svih 12 fajlova na disku je `width="45" height="45"`, bez `viewBox`-a.
Opis je tekst koji je čovek otkucao pre petnaest godina; SVG je ono što se stvarno
rasterizuje.

Plan je do tog trenutka imao zakucan `viewBox="0 0 45 45"` kao rezervu. Da je opis
bio tačan, dobili bismo gornjih levih 45 od 64 jedinice — odsečenog kralja, tiho:
dimenzija izlaza tačna, površina neprazna, obe samoprovere prolaze. `viewBox` se
zato **izvodi** iz pročitanih `width`/`height`, a fajl bez ijednog od njih je nalaz
koji zaustavlja alat.

### nanosvg ne skalira crtež — izmereno, pa tek onda zapisano

Prva verzija alata je prepisivala `width`/`height`, dodavala `viewBox` i verovala
rasterizatoru. Rezultat je izgledao ispravno na kontaktnoj tabli i prošao je **obe**
samoprovere. Uhvatio ga je tek 4× zum, slučajno.

Merenje je pokazalo zašto: bela dama je zauzimala 39×35 piksela na poziciji (3,5) —
**identično** na 80 px i na 32 px. Platno se menjalo, crtež nije. Na 32 px je bio
odsečen.

Poređenje veličina u bajtovima, koje je bilo u planu kao nezavisna provera, ovo
**takođe nije uhvatilo**: fajlovi se razlikuju jer se platna razlikuju.

Ispravka je da alat sam skalira geometriju kroz `<g transform="scale(...)">`, a
treća tvrdnja u alatu je relativna umesto apsolutne: *udeo neprovidnih piksela ne
sme da zavisi od veličine platna.* Sa namerno vraćenom starom rasterizacijom alat
prijavljuje svih 12 i vraća 1.

### „Izgubili smo kvalitet" je bila pretpostavka, pa je izmerena

ADR-038 je u prvoj verziji tvrdio da nanosvg daje lošiji izlaz od librsvg-a.
Provereno je poređenjem sa Wikimedia thumbnailom na 120 px — jedinoj standardnoj
veličini blizu naše, jer thumbnailer odbija 80 px:

| | piksela | različitih | prosek \|Δ\| |
|---|---|---|---|
| bela dama | 14 400 | 1 554 (10.8%) | 1.3 / 255 |
| beli skakač | 14 400 | 803 (5.6%) | 0.6 / 255 |

Oba broja stoje u ADR-u namerno: procenat izgleda veliko, a prosek pokazuje da je
razlika ispod praga vidljivosti i da leži isključivo na ivičnim pikselima. Jedina
uočena razlika ide **u našu korist** — librsvg ostavlja sivkastu mrlju na spoju
kuglice i kraka krune.

Ono što smo stvarno izgubili je drugo i zapisano je kao takvo: nanosvg ne poštuje
`viewBox`, i merenje važi za crtež sa konturama, ne za SVG sa gradijentima,
filterima i tekstom.

### `git add` je prijavio kvar koji se kod nas nikad ne bi pojavio

```
warning: in the working copy of 'assets/pieces/svg/wp.svg',
         LF will be replaced by CRLF the next time Git touches it
```

`core.autocrlf=true` znači da bi prvi `git clone` na Windows-u pretvorio SVG-ove u
CRLF i oborio svih 12 `sha1` vrednosti u `LICENSE.txt`. Blob u repozitorijumu
ostaje LF i kod nas se ništa ne vidi — kvar nastaje kod druge osobe.

Odbačeno je preformulisanje `LICENSE.txt`-a („sha1 važi za blob, ne za fajl"):
tvrdnja bi bila tačna, ali bi je proveravao samo onaj ko zna za `autocrlf` i ume da
izvuče blob kroz `git cat-file`. Proverljiva tvrdnja koju niko ne može lako da
proveri je za korak od tvrdnje kojoj se samo veruje.

### Čiji je dokument odlučuje šta u njega sme

`assets/pieces/LICENSE.txt` je **naš** tekst koji citira tuđu licencu, pa napomena o
`.gitattributes`-u tu pripada. `assets/fonts/LICENSE.txt` su napisali Bitstream i
Tavmjong Bah; naša rečenica umetnuta u njega putovala bi dalje kao deo uslova kod
svakoga ko ga prekopira. Zato verzija, arhiva i `sha256` idu u zaseban
`PROVENANCE.txt`, koji na jednoj rečenici objašnjava i zašto se ta dva fajla
različito tretiraju.

### Šta je `PROJECT.md` §12 tvrdio netačno

Dve stvari. Font je bio opisan kao „DejaVu Sans (slobodna licenca)" — a DejaVu nije
jedna licenca: osnovni fontovi su © Bitstream, izmene u javnom domenu, Arev glifovi
© Tavmjong Bah. I: §12 je nabrajao četiri ravnopravno ponuđene licence, a autor je
ponudio **tri** — CC BY-SA 3.0 je došla naknadno, migracijom GFDL licenci iz 2009.
Oba ispravljena istim commitom (ADR-030/032).

### Tri stvari koje su prošle a nisu trebale

Zapisano jer se ponavljalo:

1. **Rasterizacija** — dve samoprovere prošle nad odsečenim figurama.
2. **Test** — `test_every_svg_matches_its_recorded_sha1` bi prošao sa praznom
   petljom da regex prestane da hvata. Dodata tvrdnja da unosa ima 12 **pre**
   petlje; treći slučaj u dokazu pokazuje da bez nje test ćuti.
3. **Sam dokaz** — skripta koja kvari fajlove prikazala bi kao dokaz i izmenu koja
   ništa ne menja, ako obrazac prestane da se poklapa. Dodata tvrdnja da izmena
   stvarno menja bajtove, i da pada **imenovani** test, ne bilo koji.

Isti oblik greške tri puta u jednom tasku: provera koja može da prođe praznog hoda.

### Dokaz da `tests/test_assets.py` nije prazan

Pet namernih kvarova, jedan po jedan, svaki vraćen i proveren `sha1`-om:

| kvar | pao test |
|---|---|
| bajt u `svg/wq.svg` | `test_every_svg_matches_its_recorded_sha1` |
| uklonjen red za `svg/*.svg` iz `.gitattributes` | `..._carries_every_line_a_claim_depends_on` |
| `sha1` → `checksum` u `LICENSE.txt` | `test_license_documents_exactly_twelve_pieces` |
| bajt u `DejaVuSans.ttf` | `test_every_font_file_matches_its_recorded_sha256` |
| uklonjen red `*.ttf binary` | `..._carries_every_line_a_claim_depends_on` |

Svih pet oborilo je **očekivani** test; radno stablo posle ostalo čisto.

### Pitanja

**1. Provera rasterizacije živi u alatu, a provera `sha1` u testu — iako obe čuvaju
isti tuđi materijal. Šta odlučuje gde provera ide, i šta bi se izgubilo da su
zamenjene?**
Znao. Ne odlučuje kategorija „alat ili test", nego **trenutak u kom kvar nastaje i
šta se tada izvršava**. Rasterizacija može da se pokvari samo dok alat piše PNG, a
tada test suite ne radi. `autocrlf` udara pri `git clone` na drugoj mašini, gde alat
ne radi nikad — PNG-ovi su commitovani i niko nema razloga da ih regeneriše — ali
`pip install -e ".[dev]"` pa `unittest discover` je checkpoint faze 0, prva stvar
koju nova osoba uradi.

Zamenom bi `sha1` provera postala alat koji niko ne pokreće posle kloniranja: postoji
i nikad ne opali, isto što i `perft/SKILL.md` iz 0.2. Obrnuta zamena je suptilnija —
test bi gledao već commitovane, ispravne PNG-ove i prolazio zauvek, testirajući
artefakt koji se ne menja; u trenutku kad neko izmeni alat i pokrene ga, test se ne
izvršava.

> Odgovor je otišao dalje od pitanja, na razliku u **ceni**: alat vrati 1 i ne
> prikaže loš izlaz kao dobar, dok bi test to uhvatio tek posle — kad su loši fajlovi
> već u indeksu.

**2. Zašto rečenica o `.gitattributes`-u nije i u `assets/fonts/LICENSE.txt`, i zašto
`PROVENANCE.txt` namerno nema svoj red u `.gitattributes`?**
Znao, i preko onoga što je pitano. Odlučuje čiji je dokument: `pieces/LICENSE.txt` je
naš tekst koji citira tuđu licencu, `fonts/LICENSE.txt` su napisali Bitstream i
Tavmjong Bah, pa bi umetnuta rečenica putovala dalje kao deo uslova.

Jači razlog nije bio u pitanju: rečenica bi glasila „ovo je kopija bajt u bajt", a
upisati je u fajl znači učiniti je netačnom. **Tvrdnja bi sama sebe pojela** — isti
oblik kao primer iz 0.1 koji je `ruff` prepravio pa je progutao sopstvenu poentu.

`PROVENANCE.txt` nema red jer red postoji tamo gde **tačni bajtovi nose tvrdnju**; on
je naš, niko mu ne računa heš, nije kopija ničega, a `sha256` vrednosti u njemu
opisuju druge fajlove koji su već pokriveni. Uz to bi red koji ne štiti nijednu
tvrdnju učinio komentar u `.gitattributes`-u netačnim za sebe, „pa se ceo fajl počne
čitati kao spisak simpatija umesto kao spisak obaveza".

**3. Šta tvrdnja o udelu neprovidnih piksela meri što dimenzija i nepraznost ne mere,
i zašto su za nju bile potrebne dve veličine?**
Znao, i uopštio preko pitanja. Prve dve su **apsolutne osobine jedne slike** i
zadovoljava ih i pogrešna slika — odsečeni kralj je bio tačno 80×80 i nije bio
prazan. Treća je **relativna**: ako je crtež stvarno skaliran, udeo platna koji
zauzima je osobina crteža a ne platna, dakle isti u obe veličine. Kod dame je bio 49%
na 80 px i 91% na 32 px.

Dve veličine su potrebne jer sa jednom nema sa čim da se poredi: koliki udeo *treba*
da zauzima dama — 85%, 78%? To je osobina tuđeg crteža, ne nešto što alat može da
zna, a zakucan broj bi pucao čim se zameni set figura.

> Uopštenje koje nije bilo u pitanju: **provera nad jednim izlazom hvata samo ono što
> unapred umeš da iskažeš; provera koja poredi dva izlaza hvata nedoslednost, dakle i
> bagove koje nisi predvideo.** Ovaj bag niko nije predvideo.

---

## 0.5 — `sr.json`, `t()` i spona sa protokolom

Prvi task koji **veže dokument za test**. Do sada je `PROTOCOL.md` §5 nabrajao devet
`ERROR` kodova, a `CONVENTIONS.md` §7 tvrdio da svaki korisnički tekst ide kroz ključ —
ali nijedan od tih ključeva nije postojao. Pravilo je bilo obećanje.

| Šta | Gde |
|---|---|
| devet ključeva, UTF-8 bez BOM-a | `assets/i18n/sr.json` |
| `load()` i `t()`, samo stdlib | `src/chess/client/i18n.py` |
| 23 nova testa u tri grupe (A spona, B fajl, C ponašanje) | `tests/client/test_i18n.py` |
| pravilo izvođenja `message_key` + napomena da se prva kolona čita mašinski | `PROTOCOL.md` §5 |
| ADR-040 (ugovor `t()`), ADR-041 (zatvoren skup iz protokola), ispravka ADR-039 | `DECISIONS.md` |
| stablo `tests/`, putanja sa četiri `.parent`, ključevi, ugovor `t()`, ton | `CONVENTIONS.md` §5 i §7 |

### Granica koja nosi ceo ugovor

Ugovor se **ne** zove „`t()` ne baca". Zove se: `t()` ne baca **na loš podatak**.

Bez tog razlikovanja `RuntimeError` i `TypeError` u `t()` izgledaju kao rupa u pravilu.
Sa njim su njegova granica: loš podatak je sadržaj `sr.json`-a i ono što stiže sa mreže,
a pogrešan poziv je greška u našem kodu. Prvo se toleriše i prikazuje, drugo pada odmah.

Druga granica ide kroz `load()`: on je jedino mesto koje odbija glasno. Zato `load()` sme
`ValueError`, a `t()` posle njega ne sme ništa da baci na sadržaj.

WARNING je pri tom **drugi kanal pored simptoma na ekranu, nikad jedini** — zato tri reda
ugovora imaju log, a dva nemaju: kod njih na ekranu nema šta da se vidi.

### Dokaz da spona nije dekor — i bag koji je usput ispao

Suite je pokrenut **pre** nego što je napomena upisana u `PROTOCOL.md` §5. Očekivanje:
pada tačno `A5`. Palo je **četiri** testa, pa se stalo.

Uzrok nije bio u dokumentu nego u parseru: isečak teksta posle zaglavlja tabele počinje
prelaskom u nov red, pa prvi element `splitlines()` bude prazan string, ne počinje sa `|`,
i petlja pukne na `break` pre nego što vidi ijedan red. Parser je **oslepeo i vratio nula
kodova**.

Ono što je važno: nije prošao praznog hoda. Oborila ga je tvrdnja o broju kodova koja
stoji **pre** petlje — ista zaštita zbog koje je u 0.4 dodata tvrdnja „unosa ima 12".
Posle ispravke (`lstrip`) padao je tačno `A5`, i to je dokaz koji se tražio: **imenovan
test pada iz imenovanog razloga.** Sa napomenom u §5: 44 testa, `OK`.

### Pet namernih kvarova

Svaki uveden posebno, pa vraćen sa `git checkout -- <fajl>` i proveren praznim
`git diff -- <fajl>`. Pre svega toga `git add -A`, jer bez indeksa `checkout` nad
`PROTOCOL.md` vraća na HEAD i **tiho briše** napomenu iz koraka 5.

| kvar | pali testovi | predviđeno? |
|---|---|---|
| a) uklonjen red `NOT_IN_GAME` iz tabele kodova | `A2`, `A3`, `A4` | plan je predviđao `A2` i `A4` |
| b) BOM na početku `sr.json` | **FAIL** `B6`; **ERROR** `A3`, `A4`, `B7`–`B11` | da |
| c) deseti red koji ponavlja postojeći ključ istom vrednošću | `B7` | da |
| d) ispražnjena vrednost za `error.move_pending` | `B9` | da |
| e) U+0161 zamenjeno sa U+00C4 | `B11` (`code_point='U+00C4'`) | da |

Tri stvari koje ova tabela kaže, a plan nije predvideo:

1. **Zašto je (a) oborio i `A3`.** Ne na nedostajućem ključu — njegova petlja preko
   preostalih osam kodova bi prošla — nego na **straži od prazne petlje**
   (`8 != 9`, linija 167). Straža je dodata u poslednjem krugu pregleda plana, dakle
   posle predviđanja. Predviđanje je bilo tačno za test kakav je tada bio.
2. **Kod (b) izolacija nije dostižna i ne glumi se.** Ali razlika u vrsti pada nosi
   informaciju: `B6` je **FAIL** — tvrdnja je proverena i netačna; ostalih sedam su
   **ERROR** — `json.loads` je pukao pre ijedne tvrdnje. `B6` gleda bajtove baš zato da
   ne deli sudbinu sa dekodiranjem.
3. **Kod (e) `B10` i dalje prolazi.** Ostale vrednosti imaju dijakritik. To je i poenta:
   `B10` hvata **izostanak** dijakritika, `B11` **pokvaren** dijakritik. Dva kvara; prvi
   ne pokriva drugi.

### Escape sekvenca koja se pretvorila u sam znak

Nalaz iz alata, ne iz koda. Escape sekvenca za U+FEFF, napisana u izvornom kodu, stigla je
na disk kao **doslovna tri bajta `EF BB BF`** — alat za pisanje fajlova je dekodirao
sopstveni ulaz:

```
0000000   A       =       " 357 273 277   "  \n      <- napisano kao escape, upisano kao znak
0000020   B       =       c   h   r   (   0   x   F   E   F   F   )  \n
```

Provera BOM-a bi tako postala poređenje sa nevidljivim znakom — a to je tačno kvar od kog
štiti. Zato u kodu stoji `_BOM = chr(0xFEFF)`: imenuje kodnu tačku, a ne može da se tiho
pretvori ni u šta. Iz istog razloga su i bela lista u `B11` i skup u `B10` sagrađeni iz
kodnih tačaka, pa su **oba `.py` fajla čist ASCII** — provereno nad bajtovima.

> Opšte pravilo koje iz ovoga sledi: **provera ne sme da deli sudbinu sa kvarom od kog
> štiti.** Isti oblik kao `B6` nad bajtovima umesto nad tekstom.
>
> Isto važi i za ovaj odeljak: on kvar opisuje, pa ga ne sme sadržati. Zato se ovde nigde
> ne piše ni sam znak ni escape za njega, a ceo fajl se posle upisa proverava nad
> bajtovima.

Poruke o padu iz istog razloga imenuju znak kodnom tačkom i nikad ga ne ispisuju. Nije
teorijski: konzola je tokom rada stvarno pukla na `đ`
(`UnicodeEncodeError: 'charmap' codec can't encode character` U+0111) — cp1252, tačno
ono što `CONVENTIONS.md` §7 opisuje.

### `sr.json` i `.gitattributes` — izmereno, pa zapisano

`git checkout --` je uz `core.autocrlf=true` vratio `sr.json` na disk **sa CRLF-om**
(697 bajtova umesto 686), dok blob ostaje LF i `git diff` je prazan. Svih 44 testa i dalje
prolazi.

To je odgovor na pitanje zašto `sr.json` **nema** red u `.gitattributes`: red postoji tamo
gde **tačni bajtovi nose tvrdnju**, a nijedna tvrdnja ne zavisi od njegovih. Isti kriterijum
po kom reda nema ni `PROVENANCE.txt` (0.4, pitanje 2). ADR-039 je zato ispravljen — on je
`sr.json` navodio kao sledeći slučaj pravila „tuđi materijal se čuva bajt u bajt", a
`sr.json` je **naš** fajl. Pogrešan primer, ne promena odluke.

### Ispravka koja neće ostaviti trag u commitu

Zaostala ispravka br. 1 iz 0.4 — red `python tools/rasterize_pieces.py` u sekciji Komande
— upisana je u `CLAUDE.md`, a taj fajl je u `.gitignore` (ADR-012). `ROADMAP.md` je
označava kao urađenu i **ništa u repozitorijumu to ne dokazuje**: ko sutra klonira repo
vidi tvrdnju bez ijednog dokaza.

Zapisano je ovde jer je `faza-0.md` jedino mesto u gitu koje o toj izmeni može da
posvedoči. Prećutati je značilo bi ostaviti štikliranu stavku bez pokrića.

### Jedna stavka je stigla ranije nego što je tabela predviđala

Tabela za preseljenje u §0.2 dobila je red *„Notacija se ne prevodi"* — stavku koju je
sama tabela izgubila kad je pisana. Bila je predviđena za **3.7**, ali je stigla odmah:
§7 se u ovom tasku ionako prepisivao, pa bi ostaviti je u `.claude/` značilo namerno
ostaviti pravilo u fajlu bez autoriteta. Zavedena je i odmah označena kao preseljena, da
tabela opisuje stvarno stanje a ne nameru.

### Pitanja

**1. `load()` na kraju prazni skup već prijavljenih ključeva. Da je neko taj skup vezao za
modul umesto za katalog, koji jedini test bi to prijavio i zašto bi svi ostali prolazili?**
Znao, i preko onoga što je pitano. Prijavio bi ga **`C21`**, i to je jedini.

Razlog je u tome što `setUp` grupe C radi `importlib.reload`, pa svaki test počinje sa
potpuno praznim stanjem modula. Dok test uradi samo jedan `load()`, skup vezan za modul i
skup vezan za katalog ponašaju se **identično** — u oba slučaja je prazan na početku i prvi
nepostojeći ključ se prijavi. Tako prolaze `C13`, `C15`, `C16`, `C22` i `C23`.

`C20` ni ne pomaže: on zove `t()` dvaput sa istim ključem, ali između ta dva poziva nema
`load()`-a, pa tačno jedno upozorenje dobija u oba slučaja.

`C21` je jedini koji radi `load()` → `t(nepostojeći)` → `load()` ponovo → `t(isti ključ)`.
Ako skup pripada modulu i `load()` ga ne dira, ključ je već u njemu, drugo upozorenje se ne
javi, i `assertLogs` pukne jer nijedan zapis nije nastao.

To je i poenta: odluka „nema `reset_for_tests()`, skup pripada katalogu" bez `C21` ne bi
bila proverena nijednom tvrdnjom.

**2. `t()` proverava tip parametara pre nego što potraži ključ. Zašto taj redosled, kad bi
provera posle traženja uštedela posao kad ključ ne postoji?**
Znao, i preko onoga što je pitano. Zato što bi obrnut redosled dopustio da **greška u
podacima sakrije grešku u kodu**.

Poziv `t("menu.play", {"n": 1.0})` sa ključem koji ne postoji: da provera tipa ide posle
traženja, funkcija bi vratila sam ključ, upisala upozorenje o nedostajućem ključu i nikad ne
bi prijavila `TypeError`. Broj umesto stringa bi ostao neprimećen — a to je tačno onaj kvar
koji se u fazi 4 pojavljuje tiho.

Gore od toga: isto pozivno mesto bi bacalo ili ne bacalo u zavisnosti od toga da li
`sr.json` slučajno ima taj ključ. **Greška u našem kodu ne sme da zavisi od sadržaja fajla**
— mora da pukne deterministički, uvek isto.

Ušteda o kojoj je reč je jedno pretraživanje rečnika sa devet unosa. To nije cena vredna
pomena naspram progutane greške.

**3. BOM se odbija na dva mesta, ali `B6` gleda bajtove a `load()` tekst. Zašto ta razlika
nije nemar nego uslov da druga provera nešto znači?**
Znao. Zato što bi test koji čita fajl na isti način kao `load()` prolazio kroz **ista vrata
kao bag**, pa bi ponavljao `load()`-ovu pretpostavku umesto da je proverava.

`load()` radi `read_text(encoding="utf-8")` — dakle već je dekodirao pre nego što išta
tvrdi. Ako dekodiranje pukne ili uradi nešto neočekivano, njegova provera se nikad ne izvrši
i izuzetak dođe sa drugog mesta. Test koji ide istim putem tada testira dekoder, ne fajl.

`B6` otvara sirove bajtove i poredi prva tri sa `EF BB BF`. Njegova tvrdnja ne zavisi od
toga da li je dekodiranje uopšte uspelo. Zato dve provere padaju nezavisno: `load()` čuva
svaki fajl na koji pokaže u vreme izvršavanja, uključujući one koje test u fazi 4 neće
videti, a `B6` čuva fajl u repozitorijumu bez obzira šta dekoder radi.

> Opšte pravilo izvedeno u ovom tasku, i uz `chr(0xFEFF)` drugi njegov slučaj:
> **provera ne sme da deli sudbinu sa kvarom od kog štiti.** Da obe idu kroz dekoder, jedan
> pokvaren dekoder bi ućutkao obe odjednom.

---

## 0.6 — `LICENSE`, `THIRD-PARTY.txt` i SPDX oznaka u metapodacima

Prvi task u kom je **plan bio glavni predmet rada, a ne kod**. Fajlovi koji iz njega
izlaze su kratki: jedna licenca preuzeta gotova, jedan dokument uz nju, tri reda u
`pyproject.toml`. Ono što je trajalo je pitanje šta tačno tvrdimo i čime to dokazujemo —
i tri puta se pokazalo da je prva formulacija bila uža ili šira od istine.

| Šta | Gde |
|---|---|
| uslovi za naš kod, BSD-3-Clause, kanonski SPDX tekst | `LICENSE` |
| obim: šta LICENSE ne pokriva, plus blok koji čita test | `THIRD-PARTY.txt` |
| `license = "BSD-3-Clause"`, `license-files`, `setuptools>=77` | `pyproject.toml` |
| 9 novih tvrdnji u pet klasa | `tests/test_assets.py` |
| ADR-042 (uslovi naspram obima), ADR-043 (metapodaci), ⚠️ na ADR-039 | `DECISIONS.md` |
| §12 dobija pododeljak o našem kodu; §5 stablo dobija dva fajla | `PROJECT.md` |
| §5 stablo `tests/` i pravilo izolacije; §10 o `build-system.requires` | `CONVENTIONS.md` |
| unos „SPDX oznaka" | `POJMOVNIK.md` |

### Kopija u repou nije bila kanonski tekst

Plan je rekao dve stvari koje su izgledale kao jedna: *telo je kanonski SPDX tekst* i
*uzmi telo iz repozitorijuma, ne iz sećanja*. `assets/pieces/LICENSE.txt` već sadrži
BSD-3, pa se činilo da je izvor tu.

Merenje je to oborilo. Poređene su **reči**, sve beline sažete, pa prelom ne pravi lažne
razlike. Pet mesta:

| | SPDX kanonski | `assets/pieces/LICENSE.txt` |
|---|---|---|
| red o pravima | `Copyright (c) <year> <owner>. ` | `Copyright (c) 2006 Cburnett` |
| oznake klauzula | `1.` `2.` `3.` | `  * ` |
| klauzula 3 | `the copyright holder` | `Cburnett` |
| odricanje, 1. rečenica | `THE COPYRIGHT HOLDERS AND CONTRIBUTORS` | `... HOLDER AND ...` |
| odricanje, 2. rečenica | `THE COPYRIGHT HOLDER OR CONTRIBUTORS` | `... HOLDER AND ...` |

Prva tri su bila očekivana — nosilac je drugi. **Poslednja dva nisu.** Da je telo uzeto
iz repoa, naš `LICENSE` bi nasledio varijantu odricanja koju taj isti fajl u svom
objašnjenju naziva kanonskom, a koja to nije. Kvar se ne bi video ni na jednom gate-u:
`ruff`, `unittest` i `layer_check` prolaze nad savršeno pogrešnom licencom (isto kao u
0.4).

Telo je zato preuzeto sa SPDX-a, 1460 bajtova, `sha256 5a93d583…`, i heš je zapisan u
ADR-042 — isti oblik kao `sha256` arhive u `PROVENANCE.txt`.

Nalaz o `assets/pieces/LICENSE.txt` **nije ispravljen u ovom tasku**, po odluci: fajl je
naš tekst o tuđoj licenci, ispravka traži svoj plan, a commit treba da ostane o jednoj
stvari. Zaveden je uz 0.7 u `ROADMAP.md`.

### Prelom se dokazuje, ne tvrdi

`licensee`, detektor koji GitHub koristi, normalizuje beline — pa prelamanje na 75
kolona ne dira poklapanje. Ali „to je samo prelom" je tvrdnja kao svaka druga i traži
dokaz:

```
reci kanonski    : 216
reci prelomljeno : 216
razlika          : PRAZNA
a == b           : True
redova koji se zavrsavaju crticom: 0
```

Usput je pao i razlog zbog kog je provera crtica tražena: `textwrap` podrazumevano lomi
na crtici, ali **u celom kanonskom telu nema nijedne crtice** (`canon.count('-')` → `0`).
U klauzuli 2 je kosa crta, `and/or`, na koju `break_on_hyphens` ne deluje. Tvrdnja
stoji, iz drugog razloga nego što je pretpostavljeno.

Prva verzija je imala i uvlačenje nastavaka klauzula na tri razmaka. Uveo ga je
`subsequent_indent` u skripti, nije bilo odlučeno — a nema ga ni kanonski tekst ni kopija
u repou. Uklonjeno: dva različita izgleda iste licence u istom repozitorijumu, bez dobiti.

### Pravilo koje je bilo uže od istine — uhvaćeno u pregledu plana

Prva verzija tačke 3 čitala je red `SPDX-License-Identifier:` izrazom sa `re.MULTILINE`
nad celim tekstom `THIRD-PARTY.txt`-a, usidrenim sa `[ \t]*$`.

`\r` nije ni razmak ni tab. `THIRD-PARTY.txt` namerno nema red u `.gitattributes`, pa uz
`core.autocrlf=true` prvi `git clone` na Windows-u daje CRLF — izraz prestaje da pogađa,
tvrdnja o SPDX oznaci tiho pada, i to **kod druge osobe, nikad kod nas**. Isti kvar kao
`autocrlf` nad `sha1` vrednostima u 0.4, jednu tvrdnju dalje.

Uzrok nije bio previd nego **preusko formulisano pravilo**: L10 u planu je govorio o
„parseru bloka", a čitalac je bio drugi. Ispravka je zato dvostruka — fajl se čita jednom
kroz `read_bytes()` → `decode()` → `splitlines()` i **oba** čitaoca rade nad tom listom
redova, a u ADR-042 pravilo je izrečeno za **svakog** čitaoca tog fajla, ne za parser.

Izmereno posle svega, da ne ostane argument:

```
LICENSE           1493 B   CR=27   LF=27   CRLF=27      (upisan kao 1466 B, LF)
THIRD-PARTY.txt   4326 B   CR=95   LF=95   CRLF=95      (upisan kao 4231 B, LF)
core.autocrlf     true
ijedan red posle splitlines() sadrzi CR?  False
53 testa                                  OK
```

Fajlovi na disku **jesu** CRLF u ovom trenutku, `git diff` je prazan, i suite prolazi.

### Isti defekt, tri puta, na tri mesta

Ista greška se u ovom tasku ponovila u tri oblika i sva tri puta glasi: **čitalac bez
tvrdnje ispred sebe pada bez dijagnoze.**

1. `PackageMetadataTest` je čitao `THIRD-PARTY.txt` bez ijedne prethodne tvrdnje, dok je
   `ThirdPartyManifestTest` imao `setUp` sa imenovanom porukom. Isti fajl, dva čitaoca,
   dve sudbine — `FileNotFoundError` (ERROR, bez rečenice) naspram FAIL sa rečenicom.
   Nađeno u pregledu, pre pokretanja.
2. `RootLicenseTest` je imao **isti** defekt unutar sebe: jedan test je tvrdio
   `is_file()`, drugi nije. Nađeno tek pokretanjem — prvo pokretanje dalo je 6 FAIL i
   **1 ERROR**, i taj jedan ERROR je bio to.
3. Straža od `None` u sva četiri testa `ThirdPartyManifestTest`-a postoji iz istog
   razloga: bez nje bi `sorted(None)` pukao `TypeError`-om.

Treći slučaj je i razlog zašto tabela kvarova ispod ne pogađa brojeve.

### Šest namernih kvarova

Pre svega `git add -A`, jer su `LICENSE` i `THIRD-PARTY.txt` novi fajlovi pa bez indeksa
`git checkout --` nad njima ne radi uopšte, a nad `pyproject.toml` bi vratio na HEAD i
**tiho obrisao** izmenu iz koraka 6. Pouka iz 0.5, primenjena bez ponavljanja greške.
Svaki kvar uveden posebno, vraćen, i provereno praznim `git diff -- <fajl>`.

| kvar | pali testovi | poruka | predviđeno? |
|---|---|---|---|
| a) uklonjen `assets/fonts` iz bloka | `test_block_and_disk_agree_...` | `['assets/pieces'] != ['assets/fonts', 'assets/pieces']` | **da**, tačno |
| b) dodat `assets/sounds`, ne postoji | `test_block_and_disk_agree_...`, `test_every_documented_directory_...` uz `path='assets/sounds'` | oba smera | **da** |
| c) `LICENSE:` → `LICENCE:` u zaglavlju | **sva četiri** iz `ThirdPartyManifestTest` | **„header not found"** u sva četiri | **ne** — plan je rekao jedan |
| d) putanje obrisane, zaglavlje ostaje | `test_block_lists_at_least_one_directory`, `test_block_and_disk_agree_...`; `test_block_header_is_still_there` **prolazi** | **„zero paths"** | **ne** — plan je rekao jedan |
| e) `C4 87` → `63` u `LICENSE` | `test_license_carries_the_copyright_line_it_must_retain` | imenuje `U+0107`, ne ispisuje ga | **da**, tačno |
| f) `license = "MIT"` | `test_pyproject_and_third_party_state_the_same_license` | `'MIT' != 'BSD-3-Clause'` + rečenica | **da**, tačno |

Tri stvari koje ova tabela kaže, a plan nije predvideo:

1. **Kod (c) i (d) promašen je broj, ne dijagnoza.** Sva četiri testa kod (c) padaju sa
   istom, tačnom porukom „header not found"; kod (d) padaju dva, jedan sa „zero paths" a
   drugi zato što prazan blok mora da se razlikuje od diska. Uzrok je straža od `None`,
   koja je u sva četiri testa ušla **posle** nego što je tabela napisana — isti oblik kao
   pad `A3` u 0.5. Predviđanje je bilo tačno za test kakav je tada bio.
2. **Par (c)/(d) je jedini dokaz da `None` naspram `[]` nešto znači.**
   `test_block_header_is_still_there` kod (c) **pada**, kod (d) **prolazi**. Da parser u
   oba slučaja vraća `[]`, ta dva kvara bi se na izlazu videla identično — a jedan je kvar
   u oblikovanju, drugi u sadržaju.
3. **Kod (e) poruka je prošla svoj sopstveni test.** Ispisuje `b'...\xc4\x87'` i reč
   `U+0107`, nigde sam znak. Nije akademski: konzola je i u ovom tasku pukla, na `đ`
   (`UnicodeEncodeError: 'charmap' codec can't encode character` U+0111), pri običnom
   čitanju `DECISIONS.md`-a.

### Izmereno, a ne pretpostavljeno

**Wheel, pre i posle.** Premisa da `assets/` ne ulazi u paket nije pročitana iz
`pyproject.toml`-a nego izmerena nad izgrađenim wheel-om:

| | pre | posle |
|---|---|---|
| veličina | 5724 B | 6756 B |
| polja o licenci u `METADATA` | **nijedno** | `License-Expression: BSD-3-Clause`, `License-File: LICENSE` |
| `.dist-info/licenses/LICENSE` | ne postoji | postoji, sa `\xc4\x87` netaknutim |
| `assets/` u wheel-u | nema | nema |

**Nezavisna provera bajtova `LICENSE`-a — korak 7 plana, izvršen na drugom mestu.**
Plan ga je vodio kao zaseban korak posle instalacije; izvršen je odmah po upisu fajla, u
koraku 4, nad istim bajtovima i sa istim ishodom: `C4 87` na pozicijama 34–35, **jedina
dva ne-ASCII bajta u celom fajlu**, uz završni `\n`, bez BOM-a i bez ijednog zaostalog
razmaka. Zapisano ovde da se spisak koraka iz plana i ovaj zapis ne raziđu — merenje
postoji, samo ne tamo gde ga je plan najavio.

**`setuptools` 76 naspram 77.** Granica nije citirana nego proverena: 76.1.0 odbija
`license` kao string `ValueError`-om, 77 je prvo izdanje koje ga prihvata. Uz to je
izmereno da pip u izolovano build okruženje **već povlači 84.0.0**, i pre naše izmene —
pa `>=77` ne menja šta se povlači nego šta je dozvoljeno.

**Predviđen otkaz koji se nije ostvario.** SPDX oblik tera `Metadata-Version: 2.4`, a u
venv-u je `pip 24.0`; plan je predvideo mogućnost pada i tačku zaustavljanja. Instalacija
je prošla bez greške. Zapisano zato što je bilo otvoreno pitanje, ne da bi ličilo na
savladan rizik.

**Merilo koje je bilo pogrešno postavljeno.** Kontekst plana je rekao da `pip show chess`
danas ispisuje prazno `License:`. Posle taska ispisuje — **i dalje prazno**, i to je
ispravno: po PEP 639 se `License` i `License-Expression` isključuju, a `pip 24.0` u `show`
čita samo staro polje. Tvrdnja je bila tačna kao opis simptoma i pogrešna kao merilo
uspeha. Merilo je `License-Expression` u `METADATA`.

### Pitanja

**1. `assets/fonts/LICENSE.txt` ima red u `.gitattributes`, a `LICENSE` i `THIRD-PARTY.txt`
ga nemaju — iako test nad sva tri proverava bajtove. Koji je kriterijum, i zašto bi red za
`LICENSE` učinio komentar na vrhu `.gitattributes`-a netačnim za sebe?**
Znao, i preko onoga što je pitano. Kriterijum nije „test čita bajtove" nego **da li tvrdnja
zavisi od prelazaka reda** — jedino što `-text` štiti, jer `autocrlf` pretvara `\n` u `\r\n`
i ne dira nijedan drugi bajt.

`assets/fonts/LICENSE.txt` je kopija tuđeg fajla bajt u bajt i `PROVENANCE.txt` uz njega
vodi `sha256`; heš se računa nad celim sadržajem, pa jedan `\r` više obara tvrdnju. Isto
važi za `sha1` SVG originala. `LICENSE` i `THIRD-PARTY.txt` su naši i nijedan heš ih ne
pokriva: tvrdnja o prvom traži `C4 87` kao **podniz** bajtova, koji CRLF ne dira, a tvrdnje
o drugom idu kroz `splitlines()`, koji `\r\n` tretira isto kao `\n` i ne ostavlja ni jedno.
Izmereno: posle `git checkout` oba su na disku CRLF (`LICENSE` 1493 B umesto 1466) i svih
53 testa prolazi.

> Odgovor je otišao dalje od pitanja, na **samoreferentnost**: komentar na vrhu
> `.gitattributes`-a kaže da su redovi tu zbog tuđeg materijala koji se čuva bajt u bajt.
> `LICENSE` nije tuđ, **ne** čuva se bajt u bajt — prelomljen je na 75 kolona — i nijedan
> heš ga ne pokriva. Red bi stajao u fajlu koji o sebi tvrdi nešto što za tu stavku ne važi.
> Isti oblik kao rečenica koja bi samu sebe pojela iz 0.4, pitanje 2.

**2. Tvrdnja o redu sa autorskim pravima traži taj red kao podniz bajtova, ne kao ceo red i
ne nad dekodiranim tekstom. Koja dva režima otkaza se time izbegavaju odjednom?**
Znao, oba, sa konkretnim ishodom za svaki.

**Prelazak reda.** Poređenje celog reda na CRLF disku dalo bi
`'Copyright (c) 2026 Stefan Obradović\r'`, što nije jednako očekivanom — i palo bi tek kod
druge osobe posle `git clone`, nikad kod nas. Podniz ne sadrži prelazak reda, pa ga
`autocrlf` ne može dohvatiti.

**Dekodiranje.** Provera nad dekodiranim tekstom pretpostavlja da je dekodiranje uspelo.
BOM ili presnimavanje u cp1252 daju `UnicodeDecodeError` iz `read_text` — dakle **ERROR
umesto FAIL**, bez ijedne rečenice o uzroku, i to baš u slučaju koji provera treba da
imenuje. Nad sirovim bajtovima nema dekodera koji može da otkaže. Isti razlog zbog kog
`_BOM` gleda prva tri bajta a ne dekodirani znak, i isti kao kod `B6` u 0.5.

**3. SPDX oznaka stoji na tri mesta. Treći primerak košta još jedan noseći red. Šta
omogućava što prva dva sama ne mogu?**
Znao, i odgovor je otišao dalje od pitanja — na ono što lanac **ne** pokriva.

Prva dva se ne mogu porediti međusobno: `LICENSE` nosi **tekst**, ne oznaku — reč
`BSD-3-Clause` u njemu ne postoji — a `pyproject.toml` nosi oznaku bez ičega da je poredi
sa. Da neko sutra upiše `license = "MIT"`, ništa ne bi puklo, jer bi to bila jedina mašinski
čitljiva tvrdnja o licenci u repozitorijumu. Red `SPDX-License-Identifier:` u
`THIRD-PARTY.txt` daje **drugi nezavisan zapis iste tvrdnje**, pa test poredi dva umesto da
veruje jednom. Kvar (f) je to i dokazao.

> Nalaz koji nije bio u pitanju i koji je zbog toga ušao u ADR-042 kao izgubljeno:
> **lanac vezuje oznaku sa oznakom, nikad oznaku sa tekstom.** Nijedan test ne tvrdi da telo
> u `LICENSE`-u jeste BSD-3-Clause a ne neka druga licenca; poreklo tog tela čuva `sha256`
> zapisan u ADR-042, ali to je **zapis, ne provera**. Ko sutra zameni telo `LICENSE`-a
> tekstom MIT licence i ostavi red o autorskim pravima, prolazi kroz svih devet tvrdnji.
> Isti oblik kao granica iz ADR-041: test tvrdi da ključ postoji, nikad da je prevod tačan.
