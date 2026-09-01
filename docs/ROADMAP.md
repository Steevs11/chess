# ROADMAP

Ovaj fajl je i plan i trenutno stanje. Claude Code ga ažurira na kraju svakog taska.

**Kako se koristi:** pročitaj blok TRENUTNO, pa prvi neodštikliran red. To je sledeći task.

> Verzija 3 — ažurirano posle tri kruga tehničkog pregleda.
> Izmene su obrazložene u `docs/DECISIONS.md`, ADR-013 do ADR-034.

---

## TRENUTNO

```
Radimo:    0.5 — assets/i18n/sr.json + client/i18n.py sa t()
Sledeće:   0.6 — LICENSE u korenu repozitorijuma
Otvoreno:  ništa
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
- [ ] 0.5 `assets/i18n/sr.json` + `client/i18n.py` sa `t()`
      **svaki `open()` ide sa `encoding="utf-8"` eksplicitno**
- [ ] 0.6 `LICENSE` u korenu repozitorijuma
      > Javan repo bez licence je podrazumevano „sva prava zadržana" —
      > nejasan svakome ko na njega naiđe. Izbor licence je
      > korisnikova odluka i traži ADR.
- [ ] 0.7 `.claude/` se svodi na pokazivače; `CONVENTIONS.md` §1 dobija
      red o autoritetu
      > `.claude/` nije u hijerarhiji (§1) ni pod pravilom propagacije
      > (ADR-030/032), a `rules/*.md` se učitavaju AUTOMATSKI PO
      > PUTANJI — pravilo bez autoriteta stiže pred oči pre onog sa
      > autoritetom, i to baš u tasku koji dira taj sloj. Tri fajla su
      > tako protivrečila ADR-ovima (`faza-0.md`, 0.2). Sadržaj je
      > ispravljen, struktura nije, pa se ponavlja sa svakim sledećim
      > ADR-om. Kriterijum po ADR-020/028: `.claude/` sme operativno
      > uputstvo („pročitaj §2 pre nego što dodirneš `core/`"), nikad
      > tvrdnju o projektu. Traži ADR — druga opcija je da pravila
      > ostanu, uz obaveznu ADR referencu uz svaku tvrdnju.
      > Otvoreno za plan 0.7: tabela za preseljenje iz `faza-0.md` §0.2
      > šalje Kiwipete brojeve u `tools/perft.py`, koji u 0.7 još ne
      > postoji. Tri od šest stavki sele se tek u fazama 3 i 6.
- [ ] 0.8 `WORKFLOW.md` usklađen sa odlukama
      > Fajl je iz prvog commita i propušteno je pravilo propagacije.
      > Četiri neslaganja: `/model opusplan` ne postoji (§2, §6);
      > „sam pokreće perft skill" protiv ADR-028 (§2); kontrolna lista
      > ima šest stavki, CONVENTIONS §9 ima sedam (§5); §8 kaže da
      > `faza-N.md` nastaje na kraju faze iz prepričavanja, a ADR-021
      > traži dva reda posle svakog taska i CONVENTIONS §9 to vodi kao
      > stavku gotovog taska.
      > Poslednje je najgore: ostala tri pucaju glasno, ovo ne puca
      > uopšte — ko radi po dokumentu preskoči korak 4 i to se vidi
      > tek na odbrani.

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

- [ ] `docs/faze/faza-1.md` … `faza-6.md`
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
