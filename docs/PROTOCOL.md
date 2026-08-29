# PROTOKOL

Verzija: **1**

Ovaj dokument je ugovor između servera i bilo kog klijenta. Piše se kao da ga
čita neko treći ko piše svog klijenta — jer će to za koju fazu biti veb klijent.

> Verzija 2 dokumenta (protokol i dalje `v: 1`). Usklađeno sa ADR-016, 017, 018
> i novim ADR-ovima 022–029.

---

## 1. Transport

- TCP socket, poruke razdvojene znakom `\n` (newline-delimited JSON)
- Kodiranje: UTF-8
- Od faze 4 i WebSocket — **isti JSON**, isti tipovi poruka, samo drugi transport
- **Nikad `pickle`.** Protokol mora biti čitljiv iz bilo kog jezika.

Server sluša oba transporta istovremeno:

```bash
python -m chess.server --tcp 5000 --ws 8000
```

Server je **jednonitni `selectors` event loop** (ADR-016). Nema niti po klijentu.

---

## 2. Opšti oblik

Svaka poruka je JSON objekat sa najmanje dva polja:

```json
{ "v": 1, "type": "MOVE", ... }
```

| Polje | Obavezno | Opis |
|---|---|---|
| `v` | da | verzija protokola |
| `type` | da | tip poruke, UPPER_SNAKE_CASE |

Ako `v` ne odgovara → `ERROR` sa kodom `VERSION_MISMATCH`, veza se zatvara.
Nepoznat `type` → `ERROR` sa kodom `UNKNOWN_TYPE`, veza ostaje otvorena.

**Server je autoritet.** Klijent nikad ne odlučuje da li je potez legalan.

---

## 3. Konvencije

- Polja algebarski: `"e2"`, `"h8"`
- Boje: `"white"` / `"black"`
- Vreme u **milisekundama**, celobrojno
- Potezi u istoriji: SAN (`"Nf3"`, `"O-O"`, `"exd5"`, `"Qxh7#"`)
- Pozicija: FEN
- Poruke o greškama se **ne šalju na srpskom** — šalje se `message_key`,
  klijent prevodi kroz `assets/i18n/sr.json`

### Šta klijent sme, a šta ne

Ovo je granica koju je lako pogrešno pročitati, pa je zapisana eksplicitno:

| | Klijent |
|---|---|
| **Čitanje pozicije** — parsiranje FEN-a da bi nacrtao tablu | ✅ dozvoljeno |
| **Odlučivanje o legalnosti** — računanje kuda figura sme | ❌ zabranjeno |

Pygame klijent sme da uvozi **samo** `core/types.py` i `core/fen.py`.
Nikad `movegen`, `attacks`, `rules` ni `game`.

Parsiranje nije rasuđivanje. Legalni potezi uvek stižu od servera.

---

## 4. Klijent → Server

### `HELLO`
```json
{ "v": 1, "type": "HELLO", "client_name": "pygame", "client_version": "0.1.0" }
```

### `LOBBY_JOIN`
```json
{ "v": 1, "type": "LOBBY_JOIN",
  "player_name": "Marko",
  "time_control": { "initial_seconds": 300, "increment_seconds": 3 } }
```
> Faza 2: server spari prva dva klijenta u redu, ignoriše `time_control`.
> Faza 5: pravi red čekanja sa filterima. **Format poruke se ne menja.**

### `MOVE`
```json
{ "v": 1, "type": "MOVE", "from": "e7", "to": "e8", "promotion": "queen" }
```

`promotion` je obavezno **samo** kad pešak stiže na poslednji red.
Dozvoljeno: `"queen"`, `"rook"`, `"bishop"`, `"knight"`.

**Najviše jedna `MOVE` poruka bez odgovora.** Klijent šalje sledeći potez tek
kad primi `STATE` ili `ERROR`. Server ignoriše poruke koje stignu pre toga i
odgovara `ERROR` sa kodom `MOVE_PENDING`.

### `RESIGN`
```json
{ "v": 1, "type": "RESIGN" }
```

### `DRAW_OFFER`
```json
{ "v": 1, "type": "DRAW_OFFER" }
```

Pravila životnog veka:
- Nudi se **samo kad si na potezu**. Inače `ERROR` sa `NOT_YOUR_TURN`.
- Ponuda **pada čim protivnik odigra potez** (FIDE).
- Jedna ponuda po potezu. Druga u istom potezu → `ERROR` sa `DRAW_ALREADY_OFFERED`.

### `DRAW_RESPONSE`
```json
{ "v": 1, "type": "DRAW_RESPONSE", "accept": true }
```

### `RECONNECT` *(faza 5)*
```json
{ "v": 1, "type": "RECONNECT", "session_token": "..." }
```

### `PING`
```json
{ "v": 1, "type": "PING" }
```

---

## 5. Server → Klijent

### `HELLO_OK`
```json
{ "v": 1, "type": "HELLO_OK", "session_token": "a1b2c3", "server_version": "0.1.0" }
```

### `LOBBY_STATE`
```json
{ "v": 1, "type": "LOBBY_STATE", "waiting_count": 1 }
```

### `MATCH_FOUND`
```json
{ "v": 1, "type": "MATCH_FOUND",
  "game_id": "g_001",
  "your_color": "white",
  "opponent_name": "Ana",
  "time_control": { "initial_seconds": 300, "increment_seconds": 3 } }
```

### `STATE` — glavna poruka

**`STATE` je pun snapshot, ne delta.** Klijent ne akumulira ništa. Svaka
`STATE` poruka sadrži sve što treba da se nacrta ceo ekran od nule.

To čini rekonekciju (faza 5.7) besplatnom: klijent koji se vratio dobije
poslednji `STATE` i nastavi kao da ništa nije bilo.

```json
{ "v": 1, "type": "STATE",
  "game_id": "g_001",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "last_move": { "from": "e2", "to": "e4", "san": "e4" },
  "history": ["e4"],
  "legal_moves": {
    "e7": [ { "to": "e6" }, { "to": "e5" } ],
    "g8": [ { "to": "f6" }, { "to": "h6" } ]
  },
  "clocks": { "white": 300000, "black": 300000 },
  "turn": "black",
  "in_check": false,
  "move_number": 1,
  "material": { "white": 39, "black": 39 },
  "draw_offer_from": null,
  "opponent_connected": true }
```

**`legal_moves` — oblik i zašto baš takav**

Vrednost je **lista objekata**, ne lista stringova. Razlog: pešak na e7 ima
**četiri** legalna poteza na e8 (dama, top, lovac, skakač). Mapa `from → [to]`
bi ih spojila u jedan unos, pa bi klijent morao da zaključi „ovo je pešak koji
stiže na poslednji red" — a to je šahovsko pravilo u klijentu i krši ADR-001.

Zato potez koji traži promociju nosi zastavicu:

```json
"legal_moves": {
  "e7": [ { "to": "e8", "promotion": true },
          { "to": "d8", "promotion": true, "capture": true } ]
}
```

Klijent tada zna dve stvari bez ijednog pravila: gde sme da spusti figuru,
i kad da otvori dijalog iz taska 3.8.

`legal_moves` se šalje **samo igraču koji je na potezu.** Drugi dobija praznu mapu.

### `GAME_OVER`
```json
{ "v": 1, "type": "GAME_OVER",
  "result": "1-0",
  "termination": "checkmate",
  "winner": "white",
  "pgn": "[Event ...]\n1. e4 e5 ..." }
```

`result`: `"1-0"` · `"0-1"` · `"1/2-1/2"`

`termination`: `"checkmate"` · `"stalemate"` · `"resignation"` · `"timeout"` ·
`"draw_agreement"` · `"insufficient_material"` · `"fifty_move"` ·
`"threefold_repetition"` · `"abandoned"`

### `OPPONENT_DISCONNECTED`
```json
{ "v": 1, "type": "OPPONENT_DISCONNECTED", "color": "black" }
```

**Sat protivnika nastavlja da ide.** Partija se ne prekida odmah — završava se
pravilno, padom zastavice, sa `termination: "timeout"`.

Razlog za ovaj izbor: ne uvodi nijedan novi mehanizam (pad zastavice ionako
postoji), poklapa se sa ponašanjem online platformi, i ostavlja prostor za
rekonekciju u fazi 5 bez izmene protokola.

### `OPPONENT_RECONNECTED` *(faza 5)*
```json
{ "v": 1, "type": "OPPONENT_RECONNECTED", "color": "black" }
```

### `DRAW_OFFERED`
```json
{ "v": 1, "type": "DRAW_OFFERED", "from": "white" }
```

### `ERROR`
```json
{ "v": 1, "type": "ERROR",
  "code": "ILLEGAL_MOVE",
  "message_key": "error.illegal_move",
  "move": { "from": "e2", "to": "e5" } }
```

Polje `move` je prisutno **samo** kod grešaka vezanih za potez. Klijent iz
njega zna koju figuru da vrati na mesto posle neuspelog drag & drop-a.

| Kod | Značenje | Veza | Nosi `move` |
|---|---|---|---|
| `VERSION_MISMATCH` | pogrešna verzija protokola | zatvara se | ne |
| `PROTOCOL_ERROR` | neispravan JSON ili polje | zatvara se | ne |
| `UNKNOWN_TYPE` | nepoznat tip poruke | ostaje | ne |
| `ILLEGAL_MOVE` | potez nije legalan | ostaje | **da** |
| `NOT_YOUR_TURN` | nije tvoja runda | ostaje | **da** |
| `MOVE_PENDING` | prethodni potez još nije obrađen | ostaje | **da** |
| `DRAW_ALREADY_OFFERED` | remi već ponuđen u ovom potezu | ostaje | ne |
| `GAME_NOT_FOUND` | nema takve partije | ostaje | ne |
| `NOT_IN_GAME` | akcija van partije | ostaje | ne |

### `PONG`
```json
{ "v": 1, "type": "PONG" }
```

---

## 6. Tok jedne partije

```
Klijent A                    Server                    Klijent B
    │                           │                           │
    │──── HELLO ───────────────▶│                           │
    │◀─── HELLO_OK ─────────────│                           │
    │──── LOBBY_JOIN ──────────▶│                           │
    │◀─── LOBBY_STATE ──────────│                           │
    │                           │◀──── HELLO ───────────────│
    │                           │───── HELLO_OK ───────────▶│
    │                           │◀──── LOBBY_JOIN ──────────│
    │◀─── MATCH_FOUND ──────────│───── MATCH_FOUND ────────▶│
    │◀─── STATE ────────────────│───── STATE ──────────────▶│
    │                           │                           │
    │──── MOVE e2e4 ───────────▶│                           │
    │                    [validacija]                       │
    │◀─── STATE ────────────────│───── STATE ──────────────▶│
    │                           │                           │
    │                           │◀──── MOVE e7e5 ───────────│
    │◀─── STATE ────────────────│───── STATE ──────────────▶│
    │                          ...                          │
    │◀─── GAME_OVER ────────────│───── GAME_OVER ──────────▶│
```

---

## 7. Sat

- Vreme se meri na `time.monotonic()` — **nikad** `time.time()`, jer NTP
  sinhronizacija može da pomeri sistemski sat usred partije
- Server čuva `remaining_ms` po igraču i `turn_started_at`
- **Pad zastavice okida sam**, kroz `select(timeout=vreme_do_najbliže_zastavice)`
  u event loop-u. Ne čeka se poruka od igrača — inače bi partija u kojoj niko
  ništa ne šalje visila zauvek (ADR-016).
- `clocks` u `STATE` poruci je izvor istine. Klijent može da odbrojava lokalno
  radi glatkoće, ali se **uvek sinhronizuje** na dolaznu vrednost.
- Pad zastavice = poraz. Izuzetak: ako protivnik nema dovoljno materijala da
  matira nijednim nizom legalnih poteza, rezultat je remi.

---

## 8. Testiranje bez klijenta

Ceo server se testira bez ijedne linije GUI koda:

```bash
python -m chess.server --tcp 5000
python tools/cli_client.py --port 5000    # u dva terminala
```

`tools/cli_client.py` prima poteze u UCI formatu (`e2e4`, `e7e8q`), prevodi ih
u protokol poruke i ispisuje odgovore. Napisan u standardnoj biblioteci, radi na
Windows-u — `nc` ne postoji (ADR-017).

Ovo je i debug alat i dokaz da klijent i server nisu spojeni ni na koji način
osim kroz ovaj dokument.

---

## 9. Verzionisanje

Kad se format promeni **nekompatibilno**, `v` se povećava. Stari klijent tada
dobija `VERSION_MISMATCH` sa jasnom porukom, umesto da pukne na neočekivanom mestu.

Dodavanje **novog opcionog polja** ili **novog tipa poruke** nije nekompatibilna
promena — `v` ostaje isti.

> **Pravilo održavanja:** kad ADR obori nešto napisano u ovom dokumentu, ispravka
> ide u **istom commitu** kao ADR. Dokument koji zaostaje za odlukama je gori od
> dokumenta koji ne postoji, jer mu se veruje.
