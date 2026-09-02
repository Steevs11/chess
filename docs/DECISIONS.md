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
> instalaciju paketa. Princip "radi posle kloniranja" ostaje.

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
> en passanta pojedeni pešak nije na odredišnom polju. Zapis nosi **i polje**
> pojedene figure; `Move.kind` iz ADR-022 dodatno uklanja svako zaključivanje.

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

> ⚠️ **Komanda precizirana ADR-om 036.** Glasi `pip install -e ".[dev]"` —
> bez `[dev]` se `ruff` ne instalira, pa checkpoint faze 0 ne može da prođe.
> Suština ovog ADR-a (editable install zbog `src/` rasporeda, jedna komanda)
> ostaje na snazi.

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

---

## ADR-035: `ruff` ne dira `docs/`

**Kontekst.** `ruff format --check .` je od prvog dana padao — ne na kodu, nego
na dokumentaciji. Od `ruff` 0.16 formatter ulazi i u Python blokove unutar
Markdown fajlova. U `CONVENTIONS.md` §7 stoji namerno zbijen primer:

```
with path.open(encoding="utf-8") as f: ...
```

`ruff` ga hoće razlomljenog na dva reda. Primer koji pokazuje *šta ruff radi*
bio je i sam prepravljen, pa je izjednačio „napisano" i „ruff hoće" — sam sebe
je pojeo.

Time je stavka iz CONVENTIONS §9 (`ruff format --check .` čist) bila nedostižna,
a jedina alternativa bila je prepravljanje dokumentacije da bi alat ćutao.

**Odluka.** `pyproject.toml` dobija `extend-exclude = ["docs"]` u `[tool.ruff]`.
Dokumentacija nije kod; formatter je nikad ne dodiruje.

Odbačena su tri druga puta:

- **prepraviti primer** — dokumentacija se ne krivi zbog alata
- **suziti komandu** na `ruff format --check src/ tests/` — gate glasi sa tačkom;
  komanda koja se sužava dok ne prođe više ništa ne dokazuje
- **`extend-exclude = ["*.md"]`** — izmereno: ne radi. Obrazac bez kose crte
  `ruff` 0.16.5 ne primeni; `"**/*.md"` je čak uvukao fajlove koje `.gitignore`
  isključuje. Prošli su `"docs"`, `"docs/*.md"` i `"docs/**/*.md"`; izabran je
  `"docs"` jer posle njega `ruff` vidi tačno `.py` fajlove projekta i ništa više.

**Posledice.** `ruff format --check .` je od sada upotrebljiv kao gate — prolazi
ili pada na kodu, i ni na čemu drugom. Isto važi za `ruff check .`, mada on
Markdown ionako nikad nije ni čitao.

**Šta smo izgubili:** Python blokovi u `docs/` više nemaju nikakvu mašinsku
proveru. Primer sa sintaksnom greškom u dokumentaciji proći će nezapaženo dok ga
neko ne prekopira i ne pokrene. Ako to jednom zaboli, rešenje nije vraćanje
formattera nego zaseban test koji blokove samo parsira, bez prepravljanja.

---

## ADR-036: `pip install -e ".[dev]"` — `[dev]` nije opcion

**Kontekst.** ADR-029 je uveo `pip install -e .` kao jedinu komandu za
pokretanje, a `PROJECT.md` §4 je tvrdio „To je sve." Ali `ruff` stoji u
`[project.optional-dependencies] dev`, pa ga ta komanda **ne instalira**.

Posledica je da onaj ko odradi tačno ono što dokumentacija kaže nema `ruff`, a
checkpoint faze 0 i CONVENTIONS §9 od njega traže `ruff check .` i
`ruff format --check .`. Obećanje „jedna komanda i sve radi" bilo je netačno od
prvog dana; primetilo se tek kad je gate stvarno pokrenut.

**Odluka.** Uputstvo za pokretanje glasi:

```bash
pip install -e ".[dev]"
```

Navodnici su deo komande: i `bash` i PowerShell drugačije čitaju gole uglaste
zagrade.

`ruff` **ostaje** u `dev` extra, ne seli se u `dependencies`. Igraču šaha linter
ne treba, a `PROJECT.md` §4 i CONVENTIONS §10 ga izričito vode kao `dev-only`.

**Posledice.** Obećanje „jedna komanda" i dalje stoji — komanda je i dalje jedna,
samo je tačna. ADR-029 nije oboren, nego preciziran, i nosi ⚠️ oznaku koja
pokazuje ovamo (CONVENTIONS §1, ADR-032).

**Šta smo izgubili:** komanda više nije ona koju čovek napiše iz navike, pa je
lakše zaboraviti `[dev]`. Ništa to ne hvata automatski — `tests/test_package.py`
proverava da je paket instaliran, ne da je instaliran **sa** `dev` skupom.
Izostavljen `[dev]` i dalje se otkriva tek kad `ruff` ne postoji.

---

## ADR-037: Tabela slojeva postaje izvršiva

**Kontekst.** ADR-033 je tražio alat koji sprovodi tabelu iz `CONVENTIONS.md` §2.
Pisanje tog alata otvorilo je tri pitanja na koja tabela — pisana za čoveka — nije
imala odgovor: kako pravilo dolazi do koda a da ne nastane drugi izvor istine, šta
alat radi sa fajlom koji nijedan red ne opisuje, i šta sme `__init__.py`, koji se
u tabeli nije pominjao.

Tri odluke izlaze iz istog konteksta, ali se traže odvojeno. Svaka nosi svoj
podnaslov i citira se zasebno: **ADR-037.1**, **ADR-037.2**, **ADR-037.3**.

### ADR-037.1 — Tabela se prepisuje u kod, test veže imena redova

**Kontekst.** Pravila prepisana u Python su drugi izvor istine — tačno onaj problem
koji je u tasku 0.2 nađen u `.claude/`, gde je 80% sadržaja bilo prepričavanje
dokumenata koje nijedan ADR nije mogao da ispravi.

Obrnuto rešenje — da alat parsira tabelu iz `CONVENTIONS.md` — daje jedan izvor
istine doslovno, ali traži da ćelije budu gramatika. Nisu: „sve gore + `pygame`"
zavisi od redosleda redova i ne kaže da li je „gore" ceo skup redova iznad ili samo
`client` redovi, a „sve" i „—" su proza. Tabela bi morala da se prepiše u strogi
oblik — dokument bi tada služio alatu, a čita ga čovek.

**Odluka.** `RULES` u `tools/layer_check.py` je **prepis** tabele, ne njen izvor.
`tests/test_layers.py` parsira pipe-tabelu iz §2 i tvrdi da je skup imena redova
identičan skupu ključeva; uz to tvrdi da je parser našao više od nula redova, jer bi
parser koji ćutke ne uhvati ništa napravio test koji uvek prolazi. Tabela stoji
doslovno prepisana i u docstringu iznad `RULES`, da se u `git diff`-u vide jedno
pored drugog.

Prepisivanje je zahtevalo da se dvosmislena ćelija pročita do kraja. „Sve gore"
sada u §2 znači: sve što smeju `client` redovi iznad, plus ti moduli sami, uz smer
uvoza unutar `client/` koji ide samo naniže (`i18n` ← `state` ← `render` ←
`scenes`). Ta rečenica je dopisana u §2 **istim commitom** — pravilo ne živi u kodu.

**Posledice.** Razilaženje alata i tabele je glasno, a ne tiho: dodat red bez pravila
(ili obrnuto) obara test suite. U sukobu je tabela u pravu, kako §1 već propisuje.

**Šta smo izgubili:** vezana su **imena redova, ne semantika ćelije**. Ako §2 kaže da
`client/state.py` sme `core.fen`, a alat to zaboravi, nijedan test ne puca. Ta greška
se hvata samo čitanjem diffa — zato tabela i stoji u docstringu tik iznad pravila.

### ADR-037.2 — Fajl koji tabela ne pokriva je nalaz

**Kontekst.** Alat obilazi stablo i nailazi na `.py` fajlove koje nijedan red ne
opisuje — danas ni jedan, sutra `client/__main__.py` ili `core/eval.py`. Tri
mogućnosti: preskočiti ga, pasti sa `traceback`-om, ili ga prijaviti.

**Odluka.** Prijavljuje se kao nalaz, sa izlaznim kodom 1, uz poruku koja traži nov
red u tabeli.

Preskakanje znači da nov paket dobija **nula** provere i da to niko ne vidi — isti
oblik kvara kao obrisan `tests/core/__init__.py`, koji `unittest discover` ćutke
preskoči (faza 0, pitanje 2). `traceback` bi izgledao kao pokvaren alat, a alat koji
izgleda pokvareno prestaje da se pokreće.

Uz to je u §2 zapisan redosled biranja reda: tačan red → `*/__init__.py` → najduži
prefiks. Bez zapisanog redosleda `tests/core/__init__.py` potpada pod dva reda
odjednom.

**Posledice.** Pravilo propagacije iz §1 sada važi i za kod: nov modul ne može da
uđe u projekat bez reda u tabeli, u istom commitu.

**Šta smo izgubili:** trenje. Svaki nov modul traži i izmenu `CONVENTIONS.md` — što
je namera, ali usporava. U fazi 3.1 `client/__main__.py` neće proći dok mu se ne
doda red.

### ADR-037.3 — `__init__.py` ne uvozi ništa iz projekta

**Kontekst.** Sedam `__init__.py` fajlova u `src/chess/` tabela nije pominjala, pa bi
po ADR-037.2 svi odmah bili nalaz. Dve mogućnosti: da svaki nasledi pravilo svog
paketa — čime je dozvoljena fasada `from .types import Piece` — ili da ne uvozi
ništa iz projekta.

**Odluka.** Nov red `*/__init__.py`: **samo stdlib**. Važi svuda u repozitorijumu,
uključujući `tests/`, i pobeđuje nad redom `tests/*` po redosledu iz ADR-037.2.

U ovom projektu je `__init__.py` marker paketa i ništa više — tako je postavljeno u
0.1 („samo `__init__.py` fajlovi, nijedan prazan modul"). Fasada bi napravila ivicu
u grafu zavisnosti koju nijedan red tabele ne opisuje, i otvorila vrata cikličnim
uvozima između paketa.

**Posledice.** Graf zavisnosti je onakav kakav tabela kaže da jeste; uvoz uvek
pokazuje na modul u kom stvar zaista stoji, pa se `grep` po imenu klase završava na
jednom mestu.

**Šta smo izgubili:** nema `from chess.core import Piece`. Uvoz je uvek pun put,
`from chess.core.types import Piece` — duže i, za onoga ko dolazi iz paketa koji
imaju bogat `__init__.py`, neobično. Ako se fasada ikad poželi, to je izmena tabele
u §2, a ne izuzetak u alatu.

---

## ADR-038: `cairosvg` odbijen; rasterizacija kroz pygame, alat nije zavisnost

**Kontekst.** Task 0.4 traži 12 SVG figura pretvorenih u PNG u dve veličine
(80 px za tablu, 32 px za pojedene figure iz 3.7). Rasterizacija se izvršava
**jednom**; rezultat ide u git i ništa u vreme izvršavanja ne dodiruje SVG.

`cairosvg` je očigledan izbor i daje bolji izlaz od nanosvg-a u opštem slučaju.
Druga mogućnost je pygame, koji je već deklarisan u `pyproject.toml` i kroz
SDL_image nosi nanosvg. Treća je preuzimanje gotovih PNG thumbnailova sa
Wikimedia servisa, koje rasterizuje librsvg.

**Odluka.** `cairosvg` je **odbijen**. Rasterizuje se alatom
`tools/rasterize_pieces.py`, kroz pygame — bez ijedne nove zavisnosti.

Dva razloga, po težini:

1. Na Windows-u `cairosvg` vuče native cairo DLL-ove izvan `pip`-a. To je tačno
   onaj režim otkaza iz konteksta ADR-009 — prethodni projekat korisnika nije radio
   kod druge osobe jer ODBC drajver nije bio instaliran. Princip „sve što je
   projektu potrebno mora biti u repozitorijumu ili instalirano jednim `pip`"
   važi i ovde.
2. **Alat koji jednom generiše resurs nije zavisnost projekta.** Zavisnost je ono
   bez čega program ne radi kod korisnika. Igraču šaha rasterizator SVG-a ne treba
   — njemu trebaju PNG-ovi, a oni su u gitu.

**Posledice.**

`pyproject.toml` se ne menja. Lista zavisnosti ostaje `pygame` + `ruff`. Ko klonira
repozitorijum dobija gotove PNG-ove; ko hoće da ih regeneriše, pokreće alat i za to
mu ne treba ništa novo. Ista logika je zapisana u CONVENTIONS §10.

**Šta smo izgubili — prvo, izmereno, ne pretpostavljeno.**

Prva verzija ovog ADR-a tvrdila je „izgubili smo kvalitet u odnosu na librsvg".
Provereno je poređenjem sa Wikimedia thumbnailom, koji rasterizuje librsvg, na
120 px (jedina standardna veličina blizu naše — thumbnailer odbija 80 px):

| | ukupno piksela | različitih | prosek \|Δ\| | max \|Δ\| |
|---|---|---|---|---|
| bela dama | 14 400 | 1 554 (10.8%) | 1.3 / 255 | 52 |
| beli skakač | 14 400 | 803 (5.6%) | 0.6 / 255 | 121 |

Oba broja stoje namerno. Procenat sam navodi na pogrešan zaključak — 10.8% izgleda
mnogo — a prosek pokazuje da je razlika ispod praga vidljivosti i da se nalazi
isključivo na ivičnim pikselima, dakle u antialiasingu. Na 1:1 i na 4× uvećanju
razlika se ne vidi; jedina uočena razlika ide **u našu korist** (librsvg ostavlja
sivkastu mrlju na spoju kuglice i kraka krune, nanosvg ne).

**Šta smo stvarno izgubili.**

1. **nanosvg ne skalira crtež na traženo platno.** Root `width`/`height` određuju
   veličinu platna, ali crtež ostaje u razmeri koju fajl deklariše — i `viewBox` to
   ne menja. Prva verzija alata je zato dala figure u razmeri 45 na platnu 80×80,
   a na 32×32 odsečene. Alat mora sam da skalira geometriju kroz
   `<g transform="scale(...)">`. Ta cena nije hipotetička — naplatila se u ovom
   tasku, i to tiho: dve od tri provere su kvar propustile, jer je izlaz imao tačnu
   dimenziju i neprazne piksele. Zbog toga alat sada poredi udeo neprovidnih piksela
   **kroz veličine**: ono što crtež pokriva ne sme da zavisi od platna.
2. **Merenje važi za ovaj materijal.** Cburnett set je čist crtež sa konturama, bez
   gradijenata, filtera i teksta — a to je upravo ono što nanosvg podržava slabo ili
   nikako. SVG koji bi ih koristio nije proveren i zaključak se na njega ne prenosi.

Rezervni put, ako bi ikad zatrebao: PNG thumbnailovi sa Wikimedia servisa. Takođe
nula zavisnosti, ali traži mrežu pri generisanju i nudi samo standardne veličine.

---

## ADR-039: Tuđi materijal se čuva bajt u bajt — `.gitattributes` i provera

> ⚠️ **Dopunjeno ADR-om 042.** Pravilo „tuđi materijal se čuva bajt u bajt" i sva
> četiri reda u `.gitattributes` ostaju na snazi. ADR-042 dodaje suprotan slučaj:
> `LICENSE` i `THIRD-PARTY.txt` su **naši** fajlovi, nose ne-ASCII bajtove, a reda u
> `.gitattributes` nemaju — jer nijedna tvrdnja ne zavisi od njihovih **prelazaka
> reda**. Kriterijum je isti onaj po kom reda nemaju `PROVENANCE.txt` i `sr.json`.

**Kontekst.** `assets/pieces/LICENSE.txt` navodi sha1 za svaki od 12 SVG originala,
a `assets/fonts/LICENSE.txt` je kopija `LICENSE` fajla iz DejaVu arhive, bajt u
bajt. Obe tvrdnje su **proverljive** — neko ih može izračunati i uporediti.

`git add` je u 0.4 prijavio:

```
warning: in the working copy of 'assets/pieces/svg/wp.svg',
         LF will be replaced by CRLF the next time Git touches it
```

`core.autocrlf=true` je uobičajena postavka na Windows-u. Blob u repozitorijumu
ostaje LF i njegov sha1 se poklapa — ali fajl **na disku posle kloniranja** dobija
CRLF, i tada se sha1 iz `LICENSE.txt` više ne poklapa ni sa čim što se vidi.

Kvar se kod autora ne pojavljuje nikad. Nastaje kod druge osobe, posle `git clone`.

**Odluka.** `.gitattributes` u korenu repozitorijuma:

```
assets/pieces/svg/*.svg    -text
assets/fonts/LICENSE.txt   -text
*.png   binary
*.ttf   binary
```

`-text` znači da git **ne prepisuje prelaske reda**, ni pri commitu ni pri
checkoutu. To je i sve što radi: ne isključuje filtere sadržaja (`ident`,
`clean`/`smudge`), koji bi bajtove promenili jednako uspešno. Nijedan nije
konfigurisan, i za ove putanje se ne sme konfigurisati.

`-text` nije `binary` — SVG i tekstualna licenca ostaju čitljivi u diffu.

PNG i TTF nemaju prelaske reda koje bi trebalo pretvarati i git to sam zaključuje,
ali njuškanjem prvih bajtova fajla — heuristikom, ne garancijom. Zato izričito.

Odbačena je druga mogućnost: **ostaviti konverziju i preformulisati `LICENSE.txt`**
da kaže kako sha1 važi za preuzete bajtove i za blob, a ne za fajl na disku.
Tvrdnja bi bila tačna, ali bi je proveravao samo onaj ko zna za `autocrlf` i ume
da izvuče blob kroz `git cat-file`. Proverljiva tvrdnja koju niko ne može lako da
proveri je za korak od tvrdnje kojoj se samo veruje.

Pravilo se izriče šire nego što je slučaj tražio, jer će se ponoviti: **tuđi
materijal u ovom repozitorijumu čuva se bajt u bajt.** Faza 4 donosi veb resurse.

> **Ispravka primera, task 0.5.** Ova rečenica je kao sledeći slučaj pravila najavljivala
> `assets/i18n/sr.json`. To je pogrešan primer, ne promena odluke: `sr.json` je **naš**
> fajl, nastao u ovom repozitorijumu, nema zapisan heš i ne nosi nijednu tvrdnju o
> poreklu. Zato **nema red u `.gitattributes`** — po istom kriterijumu po kom ga nema ni
> `assets/fonts/PROVENANCE.txt`: red postoji tamo gde **tačni bajtovi nose tvrdnju**.
>
> Izmereno u 0.5, da ne ostane pretpostavka: uz `core.autocrlf=true` `git checkout --`
> vrati `sr.json` na disk sa CRLF-om (697 bajtova umesto 686), blob ostaje LF, `git diff`
> je prazan i svih 44 testa prolazi. Konverzija mu ne može ništa jer nijedna tvrdnja ne
> zavisi od njegovih bajtova — što je upravo razlog da reda nema.

**Posledice.**

sha1 iz `LICENSE.txt` važi na svakoj platformi, i proverava se običnim
`sha1sum`-om nad fajlom koji je pred očima.

**Lanac se proverava mašinski, u `tests/test_assets.py`.** ADR beleži odluku; on
je ne sprovodi. Test tvrdi četiri stvari: da se svih 12 sha1 iz `LICENSE.txt`
poklapa sa fajlovima na disku, da je svaki SVG sa diska naveden u `LICENSE.txt`,
da ih je tačno 12, i da `.gitattributes` postoji sa redom za
`assets/pieces/svg/*.svg`.

Četvrta tvrdnja postoji zato što bez nje test hvata posledicu a ne uzrok. Poruka
„sha1 se ne poklapa" nekoga ko je tek klonirao repozitorijum ne vodi nikuda; uz
proveru `.gitattributes`-a poruka može da kaže šta se dogodilo i šta da uradi.

Provera je **test, a ne alat u `tools/`** — suprotno od ADR-038, i iz istog
razloga. Kvar iz ADR-038 nastaje dok alat generiše PNG, pa ga alat i hvata. Ovaj
kvar nastaje pri `git clone` na drugoj mašini, gde se pokreće `pip install -e
".[dev]"` pa testovi, a rasterizator se ne pokreće nikad. Provera mora da stoji
tamo gde se izvršava u trenutku kad kvar nastaje.

Test ne uvozi `pygame` — `hashlib`, `pathlib` i `re` su dovoljni.

`CONVENTIONS.md` §5 je istim commitom precizirana: pravilo je glasilo „test ne dira
disk izvan `tempfile`", a `tests/test_layers.py` od 0.2b obilazi celo stablo sa
diska. Pravilo je htelo da zabrani **pisanje**, ne čitanje.

Rečenicu o tome **od čega tvrdnja zavisi** dobijaju `assets/pieces/LICENSE.txt` i
nov fajl `assets/fonts/PROVENANCE.txt` — **ne** `assets/fonts/LICENSE.txt`.

Razlika je u tome čiji je dokument. `assets/pieces/LICENSE.txt` je **naš** tekst
koji citira tuđu licencu, pa napomena o našem repozitorijumu tu pripada.
`assets/fonts/LICENSE.txt` su napisali Bitstream i Tavmjong Bah i kopiran je bajt u
bajt; umetnuta rečenica napravila bi dokument koji izgleda kao licenca a sadrži i
nešto što nije, pa bi je onaj ko ga sutra prekopira u svoj projekat poneo kao deo
uslova. Isto važi za sha256 vrednosti. Zato one, i napomena, idu u `PROVENANCE.txt`
pored njega — koji na jednoj rečenici objašnjava i zašto su ta dva fajla različito
tretirana, da se za mesec dana ne raspravlja ponovo.

`PROVENANCE.txt` **nema** svoj red u `.gitattributes`, namerno. Red postoji tamo
gde tačni bajtovi nose tvrdnju; `PROVENANCE.txt` je naš, niko mu ne računa heš i
nije kopija ničega. Red koji ne štiti nijednu tvrdnju učinio bi komentar u
`.gitattributes` netačnim za sebe, a spisak obaveza koji sadrži i ukrase prestaje
da se čita kao spisak obaveza. Iz istog razloga reda nema ni
`assets/pieces/LICENSE.txt`.

**Šta smo izgubili:** `.gitattributes` je od sada fajl koji se ne sme brisati ni
skraćivati bez čitanja dva `LICENSE.txt` fajla — a to niko ne pogađa iz njegovog
imena. Veza je jednosmerna i nevidljiva: ništa u `.gitattributes` ne pokazuje ko
na njega računa. Test tu vezu sada čuva, ali je i sam deo iste petlje — ko obriše
i njega, obrisao je i jedino mesto koje bi prijavilo.

---

## ADR-040: Ugovor `t()` — šta se odbija glasno, a šta se vidi na ekranu

**Kontekst.** Task 0.5 uvodi `assets/i18n/sr.json` i `src/chess/client/i18n.py`. Funkcija
`t()` se u tasku 4.7 prevodi **1:1 u JavaScript**, pa svaki izbor u njoj mora da važi i za
jezik koji nema `**kwargs`, `str.format` ni Pythonov `str()`.

Otvoreno pitanje nije bilo kako izgleda potpis, nego **šta `t()` radi kad nešto nije u
redu**. Ako baca, jedan prevod koji fali obara ceo ekran usred partije. Ako ćuti, greška se
ne primeti nikad — ni na ekranu ni u logu.

**Odluka.**

Ugovor se ne zove „`t()` ne baca". Zove se: **`t()` ne baca na loš podatak.**

- **Loš podatak** je sadržaj `sr.json`-a i ono što stigne sa mreže.
- **Pogrešan poziv** je greška u našem kodu, na pozivnom mestu.

Bez tog razlikovanja dva izuzetka ispod izgledaju kao rupa u pravilu, umesto kao njegova
granica.

| Slučaj | Šta `t()` radi | WARNING |
|---|---|---|
| ključ ne postoji | vraća sam ključ | da, **jednom po ključu** |
| parametar fali | `{{ime}}` ostaje vidljivo na ekranu | da |
| višak parametra | izlaz nepromenjen | da |
| `t()` pre `load()` | `RuntimeError` | ne |
| parametar nije `str` | `TypeError` | ne |

**WARNING je drugi kanal, pored vidljivog simptoma na ekranu — nikad jedini.** Zato prva
tri reda imaju log, a poslednja dva nemaju: kod njih na ekranu nema šta da se vidi, pa
izuzetak i jeste jedini način da se greška uopšte primeti.

**Granica `load()` naspram `t()`.** Pravilo važi za `t()`, ne za `load()`. `load()` je
mesto gde se loš podatak odbija **glasno** — `ValueError` na BOM, neispravan JSON i
duplirani ključ. `t()` posle toga radi samo sa onim što je kroz `load()` prošlo, i na
sadržaj ne baca ništa.

`CONVENTIONS.md` §6 to potvrđuje sa druge strane: `ValueError` iz `load()` nosi **englesku
poruku namenjenu programeru**, a ne tekst za korisnika — korisnički tekst ide isključivo
kroz `message_key` i `sr.json` (ADR-010). Zato izuzetak i sme da bude rečit: niko ga ne
prikazuje igraču.

**Zamena parametara: `{{ime}}`.** Ne `str.format`, ne `string.Template`, ne `${ime}`.
Sintaksa mora biti takva da je **nijedan jezik ne implementira sam**, jer se funkcija u 4.7
prevodi 1:1. `str.format` nosi pristup atributima, indeksiranje, format specifikatore i
`!r` — ništa od toga JavaScript neće imati, a sve bi se u Pythonu tiho koristilo.

Obrazac je `\{\{([a-z][a-z0-9_]*)\}\}`, sa **doslovnom klasom znakova**, ne `\w`: `\w` je u
Pythonu Unicode, a u JavaScriptu ASCII, pa bi isti obrazac na dve strane prihvatao različita
imena. Potpis prima **rečnik**, ne `**kwargs`, iz istog razloga.

**Parametri su stringovi i koriste se doslovno. `t()` ne poziva `str()` ni na čemu:**

```
Python  str(1.0)     -> "1.0"
JS      String(1.0)  -> "1"
```

Formatiranje broja ostaje na pozivnom mestu, u svakom jeziku svojim pravilima. Zapisano je
sa primerom, a ne samo kao pravilo, jer bi neko ko za godinu dana hoće da „olakša" `t()`
dodavanjem `str()` inače video samo zabranu bez razloga. Kvar bi se pojavio tek u fazi 4, na
satu iz 3.7, i to tiho.

**BOM se odbija, `utf-8-sig` se ne koristi.** Obrazloženje ne zavisi od toga kako se
ponaša `JSON.parse`: `utf-8-sig` znači **popustljivo u Pythonu** — BOM prolazi neopaženo i
ostaje u repozitorijumu, a da li će faza 4 na njega pući zavisi od izabranog puta čitanja u
JavaScriptu. Ne nasleđujemo taj rizik; cena strogosti je nula, jer fajl pišemo mi.

Odbijanje stoji na **dva sloja**, namerno duplirano: u `load()` i u testu B6. `load()` prima
putanju, pa u fazi 4 može da pokaže na fajl koji test ne vidi; test gleda **bajtove**, pa
tvrdi i kad dekodiranje ne uspe. Poruka iz `json.load` („Expecting value: line 1 column 1")
ne vodi nikuda.

**Posledice.**

Prevod koji fali degradira ekran umesto da ga obori, a nikad ne prolazi nezapaženo: vidi se
i na ekranu i u logu. Greška u našem kodu — poziv pre `load()`, broj umesto stringa — pada
odmah i glasno, tamo gde je i nastala.

Skup već prijavljenih ključeva vezan je za **katalog**, ne za modul: `load()` ga prazni, pa
ponovo učitan katalog koji i dalje nema ključ mora ponovo da se javi. Bez toga bi „jednom po
ključu" u dugoj sesiji značilo „jednom zauvek".

**Predviđeno, da u fazi 3 ne izgleda kao pokvaren test:** bela lista dozvoljenih znakova iz
testa B11 nema `{`, `}` ni `_`. Prvi tekst sa `{{ime}}` u tasku 3.7 **oboriće B11** — dakle
baš funkcija koju ovaj task uvodi. To je po logici bele liste ispravno: nov znak se dodaje
svesno, kad ga prvi tekst zatraži.

**Šta smo izgubili.** `t()` je manje udobna nego `str.format`: bez format specifikatora, bez
pozicionih argumenata, sa obaveznim `str()`-om na pozivnom mestu. Poziv sa brojem, koji bi u
Pythonu radio, sada je greška. To je cena toga da ista funkcija u dva jezika daje isti
izlaz, i plaća se na svakom pozivnom mestu, ne jednom.

---

## ADR-041: Zatvoren skup vrednosti iz protokola se čita mašinski

**Kontekst.** `PROTOCOL.md` §5 nabraja devet `ERROR` kodova. `sr.json` treba da ima ključ za
svaki. Ništa nije sprečavalo da se ta dva spiska raziđu: dodat kod bez ključa daje na ekranu
`error.nesto` umesto rečenice, a suvišan ključ ostaje zauvek jer niko ne zna da ga protokol
više ne šalje. Oba kvara su tiha.

Ovo nije pravilo o greškama. `ERROR` kodovi su samo **prvi** zatvoren skup vrednosti koji
protokol propisuje a klijent prikazuje.

**Odluka.**

**Kad protokol propiše zatvoren skup vrednosti koji korisnik vidi, taj skup se čita mašinski
iz `PROTOCOL.md` i poredi sa `sr.json`.** Pravilo izvođenja:

```
message_key = "error." + kod malim slovima
ILLEGAL_MOVE -> error.illegal_move
```

`tests/client/test_i18n.py` parsira prvu kolonu tabele iz §5 i tvrdi **oba smera**: svaki kod
ima svoj ključ, i svaki `error.*` ključ pripada nekom kodu. Jedan smer bi ostavio obim taska
kao obećanje umesto kao pravilo.

**Poznata sledeća primena:** `termination` iz `GAME_OVER` — `checkmate`, `stalemate`,
`resignation`, `timeout`, `draw_agreement`, `insufficient_material`, `fifty_move`,
`threefold_repetition`. Ti ključevi nastaju u fazi 3 i biće `termination.*`, po istom
pravilu izvođenja. Zapisano ovde da se u 3.9 ne izmišlja ponovo.

**Zašto se ovde parsira, a u §2 prepisuje.** ADR-037.1 je odbio da alat parsira tabelu
slojeva, jer bi ćelije morale da budu gramatika — „sve gore + `pygame`" i „sve" to nisu.
Ovde je drugačije: ćelija je **identifikator**, `VERSION_MISMATCH`, i ništa drugo. Parsira se
identifikator, ne proza.

**Posledice.**

Kod dodat u tabelu bez ključa u `sr.json` obara suite. Ključ bez koda takođe. Napomena o tome
stoji u §5, ispod tabele, jer se pravilo mora videti tamo gde se tabela menja.

**Cena, ista kao u ADR-037.1: oblikovanje `PROTOCOL.md` postaje noseće.** Tabela iz §5 više
nije samo tekst za čoveka — promena zaglavlja ili prelazak na drugi oblik liste obara test.
Zato prva rečenica napomene to izričito kaže, i zato test razlikuje „zaglavlje nije nađeno"
od „nula kodova": prvi je kvar u oblikovanju, drugi u sadržaju.

**Selidba u 2.1.** Kad `protocol/messages.py` dobije enum kodova, spona se seli sa dokumenta
na enum, a tvrdnja postaje jača — enum je izvršiv, dokument nije. Napomena u §5 ostaje;
menja se samo njena druga rečenica, koja imenuje test. Isti mehanizam kojim je u ROADMAP-u
zavedeno polje `captured`.

**Šta smo izgubili.** Sloboda u oblikovanju §5. Ko sutra hoće da tabelu kodova pretvori u
listu, mora prvo da prepravi test — i to je namera, ne smetnja, ali je trenje stvarno.
Takođe: test tvrdi da **ključ postoji**, nikad da je prevod tačan. Rečenica koja opisuje
pogrešnu grešku prolazi kroz svih devet tvrdnji.

---

## ADR-042: BSD-3 za naš kod; `LICENSE` nosi uslove, `THIRD-PARTY.txt` nosi obim

**Kontekst.** Repozitorijum je javan i od 0.4 nosi tuđi materijal pod dve licence, a za
**naš** kod ne izriče nijednu. Javan repo bez licence je podrazumevano „sva prava
zadržana": onaj ko na njega naiđe zna da ne sme da ga koristi, ne zna zašto, i nema koga
da pita.

Drugo pitanje je stiglo uz prvo. `LICENSE` u korenu, po prirodi tog fajla, imenuje
**jednog** nosioca i **jedne** uslove. Kod figura su uslovi isti tekst, ali je nosilac
drugi (Cburnett, 2006). Kod fonta se razlikuju i nosilac i uslovi. Dakle jedan
izostavljen nosilac i jedni izostavljeni uslovi — a ne „netačna tvrdnja".

To nije formalnost. Prva klauzula BSD-3 traži da se zadrži **baš to** obaveštenje o
autorskim pravima koje je uz materijal došlo, a treća zabranjuje korišćenje imena
nosioca za promociju. Isti tekst uz dva nosioca obavezuje **dvaput, prema dve različite
strane**.

**Odluka.**

**Naš kod ide pod BSD-3-Clause.** Repozitorijum već nosi taj tekst za figure, pa su
uslovi isti kroz celo stablo i razlikuje se samo nosilac prava. Copyleft bi
protivrečio tome što smo za iste te figure svesno odbili ponuđeni GPL (PROJECT §12).

**Telo `LICENSE`-a je kanonski SPDX tekst**, neizmenjen osim reda o autorskim pravima,
koji glasi `Copyright (c) 2026 Stefan Obradović` — godina iz prvog commita, jedna, bez
raspona. Klauzula 3 ostaje kanonska (`the copyright holder nor the names of its
contributors`), bez umetanja imena: standardni tekst licence se ne prepravlja — isto
pravilo je već izrečeno u `assets/pieces/LICENSE.txt` za odricanje od garancije — a
`licensee`, detektor koji GitHub koristi, poredi tekst, pa izmenjen tekst smanjuje
poklapanje.

Telo je **preuzeto**, ne prekucano:

```
https://raw.githubusercontent.com/spdx/license-list-data/main/text/BSD-3-Clause.txt
1460 bajtova
sha256 5a93d5831e1297ab10fe643e1a631e83be392896da14ee2951285a79012df69d
```

Kopija koja već stoji u `assets/pieces/LICENSE.txt` **nije** taj tekst i nije mogla da
posluži kao izvor. Izmereno poređenjem reči, sve beline sažete — razlikuje se na **pet**
mesta:

| | SPDX kanonski | `assets/pieces/LICENSE.txt` |
|---|---|---|
| red o pravima | `Copyright (c) <year> <owner>. ` | `Copyright (c) 2006 Cburnett` |
| oznake klauzula | `1.` `2.` `3.` | `  * ` |
| klauzula 3 | `the copyright holder` | `Cburnett` |
| odricanje, 1. rečenica | `THE COPYRIGHT **HOLDERS** AND CONTRIBUTORS` | `... **HOLDER** AND ...` |
| odricanje, 2. rečenica | `THE COPYRIGHT HOLDER **OR** CONTRIBUTORS` | `... HOLDER **AND** ...` |

Prva tri su znana i očekivana. **Poslednja dva nisu bila**, i ona su razlog zbog kog
izvor mora biti SPDX: da je telo uzeto iz repoa, naš `LICENSE` bi nasledio varijantu
odricanja koju taj fajl u sopstvenom objašnjenju naziva kanonskom, a koja to nije.
Prekucavanje iz sećanja je kvar koji nijedan gate ne hvata (faza-0.md §0.4); uzimanje
iz repoa je bio isti kvar u tišoj varijanti.

Tekst je prelomljen na 75 kolona. To **nije** izmena teksta: spisak reči prelomljenog i
kanonskog tela je identičan (216 naspram 216, prazna razlika, `a == b`), nijedan red se
ne završava crticom, a `licensee` normalizuje beline pri poređenju. Uvlačenja nastavaka
klauzula nema — nema ga ni kanonski tekst ni kopija u repou, i dva različita izgleda iste
licence u istom repozitorijumu ne donose ništa.

**Tvrdnja o obimu NE ide u `LICENSE`.** Obim nosi zaseban fajl u korenu,
`THIRD-PARTY.txt`. Isti odnos kao `assets/fonts/LICENSE.txt` naspram `PROVENANCE.txt`:
tuđ ili kanonski dokument se ne dopunjuje našom rečenicom, jer bi je onaj ko ga prekopira
poneo kao deo uslova (ADR-039).

**Ime nije `NOTICE.txt`.** `NOTICE` je konvencija Apache-2.0 sa pravnim značenjem po
§4(d) te licence i uz BSD-3 navodi na pogrešan zaključak. Nije ni `COPYRIGHT.txt`:
`licensee` boduje imena fajlova regularnim izrazima, a `COPYING_REGEX = /copy(ing|right)/i`
daje `COPYRIGHT.txt` 0.85 — odmah iza `LICENSE` (1.00). Ušao bi u isti spisak kandidata
za fajl licence, a nije licenca. `THIRD-PARTY.txt` ne pogađa nijedan regex iz te tabele.

**Obim je materijal koji stoji u ovom repozitorijumu.** Deklarisane zavisnosti se ne
nabrajaju: `pygame` pip donosi pri instalaciji i mi ga ne redistribuiramo. Preispituje se
ako faza 7 („Deploy (opciono)") ikad spakuje izvršni fajl — LGPL tada traži mogućnost
relinkovanja, jer je to uslov na **distribuciju**, ne na upotrebu.

`THIRD-PARTY.txt` je na engleskom, kao `assets/pieces/LICENSE.txt` i `PROVENANCE.txt`.
Nije ni `README.md` ni `docs/`, nego dokument uz licencu, i obraća se onome ko naiđe na
repozitorijum.

**Spisak putanja je ograničen blok koji čita test.** Red zaglavlja
`DIRECTORIES WITH THEIR OWN LICENSE:`, jedna putanja po redu **od prve kolone**, prazan
red kao kraj. Fajl nosi rečenicu koja imenuje test — opšti oblik koji `CONVENTIONS.md` §1
dobija u 0.7. Kriterijum je „direktorijum ima svoj `LICENSE.txt`", pa `assets/i18n`
ispada sam od sebe, bez izuzetka u kodu. Putanje idu od prve kolone iako parser radi
`strip()`: oblik fajla i parser se slažu izričito, umesto da uvlačenje preživi zato što
ga je `strip()` progutao.

**Svaki čitalac `THIRD-PARTY.txt`-a dekodira pa koristi `splitlines()`.** Ne deli sirove
bajtove po `\n` i **ne primenjuje nijedan izraz na ceo tekst sa `re.MULTILINE`**.

Pravilo je namerno šire od jednog čitaoca. Prva verzija plana vezala ga je za „parser
bloka", pa je drugi čitalac istog fajla — pronalaženje reda `SPDX-License-Identifier:` —
prošao sa `re.MULTILINE` i sidrom `[ \t]*$`. `\r` nije ni razmak ni tab, pa bi izraz
prestao da pogađa čim fajl na disku bude CRLF: kod nas bi prolazio, kod prve druge osobe
padao. Uže formulisano pravilo propustilo je drugog čitaoca **pre nego što je i jedan red
koda napisan** — zato ovde stoji šire.

Zbog toga `THIRD-PARTY.txt` **nema red u `.gitattributes`**: red je obaveza koju neko mora
da održava, a `splitlines()` je jednom napisan i ne traži ništa. Kad postoje dva načina da
se ista stvar obezbedi, biramo onaj koji ne traži da se neko seti.

`LICENSE` takođe **nema red u `.gitattributes`**, i obrazloženje je uže nego što bi se
očekivalo: nijedna tvrdnja ne zavisi od njegovih **prelazaka reda**, a to je jedino što
`-text` štiti. Šira formulacija („ne zavisi od njegovih bajtova") bila bi netačna — test
iz ovog istog commita čita njegove bajtove. CRLF pretvara `\n` u `\r\n` i ne dira `C4 87`.

Izmereno, ne pretpostavljeno: posle `git checkout --` uz `core.autocrlf=true` oba fajla su
na disku CRLF (`LICENSE` 1493 B umesto 1466, `THIRD-PARTY.txt` 4326 umesto 4231), `git
diff` je prazan, nijedan red posle `splitlines()` ne sadrži `\r`, i svih 53 testa prolazi.

**Lanac čuva `tests/test_assets.py`**, kao i u ADR-039 — ADR beleži odluku, on je ne
sprovodi. Provera znaka U+0107 je **stalna** tvrdnja, ne jednokratna provera: kvar
(presnimavanje kroz editor u cp1252, loš merge) nastaje kasnije, a tada se izvršava suite
a ne mi. Isti kriterijum po kom `sha1` provera iz 0.4 živi u testu a ne u alatu; uz to,
prva klauzula BSD-3 traži da baš to obaveštenje preživi.

Provera se gradi **iz kodne tačke**, `chr(0x0107)`, nikad iz doslovnog znaka u izvoru
testa, i poruka o padu imenuje `U+0107` a ne ispisuje ga. Da test sadrži doslovan znak,
isto što bi ga pokvarilo u `LICENSE`-u pokvarilo bi ga i u testu, pa bi se poredilo
pokvareno sa pokvarenim. Nije teorijski: konzola je i u ovom tasku pukla na `đ`
(`UnicodeEncodeError: 'charmap' codec can't encode character` U+0111), isto kao u 0.5.

**`LICENSE` i `THIRD-PARTY.txt` time nisu ASCII fajlovi**, za razliku od `.py` fajlova gde
smo čistotu ASCII-ja izričito tražili. Oba nose tačno dva ne-ASCII bajta, `C4 87`. Ime se
piše kako se piše.

**Posledice.**

Ko naiđe na repozitorijum vidi pod čim sme da ga koristi, i vidi da to ne važi za figure i
font. Metapodaci paketa nose istu tvrdnju (ADR-043), a test je vezuje za `THIRD-PARTY.txt`,
pa dva mesta ne mogu tiho da odlutaju.

**Šta smo izgubili.**

1. **Još dva noseća oblika.** Red `SPDX-License-Identifier:` i zaglavlje bloka su od sada
   tekst koji obara suite kad se promeni. Ista cena kao u ADR-041 za `PROTOCOL.md` §5, i
   ista namera.
2. **Pravilo o ASCII-ju se ne prenosi na ova dva fajla.** „Izvor je čist ASCII" važi za
   kod; ovde ne važi i ne sme. Razliku od sada mora da zna svako ko ta dva fajla dira.
3. **Provera ASCII-ja pokriva jedan fajl zato što fajl ima jedan.** `AsciiSourceTest` čita
   `Path(__file__)` i ništa drugo. Ako se tvrdnje o licencama ikad razdvoje na više test
   modula, provera se **ne prenosi sama** i pravilo tiho prestaje da važi za nov fajl.
   Zapisano i u komentaru iznad tog testa, jer ADR niko ne čita dok deli fajl.
4. **`THIRD-PARTY.txt` mora da se održava.** Treći direktorijum sa tuđim materijalom obara
   `LicensedDirectoriesTest` — namerno, jer hardkodovan broj 2 traži da to bude svestan
   događaj — ali je to obaveza koju niko ne pogađa iz imena fajla.
5. **Lanac vezuje oznaku sa oznakom, nikad oznaku sa tekstom.** `LICENSE` nosi **tekst**
   licence i reč `BSD-3-Clause` se u njemu ne pojavljuje; test poredi `pyproject.toml` sa
   `THIRD-PARTY.txt`, dakle dva zapisa **iste oznake**. Nijedna tvrdnja ne kaže da je telo
   u `LICENSE`-u zaista BSD-3-Clause a ne neka druga licenca — ko zameni telo tekstom MIT
   licence i ostavi red o autorskim pravima, prolazi kroz svih devet tvrdnji. Poreklo tela
   čuva `sha256` zapisan iznad, ali to je **zapis, ne provera**. Ista granica kao u
   ADR-041: test tvrdi da ključ postoji, nikad da je prevod tačan.

---

## ADR-043: Licenca se izriče i u metapodacima paketa; SPDX oblik traži `setuptools>=77`

**Kontekst.** `LICENSE` u korenu vidi čovek. `pip`, PyPI i svaki alat koji čita `METADATA`
vide `pyproject.toml`. Do ovog taska `[project]` nije imao nijedno polje o licenci, pa je
wheel koji gradimo nosio **nijedan red o licenci** — izmereno, ne pretpostavljeno.

**Odluka.**

```toml
license = "BSD-3-Clause"
license-files = ["LICENSE"]

[build-system]
requires = ["setuptools>=77"]
```

SPDX izraz, ne tabela i ne klasifikator. Razlozi su **izmereni**, ne citirani:

- `setuptools` 76.1.0 odbija `license` kao string tvrdo: `ValueError: invalid
  pyproject.toml config: 'project.license'`; šema tada zna samo `{file=}` i `{text=}`.
  Granica je stvarno 77.
- `setuptools` 84.0.0 prijavljuje `SetuptoolsDeprecationWarning` i za `project.license`
  kao TOML tabelu i za klasifikator `License :: OSI Approved :: BSD License`, sa rokom:
  „By 2027-Feb-18 ... your builds will no longer be supported".
- Klasifikator ne razlikuje dvoklauzulnu od troklauzulne BSD licence, a ceo task postoji
  da tvrdnja bude tačna. **Ispravka premise iz plana:** `pyproject.toml` klasifikator
  nikad nije ni imao, pa je ovo razlog da se **ne doda**, a ne da se ukloni.
- Paket ne ide na PyPI, što izbor pojačava u istom smeru: jedini potrošač klasifikatora je
  PyPI-jev prikaz.

**Podizanje granice ne dodaje zavisnost.** `build-system.requires` opisuje okruženje u kom
pip gradi paket, a to okruženje pip stvara sam. Lista zavisnosti projekta ostaje `pygame` i
`ruff` (CONVENTIONS §10, dopunjena istim commitom da to kaže).

Izmereno pre izmene, da granica ne bude pretpostavka: pip u izolovano build okruženje već
povlači **najnoviji** setuptools (84.0.0), pa 84 već radi. `>=77` ne menja **šta se
povlači**, nego **šta je dozvoljeno** — sprečava da neko sa zakucanim starijim
setuptools-om dobije `ValueError` umesto paketa.

**Wheel se gradi sa `pip wheel . --no-deps -w dist`**, i pre i posle izmene. `build` se
**ne** instalira — nije naša zavisnost i nikad nije bio pokrenut u ovom projektu. `pip` je
već tu i sam stvara izolovano build okruženje. `build/`, `dist/` i `*.egg-info/` su već u
`.gitignore`, pa izgradnja ne prlja radno stablo — provereno, ne pretpostavljeno.

**Posledice.**

Mereno nad wheel-om, pre i posle:

| | pre | posle |
|---|---|---|
| veličina | 5724 B | 6756 B |
| polja o licenci u `METADATA` | **nijedno** | `License-Expression: BSD-3-Clause`, `License-File: LICENSE` |
| `.dist-info/licenses/LICENSE` | ne postoji | postoji, sa `C4 87` netaknutim |
| `assets/` u wheel-u | nema | nema |

**`pip show` i dalje ispisuje prazno `License:`, i to je ispravno.** Po PEP 639 se
`License` i `License-Expression` međusobno isključuju, a `pip 24.0` u `show` čita samo
staro polje. Merilo tačnosti je `License-Expression` u `METADATA`, ne izlaz jedne stare
komande. Zapisano izričito da neko za pola godine ne „popravi" tačnu metapodatku zato što
`pip show` o njoj ćuti.

Predviđena tačka otkaza koja se **nije** ostvarila: SPDX oblik tera `Metadata-Version:
2.4`, a u venv-u je `pip 24.0`. Instalacija je prošla bez greške. Zabeleženo jer je bilo
otvoreno pitanje, ne da bi izgledalo kao rizik koji smo savladali.

**Šta smo izgubili.**

1. **Predviđen pad, isti oblik kao B11 u ADR-040.** Zbog `[tool.setuptools.packages.find]
   where = ["src"]` `assets/` ne ulazi u wheel, pa je tvrdnja o licenci u metapodacima
   danas tačna za ono što se pakuje. Kad u fazi 4 ili 7 resursi budu morali u paket,
   `license-files` **mora** da poraste, inače wheel nosi tuđi materijal bez ijedne licence.
   **Nijedna provera iz ovog taska to ne hvata.**
2. Donja granica `setuptools`-a je od sada broj koji neko mora da brani. Spuštanje ispod 77
   vraća `ValueError`, i to se vidi tek pri izgradnji, ne pri čitanju fajla.
