# PROJEKAT — šahovska aplikacija

Ovaj dokument je kompletan opis projekta. Čita se jednom, na početku.
Svakodnevna pravila su u `CLAUDE.md`, tok rada u `docs/WORKFLOW.md`,
lista taskova u `docs/ROADMAP.md`.

---

## 1. Šta pravimo

Šahovsku aplikaciju za dva igrača preko mreže. Cela šahovska logika pisana od nule.

Krajnji oblik: šahovski sajt na srpskom jeziku, sa nalozima, traženjem protivnika,
istorijom partija i kasnije botom. Do tamo se stiže kroz faze — prva je desktop
klijent koji zadovoljava zahtev mentora.

**Ključna arhitektonska odluka koja proizlazi iz zahteva mentora:**

> Server je jedini autoritet nad pravilima. Klijent ne odlučuje ništa.

Klijent šalje nameru ("hoću e2 → e4"), server validira i emituje novo stanje.
Ako se ovo obrne, dobija se chat aplikacija sa šahovskom temom, a ne šah server.

---

## 2. Kontekst — prepiska sa mentorom

### Predlog studenta

> Glavna ideja je šah igrica za 2 igrača koji će naizmenično povlačiti poteze.
> Kreiranje šahovske table i figura. Implementacija logike kretanja svih figura i
> dozvoljenog kretanja u određenom potezu. Implementacija posebnih poteza (rokada,
> en passant). Posebni slučajevi za kada je kralj šahiran ili matiran. Cela
> šahovska logika pravljena od nule. Izveštavanje igrača o poenima (kraljica 9,
> top 5, pešak 1). Mogućnost da igrač vidi dozvoljene poteze za figuru. Sat koji
> meri preostalo vreme. Igrači mogu uhvatiti figuru i prevući je do željenog polja.
>
> Alternativa/nastavak: AI šahovski bot, fokus na mašinsko učenje i razvoj bota.
>
> Pitanja: u kom okruženju raditi, da li je pygame potreban, da li koristiti
> frontend (React) ili Python GUI, da li implementirati klijent-server arhitekturu.

### Odgovor mentora

> За почетак урадите да могу 2 играча да играју преко мреже, да се проверавају
> дозвољени потези, да закључи специјалне случајеве и да реагује.
> Нека је сервер и оба клијента на истом рачунару. Када урадите снимите
> 1-минутни видео на коме се виде на екрану оба клијента и како апликација ради.

### Kako smo ovo pročitali

- *"да се проверавају дозвољени потези"* → **server validira, ne klijent**
- *"сервер и оба клијента на истом рачунару"* → `127.0.0.1`, ali kod je isti kao
  za dve mašine. Ništa privremeno se ne piše.
- *"1-минутни видео на коме се виде оба клијента"* → klijent mora vizuelno da
  komunicira stanje: čija je runda, sat, šah, kraj partije. To je deo zadatka.
- Mentor je tražio socket-e → koristimo sirovi `socket`, ne framework.

---

## 3. Zahtevi

### Prioritet 1 — pred mentora (faze 0–3)

- [ ] Dva klijenta igraju preko mreže
- [ ] Server proverava dozvoljene poteze
- [ ] Specijalni slučajevi rade: rokada, en passant, promocija, šah, mat, pat
- [ ] Server i oba klijenta na istom računaru
- [ ] Jednominutni video sa oba klijenta na ekranu

### Prioritet 2 — posle predaje (faze 4–7)

Veb klijent → baza i nalozi → bot → deploy.

---

## 4. Stack

| Sloj | Izbor | Zavisnost |
|---|---|---|
| Engine (`core/`) | čist Python, stdlib | — |
| Testovi | `unittest` | — |
| Protokol | `dataclasses` + `json` | — |
| Server | `socket` + `threading` | — |
| Klijent | **pygame** | pygame |
| Baza (faza 5) | `sqlite3` kroz repository pattern | — |
| Dev | `ruff` | dev-only |

**Pokretanje: `pip install pygame`.** To je sve.

### Svesno odbijeno

| Tehnologija | Zašto ne |
|---|---|
| FastAPI, uvicorn, Pydantic | korisnik ih već zna, previše moderno za cilj projekta |
| Django, Flask | ORM, migracije, settings — dani potrošeni na framework umesto na šah |
| React, Node, npm | build korak i drugi jezik za tablu 8×8 |
| AngularJS | mrtav projekat |
| ORM (SQLAlchemy) | skriva SQL koji treba razumeti |
| `python-chess` i slične biblioteke | cela poenta je pisati šah od nule |
| `pickle` | zaključava za Python zauvek |

### Okruženje

Windows · Python 3.11 · PyCharm sa Claude Code plugin-om · git + javni GitHub

---

## 5. Arhitektura

```
                  ┌─────────────────────────┐
  pygame klijent ─▶                         │
                  │  protocol               │
  (veb klijent)  ─▶  session                │  ← ne zna ko ga zove
                  │  core (engine)          │
  (bot)          ─▶                         │
                  └─────────────────────────┘
```

Ovo je **ports and adapters** (heksagonalna arhitektura). Domenska logika ne zna
ništa o transportu. Zbog toga:

- Veb klijent kasnije = novi adapter, server i engine se ne diraju
- Bot = treća implementacija `Player` interfejsa, ništa drugo se ne menja
- Raw TCP i WebSocket mogu raditi istovremeno

### Struktura foldera

```
chess/
├── CLAUDE.md                    (u .gitignore)
├── .gitignore
├── pyproject.toml
├── README.md                    (srpski)
├── src/chess/
│   ├── core/
│   │   ├── types.py             Color, PieceType, Square, Move, CastlingRights
│   │   ├── board.py             raspored, make/unmake
│   │   ├── movegen.py           generisanje poteza
│   │   ├── attacks.py           is_square_attacked, is_in_check
│   │   ├── rules.py             mat, pat, remi, RuleSet
│   │   ├── game.py              stanje partije, istorija
│   │   ├── fen.py
│   │   ├── san.py
│   │   └── pgn.py
│   ├── protocol/
│   │   ├── messages.py          dataclasses
│   │   └── codec.py             encode/decode, ProtocolError
│   ├── server/
│   │   ├── __main__.py
│   │   ├── session.py           Player, RemotePlayer, tok partije
│   │   ├── lobby.py
│   │   ├── clock.py
│   │   └── transport/
│   │       ├── tcp.py
│   │       └── websocket.py     (faza 4)
│   └── client/
│       ├── __main__.py
│       ├── net.py               BEZ pygame — nit + Queue
│       ├── state.py             BEZ pygame — stanje klijenta
│       ├── render.py            pygame
│       ├── i18n.py
│       └── scenes/
│           ├── menu.py
│           └── game.py
├── assets/
│   ├── pieces/                  Cburnett SVG, BSD-3
│   ├── fonts/                   DejaVu Sans
│   └── i18n/sr.json
├── docs/
└── tests/
```

---

## 6. Sedam pravila nadogradivosti

Ovo je ono što čini prelazak na veb jeftinim. Ne krše se ni pod kojim izgovorom.

1. `core/` uvozi samo standardnu biblioteku
2. Protokol je JSON, verzionisan, dokumentovan u `PROTOCOL.md` — nikad `pickle`
3. Nula šahovske logike u klijentu
4. pygame tipovi ne izlaze iz `render.py` i `scenes/`; koordinate su `Square`, ne pikseli
5. Sat je na serveru
6. Klijent podeljen na `net.py` / `state.py` / `render.py` / `scenes/` — samo poslednja dva vide pygame
7. Tekst vidljiv korisniku ide u `assets/i18n/sr.json`, nikad u kod

**Posledica:** kad se piše veb klijent, `net.py` i `state.py` se prevode 1:1 u JS.
Ne projektuje se dvaput — prevodi se.

---

## 7. Šahovska pravila — kompletna lista za implementaciju

### Kretanje

- Pešak: 1 napred; 2 sa početnog reda (**oba polja prazna**); uzima samo dijagonalno
- Skakač: 8 fiksnih pomeraja, preskače figure
- Lovac: 4 dijagonale, klizi do prepreke
- Top: 4 prava pravca, klizi do prepreke
- Dama: svih 8 pravaca
- Kralj: 1 polje u svim pravcima
- Nema uzimanja sopstvene figure

### Rokada — pet uslova

1. Kralj i **taj** top se nikada nisu pomerili (ne "nisu na početnom polju")
2. Polja između njih prazna
3. Kralj nije trenutno u šahu
4. Kralj ne prolazi kroz napadnuto polje
5. Kralj ne završava na napadnutom polju

> **Česta greška:** top **sme** biti napadnut i **sme** proći kroz napadnuto polje.
> Ograničenje važi samo za kralja. Perft ovo hvata.

### En passant

Samo **odmah** posle protivničkog dvopoteznog pomeranja pešaka. Propušten potez
znači da pravo nestaje zauvek.

### Promocija

Dama, top, lovac ili skakač. **Podpromocija mora da radi.** Ne može ostati pešak,
ne može postati kralj.

### Kraj partije

- Nijedan potez ne sme ostaviti sopstvenog kralja u šahu (pokriva vezane figure
  i otkrivene šahove)
- **Mat** = u šahu + nema legalnih poteza → poraz
- **Pat** = nije u šahu + nema legalnih poteza → remi

### Remi

| Uslov | FIDE | Detalj |
|---|---|---|
| Pat | automatski | |
| Nedovoljan materijal | automatski | K–K, K+L–K, K+S–K, K+L–K+L sa lovcima **iste boje polja** |
| Trostruko ponavljanje | na zahtev | ista pozicija, isti na potezu, **ista prava na rokadu i en passant** |
| Petostruko ponavljanje | automatski | |
| 50 poteza | na zahtev | 50 poteza svakog igrača bez pomeranja pešaka i bez uzimanja |
| 75 poteza | automatski | |
| Dogovor | automatski | |

**Implementiramo `RuleSet` sa dva profila:**

- `online` (podrazumevan) — trostruko ponavljanje i 50 poteza primenjuju se
  automatski; 75/petostruko se ne implementiraju
- `fide` — striktno po FIDE

Pravila su podatak, ne `if` zakucan u kodu.

### Vreme

- Pad zastavice = poraz
- **Izuzetak:** ako protivnik nema dovoljno materijala da matira nijednim nizom
  legalnih poteza → remi, ne poraz
- Sat na `time.monotonic()`, **nikad** `time.time()` (NTP može da skoči)
- Server ne drži nit koja otkucava: čuva `remaining_ms` i `turn_started_at`,
  računa razliku pri svakom događaju

### Kontrole vremena

```python
@dataclass(frozen=True)
class TimeControl:
    initial_seconds: int
    increment_seconds: int
```

| Kategorija | Preseti |
|---|---|
| Bullet | 1+0, 2+1 |
| Blic | 3+2, **5+3** (podrazumevano) |
| Rapid | 10+0, 15+10 |
| Klasik | 30+20 |

Kategorija se **izračunava** iz `initial + 60 × increment`, ne upisuje ručno.

### Ostalo

Predaja · ponuda remija (ponudi/prihvati/odbij) · prekid veze i rekonekcija ·
ilegalan potez → server odbija sa jasnom greškom, klijent vraća figuru

### Notacija — implementiramo sve tri

- **FEN** — pozicija (uključuje brojač polupoteza, što je tačno ono što treba za pravilo 50 poteza)
- **SAN** — potezi sa disambiguacijom (`Nbd2`)
- **PGN** — cela partija

### Poeni figura

Dama 9 · top 5 · lovac 3 · skakač 3 · pešak 1. Prikazuje se razlika u materijalu.

---

## 8. Uloge

| | Radi |
|---|---|
| **Korisnik** (student, arhitekta) | donosi odluke · čita svaki diff pre commita · objašnjava kod nazad na kraju faze · pušta testove · upravlja sesijama |
| **Claude Code** | piše kod po odobrenom planu · pita kad je dvosmisleno · objašnjava posle izmene · ne menja testove da prođu · vodi `ROADMAP.md` i `DECISIONS.md` |
| **Claude.ai (browser)** | arhitektura · objašnjenja · pregled diffova · provera razumevanja · debug razgovori |

Claude je vodeći inženjer po načinu rada: predlaže, ima mišljenje, ne čeka pitanje,
kaže kad je nešto pogrešno. Ali **odluke ostaju kod korisnika**, jer on brani
projekat i jer je učenje deklarisani cilj.

### Obrnuti pregled

Na kraju svake faze korisnik objašnjava kod **svojim rečima**. Gde zapne, tu se
vraća. To je jedini mehanizam koji stvarno rešava odbranu — sve ostalo je inženjerstvo.

---

## 9. Faze i checkpointovi

Checkpoint je **objektivan uslov**, ne osećaj. Ne prelazi se dalje dok ne prođe.

| Faza | Sadržaj | Checkpoint |
|---|---|---|
| 0 | Skelet, git, ruff | `unittest` prolazi, `ruff` čist |
| 1 | **Engine** — cela šahovska logika | **perft do dubine 5 se poklapa** |
| 2 | Protokol + server (TCP) | dva `nc` terminala odigraju partiju kucanjem |
| 3 | **Pygame klijent** | **dva prozora igraju → video za mentora** |
| 4 | Veb klijent (WebSocket + vanilla JS) | dva browser taba igraju |
| 5 | SQLite, nalozi, lobby, istorija | partija preživi restart servera |
| 6 | Bot | 100 partija bez ilegalnog poteza |
| 7 | Deploy (opciono) | |

Faze 0–3 su pred mentora. Faze 4–7 posle predaje.

Detaljna lista taskova: `docs/ROADMAP.md`.

---

## 10. Baza — kada i zašto

**Faze 0–4: bez baze.** Partije žive u memoriji servera.

**Faza 5:** SQLite (`sqlite3`, stdlib). Razlog nije "lepo je imati" nego što
refresh stranice bez perzistencije gubi partiju.

```sql
players(id, username, password_hash, rating, created_at)
games(id, white_id, black_id, result, termination,
      time_control, pgn, started_at, ended_at)
```

Partije **u toku** ostaju u memoriji. U bazu se upisuje **gotova partija kao PGN**.

### Dve stvari koje se rade od početka faze 5

**Repository pattern** — server nikad ne piše SQL:

```python
class GameRepository(Protocol):
    def save_game(self, game: FinishedGame) -> GameId: ...
    def get_game(self, game_id: GameId) -> FinishedGame | None: ...
    def list_for_player(self, player_id: PlayerId) -> list[GameSummary]: ...
```

`SqliteGameRepository`, kasnije `PostgresGameRepository`, i odmah
`InMemoryGameRepository` za testove — testovi ne diraju disk.

**Migracije bez alata** — tabela `schema_version` + `migrations/` sa numerisanim
SQL fajlovima. Server primeni što nedostaje pri startu. ~40 linija, bez Alembic-a.

### Zašto SQLite a ne SQL Server / Postgres

Prethodni projekat korisnika je pukao kod druge osobe iz četiri razloga:
SQL Server nije bio instaliran · kredencijali su bili u `.env` koji nije u gitu ·
šema nije postojala · ODBC drajver nije bio instaliran.

Princip: **sve što je projektu potrebno mora biti ili u repozitorijumu, ili
instalirano jednim `pip`, ili napravljeno automatski pri prvom pokretanju.**

SQLite obara sva četiri uzroka. Konfiguracija ide preko promenljive okruženja
sa razumnim podrazumevanim:

```python
DB_PATH = Path(os.environ.get("CHESS_DB_PATH", "chess.db"))
```

Isti kod radi lokalno i na VPS-u. `chess.db` je u `.gitignore` — isporučuje se
šema, ne podaci.

Postgres tek ako zatreba više servera nad istom bazom, replikacija, ili hosting
bez trajnog diska. Repository pattern čini tu migraciju jednodnevnom.

---

## 11. Put ka vebu i botu

### Veb (faza 4)

1. WebSocket adapter pored TCP-a; server sluša oba: `--tcp 5000 --ws 8000`
2. Serviranje statike
3. `net.js` i `state.js` — **prevod** iz Pythona, ne novi dizajn
4. `board.js` + CSS Grid; iste SVG figure, isti `sr.json`

Procena preživljavanja koda: `core` 100% · `protocol` 100% · `server` ~85% ·
klijentska logika prevod 1:1 · samo sloj crtanja se piše iznova.

### Bot (faza 6)

`BotPlayer` implementira isti `Player` interfejs kao `RemotePlayer`. Session sloj
ne zna razliku — bot vs čovek, bot vs bot i čovek vs čovek rade bez izmena servera.

Zato je make/unmake obavezno već u fazi 1: bot poziva generator miliona puta
u sekundi tokom pretrage.

Cilj kasnije: **UCI** interfejs, da bot može da igra protiv Stockfish-a.

Avatar bota se crta u klijentu koji je aktivan. SVG/PNG materijal se koristi u oba.

---

## 12. Licence

- **Figure:** Cburnett SVG set sa Wikimedia Commons. Višestruko licenciran
  (BSD-3, CC-BY-SA-3.0, GFDL, GPL) — biramo **BSD-3**, obična atribucija bez
  copyleft obaveze. Atribucija u `assets/pieces/LICENSE.txt`.
- **Font:** DejaVu Sans (slobodna licenca) — mora da podržava č ć š ž đ.
  Ne oslanjati se na podrazumevani pygame font bez provere.
