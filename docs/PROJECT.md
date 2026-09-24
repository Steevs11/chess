# PROJEKAT — šahovska aplikacija

Kompletan opis projekta. Čita se jednom, na početku.

| Dokument | Sadržaj |
|---|---|
| `docs/PROJECT.md` | šta pravimo, šahovska pravila, arhitektura |
| `docs/PROTOCOL.md` | ugovor između servera i klijenta |
| `docs/CONVENTIONS.md` | kako se piše kod |
| `docs/DECISIONS.md` | zašto je odlučeno baš tako (ADR) |
| `docs/ROADMAP.md` | lista taskova i trenutno stanje |
| `docs/WORKFLOW.md` | kako izgleda jedna sesija |

**Obim:** faze 0–3, do zahteva mentora. Faze 4–7 su pravac, ne posao.

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
| Server | `socket` + `selectors` (jedna nit) | — |
| Klijent | **pygame** | pygame |
| Baza (faza 5) | `sqlite3` kroz repository pattern | — |
| Dev | `ruff` | dev-only |

**Pokretanje: `pip install -e ".[dev]"`** — jedna komanda, instalira paket u
editable režimu i povlači `pygame` i `ruff` iz `pyproject.toml`. To je sve.

> Bez `-e` Python ne vidi paket (`src/` raspored); bez `[dev]` nema `ruff`-a, pa checkpoint
> ne prolazi. Navodnici su deo komande (ADR-029).

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
├── .gitattributes               tuđi materijal bajt u bajt (ADR-039)
├── pyproject.toml
├── LICENSE                      uslovi za naš kod, BSD-3-Clause (ADR-042)
├── THIRD-PARTY.txt              obim: šta LICENSE ne pokriva (ADR-042)
├── README.md                    (srpski)
├── src/chess/
│   ├── core/
│   │   ├── types.py             Color, PieceType, Piece, Square, Move, MoveKind, CastlingRights
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
│   ├── pieces/
│   │   ├── svg/                 12 Cburnett originala — izvor, BSD-3
│   │   ├── png/80/              rasterizovano za tablu
│   │   ├── png/32/              rasterizovano za pojedene figure (3.7)
│   │   └── LICENSE.txt
│   ├── fonts/
│   │   ├── DejaVuSans.ttf
│   │   ├── DejaVuSans-Bold.ttf
│   │   ├── LICENSE.txt          njihov — kopija iz arhive, ne dira se
│   │   └── PROVENANCE.txt       naš — verzija, izvor, sha256 (ADR-039)
│   └── i18n/sr.json
├── tools/
│   ├── check.py                 sve kapije jednom komandom (CONVENTIONS §9)
│   ├── perft.py                 perft + perft_divide (ADR-007)
│   ├── cli_client.py            CLI klijent za testiranje servera (ADR-017)
│   ├── layer_check.py           provera uvoza iz CONVENTIONS §2 (ADR-033)
│   ├── check_commit_trailers.py trajleri u porukama commita (ADR-047)
│   └── rasterize_pieces.py      SVG → PNG, dve veličine (ADR-038)
├── docs/
│   └── faze/                    faza-N.md, jedan kratak fajl po fazi
└── tests/
```

---

## 6. Sedam pravila nadogradivosti

Ovo je ono što čini prelazak na veb jeftinim. Ne krše se ni pod kojim izgovorom.

1. `core/` uvozi samo standardnu biblioteku
2. Protokol je JSON, verzionisan, dokumentovan u `PROTOCOL.md` — nikad `pickle`
3. Nula šahovske logike u klijentu — precizna granica je u `CONVENTIONS.md` §3
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
> Kod velike rokade polje `b1`/`b8` mora biti **prazno**, ali **sme biti napadnuto** —
> kralj kroz njega ne prolazi.

### En passant

Samo **odmah** posle protivničkog dvopoteznog pomeranja pešaka. Propušten potez
znači da pravo nestaje zauvek.

Pešak koji uzima mora biti na **5. redu** (beli), odnosno na **4. redu** (crni).

### Promocija

Dama, top, lovac ili skakač. **Podpromocija mora da radi.** Ne može ostati pešak,
ne može postati kralj.

Generator emituje **četiri** poteza za svaku promociju — jedan po figuri, ne jedan
potez sa izborom.

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
- Server čuva `remaining_ms` po igraču i `turn_started_at`, pa računa razliku
- **Pad zastavice okida sam**, kroz `select(timeout=vreme_do_najbliže_zastavice)`
  u `selectors` event loop-u. Ne čeka se poruka od igrača — inače bi partija u
  kojoj niko ništa ne šalje visila zauvek (ADR-016).

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

- **FEN** — pozicija; šest polja razdvojenih razmakom: raspored (od 8. reda ka 1.,
  velika slova = beli) · ko je na potezu · prava na rokadu · en passant **ciljno**
  polje · brojač polupoteza · broj poteza. Polje 5 je tačno ono što treba za
  pravilo 50 poteza.
- **SAN** — potezi sa disambiguacijom, i to **ovim redom**: kolona (`Nbd2`) → ako
  kolona ne razlikuje, red (`N1d2`) → ako ni to, oba (`Nb1d2`)
- **PGN** — cela partija

### Poeni figura

Dama 9 · top 5 · lovac 3 · skakač 3 · pešak 1. Prikazuje se razlika u materijalu.

---

## 8. Uloge

| | Radi |
|---|---|
| **Student** (arhitekta) | donosi odluke · čita ceo diff pre commita · objašnjava kod svojim rečima na kraju faze |
| **Claude Code** | piše testove i kod po odobrenom planu · pušta `tools/check.py` · ne menja testove da prođu · vodi `ROADMAP.md` i `DECISIONS.md` · piše `faza-N.md` na kraju faze |
| **Claude.ai** (planski chat) | arhitektura · objašnjenja · pregled diffova · debug razgovori |

Claude je vodeći inženjer: predlaže, ima mišljenje, kaže kad je nešto pogrešno. Odluke
ostaju kod studenta, jer on brani projekat i jer je razumevanje deklarisani cilj.

**Obrnuti pregled.** Na kraju faze (ili na kraju projekta) student objašnjava kod svojim
rečima, chat ispituje; gde zapne, tu se vraća na kod. To je mehanizam odbrane. Ne zapisuje
se.

---

## 9. Faze i checkpointovi

Checkpoint je objektivan uslov; meri se na svežem klonu u novom venv-u i ne prelazi se
dalje dok ne prođe.

| Faza | Sadržaj | Checkpoint |
|---|---|---|
| 0 | skelet, git, ruff, kapije | `python tools/check.py` zelen — **prošao** |
| 1 | **engine** — cela šahovska logika | perft se poklapa na skupu iz ADR-026 |
| 2 | protokol + server (TCP) | dva `tools/cli_client.py` terminala odigraju partiju sa rokadom i matom |
| 3 | **pygame klijent** | dva prozora igraju do mata → **video za mentora** |

Posle predaje, nije u obimu: veb klijent (4), SQLite i nalozi (5), bot (6), deploy (7).
Arhitektura ih ne isključuje: nov klijent je nov adapter, bot je treća implementacija
`Player`, baza ide iza `GameRepository` interfejsa (ADR-002, ADR-009).

Lista taskova: `docs/ROADMAP.md`.

---

## 10. Licence

- **Figure** — Cburnett set sa Wikimedia Commons, BSD-3 (autor nudi izbor; ne copyleft).
  SVG originali su u repou kao izvor, PNG-ovi u dve veličine su artefakt iz
  `tools/rasterize_pieces.py` (ADR-038). `assets/pieces/LICENSE.txt` nosi `sha1` svakog SVG-a.
- **Font** — DejaVu Sans 2.37, sopstvena licenca (Bitstream + Arev); `assets/fonts/LICENSE.txt`
  je kopija iz arhive bajt u bajt, naši podaci o poreklu su u `PROVENANCE.txt`.
- **Naš kod** — BSD-3-Clause u `LICENSE`; `THIRD-PARTY.txt` kaže šta taj fajl ne pokriva;
  ista oznaka je u `pyproject.toml` (ADR-042, ADR-043).

Tuđi materijal se čuva bajt u bajt: `.gitattributes` isključuje pretvaranje prelazaka reda,
a `tests/test_assets.py` proverava heševe, `.gitattributes` i lanac licenci (ADR-039).
