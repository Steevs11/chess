# ROADMAP

Ovaj fajl je i plan i trenutno stanje. Claude Code ga ažurira na kraju svakog taska.

**Kako se koristi:** pročitaj blok TRENUTNO, pa prvi neodštikliran red. To je sledeći task.

> Verzija 2 — ažurirano posle tehničkog pregleda plana.
> Izmene su obrazložene u `docs/DECISIONS.md`, ADR-013 do ADR-021.

---

## TRENUTNO

```
Radimo:    planiranje (pre 0.1)
Sledeće:   0.1 — struktura projekta
Otvoreno:  —
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
**Checkpoint:** `python -m unittest discover -s tests` prolazi, `ruff check .` čist

- [ ] 0.1 Struktura foldera, `src/chess/` sa `__init__.py`, `tests/`, `docs/`, `assets/`, `tools/`
- [ ] 0.2 `pyproject.toml`, konfiguracija `ruff`, **`docs/CONVENTIONS.md`**, prvi (prazan) test
- [ ] 0.3 `.gitignore` proveren, commit, push
- [ ] 0.4 Cburnett figure **rasterizovane u PNG** (dve veličine), DejaVu font, `LICENSE.txt`
- [ ] 0.5 `assets/i18n/sr.json` + `client/i18n.py` sa `t()`
      **svaki `open()` ide sa `encoding="utf-8"` eksplicitno**

---

## FAZA 1 — Engine
**Checkpoint:** perft 4 se poklapa iz početne pozicije i iz Kiwipete;
perft 5 prolazi sa `CHESS_SLOW_TESTS=1`

Najveći i najvažniji deo projekta. Ne žuriti.

- [ ] 1.1 `core/types.py` — `Color`, `PieceType`, `Piece`, `Move`, `CastlingRights`
      **`Square` je `int` 0–63** sa `file_of()`, `rank_of()`, `to_algebraic()`, `from_algebraic()`
      `Move` je `frozen=True, slots=True`, plus `from_uci()` i `to_uci()`
- [ ] 1.2 `core/board.py` — raspored, **make/unmake**, `UndoRecord`, **Zobrist heš**, `core/fen.py`
      `UndoRecord` nosi: pojedenu figuru · prethodna prava na rokadu · prethodno en passant
      polje · prethodni brojač polupoteza · prethodni Zobrist ključ
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

| Dubina | Početna pozicija | Kiwipete |
|---|---|---|
| 1 | 20 | 48 |
| 2 | 400 | 2.039 |
| 3 | 8.902 | 97.862 |
| 4 | 197.281 | 4.085.603 |
| 5 | 4.865.609 | — |

> Dubina 5 iza `CHESS_SLOW_TESTS=1`. Vrednosti proveriti na Chess Programming Wiki.

---

## FAZA 2 — Protokol i server
**Checkpoint:** dva `python tools/cli_client.py` terminala odigraju celu partiju,
uključujući rokadu i mat

- [ ] 2.0 `tools/cli_client.py` — CLI klijent, stdlib, prima UCI unos *(zamena za `nc`)*
- [ ] 2.1 `protocol/messages.py` — poruke kao `frozen` dataclass, polje `v`
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
