# ROADMAP

Ovaj fajl je i plan i trenutno stanje. Claude Code ga ažurira na kraju svakog taska.

**Kako se koristi:** pročitaj blok TRENUTNO, pa prvi neodštikliran red. To je sledeći task.

---

## TRENUTNO

```
Radimo:    0.1 — struktura projekta
Sledeće:   0.2 — pyproject, ruff, prvi test
Otvoreno:  —
Grana:     main
```

---

## Legenda

- `[ ]` nije urađeno · `[x]` urađeno i commitovano
- Svaka podfaza = jedan task = jedna sesija = jedan commit
- **Checkpoint** je objektivan uslov. Ne prelazi se dalje dok ne prođe.

---

## FAZA 0 — Skelet
**Checkpoint:** `python -m unittest discover -s tests` prolazi, `ruff check .` čist

- [ ] 0.1 Struktura foldera, `src/chess/` sa `__init__.py`, `tests/`, `docs/`, `assets/`
- [ ] 0.2 `pyproject.toml`, konfiguracija `ruff`, prvi (prazan) test
- [ ] 0.3 `.gitignore` proveren, prvi commit, push na GitHub
- [ ] 0.4 Preuzeti Cburnett figure i DejaVu font, `LICENSE.txt` uz figure
- [ ] 0.5 `assets/i18n/sr.json` sa prvih nekoliko ključeva, `client/i18n.py` sa `t()`

---

## FAZA 1 — Engine
**Checkpoint:** perft se poklapa do dubine 5 iz početne pozicije i do dubine 4 iz Kiwipete

Ovo je najveći i najvažniji deo projekta. Ne žuriti.

- [ ] 1.1 `core/types.py` — `Color`, `PieceType`, `Piece`, `Square`, `Move`, `CastlingRights`
      (`Enum` + `frozen=True` dataclass, nemoguća stanja nepredstavljiva)
- [ ] 1.2 `core/board.py` — raspored figura, **make/unmake**, `core/fen.py` parse + export
- [ ] 1.3 `core/movegen.py` — generisanje po figuri: pešak, skakač, lovac, top, dama, kralj
- [ ] 1.4 Specijalni potezi — rokada (pet uslova), en passant, promocija sa podpromocijom
- [ ] 1.5 `core/attacks.py` — `is_square_attacked`, `is_in_check`
- [ ] 1.6 Legalni potezi = pseudo-legalni + filter kroz make/unmake
- [ ] 1.7 Mat i pat
- [ ] 1.8 **PERFT** — poređenje sa referentnim brojevima ← *checkpoint*
- [ ] 1.9 `core/rules.py` — remi: nedovoljan materijal, 50 poteza, ponavljanje; `RuleSet` (`online` / `fide`)
- [ ] 1.10 `core/san.py` — SAN sa disambiguacijom
- [ ] 1.11 `core/pgn.py` — PGN izvoz
- [ ] 1.12 `core/game.py` — stanje partije, istorija poteza, rezultat, poeni figura

**Referentne perft vrednosti (proveriti na Chess Programming Wiki pre ukucavanja):**

| Dubina | Početna pozicija |
|---|---|
| 1 | 20 |
| 2 | 400 |
| 3 | 8.902 |
| 4 | 197.281 |
| 5 | 4.865.609 |

---

## FAZA 2 — Protokol i server
**Checkpoint:** dva `nc localhost 5000` terminala odigraju celu partiju kucanjem JSON-a, uključujući rokadu i mat

- [ ] 2.1 `protocol/messages.py` — sve poruke kao `frozen` dataclass, polje `v`
- [ ] 2.2 `protocol/codec.py` — encode/decode, `ProtocolError`, validacija na granici
- [ ] 2.3 `server/session.py` — `Player` interfejs, `RemotePlayer`, tok partije
- [ ] 2.4 `server/clock.py` — `time.monotonic()`, inkrement, pad zastavice + izuzetak nedovoljnog materijala
- [ ] 2.5 `server/lobby.py` — stub: prvi koji čekaju se spare
- [ ] 2.6 `server/transport/tcp.py` — accept petlja, nit po klijentu, `Lock` oko stanja
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
- [ ] 3.6 Tačkice dozvoljenih poteza, isticanje poslednjeg poteza, isticanje šaha
- [ ] 3.7 Sat, ime igrača, razlika u materijalu, istorija poteza u SAN-u
- [ ] 3.8 Dijalog za promociju (sve četiri figure)
- [ ] 3.9 Ekran kraja partije — rezultat i razlog
- [ ] 3.10 Izbor kontrole vremena u meniju
- [ ] 3.11 **README na srpskom + snimanje videa**

> Posle ove faze: `docs/faze/faza-3.md`, merge u `main`, predaja mentoru.

---

## FAZA 4 — Veb klijent
**Checkpoint:** dva browser taba igraju partiju

- [ ] 4.1 `server/transport/websocket.py` — server sluša oba transporta: `--tcp 5000 --ws 8000`
- [ ] 4.2 Serviranje statičkih fajlova
- [ ] 4.3 `web/js/net.js` — prevod `net.py` 1:1
- [ ] 4.4 `web/js/state.js` — prevod `state.py` 1:1
- [ ] 4.5 `web/js/board.js` + `style.css` — CSS Grid 8×8, iste SVG figure
- [ ] 4.6 Drag & drop preko pointer eventa
- [ ] 4.7 `sr.json` se učitava iz istog fajla kao u pygame klijentu
- [ ] 4.8 Responzivnost za mobilni browser

---

## FAZA 5 — Baza, nalozi, lobby
**Checkpoint:** partija preživi restart servera; refresh stranice te vrati u partiju

- [ ] 5.1 `GameRepository` interfejs + `InMemoryGameRepository` za testove
- [ ] 5.2 `SqliteGameRepository`
- [ ] 5.3 Migracije — `schema_version` + `migrations/` sa numerisanim SQL fajlovima
- [ ] 5.4 Nalozi — registracija, prijava, hešovanje lozinke
- [ ] 5.5 Rejting
- [ ] 5.6 Pravi lobby — red čekanja sa filterom po kontroli vremena i rejtingu
- [ ] 5.7 Rekonekcija preko `session_token`
- [ ] 5.8 Istorija partija + reprodukcija potez po potez

---

## FAZA 6 — Bot
**Checkpoint:** bot odigra 100 partija bez ijednog ilegalnog poteza

- [ ] 6.1 `BotPlayer` implementira `Player`
- [ ] 6.2 Evaluacija pozicije — materijal, pozicione tabele
- [ ] 6.3 Minimax + alfa-beta odsecanje
- [ ] 6.4 Sortiranje poteza, iterativno produbljivanje
- [ ] 6.5 Knjiga otvaranja
- [ ] 6.6 Nivoi težine
- [ ] 6.7 Scena / stranica za igru protiv bota, avatar
- [ ] 6.8 UCI interfejs (opciono) — da bot može protiv Stockfish-a

---

## FAZA 7 — Deploy (opciono)

- [ ] 7.1 `Dockerfile` za server (klijent se ne dockerizuje)
- [ ] 7.2 VPS, systemd servis
- [ ] 7.3 TLS
- [ ] 7.4 Osnovna zaštita od zloupotrebe — rate limiting

---

## Dokumentacija po fazama

- [ ] `docs/faze/faza-1.md`
- [ ] `docs/faze/faza-2.md`
- [ ] `docs/faze/faza-3.md`
- [ ] `docs/faze/faza-4.md`
- [ ] `docs/faze/faza-5.md`
- [ ] `docs/faze/faza-6.md`
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
