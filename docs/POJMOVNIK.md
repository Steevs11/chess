# POJMOVNIK

Termini koji se pojavljuju u ovom projektu. Pisano za nekoga ko zna da igra šah,
ali nije pisao šahovski program.

---

## Notacija

### FEN — Forsyth–Edwards Notation

Jedan red teksta koji **potpuno** opisuje poziciju. Fotografija table u tekstu.

```
rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
```

| Deo | Značenje |
|---|---|
| `rnbqkbnr/...` | raspored figura, od 8. reda ka 1. Velika slova = beli, brojevi = prazna polja |
| `b` | ko je na potezu |
| `KQkq` | prava na rokadu koja još postoje |
| `e3` | polje na kom je moguć en passant, ili `-` |
| `0` | brojač polupoteza bez pomeranja pešaka i bez uzimanja |
| `1` | redni broj poteza |

Peti deo je tačno ono što treba za pravilo 50 poteza — standard je to predvideo.

### SAN — Standard Algebraic Notation

Zapis poteza **za ljude**: `Nf3`, `O-O`, `exd5`, `Qxh7#`.

Kad dve iste figure mogu na isto polje, dodaje se razlikovanje: `Nbd2` (skakač
sa b-linije), pa `N1d2` ako kolona ne razlikuje, pa `Nb1d2` ako ni to.

### UCI — Universal Chess Interface

Zapis poteza **za programe**: `g1f3`, `e1g1`, `e7e8q`.

Uvek četiri slova (polazno polje + odredišno), plus peto za promociju.
Ružno za čitanje, ali jednoznačno i trivijalno za parsiranje. Standardni jezik
kojim šahovski engine-i međusobno pričaju.

### PGN — Portable Game Notation

Cela partija sa metapodacima. Format koji otvara svaki šahovski program.

---

## Reprezentacija

### Mailbox

Tabla kao niz od 64 elementa. Polje `a1` je indeks 0, `h8` je 63.
Prosto, čitljivo, dovoljno brzo za naše potrebe.

Alternative koje **ne** koristimo: 0x88 (elegantnija provera izlaska sa table)
i bitboard-i (64-bitni brojevi, najbrži, ali nečitljivi bez iskustva).

### make / unmake

Umesto da kopiraš celu tablu za svaki potez koji ispituješ, **odigraš potez na
istoj tabli pa ga vratiš.**

Kopiranje table 4,8 miliona puta je razlika između minuta i sati.

### UndoRecord

Beleška šta treba vratiti pri `unmake`:

| Polje | Zašto |
|---|---|
| pojedena figura **i njeno polje** | kod en passanta pojedeni pešak nije na odredišnom polju |
| prethodna prava na rokadu | pomeranje kralja ih gasi nepovratno |
| prethodno en passant polje | pravo traje tačno jedan potez |
| prethodni brojač polupoteza | pravilo 50 poteza |
| prethodni Zobrist ključ | jeftinije od ponovnog računanja |

### MoveKind

Oznaka na svakom potezu koje je vrste: `NORMAL`, `CAPTURE`, `DOUBLE_PAWN_PUSH`,
`EN_PASSANT`, `CASTLE`, `PROMOTION`.

Generator poteza zna koju vrstu pravi, pa je popunjavanje besplatno. Zauzvrat
`make` i `unmake` ne moraju ništa da zaključuju, a protokol može klijentu da
kaže „ovaj potez traži dijalog za promociju" bez ijednog šahovskog pravila
u klijentu.

---

## Zobrist heš

Način da poziciju pretvoriš u **jedan broj**, radi brzog poređenja.

**Kako radi.** Na startu se svakoj kombinaciji *(figura, polje)* dodeli
nasumičan 64-bitni broj. Ključ pozicije je XOR svih tih brojeva, plus brojevi
za pravo na rokadu, en passant polje i to ko je na potezu.

**Zašto XOR.** Zato što je XOR sam sebi inverz:

```
A XOR B XOR B = A
```

Kad pomeriš skakača sa g1 na f3, uradiš:

```
kljuc ^= zobrist[SKAKAC_BELI][g1]    # skloni ga sa g1
kljuc ^= zobrist[SKAKAC_BELI][f3]    # stavi ga na f3
```

Dva XOR-a umesto ponovnog računanja cele pozicije. I `unmake` je istih dva
XOR-a unazad.

**Čemu služi.** Trostruko ponavljanje — brojiš koliko puta se isti ključ
pojavio u istoriji partije. Kasnije: transpoziciona tabela bota, gde se pamte
već ocenjene pozicije.

**Dve zamke.**

*Fiksan seed.* Ako se nasumični brojevi generišu bez zadatog seed-a, ključevi
su različiti pri svakom pokretanju i testovi nisu deterministički.

*En passant uslovno.* Polje se ubacuje u ključ **samo kad je en passant
uzimanje stvarno moguće.** Ako se ubacuje uvek, pozicija posle `e2-e4` nikad
neće biti jednaka istoj poziciji dobijenoj drugim redosledom poteza, i
trostruko ponavljanje neće okinuti kad treba.

---

## Perft

### Šta je

*Performance test.* Iz zadate pozicije prebroji **sve moguće partije** do
dubine N.

| Dubina | Iz početne pozicije |
|---|---|
| 1 | 20 |
| 2 | 400 |
| 3 | 8.902 |
| 4 | 197.281 |
| 5 | 4.865.609 |

Brojevi su objavljeni i proverivi. Ako se tvoj poklopi, generator poteza je
**dokazano ispravan** — jer da bi broj bio tačan, moraju raditi rokada,
en passant, promocija, vezane figure i otkriveni šahovi.

### perft_divide

Isti račun, ali **razbijen po prvom potezu.**

```
a2a3: 8457
a2a4: 9329
b1a3: 8885     ← referenca kaže 8885, u redu
b1c3: 9750     ← referenca kaže 9755, evo bага
```

Nađeš potez koji odstupa, uđeš u tu poziciju, ponoviš na dubini N-1. Za par
koraka si lokalizovao bag na jedan konkretan potez umesto da pretražuješ
milione čvorova.

### Test pozicije

Početna pozicija hvata malo. Postoji standardni skup na Chess Programming Wiki
gde svaka pozicija gađa drugu klasu bagova:

| Pozicija | Šta lovi |
|---|---|
| Početna | osnovno kretanje |
| **Kiwipete** | rokadu i en passant istovremeno |
| Position 3 | en passant u zamršenim slučajevima |
| Position 4 | promociju i vezane figure |
| Position 5 | rokadu u neobičnim pozicijama |

Četiri pozicije na dubini 3 nađu više bagova po sekundi nego dve pozicije
na dubini 5.

> Referentne brojeve **uvek prepisati sa Chess Programming Wiki.**
> Nikad iz sećanja, ni čovekovog ni modelovog.

---

## Protokol

### Snapshot i delta

**Delta** — server šalje samo šta se promenilo. Manje podataka, ali klijent mora
da akumulira stanje, i ako propusti jednu poruku — razišao se.

**Snapshot** — server šalje kompletno stanje svaki put. Nešto više podataka,
ali klijent nema šta da pogreši, i rekonekcija je besplatna: dobiješ poslednji
snapshot i nastaviš.

Mi šaljemo snapshot. Partija od 80 poteza je par stotina bajtova.

### Verzionisanje

Svaka poruka nosi polje `v`. Kad se format promeni nekompatibilno, `v` raste, i
stari klijent dobija jasnu grešku umesto da pukne na neočekivanom mestu.

Dodavanje **novog opcionog polja** ili **novog tipa poruke** nije nekompatibilna
promena.

---

## Python i alati

### `src/` raspored i `pip install -e .`

Kod stoji u `src/chess/` umesto u `chess/` u korenu. To sprečava da testovi
slučajno uvezu fajlove iz radnog direktorijuma umesto instalirani paket.

Cena: Python ne vidi `src/` automatski. Zato:

```bash
pip install -e .
```

`-e` znači *editable* — instalira paket tako da pokazuje na tvoje fajlove.
Menjaš kod, promena važi odmah, bez reinstalacije. Ista komanda povlači i
`pygame`, jer je deklarisan u `pyproject.toml`.

### `ruff`

Linter i formatter u jednom. Formatira kod i nalazi probleme pre pokretanja:
neiskorišćen import, mutabilan podrazumevani argument, goli `except`.

Ne proverava **tipove** — to radi mypy, koji mi ne koristimo.

### `selectors`

Način da jedna nit opslužuje više konekcija. Umesto niti po klijentu, imaš
petlju koja pita „ko od vas ima nešto za mene" i obrađuje ono što je stiglo.

Ključna prednost za nas: `select(timeout=...)` se budi i kad **niko ništa ne
pošalje** — pa sat može sam da okine pad zastavice.

---

## Šahovska pravila koja se lako pogreše

**Rokada.** Top **sme** biti napadnut i **sme** proći kroz napadnuto polje.
Ograničenje važi samo za kralja.

**En passant.** Pojedeni pešak nije na polju na koje se ide — on je iza njega.
Ovo je najčešći izvor bagova u `unmake`.

**Promocija.** Četiri poteza, ne jedan. Podpromocija u skakača ponekad je
jedini potez koji ne gubi.

**Trostruko ponavljanje.** Pozicije se porede po **četiri** stvari: raspored,
ko je na potezu, prava na rokadu, en passant polje. Ne samo po rasporedu.

**Pad zastavice.** Poraz — osim ako protivnik nema dovoljno materijala da
matira nijednim nizom legalnih poteza. Tada je remi.
