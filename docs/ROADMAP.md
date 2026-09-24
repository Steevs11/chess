# ROADMAP

Plan i trenutno stanje. Claude Code ažurira blok TRENUTNO u commitu svakog taska.
Sledeći task je prvi neodštikliran red posle bloka.

## TRENUTNO

```
Grana:     faza-1
Radimo:    1.2 — core/board.py
Sledeće:   1.3 — core/movegen.py
Otvoreno:  —
```

**Obim:** faze 0–3, do zahteva mentora. Faze 4–7 stoje na dnu kao pravac, ne kao posao.

`[ ]` nije urađeno · `[x]` commitovano · **Checkpoint** je objektivan uslov: meri se na
svežem klonu u novom venv-u i ne prelazi se dalje dok ne prođe.

---

## FAZA 0 — Skelet ✅

**Checkpoint:** `pip install -e ".[dev]"` pa `python tools/check.py` zelen. Prošao
22. 9. 2026 na svežem klonu (58 testova). Šta je napravljeno: `docs/faze/faza-0.md`.

---

## FAZA 1 — Engine

**Checkpoint:** podrazumevani perft skup iz ADR-026 se poklapa; spori skup prolazi
sa `CHESS_SLOW_TESTS=1`. Najveći i najvažniji deo projekta.

- [x] 1.1 `core/types.py` — `Color`, `PieceType`, `Piece`, `Move`, `MoveKind`,
      `CastlingRights`, `Square = int` (0–63, a1 = 0, h8 = 63; ADR-013) sa `file_of()`,
      `rank_of()`, `to_algebraic()`, `from_algebraic()`.
      `Move` je `frozen=True, slots=True` i nosi `kind` (ADR-022):
      `NORMAL` · `CAPTURE` · `DOUBLE_PAWN_PUSH` · `EN_PASSANT` · `CASTLE` · `PROMOTION`,
      plus `from_uci()` i `to_uci()` — `from_uci()` ne može da odredi `kind` bez table, pa se
      potez spolja uvek traži u listi legalnih poteza.
      `ChessError` hijerarhija: `IllegalMoveError`, `InvalidFenError`, `InvalidSanError`.
- [ ] 1.2 `core/board.py` — raspored, **make/unmake**, `UndoRecord`, **Zobrist heš**; `core/fen.py`.
      `Board` je mutabilan (ADR-006). `UndoRecord` nosi pojedenu figuru **i njeno polje**,
      prethodna prava na rokadu, prethodno ep polje, prethodni brojač polupoteza, prethodni
      Zobrist ključ (ADR-014). Zobrist: fiksan seed, ep polje u ključ samo kad je uzimanje
      moguće (ADR-027).
- [ ] 1.3 `core/movegen.py` — generisanje po figuri **+ `tools/perft.py` sa `perft_divide`**
      i podrazumevani perft testovi. Od ovog taska perft se pokreće posle svake izmene
      generatora; kad se broj ne poklopi — `perft_divide`, pa binarna pretraga do poteza.
- [ ] 1.4 Specijalni potezi — rokada (pet uslova iz PROJECT §7), en passant, promocija sa
      podpromocijom (generator emituje četiri poteza).
- [ ] 1.5 `core/attacks.py` — `is_square_attacked`, `is_in_check`.
- [ ] 1.6 Legalni potezi = pseudo-legalni + filter kroz make/unmake.
- [ ] 1.7 Mat i pat.
- [ ] 1.8 **PERFT** — formalni checkpoint, ceo skup iz ADR-026.
- [ ] 1.9 `core/rules.py` — remi: nedovoljan materijal, 50 poteza, ponavljanje (kroz Zobrist);
      `RuleSet` sa profilima `online` i `fide` (ADR-008).
- [ ] 1.10 `core/san.py` — SAN sa disambiguacijom (kolona → red → oba).
- [ ] 1.11 `core/pgn.py` — PGN izvoz.
- [ ] 1.12 `core/game.py` — stanje partije, istorija, rezultat, poeni figura.

**Podrazumevani perft skup** (~300.000 čvorova, mora ostati brz da bi se stvarno pokretao):

| Pozicija | Dubina | Šta lovi |
|---|---|---|
| Početna | 4 | osnovno kretanje |
| Kiwipete | 3 | rokadu i en passant istovremeno |
| Position 3 | 4 | en passant u zamršenim slučajevima |
| Position 4 | 3 | promociju i vezane figure |

**Iza `CHESS_SLOW_TESTS=1`** (~9.000.000 čvorova): početna d5 · Kiwipete d4 · ostale dublje.

> FEN-ove i referentne brojeve prepisati sa Chess Programming Wiki. Nikad iz sećanja.
> Svaka konstanta nosi komentar sa izvorom.

---

## FAZA 2 — Protokol i server

**Checkpoint:** dva `python tools/cli_client.py` terminala odigraju celu partiju,
uključujući rokadu i mat.

- [ ] 2.0 `tools/cli_client.py` — CLI klijent, stdlib, prima UCI unos (ADR-017).
- [ ] 2.1 `protocol/messages.py` — poruke kao `frozen` dataclass, polje `v`; enum kodova
      greške. Ovde se spona `PROTOCOL.md` §5 ↔ `sr.json` seli sa tabele u dokumentu na
      enum (ADR-041). `STATE` dobija opciono polje `captured` (spisak pojedenih figura po
      boji) **uz** `material`, ne umesto njega — iz FEN-a se posle promocije ne može izvesti
      šta je pojedeno; `v` ostaje 1 (PROTOCOL §9).
- [ ] 2.2 `protocol/codec.py` — encode/decode, `ProtocolError`, validacija na granici.
- [ ] 2.3 `server/session.py` — `Player` interfejs, `RemotePlayer`, tok partije.
- [ ] 2.4 `server/clock.py` — `time.monotonic()`, inkrement, pad zastavice
      + izuzetak nedovoljnog materijala.
- [ ] 2.5 `server/lobby.py` — stub: prva dva koja čekaju se spare (ADR-011).
- [ ] 2.6 `server/transport/tcp.py` — `selectors` event loop, jedna nit, bez `Lock`-a;
      `select(timeout=vreme_do_najbliže_zastavice)` — sat okida sam (ADR-016).
- [ ] 2.7 Rukovanje greškama — diskonekcija, ilegalan potez, nevažeća poruka, timeout (ADR-025).
- [ ] 2.8 Predaja i ponuda remija.

---

## FAZA 3 — Pygame klijent ← MENTOROV ZAHTEV

**Checkpoint:** dva prozora igraju partiju od početka do mata. **Snima se video.**

- [ ] 3.1 Scene sistem — `MenuScene`, `GameScene`; `client/__main__.py`
      (nov red u CONVENTIONS §2 i komanda za pokretanje klijenta u istom commitu).
- [ ] 3.2 `client/net.py` — **bez pygame**, socket u svojoj niti + `queue.Queue`.
- [ ] 3.3 `client/state.py` — **bez pygame**, stanje klijenta.
- [ ] 3.4 `client/render.py` — tabla, figure, koordinate.
- [ ] 3.5 Drag & drop figura.
- [ ] 3.6 Tačkice dozvoljenih poteza *(iz `legal_moves` u `STATE` — klijent ništa ne računa)*.
- [ ] 3.7 Sat, ime igrača, razlika u materijalu i pojedene figure, istorija poteza u SAN-u.
- [ ] 3.8 Dijalog za promociju (sve četiri figure).
- [ ] 3.9 Ekran kraja partije — rezultat i razlog (`termination.*` ključevi, ADR-041).
- [ ] 3.10 Izbor kontrole vremena u meniju.
- [ ] 3.11 **README na srpskom + snimanje videa.**

> Posle ove faze: `docs/faze/faza-3.md`, merge u `main`, predaja mentoru.

---

## Posle predaje — nije u obimu

- **Faza 4 — veb klijent:** WebSocket adapter pored TCP-a, `net.js`/`state.js` kao prevod
  1:1, CSS Grid tabla, isti `sr.json`.
- **Faza 5 — baza, nalozi, lobby:** SQLite kroz `GameRepository` (ADR-009), registracija,
  rejting, pravi red čekanja, rekonekcija preko `session_token`, istorija partija.
- **Faza 6 — bot:** `BotPlayer` implementira `Player`, evaluacija, minimax + alfa-beta,
  transpoziciona tabela nad Zobrist hešom, knjiga otvaranja, nivoi.
- **Faza 7 — deploy:** Dockerfile za server, VPS, TLS.

---

## Ako se kasni — bacaju se ovim redom

1. `fide` profil `RuleSet`-a (1.9) — ostaje samo `online`
2. Ponuda remija (2.8) — predaja ostaje
3. Izbor kontrole vremena u meniju (3.10) — ostaje podrazumevano 5+3
4. PGN izvoz (1.11) — `GAME_OVER` tada nosi `"pgn": null`

Ništa sa liste ne dira zahtev mentora.
