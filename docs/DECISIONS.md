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

> ⚠️ **Delimično zamenjeno ADR-om 016.** Izbor `socket`-a važi. Model
> konkurentnosti ne — umesto `threading` koristi se jednonitni `selectors`
> event loop.

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

**Posledice.** Perft na dubini 5 traje minut-dva umesto desetak minuta. Bot u
fazi 6 poziva generator miliona puta u sekundi — sa kopiranjem bi bio neupotrebljiv.
Cena: `unmake` mora tačno da vrati prava na rokadu, en passant polje i brojač
polupoteza, što je izvor bagova ako se ne testira. Perft to pokriva.

---

## ADR-007: Perft kao dokaz ispravnosti

> ⚠️ **Delimično zamenjeno ADR-om 019.** Princip važi. Ali perft postoji kao
> alat od taska 1.3, ne tek na 1.8; podrazumevani checkpoint je dubina 4, a
> dubina 5 ide iza `CHESS_SLOW_TESTS=1`.

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

> ⚠️ **Komanda za pokretanje zamenjena ADR-om 029.** Umesto
> `pip install pygame` ide `pip install -e .` — `src/` raspored traži
> instalaciju paketa. Princip "radi posle klonirаnja" ostaje.

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

> ⚠️ **Precizirano ADR-om 020.** Pravila projekta se izdvajaju u
> `docs/CONVENTIONS.md` koji **ide u git**. Van gita ostaje samo `CLAUDE.md`
> i `.claude/`.

**Kontekst.** Repozitorijum je javan. U gitu se ništa ne briše — što uđe u
commit, ostaje u istoriji zauvek.

**Odluka.** `.gitignore` sa `.claude/` i `CLAUDE.md` postoji **pre prvog commita**.

**Posledice.** Istorija je čista od nultog commita, nema šta da se briše kasnije.
Cena: ti fajlovi nisu verzionisani — treba im kopija van foldera projekta.

---

## ADR-013: `Square` je `int`, ne dataclass

> ⚠️ **Precizirano ADR-om 031.** `Square` je običan alias `Square = int`, ne
> `NewType` — bez type checkera `NewType` ne daje nikakvu garanciju.

**Kontekst.** Prvobitni plan je stavljao `Square` u istu korpu sa `Move` kao
`frozen=True` dataclass. Perft na dubini 5 obilazi 4.865.609 čvorova i alocirao
bi desetine miliona `Square` objekata.

**Odluka.** `Square` je običan `int` 0–63. Čitljivost se dobija imenovanim
konstantama (`E4 = 28`) i funkcijama `file_of()`, `rank_of()`, `to_algebraic()`,
`from_algebraic()`.

`Move` ostaje `frozen=True` dataclass, ali sa `slots=True`. Pakovanje poteza u
int (kako rade pravi engine-i) razmatramo **tek ako merenje pokaže da je
potrebno** — ne optimizujemo unapred.

**Posledice.** Perft je upotrebljivo brz. Cena: `Square` nije tip-siguran, pa
funkcije koje ga primaju moraju to jasno da imenuju u potpisu i docstringu.

---

## ADR-014: Undo zapis se definiše u tasku 1.2

> ⚠️ **Dopunjeno ADR-om 022.** Nedostajalo je **polje pojedene figure** — kod
> en passanta pojedeni pešak nije na odredišnom polju. Rešeno uvođenjem
> `Move.kind`.

**Kontekst.** `unmake` ne može da vrati stanje ako se ne zapamti šta je potez
promenio. Prvobitni ROADMAP to nije naveo, pa bi se propust otkrio tek na
perft checkpointu — kad je najskuplje.

**Odluka.** `UndoRecord` se definiše zajedno sa `make/unmake` i sadrži:

| Polje | Zašto |
|---|---|
| pojedena figura **i njeno polje** | kod en passanta pojedeni pešak nije na odredišnom polju |
| prethodna prava na rokadu | pomeranje topa ili kralja ih gasi nepovratno |
| prethodno en passant polje | pravo traje tačno jedan potez |
| prethodni brojač polupoteza | pravilo 50 poteza |
| prethodni Zobrist ključ | jeftinije od ponovnog računanja |

**Posledice.** `unmake` je tačan po konstrukciji. Cena: svaki novi tip poteza
mora da dopuni undo zapis — što perft odmah uhvati ako se zaboravi.

---

## ADR-015: Zobrist heš u tasku 1.2, ne u 1.9

**Kontekst.** Trostruko ponavljanje traži poređenje pozicija po četiri stvari:
raspored, ko je na potezu, prava na rokadu, en passant polje. Plan je to stavljao
u 1.9, što bi značilo povratak u `board.py` posle checkpointa.

**Odluka.** Zobrist heš se uvodi u 1.2 i održava **inkrementalno** u
`make/unmake` — XOR ulaz i izlaz umesto ponovnog računanja cele pozicije.

**Posledice.** Ponavljanje u 1.9 je tada samo brojanje ključeva u istoriji.
Isti heš služi transpozicionoj tabeli bota u fazi 6 — plaća se jednom,
koristi dvaput. Cena: jedan koncept više u fazi 1.

---

## ADR-016: Server je jednonitni `selectors` event loop

**Kontekst.** Prvobitni plan: nit po klijentu sa `Lock` oko stanja. Uz to je
stajalo da server računa vreme "pri svakom događaju" — što znači da pad
zastavice **nikad ne bi bio detektovan** ako igrač prestane da šalje poruke.
Partija bi visila zauvek.

**Odluka.** Jedna nit, `selectors`, sa `select(timeout=vreme_do_najbliže_zastavice)`.

**Posledice.** Tri problema rešena jednom odlukom: pad zastavice okida sam,
nema `Lock`-ova, nema race condition-a. Cena: kod je organizovan oko event
loop-a, što je manje intuitivno od niti dok se ne navikneš.

---

## ADR-017: `tools/cli_client.py` umesto `nc`

**Kontekst.** Checkpoint faze 2 je bio "dva `nc localhost 5000` terminala
odigraju partiju". `nc` ne postoji na Windows-u, pa checkpoint nije bio
sprovodiv u razvojnom okruženju.

**Odluka.** Mali CLI klijent od tridesetak linija u standardnoj biblioteci,
task 2.0. Prima poteze u UCI formatu (`e2e4`), prevodi ih u protokol poruke,
ispisuje odgovore.

**Posledice.** Checkpoint radi na Windows-u. Dobijamo trajan debug alat, i
kasnije osnovu za pokretanje bota kao spoljnog klijenta. Cena: pola sata rada.

---

## ADR-018: Format poteza — strukturiran na žici, UCI u `core`

**Kontekst.** Predlog je bio da se potezi na žici šalju kao UCI stringovi
(`e2e4`, `e7e8q`) umesto strukturirano.

**Odluka.** Na žici ostaje strukturirano: `{"from": "e2", "to": "e4",
"promotion": "queen"}`. To je idiomatski JSON, čitljivije pri debug-u, i lakše
za JavaScript klijent u fazi 4.

Ali `core` dobija `Move.from_uci()` i `Move.to_uci()`, jer trebaju za CLI
klijent, za testove i za UCI interfejs bota u 6.8.

**Posledice.** Oba formata postoje, svaki tamo gde je bolji. Cena: dvadesetak
linija konverzije.

---

## ADR-019: Perft je alat od 1.3, ne checkpoint na 1.8

> ⚠️ **Podela dubina zamenjena ADR-om 026.** Kiwipete d4 (4.085.603) i početna
> d5 (4.865.609) su isti red veličine, pa podela nije postigla cilj. Princip
> "perft je alat od 1.3" ostaje.

**Kontekst.** Perft je bio zakazan tek za 1.8. To znači da se generisanje poteza
piše kroz tri taska bez ijedne provere ispravnosti.

**Odluka.** Perft harness sa `perft_divide` postoji od 1.3 i koristi se pri
svakoj izmeni generatora. `perft_divide` broji čvorove **po korenskom potezu**,
pa se odstupanje lokalizuje binarnom pretragom umesto ručnim traženjem.

Perft 4 ostaje u podrazumevanom test suite-u. Perft 5 ide iza promenljive
`CHESS_SLOW_TESTS=1`, jer minut-dva po pokretanju znači da posle nedelju dana
prestaneš da puštaš testove.

**Posledice.** Greška se hvata u tasku u kom je napravljena. 1.8 ostaje kao
formalni checkpoint, ali bez iznenađenja.

---

## ADR-020: Konvencije u git, Claude fajlovi van gita

**Kontekst.** `CLAUDE.md` je bio u `.gitignore`, što je u prividnom sukobu sa
principom iz ADR-009 — sve što je projektu potrebno mora biti u repozitorijumu.

**Odluka.** Razdvajaju se dve stvari koje su bile spojene u jedan fajl:

| Fajl | Sadržaj | Git |
|---|---|---|
| `docs/CONVENTIONS.md` | pravila projekta: slojevi, imenovanje, testovi, git tok | **da** |
| `CLAUDE.md` | uputstvo asistentu; upućuje na `CONVENTIONS.md` | ne |

Princip iz ADR-009 se odnosi na ono što je potrebno da se projekat **pokrene**.
`CLAUDE.md` tome ne pripada. Konvencije pripadaju — i pripadale bi svakom
projektu, sa asistentom ili bez njega.

**Posledice.** Konvencije su normalna inženjerska dokumentacija i njihovo
prisustvo poboljšava repozitorijum. Bilo koji chat ili alat sa pristupom
GitHub-u može ih sam učitati, bez lepljenja. Cena: dva fajla umesto jednog,
i `CLAUDE.md` i dalje nije verzionisan pa mu treba kopija van projekta.

---

## ADR-021: Razumevanje se proverava pitanjima, ne autorstvom

**Kontekst.** Cilj projekta je da korisnik nauči i razume šta je napravljeno.
U pregledu je predloženo da korisnik fazu 1 piše rukom, uz obrazloženje da
"čitanje diffa daje osećaj razumevanja bez razumevanja".

Prva rečenica je tačna. Zaključak nije bio.

Odbrana traje 15 minuta i sastoji se od prezentacije i dokumentacije. Kod se ne
pokazuje i o njemu se ne ispituje. Ručno kucanje engine-a bi produžilo fazu 1 za
nedelju dana da bi rešilo problem koji ne postoji.

Uz to, kucanje nije ono što stvara razumevanje — **odgovaranje na pitanja jeste.**
Aktivno prisećanje je efikasnije od prepisivanja i traje minute umesto dana.

**Odluka.** Claude Code piše sav kod. Razumevanje se obezbeđuje ritmom po tasku:

1. Plan mod — korisnik čita plan pre nego što kod postoji
2. Claude Code implementira
3. Claude Code objašnjava u tri do pet rečenica: šta je urađeno, zašto tako,
   koja alternativa je odbačena i zbog čega
4. **Claude Code postavlja korisniku dva do tri pitanja o upravo napisanom kodu**
5. Korisnik odgovara. Ako ne zna — Claude Code objašnjava drugačije, pa opet.
6. Na kraju faze korisnik prepričava celu fazu svojim rečima; Claude Code od
   toga piše `docs/faze/faza-N.md`

Korak 4 je obavezan i ne preskače se. Pitanja moraju biti o **zašto**, ne o
**šta**: "zašto filtriramo legalnost posle generisanja umesto tokom" je dobro
pitanje, "šta radi ova funkcija" nije.

**Pitanja i odgovori se zapisuju.** Posle svakog taska Claude Code dodaje dva
reda u `docs/faze/faza-N.md`: postavljeno pitanje i da li je korisnik znao
odgovor. Bez toga "gde zapneš, tu se vraćaš" nema gde da zapamti gde si zapeo —
sve nestaje sa `/clear`.

**Posledice.** Faza 1 ne traje duže nego u prvobitnom planu. Razumevanje se meri
odgovorom, ne osećajem. Dokumentacija po fazama nastaje kao nusprodukt umesto
kao poseban posao na kraju. Cena: dva do tri minuta po tasku.

---

## ADR-022: `Move` nosi `kind`

**Kontekst.** Tri odvojena problema pokazala su se kao isti problem:

1. `UndoRecord` ne može ispravno da vrati en passant — pojedeni pešak nije na
   odredišnom polju nego iza njega, pa bi `unmake` morao to da **zaključuje**
2. `legal_moves` u protokolu ne može da izrazi promociju — pešak na `e7` ima
   četiri legalna poteza na `e8`, a mapa `from → [to]` ih spaja u jedan
3. `make` i `unmake` bi bili gomila `if`-ova koji rekonstruišu šta je potez bio

**Odluka.** `Move` dobija polje `kind`: `NORMAL`, `CAPTURE`, `DOUBLE_PAWN_PUSH`,
`EN_PASSANT`, `CASTLE`, `PROMOTION`. Uvodi se u tasku 1.1.

Generator poteza zna koju vrstu pravi, pa je popunjavanje besplatno.

**Posledice.**

- `make`/`unmake` postaju grananje po vrsti umesto zaključivanja
- `UndoRecord` ne izvodi ništa — vrsta mu je data
- Protokol može da nosi `{"to": "e8", "promotion": true}`, pa klijent zna kad da
  otvori dijalog **bez ijednog šahovskog pravila**
- `Move.from_uci()` **ne može da odredi `kind` bez table** — i to je dobro.
  Tera na ispravan obrazac: potez iz spoljnog sveta se **traži u listi
  generisanih legalnih poteza**, nikad se ne izvršava direktno. Isto je i
  bezbednosno ispravno.

Cena: jedan enum više u fazi 1.

---

## ADR-023: `STATE` je pun snapshot, ne delta

**Kontekst.** `STATE` je nosio samo `last_move`, pa je klijent akumulirao
istoriju poteza za prikaz iz taska 3.7. To radi dok klijent ne propusti nijednu
poruku — a onda dolazi rekonekcija iz 5.7 i klijent koji se vratio nema ništa.

**Odluka.** Svaka `STATE` poruka sadrži sve što treba da se nacrta ceo ekran od
nule, uključujući `history` kao listu SAN poteza. Klijent ne akumulira ništa.

**Posledice.** Rekonekcija postaje besplatna — dobiješ poslednji `STATE` i
nastaviš. Klijent nema akumulirano stanje koje bi moglo da se raziđe sa serverom.
Cena: partija od 80 poteza nosi par stotina bajtova više po poruci, što je na
`localhost` i na vebu nemerljivo.

---

## ADR-024: Granica između čitanja pozicije i odlučivanja

> ⚠️ **Način provere zamenjen ADR-om 033.** Granica se proverava
> `tools/layer_check.py` alatom u gitu, pokrenutim kao test — ne skillom.
> Sama granica ostaje neizmenjena.

**Kontekst.** Pravilo "nula šahovske logike u klijentu" je nejasno u jednom
slučaju: klijent mora da parsira FEN da bi nacrtao tablu. Da li je to kršenje?

Bez zapisane granice, o ovome bi se raspravljalo za mesec dana.

**Odluka.** Granica je između **čitanja pozicije** i **odlučivanja o legalnosti**.

| | Klijent |
|---|---|
| parsiranje FEN-a, crtanje table | ✅ |
| računanje kuda figura sme | ❌ |

Konkretno: pygame klijent sme da uvozi **samo** `core/types.py` i `core/fen.py`.
Nikad `movegen`, `attacks`, `rules` ni `game`.

**Posledice.** Pravilo je proverivo automatski (vidi ADR-033).
Veb klijent u fazi 4 reimplementira parsiranje FEN-a u JavaScriptu, što je
takođe dozvoljeno po istoj logici. Cena: nikakva.

---

## ADR-025: Nedefinisano ponašanje — diskonekcija, remi, potez u letu

**Kontekst.** Tri situacije koje task 2.7 traži, a nigde nisu bile zapisane.

**Odluka.**

**Diskonekcija.** Server šalje `OPPONENT_DISCONNECTED`. **Sat protivnika
nastavlja da ide**, partija se završava padom zastavice sa `termination:
"timeout"`. Ne uvodi se nijedan nov mehanizam, poklapa se sa ponašanjem online
platformi, i ostavlja mesto za rekonekciju u fazi 5 bez izmene protokola.

**Ponuda remija.** Nudi se samo kad si na potezu. Pada čim protivnik odigra
potez (FIDE). Jedna ponuda po potezu — druga vraća `DRAW_ALREADY_OFFERED`.

**Potez u letu.** Najviše jedna `MOVE` poruka bez odgovora. Uz to `ERROR`
vezan za potez **nosi polje `move`**, pa klijent zna koju figuru da vrati posle
neuspelog drag & drop-a. Pojas i tregeri — pravilo je zapisano, ali klijent ne
zavisi od toga da ga server poštuje.

**Posledice.** Task 2.7 ima šta da implementira. Cena: tri nova koda greške.

---

## ADR-026: Perft — skup pozicija i podela dubina

**Kontekst.** ADR-019 je delio perft na "brz default" i "spor iza
`CHESS_SLOW_TESTS`", ali aritmetika ne podržava tu podelu: Kiwipete dubina 4 je
4.085.603 čvora, a početna pozicija dubina 5 je 4.865.609. Isti red veličine —
podrazumevani suite je već bio spor.

Uz to, dve pozicije ne pokrivaju dovoljno. Standardni skup sa Chess Programming
Wiki ima šest, i svaka gađa drugu klasu bagova.

**Odluka.**

| | Pozicije | Približno čvorova |
|---|---|---|
| Podrazumevano | početna d4 · Kiwipete d3 · Position 3 d4 · Position 4 d3 | ~300.000 |
| `CHESS_SLOW_TESTS=1` | početna d5 · Kiwipete d4 · ostale dublje | ~9.000.000 |

Position 3 lovi en passant, Position 4 promociju i vezane figure, Position 5
rokadu u neobičnim pozicijama.

> **FEN-ove i referentne brojeve prepisati sa Chess Programming Wiki.**
> Nikad iz sećanja — ni čovekovog ni modelovog. Ako referenca nije potvrđena,
> reci to umesto da pretpostaviš.

**Posledice.** Četiri pozicije na maloj dubini nalaze više bagova po sekundi
nego dve na velikoj. Podrazumevani suite ostaje brz, pa se stvarno pokreće.

---

## ADR-027: Zobrist — fiksan seed, en passant uslovno

**Kontekst.** Dve zamke koje prave suptilne bagove.

**Odluka.**

**Fiksan seed.** Tabela nasumičnih brojeva generiše se sa zadatim seed-om.
Bez toga su ključevi različiti pri svakom pokretanju i testovi nisu
deterministički — što krši pravilo determinizma iz `docs/CONVENTIONS.md` §5.

**En passant uslovno.** Ep polje ulazi u ključ **samo kad je en passant
uzimanje stvarno moguće** (postoji protivnički pešak koji sme da uzme).
Ako se XOR-uje uvek, pozicija posle `e2-e4` nikad neće biti jednaka istoj
poziciji dobijenoj drugim redosledom poteza, i trostruko ponavljanje neće
okinuti kad treba.

**Posledice.** Ponavljanje radi tačno. Testovi su ponovljivi. Cena: jedna
provera više pri ažuriranju ključa.

---

## ADR-028: `tools/perft.py` u git, skill samo poziva

**Kontekst.** Logika iz ADR-020 nije bila primenjena dosledno. Perft runner je
živeo u `.claude/skills/perft/`, što je van gita — a perft runner je **alat
projekta**, ne uputstvo asistentu.

**Odluka.** Perft harness ide u `tools/perft.py`, u git. `.claude/skills/perft/SKILL.md`
se svodi na nekoliko redova koji taj alat pozivaju i objašnjavaju kad.

Isto pravilo važi unapred: **ako nešto radi i bez asistenta, ide u git.**

**Posledice.** Perft se može pokrenuti ručno, iz CI-ja, ili od strane bilo koga
ko klonira repozitorijum. Skill ostaje tanak. Cena: nikakva.

---

## ADR-029: `pip install -e .` kao jedina komanda za pokretanje

**Kontekst.** Sa `src/chess/` rasporedom, `python -m unittest discover -s tests`
**ne nalazi paket**, jer `src/` nije na `sys.path`. Checkpoint faze 0 ne bi
prošao prvog dana.

Uz to, rečenica iz `PROJECT.md` — *"Pokretanje: `pip install pygame`. To je sve."* —
postaje netačna.

**Odluka.** `pygame` je deklarisan kao zavisnost u `pyproject.toml`, a uputstvo
za pokretanje postaje:

```bash
pip install -e .
```

Jedna komanda, koja instalira i paket u editable režimu i sve zavisnosti.

**Posledice.** `src/` raspored ostaje (sprečava da testovi slučajno uvezu fajlove
iz radnog direktorijuma umesto instalirani paket). Obećanje "jedna komanda" i
dalje stoji. `PROJECT.md` §4 mora biti ispravljen.

---

## ADR-030: ADR koji obara tekst ispravlja ga u istom commitu

**Kontekst.** Posle prvog kruga pregleda, `PROTOCOL.md` §7 je i dalje opisivao
model sata koji je ADR-016 proglasio neispravnim, a §8 je i dalje pominjao `nc`
koji je ADR-017 zamenio. `PROJECT.md` je zaostajao za tri odluke.

`DECISIONS.md` je append-only i to je ispravno. Ali nigde nije pisalo da odluka
mora biti **propagirana** u dokumente koje obara.

**Odluka.** Kad ADR obori nešto napisano u `PROJECT.md`, `PROTOCOL.md`,
`ROADMAP.md` ili `CONVENTIONS.md`, ispravka tih dokumenata ide u **istom commitu**
kao i ADR. Bez izuzetka.

Hijerarhija kad se dokumenti ne slažu:

```
DECISIONS.md  >  PROTOCOL.md  >  PROJECT.md  >  ROADMAP.md
```

**Posledice.** Dokument koji zaostaje za odlukama je gori od dokumenta koji ne
postoji, jer mu se veruje. Ovo pravilo ide i u `docs/CONVENTIONS.md` §1.
Cena: nekoliko minuta po ADR-u.

---

## ADR-031: Bez type checkera za sada

**Kontekst.** `ruff` ne proverava tipove. Bez mypy-ja, `Square = NewType("Square", int)`
iz ADR-013 ne daje nikakvu garanciju — ostaje `int` sa lepim imenom.

**Odluka.** Ne uvodimo mypy. `Square` je običan alias `Square = int`, bez
pretvaranja da je proveren. Type hints se i dalje pišu svuda — služe čitljivosti
i IDE-u.

Revidira se u fazi 4, kad `core` bude stabilan i kad dodavanje alata ne usporava.

**Posledice.** Manje alata za konfigurisanje i manje trenja u fazi u kojoj se
najviše menja. Cena: greške u tipovima se hvataju testovima, ne alatom.
Perft to uglavnom pokriva za `core`.

---

## ADR-032: Hijerarhija dokumenata i obavezna oznaka na oborenom ADR-u

**Kontekst.** ADR-030 je nabrojao četiri dokumenta u pravilu propagacije, jer
`POJMOVNIK.md` i `WORKFLOW.md` tada nisu postojali. Uz to, ADR-030 nije rekao
šta se dešava kad **novi ADR obori stariji ADR** — pa je ADR-029 oborio ADR-009
bez ijedne oznake, i propust je primećen tek u trećem krugu pregleda.

Drugim rečima: pravilo propagacije je prekršeno u istom dokumentu koji ga uvodi.

**Odluka.**

**Puna hijerarhija:**

```
DECISIONS.md > PROTOCOL.md > CONVENTIONS.md > PROJECT.md > ROADMAP.md > POJMOVNIK.md
```

`CONVENTIONS.md` obavezuje kod, ali ne sme da protivreči protokolu — protokol je
ugovor sa spoljnim svetom, konvencije su unutrašnja stvar. `POJMOVNIK.md` nema
autoritet: objašnjava, ne propisuje, i uvek je on taj koji se ispravlja.

**Propagacija važi za svaki fajl u `docs/`**, ne samo za četiri iz ADR-030.

**Novi ADR koji obara stariji obavezno stavlja ⚠️ oznaku na vrh starijeg**, sa
pokazivačem na novi. Stari ADR se ne briše — fajl je append-only i istorija
odluka se čuva cela.

**Posledice.** Čitalac koji naiđe na stari ADR odmah zna da nastavi dalje.
Bez toga bi neko implementirao `threading` po ADR-003 ili `pip install pygame`
po ADR-009. Cena: jedan blok teksta po oborenom ADR-u.

---

## ADR-033: `tools/layer_check.py` kao alat i test, ne skill

**Kontekst.** ADR-024 je rekao da se granica slojeva proverava `layer-check`
skillom. To protivreči ADR-028: *ako nešto radi i bez asistenta, ide u git.*

Provera uvoza radi bez asistenta — to je lint pravilo, ne uputstvo. Uz to,
skill se okida kad ga model prepozna kao relevantan, a to nije garancija.

**Odluka.** `tools/layer_check.py` ide u git. Parsira `import` naredbe kroz
`ast` i prijavljuje svaki uvoz koji tabela iz `CONVENTIONS.md` §2 ne dozvoljava.

Pokreće se **i kao test** (`tests/test_layers.py`), pa checkpoint faze 0 pada
ako se pravilo prekrši. `.claude/skills/layer-check/` se svodi na nekoliko redova
koji pozivaju alat.

**Posledice.** Kršenje granice hvata test suite, ne asistent koji se seti da
pozove skill. Pravilo postaje izvršivo za bilo koga ko klonira repozitorijum.
Cena: pedesetak linija koda u fazi 0.

---

## ADR-034: `capture` je uvek serverski podatak

**Kontekst.** Polje `capture` u `legal_moves` pojavljivalo se samo u primeru za
promociju, bez ijedne rečenice da li stoji na svakom potezu koji uzima.

Klijent bi mogao da ga izvede sam — „ima li figure na odredišnom polju".
Ali **kod en passanta odredišno polje je prazno**, pa bi takav klijent nacrtao
pogrešno. A klijent koji to ispravno izvede upravo je implementirao šahovsko
pravilo, što krši ADR-001.

**Odluka.** `capture: true` server šalje na **svakom** potezu koji uzima figuru,
uključujući en passant. Klijent ga nikad ne izvodi.

Isto važi za `promotion`. Promocija je uvek u jednu od četiri figure —
`queen`, `rook`, `bishop`, `knight` — i to je zapisano u `PROTOCOL.md` da ne bi
bilo neizrečena pretpostavka u klijentu.

**Posledice.** Klijent crta prsten uzimanja i otvara dijalog za promociju bez
ijednog šahovskog pravila. Cena: jedan bool po potezu u `STATE` poruci.
