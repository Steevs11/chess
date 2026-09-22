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
| ~~Kiwipete FEN + brojevi~~ | `skills/perft/SKILL.md` | **obrisani u 0.7, ne preseljeni.** U fajlu su stajali d1–d4, ne d1–d3 kako je ovaj red tvrdio. Prepisuju se sa Chess Programming Wiki u **1.3**, direktno u `tests/core/test_perft.py` uz komentar o izvoru — **nikad iz ovog fajla** |
| tabela simptom→uzrok | `skills/perft/SKILL.md` | **1.3** → docstring `tools/perft.py` |
| ✅ „`b1`/`b8` mora biti prazno, ali sme biti napadnuto" | `skills/chess-rules/SKILL.md` | **preseljeno u 0.7** → `PROJECT.md` §7 (stiglo ranije od predviđenog 1.4) |

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

---

## 0.7 — `.claude/` se svodi na pokazivače

### Šta je urađeno

Šest fajlova van gita svedeno je na adresu i okidač: gde piše pravilo i kada da se otvori.
Kriterijum je ADR-044 — rečenica sme da ostane van gita samo ako je **nijedna izmena u
`docs/` ne može učiniti netačnom** — a jedinica provere je **rečenica, ne fajl**.

**Ovaj task nema `git diff` za svoj glavni proizvod.** `.claude/` je u `.gitignore`, pa
izmena šest fajlova nigde ne ostavlja trag. Zato je tabela uklonjenih rečenica ispod jedini
dokaz u gitu da je posao urađen, i zato je red po **rečenici**, a ne po fajlu.

### Inventar

| | Redova | Bajtova |
|---|---|---|
| pre | 380 | 13.996 |
| posle | 152 | 5.823 |
| razlika | **−228 (−60 %)** | **−8.173 (−58 %)** |

Mereno sa `find .claude -type f` i `wc -lc`, bez `settings.json` — on se u ovom tasku nije
dirao. Sa njim: 423 → 195 redova.

### Tabela uklonjenih rečenica

**`rules/core-purity.md`** (44 → 17)

| Tvrdnja | Kuda |
|---|---|
| `core/` mora da radi neizmenjen u vebu i botu | PROJECT §6; CONVENTIONS §2, posledica 1 |
| nikad `pygame`, `socket`, `sqlite3` | §2, red `core/*` |
| `print()` i bilo kakav I/O | §7 „Logovanje" |
| import iz `protocol/`, `server/`, `client/` | §2 |
| `frozen=True, slots=True` za vrednosne objekte | §4 „Dataclass-ovi" |
| `Square` nije dataclass, alias `= int`, 0–63 | §4 „Tipovi" (ADR-013, ADR-031) |
| `Board` je mutabilan | §4 (ADR-006) |
| type hints na svakoj javnoj funkciji | §4 „Tipovi" |
| koordinate kroz `Square`, nikad pikseli | §2, posledica 2 |
| make/unmake, nikad kopiranje table | §4 (ADR-006); ROADMAP 1.2 |
| globalne promenljive i singletoni | **§4 „Bez stanja i bez hijerarhije" — napisano u ovom tasku** |
| komanda ≠ upit | **§4 — napisano u ovom tasku** |
| `Enum` za `Color` i `PieceType` | **§4 — napisano u ovom tasku** |
| figura je podatak, ne `class Pawn(Piece)` | **§4 — napisano u ovom tasku** |
| „`tests/core/**` sme da uvozi **sve**" | **obrisano — netačno.** §2 bira red po `*/__init__.py`, pa `tests/core/__init__.py` sme samo stdlib (ADR-037.3) |

**`rules/client-boundaries.md`** (40 → 28)

| Tvrdnja | Kuda |
|---|---|
| klijent postoji da crta i hvata unos | §3 |
| tabela fajlova „sme pygame?" | §2 |
| `net.py`/`state.py` se u fazi 4 prevode 1:1 | §2, posledica 3 (ADR-004) |
| nijedno šahovsko pravilo u klijentu | §3 (ADR-024) |
| `Rect`/`Surface` van `render.py` i `scenes/` | §2, posledica 2 |
| pikseli kao izvor istine | §2, posledica 2 |
| odbrojavanje sata kao izvor istine | §3, red „`clocks` iz `STATE`" |
| tekst za korisnika napisan u kodu | §7 |
| `MenuScene`, `GameScene` od prvog dana | ROADMAP 3.1 |
| socket u svojoj niti | **ostaje** — dom stiže u 3.2 |
| `BotScene` mora biti nov fajl | **ostaje** — dom stiže u 6.7 |

**`rules/i18n.md`** (49 → 19)

| Tvrdnja | Kuda |
|---|---|
| nijedan tekst za korisnika u kodu, uvek ključ | §7 „Font i tekst" |
| `sr.json`, JSON zbog oba jezika | §7; fajl postoji od 0.5 |
| konvencija ključeva `oblast.stvar` | §7 „Ključevi" *(preseljeno u 0.5)* |
| notacija se ne prevodi | §7 *(preseljeno u 0.5)* |
| logovi na engleskom, bez dijakritika | §7 „Logovanje" (ADR-010) |
| protokol šalje `message_key` | PROTOCOL §5 |
| font mora da nosi č ć š ž đ | §7 „Font i tekst" |
| „`t()` vraća ključ **umesto da baci izuzetak**" | **obrisano — protivreči ADR-040.** Ugovor glasi „ne baca **na loš podatak**"; `RuntimeError` i `TypeError` postoje |

**`skills/chess-rules/SKILL.md`** (118 → 28)

| Tvrdnja | Kuda |
|---|---|
| pet uslova rokade · en passant „samo odmah" · podpromocija · mat i pat · tabela remija · profili `online`/`fide` · pad zastavice i izuzetak materijala · `time.monotonic()` · poeni figura | PROJECT §7 — duplikat od ranije |
| „Test pozicije vredne pamćenja" | ADR-026 — duplikat |
| `b1`/`b8` sme biti napadnuto | **PROJECT §7 „Rokada" — napisano u ovom tasku** |
| pešak na 5. odnosno 4. redu kod en passanta | **PROJECT §7 „En passant" — u ovom tasku** |
| četiri poteza po promociji | **PROJECT §7 „Promocija" — u ovom tasku** |
| šest polja FEN-a, polje 5 je brojač polupoteza | **PROJECT §7 „Notacija" — u ovom tasku** |
| red SAN disambiguacije: kolona → red → oba | **PROJECT §7 „Notacija" — u ovom tasku** |

**`skills/layer-check/SKILL.md`** (37 → 19)

| Tvrdnja | Kuda |
|---|---|
| alat parsira uvoze kroz `ast` i prijavljuje kršenja | §2 „Provera" |
| nepokriven fajl je nalaz, ne izuzetak (ADR-037.2) | §2 „Provera" |
| u sukobu alata i tabele važi tabela | §2 „Provera", §1 |
| komanda `python tools/layer_check.py` | §2 „Provera" — komanda je tvrdnja o projektu |
| „section 2" u `description` | **obrisan broj odeljka** — eager polje ne sme da nosi broj koji se pomera |

**`skills/perft/SKILL.md`** (92 → 41)

| Tvrdnja | Kuda |
|---|---|
| početna d1–d5, Kiwipete d1–d4, Kiwipete FEN | **obrisano, ne preseljeno.** Prepisuje se sa Chess Programming Wiki u 1.3, direktno u test |
| tabela skupova i dubina, Position 3/4/5 | ADR-026 — duplikat |
| „perft mora biti brz" | ADR-026 |
| „nikad ne menjaj očekivanu vrednost" | PROJECT §8; WORKFLOW |
| komande za pokretanje | CONVENTIONS §5 i §10 |
| tabela simptom→uzrok | **ostaje** — dom stiže u 1.3, docstring `tools/perft.py` |

**`CLAUDE.md`** — tabela git dozvola obrisana, ne premeštena: kolona „Uz odobrenje" je
nosila `reset --hard`, `rebase` i `clean -fd`, a `settings.json` ih drži u `deny`, pa se to
odobrenje nije moglo ni ponuditi. Ostala je jedna rečenica: zabrane su u CONVENTIONS §8,
dozvole izvršiocu u `settings.json`.

### Devet tvrdnji je prvo dobilo dom, pa je tek onda brisano

Pet u `PROJECT.md` §7, četiri u `CONVENTIONS.md` §4. Četiri iz §4 nisu bile u planu:
grep nad `docs/` je pokazao **nula** pogodaka za `singleton`, `globaln` i `upit`, a
PROJECT §6 ima sedam pravila nadogradivosti i nijedno od ta četiri. Živele su samo u
`CLAUDE.md`, koji je takođe van gita — dakle brisanje bez pisanja bi ih izgubilo.

### `checkout --` je izmeren, pa tek onda zapisan

Plan je tvrdio: fajl koji u indeksu nema unosa se vraća sa HEAD-a i time se briše izmena
tekućeg taska. Mereno u praznom repou, tačno je **obrnuto**:

| Stanje fajla | Šta se desi |
|---|---|
| nema unos u indeksu | **odbija se**: `did not match any file(s) known to git`, izlaz `1`, fajl netaknut |
| praćen, izmenjen, nije `add`-ovan | tiho vrati HEAD verziju, izlaz `0`, bez upozorenja |
| praćen, `add`-ovan pa izmenjen | vrati `add`-ovano stanje |

Opasan je srednji red, ne prvi: nov fajl git štiti greškom, a fajl koji je pre taska
postojao odlazi u tišini. Pouka o `git add -A` pre rituala ostaje ista — razlog je drugi.
CONVENTIONS §8 nosi izmereno.

### Mehanizam je meren dvaput, sa različitim ishodom

**v2.1.258 — radilo.** U ranijoj sesiji ovog istog taska, tri `Read`-a nad `src/chess/`
donela su tri fajla iz `.claude/rules/`, svaki sa zaglavljem `Contents of ...`.

**v2.1.259 — ne reprodukuje se.** Tri `Read`-a nad tri različita `paths:` globa —
`src/chess/core/__init__.py`, `assets/i18n/sr.json`, `src/chess/client/i18n.py` — nisu
donela nijedno pravilo. Eager učitavanje jeste potvrđeno i ovde: čim su tri `SKILL.md`-a
prepisana, lista skillova se osvežila sa novim opisima.

Između dva merenja se **alat ažurirao u toku taska** — terminal je javio
`Update installed · Restart to update` — i restart nije izvršen. Uzrok nije utvrđen i nije
istraživan.

Ono što se lako propusti: da je zapisano samo poslednje merenje, dokument bi tvrdio da
mehanizam ne radi — a to nije ono što je viđeno. Mehanizam je **prestao da radi između
dve verzije, ili traži restart posle ažuriranja**, i ta razlika je vredniji nalaz od bilo
koje od dve pojedinačne tvrdnje, jer imenuje pokretni deo. ADR-044 zato nosi oba merenja i
kolonu „Potvrđeno" po verziji. Tvrdnja o tuđem sistemu i inače važi samo za verziju uz
koju je zapisana; ovaj task je to dobio kao demonstraciju, ne kao teoriju.

Svođenje se time ne dovodi u pitanje — zašto ne, stoji u odgovoru na pitanje 3.

### Nema tabele predviđenih padova

Ritual namernih kvarova od 0.4 se ne ukida, ali ovaj task ne pravi nijednu mašinski
proverljivu tvrdnju: sve što menja je proza u `docs/` i fajlovi van gita. Kvar uveden u
`.claude/` ne može da obori nijedan test, po konstrukciji — nijedan test ne sme da zavisi
od foldera koji `git clone` ne donosi. Izmišljati kvarove da bi tabela imala redove bilo bi
obrnuto od svega što ovaj projekat radi. Umesto toga je pokrenuta pozitivna provera iznad,
i ona je dala nalaz.

### Pitanja

**1. „Rečenica se sme ukloniti tek kad joj dom postoji" je pravilo propagacije okrenuto
unazad. Devet puta smo prvo pisali u `docs/`, pa tek onda brisali. Zašto redosled unutar
jednog commita uopšte igra ulogu, kad je krajnje stanje isto?**
Znao, i preko onoga što je pitano. Krajnje stanje **nije** isto ako se redosled prekine.
Commit je jedinica u istoriji, ali nije jedinica rada: između brisanja i pisanja stoji ceo
niz odobrenja, mogućnost da task stane na nalaz, i odluka korisnika da nešto ne prihvati.
Brisanje pre pisanja pravi prozor u kom tvrdnja ne postoji nigde — a jedini zapis o njoj je
tada kontekst sesije, koji `/clear` briše.

> Drugi razlog je jači i ne zavisi od prekida: **redosled je ono što tera da se dom nađe.**
> Ako se prvo piše u `docs/`, mora se odgovoriti gde tačno ide — i tada se vidi da mesta
> nema. Tako su ispala četiri pravila za §4: grep je za `singleton`, `globaln` i `upit`
> vratio nulu. Da je brisanje išlo prvo, ta četiri bi nestala tiho i niko ne bi imao razlog
> da gleda. Redosled pretvara „nađi dom" iz namere u korak koji se ne može preskočiti.

**2. Blokovi komandi su ispali iz oba skilla, a tabela simptom→uzrok je ostala u perftu.
Obe su tvrdnje koje izmena u `docs/` može učiniti netačnim. Po čemu se onda razlikuju?**
Znao. **Po tome ima li tvrdnja parnjaka u gitu, ne po tome da li je oboriva.** To su dva
različita pravila iz ADR-044: kriterijum kaže koja rečenica **ne sme** da ostane, a pravilo
o domu kaže kada **sme** da se ukloni. Obe tvrdnje padaju na prvom; samo komande prolaze na
drugom — `python tools/layer_check.py` stoji doslovno u §2, `CHESS_SLOW_TESTS=1 …` u §5,
`tools/perft.py` u §10. Brisanje ih ne gubi.

Tabela simptom→uzrok nema parnjaka nigde. Ona nije prepis pravila nego **znanje o tome kako
se generator kvari** — šta znači previše čvorova, šta premalo, šta odstupanje tek na većoj
dubini. Dom joj je docstring `tools/perft.py`, koji u 0.7 ne postoji, pa ostaje uz red koji
imenuje 1.3. Razlika dakle nije u vrsti tvrdnje, nego u tome što jednu čuva git a drugu ne
čuva niko.

**3. Provera na kraju nije donela nijedno pravilo iz `.claude/rules/`. Zašto svođenje tih
fajlova ostaje ispravan potez i ako se ispostavi da ih niko ne čita?**
Znao, sa tri razloga, i nijedan ne zavisi od isporuke.

**Prvo:** pogrešna rečenica ne postaje tačna time što možda ne stiže. `core-purity.md` je
tvrdio nešto što obara ADR-037.3, `i18n.md` nešto što obara ADR-040 — netačne bez obzira ko
ih čita. Mehanizam se uz to može vratiti sledećim ažuriranjem, a fajl bi ga dočekao spreman.

**Drugo:** task je već proizveo dobit koja sa učitavanjem nema veze. Devet tvrdnji koje su
živele samo van gita sada su u `PROJECT.md` §7 i `CONVENTIONS.md` §4. Da `.claude/` sutra
nestane, te tvrdnje ostaju — merenje je pokazalo da je baš to bio jedini pouzdan deo posla.

**Treće:** neizvesnost menja **gde se zapis oslanja**, ne da li se radi. Dve parkirane
tvrdnje u `client-boundaries.md` sada zavise od reda u migracionoj tabeli i od „Otvoreno" u
ROADMAP-u — dakle od gita, ne od mehanizma koji nije potvrđen. To je zavedeno.

---

## 0.8 — dokumenti u gitu se dovode u saglasnost

### Šta je urađeno

`WORKFLOW.md` je jedini dokument iz prvog commita koji nikad nije prošao kroz pravilo
propagacije. Pregled je našao **devet** neslaganja sa važećim ADR-ovima; ROADMAP je
tvrdio četiri. Uz njega su ispravljena tri zaostajanja u drugim fajlovima, zavedena su
dva ADR-a, i `CLAUDE.md` je sveden na adresu i okidač po ADR-044 — isto što je 0.7
uradio sa `.claude/`.

Nijedna linija koda, testa ni alata nije dirana. Broj testova je ostao 53.

### Inventar `CLAUDE.md`

| | Redova | Bajtova |
|---|---|---|
| pre | 191 | 7.479 |
| posle | 45 | 2.041 |
| razlika | **−146 (−76 %)** | **−5.438 (−73 %)** |

Mereno sa `wc -l` i `wc -c`. Fajl je i dalje u `.gitignore` (red 3), pa ni ovaj task
nema `git diff` za taj proizvod — tabela ispod je jedini zapis u gitu.

### Broj je meren četiri puta i menjao se svaki put

| Merenje | Broj | Jedinica | Zašto je pogrešno |
|---|---|---|---|
| 0.7 | ~35 | blok | cela lista „Kraj taska" = 1 umesto 12; ceo blok komandi = 1 umesto 11 |
| 0.8, prvo | 66 | mešano | uvodni pasus proglašen neoborivim, bez provere |
| 0.8, drugo | 70 | mešano | uvodni pasus ispravljen, ali sažeti redovi ostali |
| 0.8, konačno | **104** | rečenica | — |

Sva četiri se čuvaju, jer razlika među njima je nalaz. ADR-044 kaže da je jedinica
provere **rečenica**, ali nijedno od prva tri merenja se tog pravila nije držalo do
kraja, i svaki put je odstupanje išlo u istom smeru — naniže, jer je sažimanje lakše
od razlaganja.

Drugo merenje je oboreno kad je korisnik tražio `grep -rn "dvosmislen" docs/`. Uvodni
pasus je bio proglašen opisom odnosa, ne pravilom projekta; `PROJECT.md` §8 nosi i
tabelu uloga i pasus 358–360, dakle dom postoji i te rečenice **jesu** oborive. Isti
obrazac kao `checkout --` u 0.7: nalaz je stigao tek kad je izmereno ono što je zapis
već proglasio tačnim.

Treće je oboreno na sopstvenoj protivrečnosti. Iznad tabele je stajalo „jedan red =
jedna rečenica", a tri odeljka su imala zaglavlje sa većim brojem nego što su imala
redova — jer su redovi poput „sedam kućica definicije gotovog taska" sažimali po više
rečenica. To je brojanje po bloku, tačno ono što je dva pasusa iznad bilo imenovano kao
greška iz 0.7. Uz to se zbir zaglavlja (72) nije slagao sa tvrdnjom u tekstu (70).

Od 104 rečenice su **dve neoborive** — jezik razgovora sa korisnikom i „pročitaj kad
zatreba, ne unapred" — pa je oborivih **102**. Uklonjeno je **96**; osam ostaje, šest
od njih prerađeno u pokazivač ili okidač.

### Tabela uklonjenih rečenica

Jedan red = jedna rečenica iz starog fajla. **Podebljano** je ono što dom dobija tek u
ovom commitu, ili što se briše bez seljenja.

**Zaglavlje** — 8 rečenica, 7 uklonjeno

| Tvrdnja | Kuda |
|---|---|
| ti si vodeći inženjer | PROJECT §8:358 |
| korisnik je student i arhitekta: on donosi odluke, ti predlažeš i obrazlažeš | PROJECT §8, tabela i :359 |
| cilj je da korisnik razume svaku liniju — brani projekat usmeno | PROJECT §8:360; „Obrnuti pregled" |
| ako se ne slažeš sa nečim, reci | PROJECT §8:358 |
| ne izvršavaj plan za koji misliš da je pogrešan | PROJECT §8:355 i :358 |
| pravila po kojima se piše kod stoje u CONVENTIONS, ne ovde | CONVENTIONS §1; :6–7 |
| ovaj fajl je uputstvo asistentu i ne ide u git | **ostaje** — prerađeno u uvodni blok |
| kad se njih dva raziđu, važi CONVENTIONS | CONVENTIONS §1 |

**Jezik** — 11 rečenica, 10 uklonjeno

| Tvrdnja | Kuda |
|---|---|
| kod → engleski | CONVENTIONS:9 |
| komentari → engleski | :9 |
| docstringovi → engleski | :9; §4 „Komentari i docstringovi" |
| commit poruke → engleski | :9; §8 „Commit" |
| logovi → engleski | §7 „Logovanje" |
| imena grana → engleski | **obrisano — netačno.** §8:556 propisuje `faza-1`, `faza-2`; isti `CLAUDE.md` to ponavlja u redu 143 i protivreči sam sebi |
| razgovor sa korisnikom → srpski | **ostaje van gita** — tvrdnja koju nijedna izmena u `docs/` ne može oboriti; CONVENTIONS:10 pokriva dokumentaciju i interfejs, ne jezik razgovora |
| `README.md` i `docs/` → srpski | CONVENTIONS:10 |
| tekst vidljiv korisniku nikad u kodu, uvek ključ iz `sr.json` | §7 „Ključevi"; ADR-040 |
| šahovska notacija se ne prevodi | §7:497 |
| logovi bez dijakritika — Windows konzola nije UTF-8 | §7 „Logovanje" (ADR-010) |

> ⚠️ **Red „razgovor sa korisnikom → srpski" je od REZ-a norma sa domom.** 0.8 ga je po
> kriterijumu ADR-044 ostavio van gita: nijedna izmena u `docs/` ne može ga učiniti
> netačnim. Test razlikovanja iz ADR-047 (tačka 3) vodi ga drugačije — kad se prestane
> poštovati, rečenica je **prekršena**, ne netačna, pa je normativna i dom joj je `docs/`.
> Dom je `WORKFLOW.md` §1, „Predaja teksta između površina"; zapis: odeljak „REZ" u ovom
> fajlu. Telo tabele iznad ostaje kako je zapisano (CONVENTIONS §1).

**Arhitektura** — 5 rečenica, sve uklonjene

| Tvrdnja | Kuda |
|---|---|
| dijagram smera zavisnosti | §2 |
| smer zavisnosti se ne obrće nikad | §2 |
| tabela dozvoljenih uvoza po modulu je u §2 | §2 |
| sprovodi je `tools/layer_check.py` | §2 „Provera"; §10 (ADR-033) |
| pokreće se i kao test, ne skillom | §2 „Provera" (ADR-033) |

**Granice koje se ne prelaze** — 18 rečenica, 16 uklonjeno

| Tvrdnja | Kuda |
|---|---|
| `core/` uvozi samo stdlib — bez pygame, socket, `print` | §2, red `core/*` |
| pygame tipovi ne izlaze iz `render.py` i `scenes/` | §3 |
| klijent čita poziciju, ne odlučuje o legalnosti | §3 (ADR-024) |
| sme da uvozi samo `core/types.py` i `core/fen.py` | §3 |
| parsiranje FEN-a i crtanje table su dozvoljeni, računanje poteza nije | §3 |
| server je jedini autoritet | §3; PROJECT §1 |
| nikad `pickle` na mreži; protokol je JSON, verzionisan | PROTOCOL:18; PROJECT §6:221 |
| nema globalnog stanja ni singletona — tabla se prosleđuje | §4 „Bez stanja i bez hijerarhije" (0.7) |
| `Color` i `PieceType` su enumi | §4 (0.7) |
| `Piece` je `frozen=True, slots=True` dataclass | §4 „Dataclass-ovi" |
| nikad hijerarhija nasleđivanja | §4 (0.7) |
| make/unmake, nikad kopiranje table | §4 (ADR-006) |
| komanda ≠ upit: `is_legal()` ne menja ništa | §4 (0.7) |
| nikad ne menjaj test da bi prošao — pada kod dok se ne dokaže suprotno | §5 „Pravilo koje se ne krši" |
| ako je test zaista pogrešan, to je zaseban commit sa obrazloženjem | §5 |
| svaki bag prvo dobije test koji pada | **§5 „Redosled" — napisano u ovom tasku** |
| sve ostalo stoji u CONVENTIONS §4–§7 | **ostaje** — prerađeno u tabelu okidača |
| pročitaj ih pre pisanja koda; ne parafraziraj ih ovde | **ostaje** — isto |

**Radni tok** — 14 rečenica, sve uklonjene

| Tvrdnja | Kuda |
|---|---|
| plan mod za sve veće od jedne funkcije | WORKFLOW §6 |
| plan pokazuješ, ne izvršavaš odmah | WORKFLOW §2, uokvireni korak |
| test prvo, pa implementacija | **§5 „Redosled" — napisano u ovom tasku** |
| ako je zadatak dvosmislen — pitaj, ne pretpostavljaj | PROJECT §8:355 |
| ne uvodi apstrakciju koju korisnik nije tražio | **§4 „Dužina i oblik" — napisano u ovom tasku** |
| ritam po tasku ima numeraciju na koju se poziva §9 | ADR-021; CONVENTIONS §9 |
| korak 1 — plan mod, korisnik čita plan pre nego što kod postoji | ADR-021; WORKFLOW §2 |
| korak 2 — implementacija | ADR-021 |
| korak 3 — objašnjenje u 3–5 rečenica, sa odbačenom alternativom | ADR-021; WORKFLOW §2 |
| korak 4 — dva do tri pitanja korisniku, obavezno | ADR-021; §9; WORKFLOW §2 |
| pitanja su o zašto, ne o šta | ADR-021; WORKFLOW §2 |
| korak 5 — korisnik odgovara; ako ne zna, objasni drugačije | ADR-021; WORKFLOW §2 |
| korak 6 — na kraju faze korisnik prepričava celu fazu | ADR-021; WORKFLOW §8 |
| posle svakog taska dva reda u `faza-N.md` | CONVENTIONS §9; WORKFLOW §8 |

**Propagacija odluka** — 7 rečenica, sve uklonjene

| Tvrdnja | Kuda |
|---|---|
| ADR koji obori dokument ispravlja ga u istom commitu, bez izuzetka | §1 „Pravilo propagacije" i „Proširenje" |
| dokument koji zaostaje gori je od dokumenta koji ne postoji | §1, isto mesto |
| stari ADR se ne briše, dobija ⚠️ koja pokazuje na novi | §1 (ADR-032) |
| `DECISIONS.md` je append-only | §1 |
| ADR se piše u četiri slučaja | §1 „Kad se piše ADR" |
| ne piše se za imena promenljivih ni sitne refaktore | §1 |
| format je Kontekst → Odluka → Posledice, uz „šta smo izgubili" | §1 |

**Kraj taska** — 12 rečenica, sve uklonjene

| Tvrdnja | Kuda |
|---|---|
| task nije gotov dok ne prođe svih sedam stavki | §9, uvodna rečenica |
| kućica: `unittest discover` prolazi | §9 |
| kućica: `ruff check` i `ruff format --check` čisti | §9 |
| kućica: perft pokrenut ako je diran generator, obavezno od 1.3 | §9 |
| kućica: pročitan `git diff`, ceo | §9 |
| kućica: odgovoreno na pitanja iz koraka 4, zapisano u `faza-N.md` | §9 |
| kućica: `ROADMAP.md` ažuriran, `DECISIONS.md` dopunjen uz propagaciju | §9 |
| kućica: commitovano | §9 |
| provera koja se ne štiklira: korisnik može naglas da objasni | §9 |
| ako to ne prolazi, ne prelazi se na sledeći task | §9 |
| predloži commit poruku u Conventional Commits formatu | **§8 „Commit" — ime standarda upisano u ovom tasku** |
| reci koji je sledeći task i predloži `/clear` | ROADMAP, blok TRENUTNO; WORKFLOW §4 |

**Git** — 5 rečenica, 4 uklonjene

| Tvrdnja | Kuda |
|---|---|
| zabrane su u §8, dozvole izvršiocu u `settings.json`, to su dva pitanja | **ostaje** — prerađeno u okidač |
| grana po fazi: `faza-1`, `faza-2` | §8 „Grane" |
| merge u `main` sa `--no-ff` kad checkpoint prođe | §8 „Grane" |
| nikad commit koji meša implementaciju sa ispravkom testa | §5 |
| nikad commit koji nosi ADR bez propagacije | §1 |

**Komande** — 11 rečenica, sve uklonjene

| Tvrdnja | Kuda |
|---|---|
| `pip install -e ".[dev]"` | §10; ADR-029 |
| bez toga `discover` ne nalazi paket | ADR-029; §10 |
| `[dev]` nije opcion — bez njega nema `ruff`-a | ADR-036 |
| `python -m unittest discover -s tests` | §9, prva kućica |
| `CHESS_SLOW_TESTS=1 …` | §5 „Perft" |
| `ruff check . && ruff format .` | §10 |
| `ruff check . && ruff format --check .` | §9, druga kućica |
| `python tools/layer_check.py` | §2 „Provera"; §10 |
| `python tools/rasterize_pieces.py` | §10 (ADR-038) |
| `python -m chess.server` | PROTOCOL:23 |
| `python -m chess.client` | **obrisano — jedina komanda bez doma.** `client/__main__.py` ne postoji; dom dobija u 3.1, dotle stoji red u ROADMAP „Otvoreno" |

**Referentni dokumenti** — 13 rečenica, 10 uklonjeno

| Tvrdnja | Kuda |
|---|---|
| pročitaj kad zatreba, ne unapred | **ostaje** — nije oboriva |
| `CONVENTIONS.md` — kako se piše kod | §1 „Ko odgovara na koje pitanje" |
| `DECISIONS.md` — zašto je nešto odlučeno | §1 |
| `PROTOCOL.md` — kako server i klijent razgovaraju | §1 |
| `PROJECT.md` — šta pravimo i zašto | §1 |
| `ROADMAP.md` — šta je sledeće i gde smo stali | §1 |
| `WORKFLOW.md` — kako izgleda jedna radna sesija | §1 |
| `POJMOVNIK.md` — šta znače termini | §1 |
| hijerarhija od šest dokumenata | §1 „Hijerarhija kad se dokumenti ne slažu" |
| CONVENTIONS ne sme da protivreči protokolu | §1 (ADR-032) |
| POJMOVNIK nema autoritet: objašnjava, ne propisuje | §1 |
| ovaj fajl nije u toj listi | **ostaje** — prerađeno u uvodni blok |
| ne propisuje ništa što CONVENTIONS već ne kaže | **ostaje** — isto |

### Devet neslaganja u `WORKFLOW.md`

| # | Šta je pisalo | Šta je radilo pre ispravke |
|---|---|---|
| 1 | `/model opusplan` (§2, §6) | komanda ne postoji; ko je otkuca dobije grešku i ne zna da li mu fali podešavanje |
| 2 | „testovi prolaze → sam pokreće perft skill" (§2) | obara ADR-028 — perft je `tools/perft.py` i pokreće se izričito; dokument je obećavao automatiku koje nema |
| 3 | kontrolna lista od sedam kućica (§5) | šest se poklapalo sa CONVENTIONS §9, **falili su perft i pitanja iz koraka 4**, a sedma („razumem naglas") je greška kategorije: §9 je izričito drži van liste jer se ne može odštiklirati |
| 4 | „napiši `faza-N.md`" na kraju faze (§8) | ko radi po dokumentu preskoči korak 4 iz ADR-021 — i to se ne vidi ni na jednom testu, nego tek na odbrani |
| 5 | „Izvršavanje ide samo" (§9) | dozvoljavalo je da se posle odobrenog plana ne pita više ništa |
| 6 | tabela git dozvola (§9) | poslednja preživela kopija one koja je u 0.7 obrisana iz `CLAUDE.md`-a **zato što je bila netačna**; ista greška je preživela u drugom fajlu |
| 7 | spisak „šta se automatski učita" (§4) | opis tuđeg alata bez verzije; ADR-044 je isti spisak izmerio i dobio različit rezultat po verziji |
| 8 | „Zašto si X odvojio od Y?" kao jedini prikaz pitanja (§2) | obrnut smer — po ADR-021 Claude pita korisnika; obavezan korak je bio nevidljiv |
| 9 | „šta iz `CLAUDE.md` se odnosi na ovo" (§7) | posle ADR-044 `CLAUDE.md` ne nosi pravila, pa je šablon upućivao na prazno |

Uz devet je ispravljeno i poravnanje kutije oko `git diff`, koja je tvrdila da je čitanje
diffa **jedini** korak koji se ne preskače. Otkako korak 4 iz ADR-021 stoji u istom
odeljku, ta reč nije tačna.

### Merenje: `.claude/rules/` traži restart, ne novu verziju

Ovo je zapis na koji pokazuje ⚠️ oznaka sa ADR-044, pa mora da stoji sam za sebe.

| Kada | Verzija | Ishod |
|---|---|---|
| 3. septembra 2026, ranija sesija 0.7 | v2.1.258 | tri `Read`-a nad `src/chess/` donela tri fajla iz `.claude/rules/`, svaki sa zaglavljem `Contents of …` |
| 3. septembra 2026, kasnija sesija 0.7 | v2.1.259, **bez restarta** | tri `Read`-a nad tri različita `paths:` globa — nijedno pravilo |
| 4. septembra 2026 | v2.1.259, **posle restarta** | pravila se učitavaju |

Između prva dva merenja alat se ažurirao u toku taska; terminal je javio
`Update installed · Restart to update` i restart nije izvršen. ADR-044 je zato zapisao
„uzrok nije utvrđen", što je u trenutku pisanja bilo tačno. Treće merenje ga obara:
**uzrok je neizvršen restart, ne promena između verzija.**

Tvrdnja i dalje važi samo za v2.1.259 i i dalje je tvrdnja o tuđem sistemu, pa red u
ROADMAP „Otvoreno" ostaje — skraćen, ne obrisan. Operativna posledica je jedan red u
`WORKFLOW.md` §4: alat javio ažuriranje u toku taska → restartuj pre nastavka.

### Zašto rečenica napisana kao mehanizam ne može da otkaže

U 0.7 su dva pravila iz korpusa van gita prekršena više puta i nijedno kršenje nije
imalo posledicu. Oba su bila napisana kao **mehanizam**: imenovala su poklapanje stringa
u izlazu alata („neuspeo upis"), a ne zahtev. Kad je stvarna potreba bila zadovoljena
drugim putem, uslov se nije okinuo — pravilo je ćutalo, iako je ono što štiti bilo
prekršeno.

Odatle merilo po kom je pisana svaka rečenica koja se u ovom tasku selila:

- **zahtev, ne mehanizam** — rečenica ne imenuje interfejs alata, jer interfejs se menja
  bez najave i tada rečenica postaje tačna o ničemu;
- **opseg, ne apsolut** — ako izuzetak postoji, nosi ga i sama rečenica. Zato „test prvo"
  u CONVENTIONS §5 izričito kaže da obavezuje `src/` i `tools/`: task koji menja samo
  `docs/` nema šta da testira, a pravilo bez te klauzule bi ga proglasilo prekršajem.

Isto merilo je oborilo prvu formulaciju četvrtog STOP-a u ADR-046 i zamenilo je onom
koja imenuje situaciju: zatečeno stanje drugačije od onog koje plan pretpostavlja.

### Nema tabele predviđenih padova

Isti razlog kao u 0.7, i ponavlja se jer je klasa ista: task ne pravi nijednu mašinski
proverljivu tvrdnju. Sve što menja je proza u `docs/` i fajl van gita. Kvar uveden u
`CLAUDE.md` ne može da obori nijedan test, po konstrukciji — nijedan test ne sme da
zavisi od fajla koji `git clone` ne donosi.

Kapije su zato inventar pre i posle, stari i novi tekst prikazan pre svake izmene van
gita, i tabela uklonjenih rečenica iznad. Dodata je jedna pozitivna: za svaku od četiri
novonapisane tvrdnje `grep` prvo mora da vrati **bar jedan** pogodak, pa se tek onda
poredi broj — provera koja prolazi na praznom ulazu nije provera. Sve četiri su vratile
tačno po jedan normativni pogodak.

Dve mašinske kapije koje su razmatrane — provera upisa nad bajtovima i provera da
trajleri ne ulaze u istoriju poruka — odložene su u 0.9, zajedno sa korpusima van gita
na koje se odnose.

### Pitanja

**1. ADR-045 kaže da merenje koje obori ADR ne dobija svoj ADR, nego se zapisuje u
`faza-N.md`, a ADR na njega samo pokazuje. Time je `DECISIONS.md` — fajl na vrhu
hijerarhije — postao zavisan od fajla ispod sebe. Zašto je to ipak ispravno, i šta bi se
pokvarilo da smo merenje proglasili ADR-om?**

Znao. **ADR i merenje imaju suprotna svojstva trajanja.** ADR je odluka: ne otvara se
ponovo, i tačan je zato što smo ga mi tako odlučili — svet ga ne može oboriti. Merenje je
tvrdnja o tuđem sistemu i mora ostati oborivo prvim sledećim pokretanjem. Da je merenje o
restartu proglašeno ADR-om, dobilo bi zaštitu „ne otvara se ponovo", pa bi svaka sledeća
verzija alata koja se ponaša drugačije morala da **obara ADR** umesto da doda red u
tabelu — lanac bi rastao za jedan ADR po ažuriranju tuđeg programa. Uz to bi CONVENTIONS
§1 bio prekršen, jer nabraja četiri slučaja u kojima se ADR piše i merenje nije nijedan.

> Zavisnost `DECISIONS.md`-a od fajla ispod njega je stvarna cena i zato je ADR-045
> imenuje pod „šta smo izgubili". Ispravna je zato što **hijerarhija uređuje ko pobeđuje
> kad se dva dokumenta ne slažu, a ovde sukoba nema**: merenje ne protivreči odluci, nego
> činjenici koju je odluka usput zapisala. Autoritet zapisa dolazi od toga što je
> izmereno, ne od ranga fajla u kom stoji.

**2. U CONVENTIONS §5 pravilo „test prvo" nosi klauzulu da obavezuje samo `src/` i
`tools/`. Klauzula je duža od samog pravila i lako je reći da je suvišna. Zašto mora da
stoji u samoj rečenici, a ne u obrazloženju ispod nje?**

Znao, sa dva razloga. **Prvi: obrazloženje nema ko da pročita u trenutku kad pravilo
otkazuje.** Pravilo se primenjuje tako što neko proveri da li ga je prekršio; ako je opseg
dole u prozi, provera se radi nad rečenicom koja bez klauzule glasi apsolutno — i 0.8 i
0.9, koji ne diraju nijednu liniju koda, ispadaju prekršaj. Rečenica koja mora da se čita
zajedno sa pasusom ispod nije pravilo nego nacrt pravila.

**Drugi je iz ovog istog taska.** Dva pravila iz `MEMORY.md`-a napisana kao apsolut ispala
su već oborena onim što projekat radi: „ime nikad ni u jedan fajl" protivreči redu o
autorskim pravima u `LICENSE`-u, koji tamo stoji po ADR-042. Apsolut nastaje kad se
pravilo napiše iz jednog slučaja, a izuzetak se otkrije kasnije — i tada niko ne zna da li
je izuzetak dozvoljen ili je pravilo prekršeno. **Klauzula je duža od pravila zato što je
opseg deo pravila, ne komentar na njega.** Nalaz je zaveden u 0.9.

**3. Broj oborivih tvrdnji je meren četiri puta i svaki put je ispao drugačiji — ~35, 66,
70, 104. Zapisana su sva četiri. Šta bismo izgubili da stoji samo „104", i zašto je
odstupanje išlo baš naniže sva tri puta?**

Znao, i drugi deo odgovora je bio bolji od onoga zbog čega je pitanje postavljeno.

**Šta bismo izgubili:** jedini nalaz koji je taj niz proizveo. „104" sam za sebe je broj
rečenica u fajlu koji od ovog commita više ne postoji u tom obliku — neupotrebljiv posle
njega. Upotrebljivo je to što je **isti fajl, po istom pravilu iz ADR-044, tri puta
izbrojan pogrešno**: pravilo „jedinica je rečenica" nije samoprimenljivo i traži da broj
uvek nosi jedinicu pored sebe. Bez tri odbačena merenja, §0.8 bi tvrdio da je brojanje
bilo tačno iz prvog puta.

**Zašto naniže:** sažimanje je podrazumevano stanje čitanja, a razlaganje traži odluku. Ko
čita listu od sedam kućica vidi jednu stvar — „definicija gotovog taska" — jer je tako i
napisana, kao celina. Da ispadne sedam, mora se stati i pitati koliko tvrdnji taj blok
nosi. **Greška zato ima smer: nijedno pogrešno brojanje nije dalo previše, sva tri su dala
premalo.** Isti oblik kao merenje koje se pokrene jednom i potvrdi ono što se očekivalo —
tri puta u ovom tasku je tek **ponovljeno** merenje oborilo prethodno.

---

## 0.9 — korpusi van gita se svode

### Šta je urađeno

Kriterijum ADR-044 je ADR-047 proširio na **tri** korpusa: `.claude/`, `MEMORY.md` sa
folderom i memoriju planskog chata. `settings.json` nije korpus pravila, nego odredište za
dozvole izvršiocu. Pravila iz MEMORY foldera su dobila dom u `CONVENTIONS.md` i
`WORKFLOW.md`, ili su obrisana, pa je folder sveden na prazan `MEMORY.md`. Dodate su dve
mašinske kapije, **prve u luku 0.7–0.9**: test `tests/test_encoding_bytes.py` (K1) i alat
`tools/check_commit_trailers.py` (K2). Testova je bilo 53, sada ih je 58.

### Inventar

Mereno sa `find` i `wc -l` / `wc -c` po fajlu, 17. 9. 2026, pre ijedne izmene i posle
svođenja. U 0.7 je zapisan samo zbir bajtova, pa se po fajlu meri prvi put sada.

**Korpus 1: `.claude/`.** Bez izmena, pa je stanje posle isto kao pre. Poklapa se sa 0.7 i
po zbiru: 152 reda, 5.823 bajta.

| Fajl | Redova | Bajtova |
|---|---|---|
| `rules/client-boundaries.md` | 28 | 897 |
| `rules/core-purity.md` | 17 | 480 |
| `rules/i18n.md` | 19 | 578 |
| `skills/chess-rules/SKILL.md` | 28 | 1.155 |
| `skills/layer-check/SKILL.md` | 19 | 734 |
| `skills/perft/SKILL.md` | 41 | 1.979 |
| `settings.json` (nije korpus) | 43 | 1.240 |

**Korpus 2: MEMORY folder.**

| Fajl | Nastao | Redova | Bajtova | Posle |
|---|---|---|---|---|
| `MEMORY.md` | — | 9 | 1.413 | 0 / 0 |
| `batch-doc-edits-one-call.md` | 31. 8. | 24 | 1.245 | obrisan |
| `conditional-stops-between-plan-steps.md` | 2. 9. | 25 | 1.127 | obrisan |
| `measure-before-declaring-absence.md` | **5. 9. 04:09** | 26 | 1.490 | obrisan |
| `no-claude-attribution-in-repo.md` | 30. 8. | 23 | 1.129 | obrisan |
| `no-personal-data-in-files.md` | 31. 8. | 28 | 1.372 | obrisan |
| `record-both-measurements.md` | **3. 9.** | 27 | 1.519 | obrisan |
| `relay-command-output.md` | 1. 9. | 30 | 1.406 | obrisan |
| `roadmap-checkbox-and-trenutno.md` | 31. 8. | 20 | 918 | obrisan |
| `verify-writes-over-bytes.md` | 2. 9. | 25 | 1.261 | obrisan |

Ukupno 237 redova i 12.880 bajtova pre; posle 0 i 0. Datum nastanka je vreme izmene fajla.

**Korpus 3: memorija planskog chata.** Samo inventar pre: četiri fajla, 6.349 bajtova, oko
50 stavki, mereno 15. 9. 2026 u planskom chatu. Redovi nisu mereni. Svodi se **posle**
ovog commita, u planskom chatu, jer dom mora prvo da postoji u gitu. **Nijedna kapija ga ne
dohvata**: ni K1, ni K2, ni četiri kapije iz prve kućice CONVENTIONS §9. To je jedini deo
taska bez ijedne provere.

### Devet pravila, ne sedam

Plan je poznavao sedam pravila; u folderu ih je bilo devet. Nalaz iz plan moda je bio
četvrti STOP. Pravilo `record-both-measurements` je dobilo dom u CONVENTIONS §1 („Merenje u
zapisu"), a `measure-before-declaring-absence` u §5, uz nalaz 1 iz plana. Drugo je nastalo
**posle** commita `4c71791`, na kraju sesije 0.8. Time je izmereno ono što je plan vodio kao
neizmereno: pravila u ovom korpusu **nastaju iz razgovora**, bez ijedne odluke po fajlu.
T4 ostaje na snazi: pravilo koje se vrati samo od sebe obara ADR-047, tačku 2.

`conditional-stops-between-plan-steps` je nabrajao **tri** uslovna STOP-a, a ADR-046 ih ima
četiri. Truljenje kopije koje ADR-044 opisuje uhvaćeno je u korpusu koji se upravo svodio.

### Nova nit: provera nije užeg domena od tvrdnje

U nizu sa nitima iz 0.4–0.8. U 0.8 je za svaku rečenicu iz korpusa postavljeno pitanje „ima
li dom u `docs/`", i grep je išao nad `docs/`. Takva provera utvrđuje **gde** rečenica
pripada, ne **da li je tačna**. Kontraprimer za „ime nikad ni u jedan fajl" živeo je u
`LICENSE`-u, u korenu, van domena grepa.

> **Provera koja traži kontraprimer samo tamo gde se pravilo očekuje ne proverava tvrdnju,
> nego adresu na koju tvrdnja upućuje.**

Dom: CONVENTIONS §5, „Provera i njen domen".

### Devet grepova

Grepovi su pokrenuti **pre** svođenja, kroz Bash `grep -rnIE`, ne kroz alat za pretragu,
jer on poštuje `.gitignore` (T1). Za svaki domen je prvo dokazano da nije prazan.

| Domen | Tekstualnih fajlova | Uslov |
|---|---|---|
| A: stablo | **52** | bez `.git/`, `.venv/`, `__pycache__`, `*.egg-info`, `.claude/`, `.idea/`, `.ruff_cache/` |
| A: stablo, plan mod | **68** | bez `.git/`, `.venv/`, `__pycache__`, `*.egg-info` |
| B: `.claude/` + MEMORY | 7 + 10 | — |
| C: korpus 3 | 4 | grepovao planski chat, 17. 9. 2026 |

**68 − 52 = 16 = 7 (`.claude/`, premešten u B) + 7 (`.idea/`) + 2 (`.ruff_cache/`).** Oba
merenja su koristila `-I`, pa se razlika ne duguje njemu. U dodatim izuzećima nema teksta
koji pišemo mi. `build/lib/` je ostao u domenu A; njegov pogodak uz grep 6 je generisana
kopija `src/` i broji se kao zavisan.

Upisani su broj pogodaka i mesta, **nikad pogođeni red**. Uz grep 4 bi pogođeni red bio baš
prekršaj pravila koje se u ovom commitu piše.

| # | Pravilo | A: stablo | B | C: korpus 3 |
|---|---|---|---|---|
| 1 | conditional-stops | 14: ADR-046, WORKFLOW §2, ROADMAP:139, faza-0:1561; 2 šum (ADR-027, POJMOVNIK) | 4, samo u pravilu | 1, poklapa se sa ADR-046 (duplikat) |
| 2 | roadmap-checkbox | 26: ROADMAP, tabele faza-0 §0.8, `CLAUDE.md`:30 | 8, samo u pravilu | 2, pokazivač na TRENUTNO |
| 3 | relay-command-output | „ne vidi" / „sažet" 17, sve šum; „izlaz" 33 | 6 + 8 | 0 |
| 4 | no-personal-data | ime: 5 mesta (`LICENSE`:1, `THIRD-PARTY.txt`:6, `tests/test_assets.py`:116 očekivana; `DECISIONS.md`:1229, `faza-0.md`:1051 kontekst ADR-a); e-mail 0; autor 16/16 commitova | 0 | **kontraprimer**: ime arhitekte 10 mesta; prezime i indeks 1; ime mentora 1; e-mail 0 |
| 5 | batch-doc-edits | 5: faza-0 176, 632, 745; 2 šum | 5, samo u pravilima | 0 |
| 6 | verify-writes | 34 u 7 fajlova (jedan je `build/lib/`, zavisan) | 8 | 0 po obrascu; načelo na 2 mesta |
| 7 | no-claude-attribution | 2, šum (BSD „atribucija"); trajleri 0 | 4 | 0 |
| 8 | record-both | 130 u 9 fajlova, širok obrazac | 20 | 3, sve šum |
| 9 | measure-absence | 5: `CLAUDE.md`:42, CONVENTIONS:52 (šum), DECISIONS:1523, **faza-0:1488**, ROADMAP:120 | 5 | 0; kandidat po sadržaju u `overview` |

**Presuda o `faza-0.md`:1488** („jedina komanda bez doma"): nije kontraprimer, jer je iza
nje stajao grep iz 0.8. Merenje ipak nije zapisano uz rečenicu, pa ga čitalac ne vidi. Zbog
tog slučaja je CONVENTIONS §5 dopunjen: tvrdnja o odsustvu nosi merenje **uz sebe**, ne
samo iza sebe.

**Ime mentora** se briše i ne dobija dom (DECIDED 7). Nalazi se na jednom mestu u korpusu 3
i uklanja se pri svođenju tog korpusa.

### Tabela uklonjenih rečenica

Jedinica je stavka: rečenica, ili grupa rečenica koje nose istu tvrdnju. Brojano jednom.

| Pravilo | Stavka | Kuda |
|---|---|---|
| batch-doc-edits | sve izmene jednog fajla zajedno | **okrenuto**: WORKFLOW §2, sve se pokazuju pre prve |
| | ako nisu susedne, ceo fajl kroz `Write` | obrisano; za fajl od 1.600 redova to je prepisivanje iz konteksta (ADR-042) |
| | pokaži stari i novi tekst; prva od četiri izgleda kao ceo plan | WORKFLOW §2 |
| | delimična izmena je rizik; spoji `old_string`; ako ne pogađa, pitaj | obrisano: okrenuto pravilo / mehanizam |
| | „tri puta zaredom u 0.2" | keširana činjenica, obrisano |
| conditional-stops | ceo fajl | obrisano, ADR-046 i WORKFLOW §2 |
| measure-absence | odsustvo se meri, bar dve formulacije | CONVENTIONS §5 |
| | nula iz grepa se zapisuje sa komandom | CONVENTIONS §5, „ostaje uz tvrdnju" |
| | primeri iz 0.8; odsustvo deluje očiglednije | keširana činjenica / obrazloženje, obrisano |
| no-claude-attribution | bez `Co-Authored-By` i `Claude-Session`, i kad uputstvo alata traži | CONVENTIONS §8 „Commit" |
| | isto za opise PR-a | CONVENTIONS §8 „Commit" (dom posle STOP-a) |
| | „sve Claude-ovo što nije neophodno"; „sve novo u `docs/`" | šira polovina, obrisano: nema kriterijum |
| | `CLAUDE.md` gitignorisan; javan repo | već u §8 |
| no-personal-data | nijedan lični podatak, ni u privremen fajl; odobrenje po slučaju; neutralna vrednost | CONVENTIONS §8 „Lični podaci", proširen na **svačiji** |
| | Wikimedia User-Agent; „ne popunjavaj iz `userEmail`" | primer / mehanizam, obrisano |
| record-both | oba merenja sa uslovima; razlika je nalaz; „uzrok nije utvrđen" | CONVENTIONS §1 |
| | izveštaj arhitekte je merenje, ne anegdota | CONVENTIONS §1 (dom posle STOP-a) |
| | primer 0.7; „kolona, ne novi red" | već u ADR-044 / mehanizam, obrisano |
| relay-command-output | izlaz doslovno; pre izmene šta bi promenila; skrati ponavljanje, ne zaključak | WORKFLOW §9 |
| | „korisnik ne vidi rezultate alata" | tvrdnja o UI-u bez verzije, obrisano |
| | „više puta zaustavio rad"; „kad zaboravim, pošalji" | keširana činjenica / posledica, obrisano |
| roadmap-checkbox | `[x]` i TRENUTNO u istoj izmeni; legenda protivreči | CONVENTIONS §9, šesta kućica |
| | propušteno u 0.1–0.2b; „jedan `Edit`" | keširana činjenica / mehanizam, obrisano |
| verify-writes | tvrdnja o znacima nad bajtovima; kodna tačka, ne escape | CONVENTIONS §7 |
| | provera ne sme da deli sudbinu sa kvarom | CONVENTIONS §5, podignuto u načelo |
| `MEMORY.md` | devet redova indeksa | obrisano sa pravilima |

Pre brisanja su dve normativne rečenice bile bez doma: arhitektin izveštaj kao merenje, i
opis PR-a. To je bio STOP po DECIDED 5, i obe su dobile dom. **K2 ne čita opise PR-ova**,
pa je pravilo u §8 šire od kapije, i to u §8 piše naglas.

### Kapije i predviđeni padovi

Ritual: `git add -A` → namerni kvar → kapija → dijagnoza → povratak → kapija ponovo.

| Kapija | Kvar | Predviđeno | Viđeno |
|---|---|---|---|
| K1 | `EF BB BF` na početak `sr.json`, sastavljen iz celih brojeva | pad imenuje `sr.json`, pomeraj `0`, bajtovi u hex obliku; uz njega B6 i čitači kataloga | **tačno**: „contains the bytes EF BB BF at byte offset 0"; ukupno 2 FAIL (K1, B6) i 7 ERROR (`JSONDecodeError` u A3, A4, B7–B11) |
| K2 | prazan commit sa `Co-Authored-By:` na grani `tmp/k2-drill` | izlaz `1`, SHA i red, commitova > 0 | **tačno**: 17 commitova, `1916a29…` i red, izlaz `1`; posle brisanja grane 16 commitova, izlaz `0` |

Povratak za K1 je bio `git checkout -- assets/i18n/sr.json`, uz izričito odobrenje po §8,
posle čega je suite dao 58/58. Viseći objekat `1916a29` ostaje lokalno do `gc`, i to je
prihvaćeno.

**K2 proba nije izvedena doslovno po planu.** Posle `git add -A` indeks je nosio ceo task.
Commit na probnoj grani bi ga povukao u sebe, a `git switch main` bi ga zatim skinuo sa
radnog stabla. Umesto toga je prazan commit napravljen kroz `git commit-tree` nad stablom
`HEAD`-a, a ime mu je dato kroz `git branch`. Indeks i radno stablo nisu dirani, a ishod je
onaj iz plana.

**Izmereno uz ritual:** `settings.json` drži `git switch*` i `git branch*` u `allow`, pa
predviđena smetnja sa dozvolama nije postojala. `git commit-tree` nije u `allow` i tražio je
upit.

**Prvo merenje istorije poruka** (T3): 16 commitova, nijedan trajler, `shallow: false`.
Plan je ovo vodio kao nikad mereno.

**Test prvo za K2.** Test protiv nepostojećeg alata pada na `FileNotFoundError`, a to ne
razlikuje ponašanja. Zato je prvo napisan kostur koji vraća `[]`. Pao je na tvrdnji, četiri
puta: tri `subTest`-a pogotka i prazan ulaz. Test čiste poruke je prošao, i tako treba.
Implementacija je dala 3/3.

### Prikaz upisa i predati ulaz: dva merenja

Claude Code, 17. 9. 2026. Posle sesije `claude --version` daje 2.1.274; da li se verzija
menjala tokom sesije nije mereno.

| Merenje | Ko | Šta je viđeno |
|---|---|---|
| prikaz u upitu za odobrenje `Write`-a nad postojećim fajlom (kosturom), dvaput | arhitekta | novi sadržaj nosi dva reda kostura: rečenicu „Skeleton written…" i `return []` pre docstringa |
| tekst predat alatu, isti oba puta; ispisano prvih 40 redova | izvršilac | nijedno od ta dva mesta |

**Uzrok nije utvrđen.** Arhitekta je svoje merenje povukao kao slabije, jer je imao prikaz
ulaza, a ne sam ulaz. Upis je zatim izveden tako da ne deli sudbinu sa prikazom: fajl je
upisan u scratchpad, ispisan kroz `cat -n` sa `sha256sum`, kopiran kroz `cp`, pa je otisak
ponovo izmeren nad odredištem. Oba otiska su `104cd372…1203`. Istim putem je upisan K1:
otisak `15a68c99…64ff`, ASCII, bez BOM-a i bez NUL bajta. Predloženo merenje za kasnije je
u ROADMAP „Otvoreno".

### Ostale presude u toku taska

- **K1 domen:** „praćeni fajl" bi tražio `git`, a DECIDED 8 ga isključuje. Tvrdnja je
  prepisana na obrasce `assets/**/*.json`, `src/**/*.py` i `docs/**/*.md`. Svaki obrazac
  sam dokazuje da nije prazan; bez praga u broju fajlova. PNG i TTF su izvan domena namerno.
  Stanje pre: 1 + 8 + 8 fajlova, nula pogodaka.
- **K1 docstring:** samo engleski, a tvrdnja stoji ovde. Citat bez dijakritike bio bi treća
  verzija iste rečenice, koju nijedna kapija ne drži u skladu sa ostale dve.

  > Nijedan fajl koji odgovara obrascima `assets/**/*.json`, `src/**/*.py` i
  > `docs/**/*.md` ne sadrži sekvencu `EF BB BF`. Provera se izvodi nad
  > `Path.read_bytes()`; dekodirani tekst se ne koristi.

- **Formalni PDF:** nije u `git ls-files`, nije na disku, nijedna putanja u istoriji nije
  `.pdf`, a indeks nema pogodaka ni u stablu ni u sadržaju commita. **Prezime nije mereno**:
  `git config user.name` je jedna reč. To je neizmereno, ne nula.
- **Kraj reda:** `CONVENTIONS.md` je u radnoj kopiji CRLF (`w/crlf`, indeks `i/lf`), i pre i
  posle izmene. Golih LF nema. Git pri svakom `add`-u javlja `LF will be replaced by CRLF`
  za nove i izmenjene fajlove. Nije dirano.
- **Korpus 1:** bez izmena. Dva kandidata su van obima i zavedena u „Otvoreno".
- **Privremen fajl u indeksu:** diff sačuvan za čitanje u korenu repoa ušao je u indeks kroz
  `git add -A`, koji ritual predviđenih padova zahteva. Uhvaćen je pre commita, pregledom
  `git diff --cached --name-status`, a ne kapijom; nijedna kapija ovog taska ga ne dohvata.
  Skinut je iz indeksa kroz `git rm --cached` i obrisan sa diska.

### Budžet

| Šta | Budžet | Izmereno |
|---|---|---|
| ADR-047 | ≤ 90 | 59 |
| normativni tekst u `docs/` | ≤ 140 (bilo ≤ 130, +10 za dva zatečena pravila) | 135 dodatih redova naspram `HEAD`: CONVENTIONS 67, ROADMAP 45, WORKFLOW 23 |
| ovaj odeljak | ≤ 300 | 275 |
| `CLAUDE.md` | ≤ 55 | 44 (bilo 45) |

### Pitanja

**1. `find_trailers` na prazan ulaz baca `ValueError`, pa alat vraća izlaz `2`, ne `0`.
Prazna istorija nema nijedan trajler, pa „čisto" izgleda logično. Šta bi prošlo
neprimećeno da prazan ulaz vraća `0`, i kada se to može desiti?**

Znao. Prošlo bi neprimećeno da alat uopšte nije pročitao istoriju. Izlaz `0` tada ne znači
„nema trajlera" nego „nisam gledao", a to su dve različite tvrdnje zapisane istim brojem.
To se dešava kad `git log` uspe a vrati prazan izlaz: u repou bez ijednog commita, pri
pokretanju iz foldera koji nije git repo, ili kad promena format stringa dovede do prazne
liste bez greške. Najopasniji slučaj je CI ili tuđ klon gde niko ne gleda ispis, nego samo
izlazni kod: kapija je zelena, a nije radila. Zato postoji treći ishod: izlaz `2` razdvaja
„čisto" od „nije se izvršilo". Zato alat i ispisuje broj pročitanih commitova, da se domen
vidi, a ne pretpostavlja.

**2. Test iz ADR-047 pita da li rečenica, kad se svet promeni, postaje netačna ili
prekršena. Zašto se „korisnik ne vidi rezultate poziva alata" briše, a „izlaz komande ide
doslovno u odgovor" seli, iako obe govore o istoj stvari?**

Znao. Ako sutra alat počne da prikazuje pun izlaz, prva rečenica postaje **netačna**. Ona
tvrdi nešto o UI-u koji se menja bez najave, dakle to je keširana činjenica, i po ADR-045 se
u tom obliku ne piše nigde bez verzije i datuma. Druga u istom svetu ne postaje netačna,
nego se samo lakše poštuje: zahtev i dalje važi, i ako se ne poštuje, **prekršen je**. To je
normativna rečenica. Obe govore o istoj stvari, ali jedna je razlog, a druga zahtev. Razlog
je oboriv, zahtev nije: sažetak se ne može proveriti bez obzira na to šta UI prikazuje.

**3. K2 proba je izvedena kroz `git commit-tree`, ne kroz `git switch -c` i `git commit`
kako plan kaže. Šta bi se desilo sa radom na tasku da je izvedena doslovno, i zašto je baš
`git add -A` koji štiti K1 probu ono što bi K2 probu učinilo opasnom?**

Znao. `git add -A` je pre rituala stavio ceo rad na tasku u indeks. Za K1 je to zaštita:
`git checkout --` vraća fajl iz indeksa, pa je namerni BOM poništen bez gubitka. Za K2 je
ista stvar opasnost. `git commit -m` sa trajlerom pokupio bi ceo indeks u commit na probnoj
grani, a `git switch main` bi ga zatim skinuo sa radnog stabla: rad bi „nestao" u commitu
na grani koja se posle briše sa `-D`. `git commit-tree` pravi commit direktno iz stabla
`HEAD`-a i ne dira ni indeks ni radno stablo, a `git branch` mu samo daje ime. Ishod je
isti, cena nije.

> Ispravka uz odgovor 3: `CLAUDE.md` nije bio u indeksu. Gitignorisan je, a menjan je tek
> posle rituala. `git add -A` je u indeks stavio `docs/`, dva testa i alat.

---

## Checkpoint faze 0

Checkpoint ne piše kod i ništa ne popravlja — meri i zapisuje. Predmet merenja je
`b8a35dcce426e52d60349d924709c8c7def2d1bd` kroz **svež klon sa GitHub-a, u novom venv-u,
van radnog stabla**: da li prolazi red checkpointa faze 0, da li su obe provere istorije
čiste nad objavljenom istorijom, i da li su korpusi van gita u stanju u kom ih je 0.9
ostavio.

**Šta se ovim ne tvrdi.** Ništa o radnom stablu osim onoga što tabela izričito nosi;
ništa o drugim mašinama; ništa o opisima PR-ova, jer ih K2 ne čita (CONVENTIONS §8);
ništa o putanjama koje nikad nisu bile u stablu repozitorijuma — to je granica provere
iz §8, zapisana tamo.

> **Ishod: red checkpointa na svežem klonu nije zelen.** Pet subtestova
> `test_every_svg_matches_its_recorded_sha1` pada, na Linux-u i na Windows-u jednako.
> Prolazi samo radno stablo, i to iz razloga koji je nalaz 2.

### Tabela merenja

Dva merenja iste stvari stoje **oba**, svako sa svojim uslovima (CONVENTIONS §1).
Referentne vrednosti iz 0.9 i sa Linux klona su merenja, ne očekivanja.

| Merenje | Uslovi | Ishod |
|---|---|---|
| četvrti korpus, inventar „pre" | planski chat, 19. 9. 2026; tekst kakav stiže u kontekst, prepisan u fajl; nije dokazano da je bajt u bajt jednak onome u podešavanjima Projekta | 52 reda (39 nepraznih), 2.684 bajta, 2.623 znaka, 14 pasusa, 8 stavki, 28 rečenica; bez BOM-a i CRLF-a |
| red checkpointa, svež klon | Linux (Ubuntu 24.04), Python 3.12.3, pip 24.0, ruff 0.16.8, pygame 2.6.1, git 2.43.0, `core.autocrlf` nije postavljen, 19. 9. 2026 | `pip install -e ".[dev]"` prošao; `Ran 58 tests` → `FAILED (failures=5)`; `All checks passed!`; `22 files already formatted` |
| pet `sha1` vrednosti | isti klon | `wn`, `wb`, `wr`, `bn`, `bb`: zapisana vrednost je `sha1` CRLF oblika; commitovani bajtovi su LF (`i/lf w/lf attr/-text`), jedan commit po fajlu (`cb60748`); ostalih sedam se poklapa |
| K2 | isti klon | `commits read: 17 … shallow: false`, izlaz `0` |
| provera iz §8 | isti klon | 95 ulaznih putanja, izlaz `1` |
| zatečeno stanje radnog stabla | Windows 11, git 2.54.0.windows.1, Claude Code 2.1.278, 20. 9. 2026 | `git status --porcelain` prazno; `HEAD` = `origin/main` = `b8a35dc…`; `core.autocrlf` = `true` (T1 iz plana, poslednji zapis je iz 0.6 i isti je) |
| red checkpointa, svež klon | Windows 11, Python 3.11.9, pip 24.0, ruff 0.16.8, pygame 2.6.1, git 2.54.0.windows.1, `core.autocrlf=true`, 20. 9. 2026 | `pip install -e ".[dev]"` prošao (T5); `Ran 58 tests` → `FAILED (failures=5)`; `All checks passed!`; `22 files already formatted` |
| pet `sha1` vrednosti, klon | isti Windows klon | svih 12 `i/lf w/lf attr/-text` **iako je `core.autocrlf=true`**; `sha1` sa diska jednak blobu za svih 12; pet (`bb`, `bn`, `wb`, `wn`, `wr`) se ne poklapa sa zapisanim u `assets/pieces/LICENSE.txt` |
| pet `sha1` vrednosti, radno stablo | radno stablo, 20. 9. 2026, samo čitanje | tih pet je `i/lf w/crlf attr/-text`; `sha1` sa diska == zapisani, blob != zapisani; ostalih sedam `i/lf w/lf`, disk == blob == zapisani; `git status --porcelain assets/pieces/svg/` **prazno** |
| stat u indeksu | isto | `git ls-files --debug assets/pieces/svg/wn.svg` → `size: 1325`, jednako veličini CRLF fajla na disku (blob je manji) |
| K2 | isti Windows klon | `commits read: 17 (local history, all refs; shallow: false)`, izlaz `0` |
| provera iz §8 | isti Windows klon | 95 ulaznih putanja, izlaz `1` |
| provera iz §8, oblik komande | Bash alat pod Claude Code-om (Git Bash; `awk` i `sort` postoje), 20. 9. 2026 | oblik iz §8 se izvršava **doslovno**, bez zamene; radno stablo: 95 ulaznih putanja |
| korpusi van gita | mašina, 20. 9. 2026 | `.claude/` bez `settings.json` 152 reda i 5.823 bajta, po fajlu identično zapisu 0.9; MEMORY folder sadrži samo prazan `MEMORY.md` (0 / 0); `CLAUDE.md` 44 reda, **2.437 bajtova** |

Bajtovi `CLAUDE.md`-a nemaju parnjaka: 0.9 je zapisao samo redove („44 (bilo 45)"), a
0.8 bajtove za 45 redova. Ovo je zato **prvo merenje bajtova**, ne odstupanje.

### Nalazi

**1. Windows klon potvrđuje pet padova, i obara pretpostavljeni uzrok.** Klon je
napravljen na mašini sa `core.autocrlf=true`, a checkout je svih 12 SVG-ova ipak zapisao
sa LF. `.gitattributes` dakle radi tačno onako kako ADR-039 kaže. Pad ne dolazi od
konverzije prelazaka reda pri kloniranju: **zapisane vrednosti su pogrešne za pet
fajlova.**

> **Poslednju rečenicu obara merenje iz R9** (20. 9. 2026, preuzimanje sa Commons-a).
> Zapisane vrednosti su tačni otisci **preuzetih** bajtova; pogrešni su bili blobovi.
> Ostatak nalaza stoji. Zapis: odeljak „R9 — pet sha1 vrednosti" u ovom fajlu.

**2. Radno stablo nosi pet fajlova koji se razlikuju od svojih blobova, a `git status`
ćuti.** U radnom stablu su `bb`, `bn`, `wb`, `wn`, `wr` u CRLF obliku, blobovi su LF, i
`git status --porcelain` je prazan. Uzrok je izmeren, ne pretpostavljen: unos u indeksu
za `wn.svg` nosi `size: 1325`, što je veličina **CRLF** fajla na disku. Git poredi stat
pre sadržaja, nalazi poklapanje i sadržaj nikad ne pročita.

Kako su tu dospeli, izvedeno iz izmerenog: `.gitattributes` i svih 12 SVG-ova ušli su
**istim commitom** (`cb60748`, `git log --diff-filter=A`), ali `-text` u trenutku
`git add`-a nije važio — da jeste, blob bi nosio CRLF, a nosi LF. Tih pet je dakle na
disku već bilo u CRLF obliku i git ih je pri `add`-u normalizovao u LF, dok je `sha1` za
`LICENSE.txt` računat sa diska. **Zašto je pet od dvanaest bilo CRLF na disku nije
utvrđeno** — alat kojim su preuzeti nije meren.

> Ovo je jedino što razdvaja zapis „58 OK" iz 0.9 od pet padova na klonu. Razlika između
> dva merenja imenuje pokretni deo (CONVENTIONS §1): nije platforma, nije `autocrlf`,
> nego **koji bajtovi su na disku** — a to je kod autora slučajan ostatak, kod svakog
> drugog ono što je commitovano.

**3. Poruka uz pad pogrešno dijagnostikuje.** `CAUSE` u `tests/test_assets.py` glasi:
„The recorded sha1 values hold only while .gitattributes keeps git from rewriting line
endings… with core.autocrlf=true a checkout turns LF into CRLF and every sha1 differs."
Merenje 1 pokazuje da je `.gitattributes` ispravan, da checkout **ne** pravi CRLF, i da
se ne razlikuje „svaki" nego tačno pet. Kapija radi — njena dijagnoza ne. Nalaz se ovde
zavodi; ispravka ide uz R9, jer ista rečenica stoji u tri dokumenta.

**4. Ista tvrdnja je netačna i van testa.** `assets/pieces/LICENSE.txt` kaže „The sha1 is
of the SVG file as committed here", a ADR-039 u „Posledicama" kaže da `sha1` iz
`LICENSE.txt` važi na svakoj platformi i proverava se običnim `sha1sum`-om nad fajlom
koji je pred očima. Za pet od dvanaest fajlova nijedno od toga ne stoji. ADR-039 zato
dobija ⚠️ po ADR-045, sa pokazivačem na ovaj odeljak; telo ADR-a ostaje netaknuto.
`LICENSE.txt` se u ovom tasku **ne dira** — to je proizvod, i pripada R9.

**5. Šta je od neizmerenog zatvoreno.** `core.autocrlf` na ovoj mašini je `true` (T1).
Red checkpointa na Windows klonu je izmeren (T2). Oblik komande iz §8 se pod Claude
Code-om izvršava doslovno, jer je Bash alat Git Bash (T3 — ali samo za ovu sesiju; šta je
„ljuska projekta" kao propis ostaje R1). MEMORY folder je i dalje prazan (T4 — merenje
važi za ovaj trenutak, ne za ceo period od `b8a35dc`, pa ADR-047 tačka 2 nije potvrđena,
samo nije oborena). `pip install -e ".[dev]"` u praznom venv-u na Windows-u prolazi (T5).
Upit po dozvolama tražile su `git clone`, `python -m venv` i `pip install`, a uz njih i
**pozivi punom putanjom iz klona** (`…/.venv/Scripts/python.exe -m unittest`, `ruff`) —
sve četiri predviđene u T6, nijedna nije bila STOP. Sadašnja rečenica je imenovala samo
tri komande; četvrta kategorija se ovde dopisuje.

**6. `ruff format --check .` ne dokazuje ništa o ovom tasku.** `extend-exclude =
["docs"]` (ADR-035) izbacuje ceo domen izmene. Kapija se pokreće jer je CONVENTIONS §9
traži, ali njen zeleni ishod ovde nije dokaz.

### Presude

- **Kraj faze iz WORKFLOW §8 ne važi za fazu 0.** Obrnuti pregled je pregled koda, a faza
  0 ga nema — nijedan `core/` modul još ne postoji. Prvi stvarni obrnuti pregled je na
  kraju faze 1. Presuda se zapisuje izričito, sa opsegom, da se ne bi čitala kao tiho
  preskakanje.
- **Red checkpointa nad svežim klonom ponavlja se jednom**, nad poslednjim `main`-om pre
  grane `faza-1`. Odluka se zapisuje sada, izvršava posle REZ-a.
- **Izlazni kod provere iz §8 nije dokaz bez broja ulaznih putanja**, dok R1 ne uđe. Zato
  oba merenja u tabeli nose i broj ulaza; prazan ulaz bi se prijavio kao „nije imala
  ulaz", nikad kao čisto.
- **Pet padova se u ovom tasku ne popravlja** — ni u `assets/`, ni u testu, ni u ADR-u.
  Ispravka je zaseban task, sa rokom pre 1.1 (R9). Razlog za rok: checkpoint faze je po
  `PROJECT.md` §9 objektivan uslov, a ovaj ne prolazi kod nikoga osim kod autora.
- **Zatečeno stanje ostaje netaknuto** (ADR-046): nijedan fajl u `assets/` nije diran,
  ni u radnom stablu ni u klonu, a korpusi van gita se samo mere.

### Grana koja se ovde ne pravi

`faza-1` se ne otvara u ovom tasku. Između checkpointa i 1.1 stoji REZ — osam stavki
(R1–R8) u `ROADMAP.md`, „Otvoreno", sve pravila i presude. **R9 nije REZ stavka**: REZ
seče pravila, a ovo je kvar u proizvodu, i prvo što čitalac ovog repoa uradi jeste klon.
Zato mu je rok **pre 1.1**, nezavisno od REZ-a.

### Pitanja

**1. ADR-045 traži ⚠️ na oborenom ADR-u, a telo ostaje netaknuto. Ista netačna tvrdnja
stoji i u `assets/pieces/LICENSE.txt` i u `CAUSE` poruci testa. Zašto ⚠️ ide samo na ADR,
a druga dva mesta čekaju R9 — i šta bi se izgubilo da su sva tri ispravljena sada?**
Znao. To su dve različite radnje. ⚠️ je **zapis o merenju**: ne menja telo ADR-039, ne
dira proizvod, i ide odmah, jer ADR koji je oboren a ćuti o tome je gori od ADR-a koga
nema — veruje mu se. `LICENSE.txt` i `CAUSE` su **proizvod**: tamo se menjaju bajtovi
koje test proverava i rečenica koju kapija ispisuje. To je ispravka, a checkpoint meri i
zapisuje, ne popravlja. Ispravkom sada gube se tri stvari: commit bi mešao klasu merenja
sa klasom ispravke, pa bi se `git diff` čitao kao dva taska odjednom; ispravka
`LICENSE.txt`-a traži presudu **koje bajtove proglašavamo tačnim** (disk ili blob) i da
li se radno stablo renormalizuje — odluka koja zaslužuje svoj plan i svoja pitanja; i R9
bi nestao kao red u „Otvoreno", pa bi rok „pre 1.1" prestao da postoji kao obaveza
vidljiva u gitu.

**2. Klon je dao pet padova, radno stablo `58 OK`. Po CONVENTIONS §1 oba ulaze u zapis.
Koje merenje je dokaz o proizvodu, a koje o nečem drugom — i šta bi čitalac pogrešno
zaključio da je ostalo samo jedno?**
Znao, i preko onoga što je pitano. **Klon je dokaz o proizvodu**: u njemu su tačno
commitovani bajtovi i ništa drugo, i on kaže da repozitorijum ne prolazi sopstvene
testove. Radno stablo nije dokaz o proizvodu nego **o jednom disku** — ono meri istoriju
te mašine, pet fajlova koji su tu ostali od `add`-a u 0.4. Da je ostalo samo radno
stablo, čitalac bi zaključio da je faza 0 zatvorena i checkpoint ispunjen, a mentor bi to
oborio prvim klonom. Da je ostao samo klon, tražio bi kvar u kloniranju ili u
`autocrlf`-u, dakle u `.gitattributes`-u koji je ispravan — i nikad ne bi saznao zašto
„58 OK" iz 0.9 nije laž. Tek oba zajedno imenuju pokretni deo: nije platforma, nego koji
su bajtovi na disku.

**3. `git status` je prazan iako se pet fajlova razlikuje od svojih blobova. Koja provera
bi ovo uhvatila, i zašto je baš ovaj oblik kvara opasniji od pada koji se vidi odmah?**
Znao, i uopštio preko pitanja. Uhvatila bi ga svaka provera čiji domen nisu bajtovi na
disku nego **bajtovi u gitu**: `git ls-files --eol` nad `assets/pieces/svg/`, `sha1` nad
izlazom `git cat-file blob` umesto nad fajlom, ili — najjeftinije — pokretanje suite-a na
svežem klonu, što je upravo ono što checkpoint uvodi. `git status` ovde nije zakazao: on
poredi stat pre sadržaja, stat se poklapa, pa **deli sudbinu sa kvarom od kog bi trebalo
da štiti** (CONVENTIONS §5). Pad koji se vidi odmah košta minut i sam nosi dijagnozu.
Ovaj oblik ne troši ništa, jer sve kapije stoje zelene — i to zeleno se svakim commitom
potpisuje kao dokaz. Kvar živi tačno onoliko dugo koliko niko ne klonira repo, a kad se
pojavi, pojavi se na tuđoj mašini, gde dijagnoza više nije tvoja — a ovde je uz to bila i
pogrešna, jer je `CAUSE` sve vreme pokazivao na `autocrlf`.

---

## R9 — pet sha1 vrednosti

Checkpoint faze 0 je ostavio `main` u stanju u kom ne prolazi sopstveni uslov: pet
subtestova `test_every_svg_matches_its_recorded_sha1` pada na svežem klonu. Ovaj task to
popravlja. Checkpoint je merio i zapisivao; ovde se prvi put dira proizvod.

### Merenja

Sva su izvedena 20. 9. 2026, Windows 11, git 2.54.0.windows.1, Python 3.11.9,
`core.autocrlf=true`, nad `b716eb4`.

| Merenje | Uslovi | Ishod |
|---|---|---|
| M1 — tri otiska po fajlu | radno stablo, samo čitanje; `sha1sum` nad diskom, `git cat-file blob HEAD:…`, vrednost iz `LICENSE.txt` | za `bb`, `bn`, `wb`, `wn`, `wr`: disk == zapisano, blob != zapisano; za ostalih sedam sve tri jednake. Veličine diska 1282/1620/1282/1325/1198, blobova 1270/1598/1270/1306/1173 |
| M2 — priroda razlike | isto | `sha1` bloba propuštenog kroz `sed 's/$/\r/'` jednak je `sha1`-u diska za svih pet; `tr -d '\r\n'` daje isti `sha1` za blob i disk. Razlika je **isključivo** u prelascima reda |
| M3 — šta Commons prijavljuje | Commons API, `prop=imageinfo&iiprop=sha1\|size`, tekuća revizija fajla; čitano kroz alat koji stranicu pretvara u markdown, ne preuzimanjem bajtova | prijavljeni `sha1` jednak zapisanom za svih pet; prijavljena veličina jednaka veličini **CRLF** fajla (1325/1282/1198/1620/1282). Kontrolni `wp`: `sha1` zapisan, veličina 766 na obe strane |
| **Korak 2 — preuzimanje** | `curl.exe -sS -L` sa `https://commons.wikimedia.org/wiki/Special:FilePath/<ime>`, binarno, u scratchpad; pet spornih + `wp` kao kontrola | **preuzeto == zapisano** za svih pet, i **preuzeto != blob**. Kontrolni `wp`: preuzeto == zapisano == blob |
| broj CR i LF bajtova | nad preuzetim, blobom i radnim stablom | preuzeto i radno stablo: CR=LF za svih pet (19/12/25/22/12); blob: CR=0. `wp`: CR=0 svuda |
| preuzeto naspram radnog stabla | `cmp` | bajt u bajt jednako za svih pet |
| posle `git add`-a | `git cat-file blob :<putanja>` | svih **12** blobova u indeksu jednako zapisanom u `LICENSE.txt`; `git ls-files --eol` daje `i/crlf w/crlf attr/-text` za tih pet, `i/lf w/lf attr/-text` za ostalih sedam |
| suite i ruff, radno stablo | isto okruženje | `Ran 58 tests` → `OK`; `All checks passed!`; `22 files already formatted` |
| **kapija taska — svež klon** | klon ovog commita pre dopune ova dva pasusa, iz lokalnog repoa u scratchpad, nov venv, `pip install -e ".[dev]"`, pozivi punom putanjom; Windows 11, Python 3.11.9, pip 24.0, git 2.54.0.windows.1, `core.autocrlf=true` | `git ls-files --eol` u klonu: `i/crlf w/crlf attr/-text` za tih pet, `i/lf w/lf attr/-text` za ostalih sedam — dakle `-text` radi **u oba smera**. `Ran 58 tests` → `OK`; `All checks passed!`; `22 files already formatted` |
| **kapija taska — klon sa GitHub-a** | klon `8f39d6e` sa `github.com/Steevs11/chess`, nov venv, `pip install -e ".[dev]"`, pozivi punom putanjom; Windows 11, Python 3.11.9, git 2.54.0.windows.1, `core.autocrlf=true`, 20. 9. 2026 | `Ran 58 tests` → `OK`; `All checks passed!`; `22 files already formatted` |

**Dva preuzimanja od šest vratila su Wikimedia stranicu greške** (`bb` 1964 B, `wp` 2172 B
umesto 1282 i 766). Ponovljeno sa `--retry 3` i opisnim `User-Agent`-om → `http=200` i
tačne veličine. To nije bio S2: adresa je bila ispravna, odgovor privremen. Razlika u
veličini je ono što je kvar pokazalo, pre nego ijedan `sha1`.

### Presuda: grana A

Preuzeti bajtovi nose CRLF i njihov `sha1` je tačno ono što `LICENSE.txt` zapisuje. Dakle
**zapisane vrednosti su bile tačne sve vreme**; ono što u repozitorijumu nisu bili preuzeti
bajtovi jesu **blobovi**. To potvrđuje nalaz 2 iz „Checkpoint faze 0" (normalizacija pri
`git add`-u u 0.4, pre nego što je `-text` počeo da važi) i obara poslednju rečenicu
nalaza 1.

Ispravka je zato **vraćanje originalnih bajtova**, ne prepisivanje vrednosti. Grana B
(prepisati pet `sha1` vrednosti na otiske blobova) je odbijena merenjem, ne ukusom — ona
bi u `LICENSE.txt` upisala otiske bajtova koje Commons nikad nije isporučio, i time
oborila i uvodni red („compared against the sha1 Commons reports") i red 182 („byte for
byte as downloaded"). Uz to bi tražila svoj ADR, jer je blizu alternative koju je ADR-039
izričito odbio, i vraćanje radnog stabla na LF, jer test čita disk.

### Šta je izmenjeno

- `assets/pieces/svg/` — pet fajlova vraćeno na preuzete bajtove. **Nijedna `sha1`
  vrednost u `LICENSE.txt` nije dirana.**
- `assets/pieces/LICENSE.txt`, pasus iznad tabele — imenuje stvarni kvar i mešavinu
  prelazaka reda; više ne tvrdi „every sha1 below would differ", što je izmereno kao
  netačno na dva načina (checkout uz `autocrlf=true` daje LF za svih 12, a razlikovalo se
  pet).
- `tests/test_assets.py` — `CAUSE` i docstring modula. **Provera se ne menja**: domen,
  broj subtestova i tvrdnja su isti; menja se samo rečenica koju kapija ispisuje. Obe sada
  imenuju **oba** uzroka i kažu šta da se izmeri (`git cat-file blob`, `git ls-files --eol`).

### Šta je zatvoreno od neizmerenog

- **T3 iz plana** („zašto je pet od dvanaest bilo CRLF na disku") — plan ga je proglasio
  verovatno nerekonstruisanim. Zatvoren: takvi su **na Commons-u**. Alat preuzimanja i
  dalje nije poznat, ali više nije potreban da bi se objasnilo pet CRLF fajlova.
- **T2** („da li Commons isporučuje bajt u bajt isti fajl") — zatvoren za 20. 9. 2026:
  isporučuje. Ne tvrdi se ništa o drugim datumima.
- **N4 iz plana** — treća tvrdnja `LICENSE.txt`-a („matches the value Commons reports")
  izmerena je prvi put, kroz M3 i korak 2. Stoji.

### Šta ostaje neizmereno

- **T1 iz plana.** Permalinkovi u `LICENSE.txt` su oblika `index.php?…&oldid=…` — to je
  permalink **stranice opisa**, ne fajla, i vraća HTML. `LICENSE.txt` to kaže tačno („the
  exact revision whose license block and author line were read"), ali `oldid` ne zakucava
  reviziju binarnog fajla. Bajtovi su zato uzeti sa `Special:FilePath/`, koji uvek daje
  **tekuću** reviziju. Da Commons sutra zameni fajl, zapisan `sha1` bi to prijavio, ali
  permalink ne bi vratio stari bajt. Nije rešeno ovde.
- Da li ijedan drugi alat u lancu (editor, arhiva, veb klijent iz faze 4) dira prelaske
  reda u `assets/pieces/svg/`. Nije mereno.

### Redosled kapije i commita

Kapija svežeg klona vidi samo **commitovano** stanje, a CONVENTIONS §9 commit stavlja
poslednji. Zato je commit napravljen prvi, pa je klon meren nad njim, pa je ishod klona
dopisan u ovaj fajl i u `ROADMAP.md` i commit je izmenjen sa `--amend` — dozvoljeno, jer
istorija do `push`-a stoji samo lokalno (CONVENTIONS §8). **Šta to znači za dokaz:** klon
je meren nad stablom koje se od konačnog razlikuje samo u dva pasusa u `docs/`, koje ne
čita nijedan test. Ista razlika nad `src/`, `tests/` ili `assets/` tražila bi ponovljeno
merenje. **Ta ograda više ne važi:** isti red checkpointa izmeren je i nad konačnim
stablom, klonom sa GitHub-a (red u tabeli iznad).

### Pitanja (ADR-021, korak 4)

**1. Grana B bi prepisala pet `sha1` vrednosti na otiske blobova i test bi na svežem klonu
prošao. Zašto to ipak nije ispravka, nego zamena jednog kvara drugim — i koju tvrdnju iz
`LICENSE.txt` bi oborila, a da je test nikad ne bi prijavio?**

Znao. Test proverava samo **prvu** od tri tvrdnje — poredi disk sa zapisanim brojem. Grana
B bi prvu učinila tačnom tako što bi drugu („računat iz preuzetih bajtova") i treću
(„poklapa se sa onim što Commons prijavljuje") učinila netačnim, uz red 182 („byte for
byte as downloaded"), i nijedna kapija to ne bi prijavila, jer nijedna ne ide do Commons-a.
To je isti oblik kvara koji R9 popravlja, prebačen sa bajtova na tvrdnje: zeleno koje ne
znači ono što čitalac misli da znači. Preko pitanja: `LICENSE.txt` nije naš dokument — u
njemu smemo da zapišemo šta smo preuzeli, ne da izmislimo otisak koji izvor ne bi
potvrdio.

**2. `git add` je u koraku 3 morao ponovo da pročita sadržaj tih pet fajlova, iako se
nijedan bajt na disku nije promenio. Zašto to nije bilo sigurno unapred, i šta bi se
videlo u kapiji 3.4 da se nije desilo?**

Znao, i preko onoga što je pitano. `git add` prvo poredi stat iz indeksa sa statom fajla —
veličinu i `mtime` — i ako se poklope, sadržaj ne čita. Ovde je **veličina bila jednaka na
obe strane**, jer je indeks od 0.4 nosio CRLF veličinu, pa je jedini razlog da pročita
bajtove bio nov `mtime` od `cp`-a. Da je `cp` sačuvao vreme (`-p`), **ili da je
granularnost `mtime`-a progutala razliku**, `add` bi bio no-op: kapija 3.4 bi za tih pet i
dalje vraćala stare LF otiske — `56444929…` umesto `126b7779…` za `wr` — i to bi bio S3.
Zato kapija stoji nad `git cat-file blob :<putanja>`, dakle nad **indeksom**: disk je bio
tačan i pre `add`-a i ništa ne bi dokazao.

**3. Nova `CAUSE` poruka imenuje dva uzroka i dve komande umesto jednog uzroka i jedne
provere. Zašto je poruka koja nudi merenje bolja od poruke koja nudi zaključak — iako je
stara bila kraća i, za slučaj koji opisuje, tačna?**

Znao. Stara poruka je bila tačna za jedan slučaj, a čitalac je ne dobija kad zna koji je
slučaj — dobija je kad ne zna. Tvrdila je uzrok umesto da ga imenuje kao jedan od mogućih,
pa je svakog ko je naleteo na pravi kvar slala da proverava `.gitattributes`, koji je sve
vreme bio ispravan. **Kratka poruka koja pogađa devedeset posto slučajeva u preostalih
deset radi gore nego nikakva**, jer nosi autoritet i skreće sa traga. Nova imenuje oba
kraja na kojima git može da prepiše bajtove i uz svaki daje komandu čiji ishod razdvaja
jedan od drugog. Isto pravilo po kom projekat piše sve ostalo: tvrdnja bez merenja iza
sebe je pretpostavka, i kad stoji u poruci o grešci.

---

## REZ — osam stavki iz „Otvoreno"

Checkpoint faze 0 je ostavio osam stavki (R1–R8) u `ROADMAP.md`, „Otvoreno": tri imenuju
normu bez doma ili opis širi od domena, pet traže presudu. REZ ih zatvara u **dva commita,
bez ijedne linije koda** — menja se samo `docs/`. R1 ne ide sada; rok mu je najkasnije 1.8
i red u „Otvoreno" ostaje nepromenjen.

### Šta je dobilo dom (commit 1)

| Norma ili pravilo | Odakle | Dom |
|---|---|---|
| test ne poziva spoljni program (R2) | nigde — nalaz iz 0.9 | CONVENTIONS §5 „Izolacija" |
| raspored opisuje K1 šire od domena (R3) | CONVENTIONS §5 „Raspored" | isti red, sužen na `assets/**/*.json`, `src/**/*.py`, `docs/**/*.md` |
| razgovor sa arhitektom → srpski | instrukcije Projekta; 0.8 ga ostavio van gita | WORKFLOW §1 „Predaja teksta" |
| planski chat sam učitava fajl iz repoa | instrukcije Projekta | WORKFLOW §1; zakucavanje na SHA ostaje u CONVENTIONS §8 |
| kod se prvo objašnjava, pa prepravlja | instrukcije Projekta | WORKFLOW §1; podela poslova ostaje u PROJECT §8 |
| nacrt odgovora na korak 4 sastavlja planski chat | instrukcije Projekta | WORKFLOW §1 |
| konkretno i kratko | instrukcije Projekta | WORKFLOW §1 |
| izbor opcije u dve-tri rečenice; problem u diffu = STOP | instrukcije Projekta | WORKFLOW §1 |
| checkpoint se meri na svežem klonu (R9) | presuda iz „Checkpoint faze 0" | PROJECT §9 |

Sedma rečenica iz instrukcija Projekta — šta planski chat vidi — **ne seli se**: keširana
činjenica po testu razlikovanja (ADR-047, tačka 3). Instrukcije Projekta su **četvrti
korpus** i do ovog commita nisu bile pod kriterijumom ADR-044; ADR-047 zato dobija ⚠️ po
ADR-045.

### Merenje: da li ijedan test poziva spoljni program (R2)

Uslovi: radno stablo nad `4b087ee`, čisto; Windows 11, Git Bash, GNU grep 3.0, git
2.54.0.windows.1, Python 3.11.9, `core.autocrlf=true`, 21. 9. 2026. Mereno **pre** ijedne
izmene ovog commita.

```
grep -rnE "subprocess|os\.system|os\.popen|popen|Popen|shutil\.which|os\.exec|os\.spawn" tests/
git ls-files "tests/*.py"
```

| Šta je brojano | Kako | Broj |
|---|---|---|
| praćeni `.py` fajlovi u `tests/` | `git ls-files "tests/*.py"` | **11** |
| test moduli među njima | isto, bez `__init__.py` | **6** |
| pogodaka grepa | izlaz `1`, nijedan red ispisan | **0** |

Šest modula: `client/test_i18n`, `test_assets`, `test_check_commit_trailers`,
`test_encoding_bytes`, `test_layers`, `test_package`; ostalih pet su `__init__.py`. **Go
broj bez definicije šta je brojano nije merenje** — zato stoje oba broja i pravilo po kom
su dobijena.

**Referentno merenje** (planski chat, Linux klon `4b087ee`): isti brojevi — 11 praćenih
`.py`, 6 test modula, 0 pogodaka. Oba merenja stoje jedno pored drugog, svako sa svojim
uslovima (CONVENTIONS §1). Poklapaju se, pa ovde nema pokretnog dela koji bi se imenovao.

Prvi unapred imenovan STOP iz plana — „grep nađe test koji poziva spoljni program" — **nije
se okinuo**.

### Nalaz: pokazivač koji je pokazivao na prazno

`tests/test_check_commit_trailers.py:3–4` od 0.9 citira „CONVENTIONS 5, 'Izolacija'" kao
razlog zašto `tests/` nema zavisnost od spoljnog programa — a to pravilo tamo do ovog
commita **nije stajalo**. R2 dakle ne uvodi novo pravilo nego zatvara pokazivač na
nepostojeći tekst. Isti razred kao tvrdnje bez doma iz 0.7 i 0.8, samo u suprotnom smeru:
ovde je kod pokazao na `docs/`, a ne `docs/` na kod. Nijedna kapija to ne hvata; uhvatio ga
je grep za R2.

### Šest grepova (R4)

Isti uslovi i isti trenutak kao merenje iznad. Svaki obrazac nosi bar dve formulacije pojma
(CONVENTIONS §5, „odsustvo se meri"). Domen je `docs/`, uključujući tabele u §0.8 i §0.9
ovog fajla, koje su pregledane posebno. **Upisani su broj pogodaka i mesta, nikad pogođeni
red.** Oba smera: iz norme u `docs/` obrascem, pa iz svakog pogotka nazad u normu — pogodak
koji nije pročitan ne razlikuje dom od šuma.

| # | Norma | Obrazac | Pogodaka | Mesta koja nisu šum | Presuda |
|---|---|---|---|---|---|
| 1 | razgovor sa arhitektom → srpski | `srpsk\|razgovor` | 18 | CONVENTIONS:10; faza-0 §0.8:1345 i :1377 | **nema dom**: :10 pokriva dokumentaciju i interfejs, ne jezik razgovora; :1377 je vodi kao „ostaje van gita" |
| 2 | planski chat sam učitava fajl, zakucan na SHA | `SHA\|zakuca\|lepi\|lepljen\|raw\.githubusercontent` | 15 | CONVENTIONS §8:710 i :714; DECISIONS:346 (ADR-020, Posledice) | **dom za zakucavanje postoji** → pokazivač; ko učitava nema dom, jer ADR-020 nudi mogućnost, ne zahtev |
| 3 | kod se prvo objašnjava, pa prepravlja | `prepravl\|prepravi\|pregled diff\|objasni.*pa` | 14 | PROJECT §8:356 | **dom za podelu poslova postoji** → pokazivač; redosled nema dom |
| 4 | nacrt odgovora na korak 4 sastavlja planski chat | `korak 4\|koraka 4\|nacrt\|sastavlja` | 27 | WORKFLOW:23 i :26; ADR-021 korak 5 | **nema dom**: :23 govori o tekstu koji se predaje Claude Code-u, ne o odgovorima na korak 4 |
| 5 | konkretno i kratko | `kratk\|konkretn\|sažet\|sazet` | 14 | — | **nema dom**; svi pogoci su o drugim predmetima |
| 6 | izbor opcije u dve-tri rečenice | `opcij\|bira između\|biraš\|izbor između` | 1 | — | **nema dom**; jedini pogodak (CONVENTIONS:96) je o pisanju ADR-a |

Dva pogotka za normu 4 u `ROADMAP`-u (:41, :44) su redovi REZ R4 i R6, koje ovaj commit
briše, odnosno commit 2 rešava. Ni jedan ni drugi nisu dom — to je opis zadatka, ne pravilo.

### Presuda: tabela u WORKFLOW §1 se ne dira

Tabela odgovara na pitanje **koja površina radi koju radnju**. Nijedna od šest normi na to
pitanje ne odgovara: pet ih propisuje kako se radi unutar površine ili kako se tekst
predaje, a šesta (kod se prvo objašnjava) je redosled unutar radnje koju tabela već nosi
(„Objašnjenja, 'ne razumem ovaj kod'"). Red bi zato bio duplikat, ne rutiranje. Red
„Provera da si razumeo (ti pričaš, Claude ispituje)" se **ne dira**: to je provera na kraju
faze, isti oblik kao WORKFLOW §8, korak 1, i nijedna nova rečenica je ne dodiruje.

### Pitanja (ADR-021, korak 4) — commit 1

**1. R2 je napisan kao zahtev sa opsegom, a ne kao mašinski proverivo „nijedan test ne
uvozi `subprocess`". Zašto je izabrana formulacija koju nijedna kapija ne hvata?**

Znao. Proveriva formulacija bi propisala **mehanizam**, a mehanizama za pokretanje procesa
ima koliko i imena funkcija — `subprocess`, `os.system`, `os.popen`, `shutil.which`,
`os.exec*`, `os.spawn*`, pa i `importlib` nad skriptom koja sama zove ljusku. Kapija nad
spiskom imena hvata tačno taj spisak; prvi test koji proces pokrene sedmim imenom prolazi
kroz nju zelen, pa pravilo pada **tiho** — isti razred kvara kao provera koja ćuti kad nema
ulaz. Zahtev sa opsegom ne stari sa spiskom: kaže šta ne sme i gde važi, pa i nov način
pokretanja procesa pada pod njega bez izmene pravila.

> Cena je poznata i prihvaćena: norma nema kapiju i oslanja se na pregled diffa. Zato
> spisak imena stoji **u zapisu, kao domen merenja**, a ne u pravilu.

**2. R3 je sužio red u §5, a test nije diran — provera je i pre i posle identična i 58
testova prolazi oba puta. U čemu je onda bio kvar, i šta bi se pokvarilo da smo umesto reda
proširili test na ceo `assets/`, `src/` i `docs/`?**

Znao, i preko onoga zbog čega je pitanje postavljeno. **Kvar je bio u čitaocu, ne u kodu.**
Red je tvrdio da K1 pokriva `assets/`, `src/` i `docs/` cele, a `PATTERNS` pokriva samo
`*.json`, `*.py` i `*.md` u njima. Ko doda `.svg` u `assets/` ili `.txt` u `docs/` i
pročita taj red, veruje da ga kapija čuva — a ne čuva ga. Razred je „zeleno kod autora nije
dokaz": provera je zelena zato što je **uža nego što dokument tvrdi**, i ćuti tamo gde
čitalac očekuje da progovori.

Širenje testa bi pokvarilo dva mesta. **Prvo**, test bi čitao i binarne fajlove — pet
SVG-ova sa CRLF-om, TTF font, PNG-ove — pa bi ili padao na njima ili dobio izuzetke po
tipu, čime bi **opet** postao uži od tvrdnje, samo skriveno u kodu umesto u dokumentu.
**Drugo**, menjali bismo kapiju da bismo popravili rečenicu: domen K1 je regresioni,
izabran po mestima gde je kvar iz 0.5 stvarno udario, i njegovo širenje je odluka koja
traži merenje da BOM tamo može da promeni ishod — a to merenje ne postoji. Jeftinije je i
poštenije da dokument kaže istinu o proveri nego da se provera rasteže da bi dokument
ostao tačan.

**3. Tri od šest normi nose pokazivač umesto ponovljenog pravila, iako bi ponovljena
rečenica bila čitljivija na mestu gde stoji. Zašto je pokazivač uslov da norma preživi, a
ne samo šteda u redovima?**

Znao. **Kopija ima svoj životni vek.** Ponovljena rečenica je tačna na dan upisa i počinje
da truli čim se original promeni — a niko ne zna da mora da je menja, jer propagacija prati
ADR, ne njegove prepise. Projekat to već ima izmereno: pravilo u korpusu van gita nabrajalo
je **tri** uslovna STOP-a, a ADR-046 ih ima **četiri**; kopija je bila čitljiva i pogrešna
(0.9, „Devet pravila, ne sedam"). Pokazivač ne može da zastari na taj način: ako se
CONVENTIONS §8 promeni, WORKFLOW i dalje upućuje na tačan tekst. Gubi se jedan skok
pogledom; dobija se to da dokument ne može da zaostane a da to niko ne primeti — a to je
tačno kvar koji ADR-044 zove gorim od dokumenta koji ne postoji.

### Presude (commit 2)

**R5 — budžet u redovima ostaje merenje, ne postaje norma.** Budžet iz §0.9 odradio je
svoje u tasku u kom je postavljen. Norma bi tražila sledećeg potrošača, a njega nema:
korpusi van gita su svedeni, faza 1 je kod, a broj redova u `docs/` o kodu ne tvrdi ništa.
Ostaje zapisan tamo gde je i izmeren.

**R6 — u ADR-021 se ne menja ništa.** Korak 4 kaže „o upravo napisanom kodu", a 0.7–0.9,
checkpoint, R9 i REZ kod ne pišu. To nije sukob nego **praznina**: ADR je pisan iz taska
koji piše kod i drugi slučaj nije predvideo. Telo se ne dira i ⚠️ ne dobija — ADR-045
pokriva merenje koje obara tvrdnju, a ovde ništa nije oboreno. Praznina se popunjava jednom
rečenicom u WORKFLOW §2, uz mesto gde se korak 4 izvodi.

**R7 — `settings.json` sme biti stroži od CONVENTIONS §8.** Dve liste odgovaraju na
različita pitanja: §8 kaže šta je **projektu** zabranjeno, `settings.json` šta izvršilac
sme **bez pitanja** (ADR-044, tri odredišta). Zabrana šira od §8 — `push --force` nad
svakom granom, a ne samo nad `main`-om — zato nije neslaganje nego uža kapija, a dozvola za
`git show` i `git switch`, koje §8 ne pominje, nije rupa. Sukob bi postojao samo u jednom
smeru: da `settings.json` pusti bez pitanja ono što §8 zabranjuje. Ni §8 ni `settings.json`
se u ovoj sesiji ne diraju.

**R8, prva polovina — razlog granice K1 stoji ovde, ne u docstringu testa.** Domen
`assets/**/*.json`, `src/**/*.py` i `docs/**/*.md` nije izveden iz načela nego iz mesta
gde je kvar iz 0.5 udario: provera je **regresiona**. `tests/` i `tools/` ostaju van dok se
ne izmeri da BOM tamo može da promeni ishod — dok tog merenja nema, širenje domena bi bilo
pretpostavka sa zelenom kapijom. Docstring nosi tvrdnju koju test proverava; razlog izbora
domena nije tvrdnja o bajtovima i tamo bi bio treća verzija iste rečenice, koju nijedna
kapija ne drži u skladu sa ostale dve (§0.9, „Ostale presude u toku taska").

**R8, druga polovina — `WORKFLOW.md` je van ranga, sa klauzulom sudara.** Ne ulazi u
hijerarhiju iz CONVENTIONS §1 jer ne propisuje proizvod nego tok rada, ali ne sme da
protivreči nijednom dokumentu sa liste; kad se sudare, pobeđuje dokument sa liste.
Propagacija ga je i pre ovog commita obavezivala — §1, „Pravilo propagacije (ADR-030)",
pasus „Proširenje" — pa red ne uvodi obavezu nego imenuje ko pobeđuje kad obaveza zakaže.

**„canonical" u `assets/pieces/LICENSE.txt` — ostaje otvoreno, bez roka.** Nalaz iz 0.6:
taj fajl svoje odricanje naziva kanonskim, a kanonski SPDX oblik glasi drugačije. Tuđi je
dokument, nijedan test ga po toj reči ne čita, i ne stoji ni na jednom putu do partije. Red
u „Otvoreno" ostaje; rok se ne postavlja, jer rok bez posledice je obećanje, ne obaveza.

### Šta je ostalo van REZ-a

**R1** — provera iz §8 prepisana u Python, po uzoru na K2. Ne ide sada; rok je najkasnije
1.8 i red u „Otvoreno" je nepromenjen, zajedno sa klauzulom da radna zamena za PowerShell
živi van repoa dok R1 ne uđe. Razlog odlaganja: R1 piše alat i test, a REZ je seča pravila
— to su dva taska, ne jedan.

Svaki nalaz koji je REZ otvorio ušao je u „Otvoreno", nijedan nije rešen u istoj sesiji.

### Pitanja (ADR-021, korak 4) — commit 2

**1. R6 je popunjen jednom rečenicom u WORKFLOW §2, a ADR-021 nije dirao — ni telo, ni ⚠️.
Zašto oznaka ne ide, iako korak 4 pet taskova zaredom nije izveden onako kako ADR kaže?**

Znao, i imenovao cenu koju pitanje nije tražilo. ⚠️ po ADR-045 nosi **merenje koje obara
tvrdnju**, a ovde ništa nije oboreno. ADR-021 tvrdi da se korak 4 ne preskače i da pitanja
idu o „zašto"; obe tvrdnje su u 0.7–0.9, checkpointu, R9 i REZ-u ispunjene — pitanja su
postavljena i odgovorena svaki put. Ono što ADR nije rekao jeste **šta su pitanja kad koda
nema**: praznina u opsegu, ne pogrešna tvrdnja.

> Oznaka koja kaže „ovo je oboreno" tamo gde ništa nije oboreno **sama je netačna**, a ⚠️
> koji se stavlja preventivno gubi vrednost koju mu je dao slučaj iz R9 — čitalac prestane
> da ga čita kao alarm. Praznina se zato popunjava tamo gde se korak izvodi, a ADR ostaje
> ono što jeste: odluka zašto pitanja uopšte postoje.

**2. R7 ostavlja dve liste koje se ne poklapaju takvima kakve jesu. Šta bi moralo da se
desi da isto neslaganje postane kvar — i zašto se to ne vidi ni iz jedne liste ponaosob?**

Znao. Kvar nastaje **samo u jednom smeru**: da `settings.json` pusti bez pitanja ono što §8
zabranjuje — da se u dozvole doda `git reset --hard`, `rebase`, `clean -fd` ili
`push --force` nad `main`-om, ili da se neka od tih zabrana iz §8 ukloni dok dozvola
ostane. Tada zabrana i dalje piše u dokumentu, a izvršilac je krši bez ijednog upita, pa
pravilo postoji samo na papiru.

Iz jedne liste se to ne vidi zato što **nijedna ne tvrdi ništa o drugoj**: §8 govori šta je
projektu zabranjeno, `settings.json` šta izvršilac sme bez pitanja. Svaka je iznutra
dosledna i izgleda isto u oba slučaja — i kad je kapija uža i kad je šira. Razlika se vidi
tek kad se čitaju jedna uz drugu, a to ne radi nijedan test: `settings.json` nije u gitu i
nijedna kapija ga ne dohvata. Zato ovo i jeste presuda, a ne pravilo sa kapijom.

**3. Ovaj commit svodi blok „Ritam po tasku" na pokazivač, a red o tome da CONVENTIONS §1
prepričava ADR-030 i ADR-032 ostavlja u „Otvoreno" — isti kvar, ista sesija, dve sudbine.
Zašto to nije nedoslednost?**

Znao, sa dva razloga. **Prvi je mesto, ne kvar.** `ROADMAP` je plan i stanje; ritam po tasku
tu nije potreban da bi se plan čitao, pa je prepričavanje čist višak i uklanja se bez
ijedne posledice. `CONVENTIONS` §1 je vrh hijerarhije i propisuje propagaciju — ono što
tamo piše o ADR-030 i ADR-032 nosi pravilo koje se primenjuje na licu mesta, pa zamena
pokazivačem znači odlučiti **koliko teksta sme da ode a da odeljak i dalje bude izvršiv**.
To je presuda o dokumentu koji rangira sve ostale i traži svoj task.

**Drugi je obim.** REZ je imenovao osam stavki i za svaku postoji zapis zašto ulazi.
Rešavanje devetog nalaza usput je tačno ono što je plan zabranio. Red u „Otvoreno" znači da
je nalaz **imenovan, ne zaboravljen** — a to je i cela svrha tog bloka.

### Merenje: red checkpointa nad commitom 2

Klon commita `f818e0d` iz **lokalnog** repoa u scratchpad, van radnog stabla; nov venv,
`pip install -e ".[dev]"`, pa pozivi punom putanjom iz klona. Windows 11, Python 3.11.9,
pip 24.0, ruff 0.16.8, pygame 2.6.1, git 2.54.0.windows.1, `core.autocrlf=true`,
22. 9. 2026.

| Korak | Ishod |
|---|---|
| `git clone` | `HEAD` = `f818e0d`, `git status --porcelain` prazan, `core.autocrlf=true` |
| `pip install -e ".[dev]"` | `Successfully installed chess-0.1.0 pygame-2.6.1 ruff-0.16.8` |
| `…/.venv/Scripts/python.exe -m unittest discover -s tests` | `Ran 58 tests` → `OK` |
| `…/.venv/Scripts/ruff.exe check .` | `All checks passed!` |
| `…/.venv/Scripts/ruff.exe format --check .` | `22 files already formatted` |

Ovo je **treće** merenje reda checkpointa. Prva dva — `b8a35dc` sa pet padova i, posle R9,
zeleno — ostaju u `ROADMAP`-u i u „Checkpoint faze 0" (CONVENTIONS §1). Četvrti unapred
imenovan STOP iz plana, „klon nije zelen", **nije se okinuo**. REZ nije dirao `src/`,
`tests/` ni `assets/`, pa se zeleno odnosi na isti proizvod kao merenje posle R9.

**Ograda, i gde je uža nego u R9.** Klon je meren nad `f818e0d`, a konačan commit se od
njega razlikuje za redove dopisane u ovaj fajl i u `ROADMAP.md`. Od 58 testova te redove
čita **jedan** — `tests/test_encoding_bytes.py`, koji nad `docs/**/*.md` traži bajtove
`EF BB BF` **bilo gde** u fajlu. `ruff` ih ne čita uopšte (`extend-exclude = ["docs"]`), a
nijedan drugi test ne dodiruje `docs/`. Presuda te jedine kapije nad konačnim tekstom
izmerena je u radnom stablu neposredno pre `--amend`-a, a `git status` je posle amend-a
prazan, pa commit nosi iste bajtove. **Klon sam nije ponovljen: regres se imenuje, ne
zatvara.**

> Ista formulacija u R9 — „klon je meren nad stablom koje se od konačnog razlikuje samo u
> dva pasusa u `docs/`, koje **ne čita nijedan test**" — netačna je iz istog razloga: K1 ih
> čita. Nalaz je zaveden u `ROADMAP` „Otvoreno"; telo R9 ostaje kako je zapisano
> (CONVENTIONS §1, ADR-045).
