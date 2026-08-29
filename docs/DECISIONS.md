# ODLUKE (ADR)

*Architecture Decision Records.* Svaka odluka sa kontekstom i posledicama.
Dopunjava se kad god se donese arhitektonska odluka. Append-only — stare odluke
se ne brišu, nego se nadograđuju novim ADR-om koji ih menja.

Format: **Kontekst** (zašto je pitanje uopšte postavljeno) → **Odluka** →
**Posledice** (šta smo dobili, šta smo izgubili).

---

## ADR-001: Server je autoritet nad pravilima

**Kontekst.** Mentor traži da se proveravaju dozvoljeni potezi. Logika može da
živi u klijentu ili u serveru.

**Odluka.** Sva šahovska pravila su na serveru. Klijent šalje nameru, server
validira i emituje stanje. Klijent ne sadrži nijedno šahovsko pravilo.

**Posledice.** Svaki budući klijent (veb, mobilni) je trivijalan jer ne mora da
implementira pravila. Klijent ne može da vara. Cena: jedno mrežno kruženje po
potezu, što je na `localhost` nemerljivo.

---

## ADR-002: Ports and adapters

**Kontekst.** Projekat treba da preraste iz desktop aplikacije u sajt, i kasnije
da dobije bota. Ne sme se pisati dvaput.

**Odluka.** `core` i session sloj ne znaju ko ih poziva. Transport je adapter.
Smer zavisnosti: `client → protocol → core`, nikad obrnuto.

**Posledice.** Veb klijent, bot i eventualni mobilni klijent su adapteri, ne
prepisivanja. Procena preživljavanja koda pri prelasku na veb: `core` 100%,
`protocol` 100%, `server` ~85%. Cena: nešto više fajlova nego kod monolita.

---

## ADR-003: Sirovi `socket` umesto framework-a

**Kontekst.** Mentor je tražio socket-e. Kandidati: `socket` + `threading`,
FastAPI, Flask, `websockets`.

**Odluka.** `socket` + `threading` iz standardne biblioteke, JSON razdvojen
znakom `\n`. FastAPI, uvicorn i Pydantic svesno odbijeni — korisnik ih već zna
i traži jednostavnije tehnologije.

**Posledice.** Nula zavisnosti za mrežni sloj. Zahtev mentora ispunjen doslovno.
Validaciju poruka pišemo sami (~80 linija) umesto da je dobijemo od Pydantic-a —
što je i namera, jer korisnik treba da razume granicu sistema.

---

## ADR-004: pygame klijent prvi, veb kasnije

**Kontekst.** Krajnji cilj je sajt. Ali kratkoročni prioritet je zahtev mentora,
a korisnik je tražio malo tehnologija i sve u Pythonu.

**Odluka.** Faza 3 je pygame klijent. Faza 4 je veb klijent u vanilla JS
(bez React-a, bez Node-a, bez build koraka).

**Posledice.** Klijentski sloj se piše dvaput — ukupno oko nedelju dana više nego
da se odmah išlo na veb. Zauzvrat: faze 0–3 su u jednom jeziku, sa jednom
zavisnošću, i mentorov zahtev je ispunjen najdirektnije mogućim putem.
`net.py` i `state.py` pišu se **bez pygame-a** baš zato da bi se kasnije preveli
1:1 u JavaScript.

---

## ADR-005: `unittest` umesto `pytest`

**Kontekst.** `pytest` je industrijski standard, ali je dodatna zavisnost.

**Odluka.** `unittest` iz standardne biblioteke. Perft tabele kroz `subTest()`.

**Posledice.** Nula zavisnosti za testove, `python -m unittest discover` radi bez
instalacije. Verboznije nego `pytest`. `pytest` može da pokrene `unittest` testove,
pa nijedna vrata nisu zatvorena.

---

## ADR-006: make/unmake umesto kopiranja table

**Kontekst.** Pri generisanju legalnih poteza treba proveriti da li potez ostavlja
kralja u šahu. Najjednostavnije je kopirati tablu, odigrati, proveriti.

**Odluka.** Potez se odigra na istoj tabli i vrati (`make` / `unmake`).

**Posledice.** Perft na dubini 5 traje sekunde umesto minuta. Bot u fazi 6 poziva
generator miliona puta u sekundi — sa kopiranjem bi bio neupotrebljiv.
Cena: `unmake` mora tačno da vrati prava na rokadu, en passant polje i brojač
polupoteza, što je izvor bagova ako se ne testira. Perft to pokriva.

---

## ADR-007: Perft kao dokaz ispravnosti

**Kontekst.** Kako dokazati da generator poteza radi ispravno u svim slučajevima,
uključujući rokadu, en passant, vezane figure i otkrivene šahove.

**Odluka.** Perft — brojanje čvorova do dubine N i poređenje sa objavljenim
referentnim vrednostima. Checkpoint faze 1: dubina 5 iz početne pozicije i
dubina 4 iz Kiwipete pozicije.

**Posledice.** Ispravnost je dokazana, ne pretpostavljena. Bag se lokalizuje
poređenjem po prvom potezu umesto ručnim traženjem. Cena: perft mora biti brz,
što povezuje ovu odluku sa ADR-006.

---

## ADR-008: `RuleSet` sa profilima `online` i `fide`

**Kontekst.** FIDE razlikuje remi na zahtev (trostruko ponavljanje, 50 poteza) od
automatskog (petostruko, 75 poteza). Online platforme se namerno ponašaju drugačije.

**Odluka.** Pravila su konfiguracija, ne `if` u kodu. Podrazumevan profil `online`:
trostruko ponavljanje i 50 poteza primenjuju se automatski. Profil `fide` je striktan.

**Posledice.** Ponašanje je eksplicitno i dokumentovano umesto slučajno. Lako se
dodaje treći profil. Cena: jedan sloj konfiguracije više.

---

## ADR-009: SQLite, sa repository pattern-om od početka

**Kontekst.** Prethodni projekat korisnika (FastAPI + SQL Server) nije radio kod
druge osobe: baza nije bila instalirana, kredencijali nisu bili u repozitorijumu,
šema nije postojala, ODBC drajver je nedostajao.

**Odluka.** SQLite iz standardne biblioteke, od faze 5. Server nikad ne piše SQL
direktno — koristi `GameRepository` interfejs. Migracije kao numerisani SQL fajlovi
sa tabelom `schema_version`. Putanja kroz `CHESS_DB_PATH` sa podrazumevanom vrednošću.

**Posledice.** `git clone` + `pip install pygame` + pokretanje = radi, baza se
napravi sama. Migracija na Postgres je jedan dan (nova implementacija interfejsa).
`InMemoryGameRepository` čini testove brzim i determinističkim.
Cena: interfejs koji u fazi 5 ima samo jednu implementaciju.

---

## ADR-010: Tekst korisničkog interfejsa u `sr.json`

**Kontekst.** Interfejs je na srpskom, kod na engleskom, a kasnije dolazi veb
klijent koji bi tražio iste tekstove.

**Odluka.** Nijedan tekst vidljiv korisniku ne sme biti u kodu. Sve ide kroz
ključeve u `assets/i18n/sr.json`. Isti fajl čitaju i pygame i JavaScript klijent.

**Posledice.** Prevodi se pišu jednom. Engleska verzija je kasnije samo `en.json`.
Logovi ostaju na engleskom bez dijakritika zbog Windows konzole. Font mora da
podržava č ć š ž đ — pakuje se DejaVu Sans, ne oslanjamo se na podrazumevani.

---

## ADR-011: Lobby poruke definisane od faze 2

**Kontekst.** Traženje protivnika je funkcija servera, ne frontenda, i trebaće u
fazi 5. Naknadno dodavanje bi lomilo postojeće klijente.

**Odluka.** `LOBBY_JOIN`, `LOBBY_STATE` i `MATCH_FOUND` postoje u protokolu od
faze 2. U fazi 2 server samo spari prva dva klijenta u redu.

**Posledice.** Faza 5 popunjava prazno mesto umesto da menja verziju protokola.
Cena sada: oko 20 linija koda.

---

## ADR-012: Claude Code fajlovi izvan repozitorijuma

**Kontekst.** Repozitorijum je javan. U gitu se ništa ne briše — što uđe u
commit, ostaje u istoriji zauvek.

**Odluka.** `.gitignore` sa `.claude/` i `CLAUDE.md` postoji **pre prvog commita**.

**Posledice.** Istorija je čista od nultog commita, nema šta da se briše kasnije.
Cena: ti fajlovi nisu verzionisani — treba im kopija van foldera projekta.
