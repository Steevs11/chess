# PROTOKOL

Verzija: **1**

Ovaj dokument je ugovor između servera i bilo kog klijenta. Piše se kao da ga
čita neko treći ko piše svog klijenta — jer će to za koju fazu biti veb klijent.

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

Ako `v` ne odgovara, server odgovara `ERROR` sa kodom `VERSION_MISMATCH` i zatvara vezu.
Nepoznat `type` → `ERROR` sa kodom `UNKNOWN_TYPE`. Veza ostaje otvorena.

**Server je autoritet.** Klijent nikad ne odlučuje da li je potez legalan.

---

## 3. Konvencije

- Polja se zapisuju algebarski: `"e2"`, `"h8"`
- Boje: `"white"` / `"black"`
- Vreme u **milisekundama**, celobrojno
- Potezi u istoriji: SAN (`"Nf3"`, `"O-O"`, `"exd5"`, `"Qxh7#"`)
- Pozicija: FEN
- Tekstovi grešaka se **ne šalju na srpskom** — šalje se ključ (`message_key`),
  klijent ga prevodi kroz `assets/i18n/sr.json`

---

## 4. Klijent → Server

### `HELLO`
Prva poruka na konekciji.
```json
{ "v": 1, "type": "HELLO", "client_name": "pygame", "client_version": "0.1.0" }
```

### `LOBBY_JOIN`
Prijava u red za partiju.
```json
{ "v": 1, "type": "LOBBY_JOIN",
  "player_name": "Marko",
  "time_control": { "initial_seconds": 300, "increment_seconds": 3 } }
```
> **Faza 2:** server samo spari prva dva klijenta u redu, ignoriše `time_control`.
> **Faza 5:** pravi red čekanja sa filterima. Format poruke se **ne menja**.

### `MOVE`
```json
{ "v": 1, "type": "MOVE", "from": "e7", "to": "e8", "promotion": "queen" }
```
`promotion` je obavezno samo kad pešak stiže na poslednji red.
Dozvoljeno: `"queen"`, `"rook"`, `"bishop"`, `"knight"`.

### `RESIGN`
```json
{ "v": 1, "type": "RESIGN" }
```

### `DRAW_OFFER`
```json
{ "v": 1, "type": "DRAW_OFFER" }
```

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

### `STATE`
Glavna poruka. Šalje se posle svakog poteza i na početku partije.

```json
{ "v": 1, "type": "STATE",
  "game_id": "g_001",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "last_move": { "from": "e2", "to": "e4", "san": "e4" },
  "legal_moves": { "e7": ["e6", "e5"], "g8": ["f6", "h6"] },
  "clocks": { "white": 300000, "black": 300000 },
  "turn": "black",
  "in_check": false,
  "move_number": 1,
  "material": { "white": 39, "black": 39 } }
```

**`legal_moves` šalje server**, i to samo za igrača koji je na potezu.
Zato klijentu ne treba nijedno šahovsko pravilo — samo crta tačkice po ovoj mapi.

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
`"draw_agreement"` · `"insufficient_material"` · `"fifty_move"` · `"threefold_repetition"` · `"abandoned"`

### `DRAW_OFFERED`
```json
{ "v": 1, "type": "DRAW_OFFERED", "from": "white" }
```

### `ERROR`
```json
{ "v": 1, "type": "ERROR", "code": "ILLEGAL_MOVE", "message_key": "error.illegal_move" }
```

| Kod | Značenje | Veza |
|---|---|---|
| `VERSION_MISMATCH` | pogrešna verzija protokola | zatvara se |
| `PROTOCOL_ERROR` | neispravan JSON ili polje | zatvara se |
| `UNKNOWN_TYPE` | nepoznat tip poruke | ostaje |
| `ILLEGAL_MOVE` | potez nije legalan | ostaje |
| `NOT_YOUR_TURN` | nije tvoja runda | ostaje |
| `GAME_NOT_FOUND` | nema takve partije | ostaje |
| `NOT_IN_GAME` | akcija van partije | ostaje |

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
    │                           │                           │
    │                          ...                          │
    │◀─── GAME_OVER ────────────│───── GAME_OVER ──────────▶│
```

---

## 7. Sat

- Server računa vreme na `time.monotonic()` — **nikad** `time.time()`
- Ne postoji nit koja otkucava. Server čuva `remaining_ms` po igraču i
  `turn_started_at`, pa računa razliku pri svakom događaju.
- `clocks` u `STATE` poruci je izvor istine. Klijent može da odbrojava lokalno
  radi glatkoće, ali se **uvek sinhronizuje** na dolaznu vrednost.
- Pad zastavice = poraz. Izuzetak: ako protivnik nema dovoljno materijala da
  matira, rezultat je remi.

---

## 8. Testiranje bez klijenta

Ceo server se testira bez ijedne linije GUI koda:

```bash
python -m chess.server --tcp 5000
nc localhost 5000
```

Zatim se kuca JSON, red po red. Ovo je i debug alat i dokaz da klijent i server
nisu spojeni ni na koji način osim kroz ovaj dokument.

---

## 9. Verzionisanje

Kad se format promeni **nekompatibilno**, `v` se povećava. Stari klijent tada
dobija `VERSION_MISMATCH` sa jasnom porukom, umesto da pukne na neočekivanom mestu.

Dodavanje **novog opcionog polja** ili **novog tipa poruke** nije nekompatibilna
promena — `v` ostaje isti.
