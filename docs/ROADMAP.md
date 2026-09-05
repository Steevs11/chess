# ROADMAP

Ovaj fajl je i plan i trenutno stanje. Claude Code ga ažurira na kraju svakog taska.

**Kako se koristi:** pročitaj blok TRENUTNO, pa prvi neodštikliran red. To je sledeći task.

> Verzija 3 — ažurirano posle tri kruga tehničkog pregleda.
> Izmene su obrazložene u `docs/DECISIONS.md` — svaka odluka nosi svoj ADR.

---

## TRENUTNO

```
Radimo:    0.9 — korpusi van gita se svode
Sledeće:   1.1 — core/types.py
Otvoreno:  .claude/rules/ traži restart posle ažuriranja — potvrđeno na v2.1.259,
           i dalje tvrdnja o tuđem sistemu, pa ostaje otvoreno
           MEMORY.md i samopišuće memorije van stabla — četiri korpusa, rešava 0.9
           tabela ugovora t() iz ADR-040 nije vezana ni za jedan test nad client/i18n.py
           indeks ADR-ova u DECISIONS.md, mašinski proveren u oba smera
           ritual šest namernih kvarova nije zaveden nigde od 0.4
           CONVENTIONS §2 nema red za client/__main__.py, ni komandu za pokretanje
           klijenta — obe čekaju task u kom se ta ulazna tačka napiše (3.1)
           CONVENTIONS §1 prepričava ADR-030 i ADR-032 umesto da pokazuje na njih
           blok „Ritam po tasku" u ovom fajlu prepričava ADR-021 — isti oblik
           gde se sastavljaju odgovori na korak 4 nije zapisano nigde
           settings.json: git show/switch nisu u §8; push --force širi nego §8
           assets/pieces/LICENSE.txt svoje odricanje zove „canonical" a nije (iz 0.6)
Grana:     main
```

---

## Legenda

- `[ ]` nije urađeno · `[x]` urađeno i commitovano
- Svaka podfaza = jedan task = jedna sesija = jedan commit
- **Checkpoint** je objektivan uslov. Ne prelazi se dalje dok ne prođe.

**Ritam po tasku (ADR-021):** plan mod → implementacija → objašnjenje u
3–5 rečenica → **2–3 pitanja korisniku o napisanom kodu** → odgovori → commit.
Korak sa pitanjima se ne preskače.

---

## FAZA 0 — Skelet
**Checkpoint:** `pip install -e ".[dev]"` pa `python -m unittest discover -s tests`
prolazi (uključujući `test_layers.py`), `ruff check .` i `ruff format --check .` čisti

- [x] 0.1 Struktura foldera, `src/chess/` sa `__init__.py`, `tests/`, `docs/`, `assets/`, `tools/`
- [x] 0.2 `pyproject.toml` sa **`pygame` kao zavisnošću**, `ruff` (`line-length = 100`),
      **`pip install -e ".[dev]"`**, prvi test
      > Bez editable instalacije `unittest discover` ne nalazi paket — `src/`
      > raspored znači da `src/` nije na `sys.path` (ADR-029).
- [x] 0.2b `tools/layer_check.py` + `tests/test_layers.py` — provera uvoza kroz `ast` (ADR-033)
      > Nepokriven fajl je nalaz, ne tišina; `*/__init__.py` ne uvozi iz projekta (ADR-037).
- [x] 0.3 `.gitignore` proveren, commit, push
      > Provera ide kroz celu istoriju, ne kroz `git status` — komanda je u
      > CONVENTIONS §8. Dodat `*.log`, koji je §8 tražio a `.gitignore` nije imao.
- [x] 0.4 Cburnett figure **rasterizovane u PNG** (dve veličine), DejaVu font,
      **dva** `LICENSE.txt` — figure i font nemaju istu licencu
      > SVG originali ostaju u repou uz PNG: SVG je izvor, PNG je artefakt.
      > nanosvg iz SDL_image-a **ne skalira crtež na traženo platno**, pa alat sam
      > skalira geometriju i poredi udeo neprovidnih piksela kroz veličine —
      > provera dimenzije i nepraznosti taj kvar propušta (ADR-038).
      > Tuđi materijal se čuva bajt u bajt: `.gitattributes` isključuje pretvaranje
      > prelazaka reda, jer bi `core.autocrlf` na Windows-u oborio svih 12 `sha1`
      > vrednosti pri prvom kloniranju. `tests/test_assets.py` proverava i vrednosti
      > i redove od kojih zavise (ADR-039).
- [x] 0.5 `assets/i18n/sr.json` + `client/i18n.py` sa `t()`
      **svaki `open()` ide sa `encoding="utf-8"` eksplicitno**
      > Devet ključeva izvedenih iz tabele kodova u `PROTOCOL.md` §5. Spona se čita
      > mašinski i tvrdi **oba** smera — kod bez ključa i ključ bez koda (ADR-041).
      > `t()` ne baca na loš podatak; `load()` ga odbija glasno (ADR-040).
      > Dokaz da spona nije dekor: pre napomene u §5 padao je tačno `A5`. Pet namernih
      > kvarova oborilo je očekivane testove — tabela stoji u `faza-0.md` §0.5, zajedno
      > sa razlogom zašto je kvar (a) oborio i `A3`, koji plan nije predvideo.
      > Obe zaostale ispravke iz 0.4 su izvršene ovim commitom.
- [x] 0.6 `LICENSE` u korenu repozitorijuma, uz `THIRD-PARTY.txt` i SPDX
      oznaku u `pyproject.toml`
      > Javan repo bez licence je podrazumevano „sva prava zadržana" —
      > nejasan svakome ko na njega naiđe. Izabran je BSD-3-Clause, isti
      > tekst pod kojim uzimamo figure (ADR-042).
      > `LICENSE` nosi **uslove**, `THIRD-PARTY.txt` **obim** — jer LICENSE
      > imenuje jednog nosioca, a figure i font imaju svoje. Naša rečenica
      > umetnuta u standardni tekst licence putovala bi dalje kao deo uslova,
      > isto kao kod fonta u 0.4.
      > Telo licence je preuzeto sa SPDX-a, ne iz repoa: kopija u
      > `assets/pieces/LICENSE.txt` razlikuje se na **pet** mesta, od kojih dva
      > u odricanju od garancije (`HOLDERS`/`OR` naspram `HOLDER`/`AND`).
      > Blok putanja u `THIRD-PARTY.txt` čita `tests/test_assets.py`, u oba
      > smera; ista licenca stoji i u `pyproject.toml`, i test veže to dvoje.
      > Šest namernih kvarova stoji u `faza-0.md` §0.6 — četiri predviđena
      > tačno, dva sa tačnom dijagnozom ali većim brojem padova nego što je
      > tabela rekla.
      > Nalaz zaveden a ne rešen: `assets/pieces/LICENSE.txt` svoje odricanje
      > naziva „canonical", a SPDX kanonski oblik glasi drugačije. Vidi 0.7.
- [x] 0.7 `.claude/` se svodi na pokazivače; `CONVENTIONS.md` §1 dobija
      red o autoritetu
      > Kriterijum (ADR-044): rečenica sme da ostane van gita samo ako je
      > nijedna izmena u `docs/` ne može učiniti netačnom. Jedinica provere
      > je **rečenica**, ne fajl. Bez `settings.json`: **380 → 152 reda**,
      > 13.996 → 5.823 bajta.
      > Novo pre duplikata: `PROJECT.md` §7 dobio pet tvrdnji, `CONVENTIONS.md`
      > §4 četiri — devet koje su živele samo van gita. Bez toga bi brisanje
      > prekršilo pravilo da dom mora postojati pre uklanjanja.
      > Dve netačnosti su nestale svođenjem, ne pojedinačnom ispravkom:
      > `core-purity.md` je tvrdio da `tests/core/**` sme da uvozi sve (obara
      > ADR-037.3), `i18n.md` da `t()` ne baca (ADR-040: ne baca **na loš
      > podatak**).
      > `checkout --` je izmeren, ne prepisan: fajl bez unosa u indeksu se
      > **odbija greškom**, a praćen fajl koji nije `add`-ovan odlazi u tišini —
      > plan je tvrdio obrnuto. CONVENTIONS §8 nosi izmereno.
      > Mehanizam je meren dvaput, sa različitim ishodom: na v2.1.258 su tri
      > `Read`-a donela tri fajla iz `.claude/rules/`, na v2.1.259 nijedan.
      > Alat se ažurirao u toku taska i restart nije izvršen; uzrok nije
      > utvrđen. Eager učitavanje `description` polja potvrđeno u obe.
      > Zavedeno u „Otvoreno", ne rešeno.
      > Tri tvrdnje su ostale bez doma, sa imenovanim taskom isteka: socket u
      > svojoj niti (3.2), `BotScene` (6.7), tabela simptom→uzrok (1.3).
      > Nalaz iz 0.6 koji ovaj task nije dirao: `assets/pieces/LICENSE.txt`
      > svoje odricanje naziva „canonical", a kanonski SPDX oblik glasi
      > `HOLDERS ... OR`, ne `HOLDER ... AND`. Tuđa licenca — traži svoj plan.
- [x] 0.8 `WORKFLOW.md` usklađen sa odlukama; ADR-045 i ADR-046
      > **Devet** neslaganja, ne četiri koliko je ovaj red tvrdio. Uz
      > `/model opusplan` (§2, §6), „sam pokreće perft skill" (§2),
      > kontrolnu listu (§5) i nastanak `faza-N.md` (§8) — još i spisak
      > šta se automatski učita (§4), smer pitanja iz koraka 4 (§2),
      > `CLAUDE.md` u šablonu prompta (§7), tabela git dozvola i
      > „Izvršavanje ide samo" (§9). Ta tabela je bila poslednja preživela
      > kopija one koja je u 0.7 pala kao netačna.
      > `CLAUDE.md` 191 → 45 redova, 7479 → 2041 bajta. Sto četiri rečenice,
      > od toga 102 oborive; uklonjeno 96, osam ostaje. Četiri su dom dobile
      > u ovom commitu (CONVENTIONS §4, §5, §8), dve su obrisane bez seljenja.
      > Broj je meren četiri puta i menjao se svaki put — sva merenja stoje
      > u faza-0.md §0.8, jer je razlika među njima nalaz o jedinici brojanja.
      > ADR-045: merenje koje obara ADR nosi oznaku, telo ADR-a se ne menja.
      > ADR-046: četiri uslovna STOP-a, do sada samo u planovima.
- [ ] 0.9 Korpusi van gita se svode
      > Četiri korpusa: `MEMORY.md` i njegov folder, memorija planskog
      > chata, `.claude/rules/`, `settings.json`. ADR-047 im daje isti
      > kriterijum koji ADR-044 već daje `CLAUDE.md`-u.
      > Dve mašinske kapije: upis se proverava nad bajtovima (§7);
      > trajleri ne ulaze u istoriju poruka (§8).
      > Nalaz iz 0.8: pravilo „ime nikad ni u jedan fajl" je apsolut koji
      > `LICENSE` već obara, jer ime nosioca stoji tamo po ADR-042. Klasa
      > je ista kao kod trajlera — opseg, ne apsolut.
      > Načelo koje se podiže iz obrazloženja jedne stavke u pravilo:
      > provera ne sme da deli sudbinu sa kvarom od kog štiti — §5, sa
      > izvršnim delom u §7.

---

## FAZA 1 — Engine
**Checkpoint:** podrazumevani perft skup iz ADR-026 se poklapa;
spori skup prolazi sa `CHESS_SLOW_TESTS=1`

Najveći i najvažniji deo projekta. Ne žuriti.

- [ ] 1.1 `core/types.py` — `Color`, `PieceType`, `Piece`, `Move`, `CastlingRights`, **`MoveKind`**
      **`Square` je običan alias `Square = int`** (0–63, a1=0, h8=63), ne `NewType` (ADR-031)
      sa `file_of()`, `rank_of()`, `to_algebraic()`, `from_algebraic()`
      `Move` je `frozen=True, slots=True` i **nosi `kind`** (ADR-022):
      `NORMAL` · `CAPTURE` · `DOUBLE_PAWN_PUSH` · `EN_PASSANT` · `CASTLE` · `PROMOTION`
      plus `from_uci()` i `to_uci()` — `from_uci()` **ne može da odredi `kind` bez table**,
      pa se potez iz spoljnog sveta uvek traži u listi legalnih poteza
      `ChessError` hijerarhija: `IllegalMoveError`, `InvalidFenError`, `InvalidSanError`
      > `PROJECT.md` §5 ne navodi `Piece` u `core/types.py`, iako ga
      > CONVENTIONS §4 vodi kao `frozen=True, slots=True`. Ispraviti u
      > istom commitu kao 1.1.
- [ ] 1.2 `core/board.py` — raspored, **make/unmake**, `UndoRecord`, **Zobrist heš**, `core/fen.py`
      `Board` je **mutabilan** — na tome počiva make/unmake (ADR-006)
      `UndoRecord` nosi: **pojedenu figuru i njeno polje** (kod en passanta pešak nije
      na odredišnom polju) · prethodna prava na rokadu · prethodno en passant polje ·
      prethodni brojač polupoteza · prethodni Zobrist ključ
      Zobrist: **fiksan seed**, ep polje u ključ **samo kad je uzimanje moguće** (ADR-027)
- [ ] 1.3 `core/movegen.py` — generisanje po figuri
      **+ `perft` i `perft_divide` harness — od ovog taska, ne od 1.8**
- [ ] 1.4 Specijalni potezi — rokada (pet uslova), en passant, promocija sa podpromocijom
- [ ] 1.5 `core/attacks.py` — `is_square_attacked`, `is_in_check`
- [ ] 1.6 Legalni potezi = pseudo-legalni + filter kroz make/unmake
- [ ] 1.7 Mat i pat
- [ ] 1.8 **PERFT** — formalni checkpoint
- [ ] 1.9 `core/rules.py` — remi: nedovoljan materijal, 50 poteza, ponavljanje (kroz Zobrist); `RuleSet`
- [ ] 1.10 `core/san.py` — SAN sa disambiguacijom
- [ ] 1.11 `core/pgn.py` — PGN izvoz
- [ ] 1.12 `core/game.py` — stanje partije, istorija, rezultat, poeni figura

**Perft se pokreće posle svake izmene generatora, počev od 1.3.**
Kad se broj ne poklopi — `perft_divide`, pa binarna pretraga do konkretnog poteza.

**Podrazumevani skup** (~300.000 čvorova, mora ostati brz da bi se stvarno pokretao):

| Pozicija | Dubina | Šta lovi |
|---|---|---|
| Početna | 4 | osnovno kretanje |
| Kiwipete | 3 | rokadu i en passant istovremeno |
| Position 3 | 4 | en passant u zamršenim slučajevima |
| Position 4 | 3 | promociju i vezane figure |

**Iza `CHESS_SLOW_TESTS=1`** (~9.000.000 čvorova): početna d5 · Kiwipete d4 · ostale dublje

> **FEN-ove i referentne brojeve prepisati sa Chess Programming Wiki.**
> Nikad iz sećanja — ni čovekovog ni modelovog. Svaka konstanta nosi komentar sa izvorom.

---

## FAZA 2 — Protokol i server
**Checkpoint:** dva `python tools/cli_client.py` terminala odigraju celu partiju,
uključujući rokadu i mat

- [ ] 2.0 `tools/cli_client.py` — CLI klijent, stdlib, prima UCI unos *(zamena za `nc`)*
- [ ] 2.1 `protocol/messages.py` — poruke kao `frozen` dataclass, polje `v`
      > `STATE` nosi `material` kao dva zbira. Razlika se dobija
      > oduzimanjem, što nije šahovsko pravilo — `material` nije
      > pogrešan, nego nedovoljan. Prikaz POJEDENIH FIGURA iz 3.7
      > klijent ne može da izvede: brojanjem iz FEN-a promocija daje
      > „beli je izgubio pešaka". Isti argument kao ADR-034. Odluka o
      > dodavanju polja `captured` donosi se OVDE, ne u 3.7.
      > `captured` se DODAJE uz `material`, ne zamenjuje ga. Dodavanje
      > opcionog polja nije nekompatibilna promena (PROTOCOL §9), pa
      > `v` ostaje 1.
      > Ovde se seli i **spona `PROTOCOL.md` ↔ `sr.json`**: sa tabele u dokumentu
      > na enum kodova iz `messages.py`. Enum je izvršiv, dokument nije. Napomena u
      > §5 ostaje; menja se samo njena druga rečenica, koja imenuje test (ADR-041).
      > Isti mehanizam kojim je ovde zavedeno polje `captured`.
- [ ] 2.2 `protocol/codec.py` — encode/decode, `ProtocolError`, validacija na granici
- [ ] 2.3 `server/session.py` — `Player` interfejs, `RemotePlayer`, tok partije
- [ ] 2.4 `server/clock.py` — `time.monotonic()`, inkrement, pad zastavice
      + izuzetak nedovoljnog materijala
- [ ] 2.5 `server/lobby.py` — stub: prvi koji čekaju se spare
- [ ] 2.6 `server/transport/tcp.py` — **`selectors` event loop, jedna nit, bez `Lock`-a**
      `select(timeout=vreme_do_najbliže_zastavice)` — sat okida sam
- [ ] 2.7 Rukovanje greškama — diskonekcija, ilegalan potez, nevažeća poruka, timeout
- [ ] 2.8 Predaja i ponuda remija

---

## FAZA 3 — Pygame klijent ← MENTOROV ZAHTEV
**Checkpoint:** dva prozora igraju partiju od početka do mata. **Snima se video.**

- [ ] 3.1 Scene sistem — `MenuScene`, `GameScene`
- [ ] 3.2 `client/net.py` — **bez pygame**, nit + `queue.Queue`
- [ ] 3.3 `client/state.py` — **bez pygame**, stanje klijenta
- [ ] 3.4 `client/render.py` — tabla, figure, koordinate
- [ ] 3.5 Drag & drop figura
- [ ] 3.6 Tačkice dozvoljenih poteza *(iz `legal_moves` u `STATE` — klijent ništa ne računa)*
- [ ] 3.7 Sat, ime igrača, razlika u materijalu, istorija poteza u SAN-u
- [ ] 3.8 Dijalog za promociju (sve četiri figure)
- [ ] 3.9 Ekran kraja partije — rezultat i razlog
- [ ] 3.10 Izbor kontrole vremena u meniju
- [ ] 3.11 **README na srpskom + snimanje videa**

> Posle ove faze: `docs/faze/faza-3.md`, merge u `main`, predaja mentoru.

---

## FAZA 4 — Veb klijent
**Checkpoint:** dva browser taba igraju partiju

- [ ] 4.1 `server/transport/websocket.py` — server sluša oba: `--tcp 5000 --ws 8000`
- [ ] 4.2 Serviranje statičkih fajlova
- [ ] 4.3 `web/js/net.js` — prevod `net.py` 1:1
- [ ] 4.4 `web/js/state.js` — prevod `state.py` 1:1
- [ ] 4.5 `web/js/board.js` + `style.css` — CSS Grid 8×8, iste figure
- [ ] 4.6 Drag & drop preko pointer eventa
- [ ] 4.7 `sr.json` se učitava iz istog fajla kao u pygame klijentu
- [ ] 4.8 Responzivnost za mobilni browser

---

## FAZA 5 — Baza, nalozi, lobby
**Checkpoint:** partija preživi restart servera; refresh stranice te vrati u partiju

- [ ] 5.1 `GameRepository` interfejs + `InMemoryGameRepository` za testove
- [ ] 5.2 `SqliteGameRepository`
- [ ] 5.3 Migracije — `schema_version` + numerisani SQL fajlovi
- [ ] 5.4 Nalozi — registracija, prijava, hešovanje lozinke
- [ ] 5.5 Rejting
- [ ] 5.6 Pravi lobby — red čekanja sa filterom po kontroli vremena i rejtingu
- [ ] 5.7 Rekonekcija preko `session_token`
- [ ] 5.8 Istorija partija + reprodukcija potez po potez

---

## FAZA 6 — Bot
**Checkpoint:** bot odigra 100 partija bez ijednog ilegalnog poteza

- [ ] 6.1 `BotPlayer` implementira `Player`
- [ ] 6.2 Evaluacija — materijal, pozicione tabele
- [ ] 6.3 Minimax + alfa-beta odsecanje
- [ ] 6.4 Sortiranje poteza, iterativno produbljivanje,
      **transpoziciona tabela** *(Zobrist postoji od 1.2)*
- [ ] 6.5 Knjiga otvaranja
- [ ] 6.6 Nivoi težine
- [ ] 6.7 `BotScene` / stranica za igru protiv bota, avatar
- [ ] 6.8 UCI interfejs (opciono) — `Move.from_uci()` postoji od 1.1

---

## FAZA 7 — Deploy (opciono)

- [ ] 7.1 `Dockerfile` za server (klijent se ne dockerizuje)
- [ ] 7.2 VPS, systemd servis
- [ ] 7.3 TLS
- [ ] 7.4 Rate limiting

---

## Dokumentacija po fazama

Nastaje iz koraka 6 u ritmu po tasku — korisnik prepričava, Claude Code piše.

- [ ] `docs/faze/faza-0.md` … `faza-6.md`
- [ ] Finalna dokumentacija (sastavlja se iz gornjih)
- [ ] Prezentacija

---

## Ako se kasni — lista za bacanje, ovim redom

1. Pravilo 75 poteza i petostruko ponavljanje
2. Docker
3. Istorija partija i reprodukcija
4. Uvoz PGN-a
5. Rekonekcija

Ništa sa ove liste ne dira zahtev mentora.
