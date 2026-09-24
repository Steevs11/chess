# ODLUKE (ADR)

Odluke o proizvodu, svaka sa razlogom i cenom. Oblik: **Odluka · Zašto · Cena**.
Promenjena odluka se ispravlja na mestu, uz jednu rečenicu šta je bilo i kad je promenjeno.

Brojevi koji nedostaju su odluke o procesu rada, spojene u proizvodne (019→007, 031→013,
036→029, 037→033) ili ukinute (012, 020, 021, 028, 030, 032, 044, 045, 046) REZ-om 2
(ADR-048). Pun tekst svih 47 stoji u istoriji gita do commita `4770159`.

---

## ADR-001 — Server je autoritet nad pravilima

**Odluka.** Sva šahovska pravila su na serveru. Klijent šalje nameru, server validira i
emituje stanje; klijent ne sadrži nijedno pravilo.
**Zašto.** Mentor traži proveru dozvoljenih poteza; klijent ne može da vara; svaki budući
klijent je trivijalan.
**Cena.** Jedno mrežno kruženje po potezu — na `localhost` nemerljivo.

## ADR-002 — Ports and adapters

**Odluka.** `core` i session sloj ne znaju ko ih zove; transport je adapter. Smer uvoza
`client/server → protocol → core → stdlib`, nikad obrnuto.
**Zašto.** Veb klijent, bot i drugi transport su adapteri, ne prepisivanje.
**Cena.** Više fajlova nego kod monolita.

## ADR-003 — Sirovi `socket`, bez framework-a

**Odluka.** `socket` iz standardne biblioteke, JSON razdvojen sa `\n`. FastAPI, Flask,
uvicorn, Pydantic odbijeni. Model konkurentnosti je u ADR-016 (ranije `threading`).
**Zašto.** Mentor je tražio socket-e; cilj je razumeti granicu sistema, pa se validacija
poruka piše sama (~80 linija).
**Cena.** Ono što bi Pydantic dao besplatno pišemo ručno.

## ADR-004 — pygame klijent prvi, veb kasnije

**Odluka.** Faza 3 je pygame. `net.py` i `state.py` se pišu bez pygame-a da bi se, ako
ikad dođe veb klijent (vanilla JS, bez build koraka), preveli 1:1.
**Zašto.** Zahtev mentora se ispunjava u jednom jeziku sa jednom zavisnošću.
**Cena.** Sloj crtanja bi se za veb pisao drugi put.

## ADR-005 — `unittest`, ne `pytest`

**Odluka.** Standardna biblioteka; tabele kroz `subTest()`.
**Zašto.** Nula zavisnosti za testove; `pytest` može da ih pokrene kad zatreba.
**Cena.** Verboznije.

## ADR-006 — make/unmake umesto kopiranja table

**Odluka.** Potez se odigra na istoj tabli i vrati. `Board` je mutabilan; `UndoRecord`
čuva šta je promenjeno.
**Zašto.** Perft dubine 5 traje minute umesto desetina minuta; bot bi sa kopiranjem bio
neupotrebljiv.
**Cena.** `unmake` mora tačno da vrati rokadu, en passant i brojač polupoteza — perft to hvata.

## ADR-007 — Perft kao dokaz ispravnosti, alat od 1.3

**Odluka.** Ispravnost generatora se dokazuje perft brojevima sa Chess Programming Wiki.
`tools/perft.py` sa `perft_divide` postoji od taska 1.3 i pokreće se posle svake izmene
generatora; 1.8 je formalni checkpoint. Skup i dubine: ADR-026.
**Zašto.** Bag se hvata u tasku u kom nastane i lokalizuje po korenskom potezu.
**Cena.** Perft mora biti brz (ADR-006).

## ADR-008 — `RuleSet` sa profilima `online` i `fide`

**Odluka.** Pravila remija su konfiguracija. `online` (podrazumevan): trostruko ponavljanje
i 50 poteza automatski; 75/petostruko se ne implementiraju. `fide`: striktno po FIDE.
**Zašto.** Online platforme se namerno razlikuju od FIDE; ponašanje je eksplicitno.
**Cena.** Jedan sloj konfiguracije.

## ADR-009 — SQLite kroz `GameRepository` (faza 5, posle predaje)

**Odluka.** `sqlite3` iz stdlib-a; server ne piše SQL nego zove `GameRepository`, sa
`InMemoryGameRepository` za testove; migracije kao numerisani SQL fajlovi; putanja iz
`CHESS_DB_PATH`.
**Zašto.** Sve što projektu treba mora biti u repou, jednom `pip` komandom ili napravljeno
pri prvom pokretanju — prethodni projekat je pukao kod druge osobe na SQL Server + ODBC + `.env`.
**Cena.** Interfejs sa jednom implementacijom.

## ADR-010 — Tekst interfejsa u `sr.json`

**Odluka.** Nijedan tekst vidljiv korisniku nije u kodu; ključevi u `assets/i18n/sr.json`.
Logovi na engleskom bez dijakritika. Font DejaVu Sans.
**Zašto.** Isti fajl bi čitao i veb klijent; Windows konzola puca na č ć š ž đ.
**Cena.** Jedan skok kroz `t()` po tekstu.

## ADR-011 — Lobby poruke od faze 2

**Odluka.** `LOBBY_JOIN`, `LOBBY_STATE`, `MATCH_FOUND` postoje od faze 2; server samo
spari prva dva u redu.
**Zašto.** Kasnije dodavanje bi lomilo klijente.
**Cena.** ~20 linija.

## ADR-013 — `Square` je `int`, bez type checkera

**Odluka.** `Square = int` (0–63, a1 = 0, h8 = 63) — običan alias, ne `NewType` ni
dataclass; imenovane konstante i `file_of()`, `rank_of()`, `to_algebraic()`,
`from_algebraic()`. `Move` ostaje `frozen=True, slots=True`. mypy se ne koristi; hintovi
su dokumentacija.
**Zašto.** Perft dubine 5 obilazi 4,8 miliona čvorova — desetine miliona `Square` objekata
su preskupe; bez type checkera `NewType` ne daje ništa osim imena.
**Cena.** Funkcija koja prima `Square` to kaže u potpisu i docstringu. Pakovanje poteza u
`int` tek ako merenje pokaže potrebu.

## ADR-014 — `UndoRecord` (task 1.2)

**Odluka.** Nosi pojedenu figuru **i njeno polje** (kod en passanta pešak nije na
odredištu), prethodna prava na rokadu, prethodno ep polje, prethodni brojač polupoteza,
prethodni Zobrist ključ.
**Zašto.** `unmake` je tačan po konstrukciji, ne zaključivanjem.
**Cena.** Svaki nov tip poteza dopunjava zapis — perft hvata ako se zaboravi.

## ADR-015 — Zobrist heš od 1.2, inkrementalno

**Odluka.** Ključ se održava XOR-om u `make`/`unmake`, ne računa iznova.
**Zašto.** Ponavljanje pozicije (1.9) postaje brojanje ključeva u istoriji; isti heš služi
transpozicionoj tabeli bota.
**Cena.** Jedan koncept više u fazi 1.

## ADR-016 — Server je jednonitni `selectors` event loop

**Odluka.** Jedna nit, `selectors`, `select(timeout=vreme_do_najbliže_zastavice)`.
**Zašto.** Pad zastavice okida sam i kad niko ništa ne šalje; nema `Lock`-ova ni trka.
**Cena.** Kod organizovan oko event loop-a, manje intuitivno od niti.

## ADR-017 — `tools/cli_client.py` umesto `nc`

**Odluka.** CLI klijent u stdlib-u (task 2.0), prima UCI unos, ispisuje odgovore.
**Zašto.** `nc` ne postoji na Windows-u; dobija se trajan debug alat.
**Cena.** Pola sata.

## ADR-018 — Potez na žici strukturiran, UCI u `core`

**Odluka.** Na žici `{"from": "e2", "to": "e4", "promotion": "queen"}`; u `core`
`Move.from_uci()` i `to_uci()` za CLI klijent, testove i bota.
**Zašto.** Idiomatski JSON, čitljiv u debug-u.
**Cena.** Dvadesetak linija konverzije.

## ADR-022 — `Move` nosi `kind`

**Odluka.** `MoveKind`: `NORMAL`, `CAPTURE`, `DOUBLE_PAWN_PUSH`, `EN_PASSANT`, `CASTLE`,
`PROMOTION`; generator ga popunjava. `from_uci()` ne može da odredi `kind` bez table, pa
se potez spolja uvek traži u listi legalnih poteza, nikad ne izvršava direktno.
**Zašto.** `make`/`unmake` postaju grananje po vrsti; `legal_moves` može da izrazi četiri
promocije; klijent zna kad da otvori dijalog bez ijednog pravila.
**Cena.** Jedan enum.

## ADR-023 — `STATE` je pun snapshot, ne delta

**Odluka.** Svaka `STATE` poruka nosi sve za ceo ekran, uključujući `history` u SAN-u.
Klijent ne akumulira ništa.
**Zašto.** Rekonekcija je besplatna; klijent ne može da se raziđe sa serverom.
**Cena.** Par stotina bajtova po poruci.

## ADR-024 — Granica: čitanje pozicije naspram odlučivanja

**Odluka.** Klijent sme da parsira FEN i crta; ne sme da računa kuda figura sme. Uvozi
samo `core/types.py` i `core/fen.py`; proverava `tools/layer_check.py`.
**Zašto.** Bez zapisane granice bi se o FEN-u u klijentu raspravljalo iznova.
**Cena.** Nikakva.

## ADR-025 — Diskonekcija, ponuda remija, potez u letu

**Odluka.** Diskonekcija: `OPPONENT_DISCONNECTED`, sat protivnika ide, partija se završava
padom zastavice (`timeout`). Remi: nudi se samo na potezu, pada čim protivnik odigra, jedna
ponuda po potezu. Najviše jedna `MOVE` bez odgovora; `ERROR` vezan za potez nosi `move`.
**Zašto.** Ništa novo se ne uvodi; poklapa se sa online platformama; ostavlja mesto za
rekonekciju bez izmene protokola.
**Cena.** Tri koda greške.

## ADR-026 — Perft: skup pozicija i dubine

**Odluka.** Podrazumevano (~300.000 čvorova): početna d4 · Kiwipete d3 · Position 3 d4 ·
Position 4 d3. Iza `CHESS_SLOW_TESTS=1` (~9 miliona): početna d5 · Kiwipete d4 · ostale
dublje. FEN-ovi i brojevi sa Chess Programming Wiki, nikad iz sećanja.
**Zašto.** Četiri pozicije na maloj dubini nađu više bagova po sekundi nego dve na velikoj;
podrazumevani suite ostaje brz, pa se stvarno pokreće.
**Cena.** Nijedna.

## ADR-027 — Zobrist: fiksan seed, ep polje uslovno

**Odluka.** Tabela se generiše sa fiksnim seed-om. Ep polje ulazi u ključ samo kad je
en passant uzimanje stvarno moguće.
**Zašto.** Determinizam testova; bez uslova ista pozicija dobijena drugim redosledom poteza
ne bi bila jednaka i trostruko ponavljanje ne bi okinulo.
**Cena.** Jedna provera pri ažuriranju ključa.

## ADR-029 — `pip install -e ".[dev]"` je jedina komanda za pokretanje

**Odluka.** `src/` raspored traži editable instalaciju; `[dev]` donosi `ruff`, bez kog
checkpoint ne prolazi. `ruff` ostaje dev-only.
**Zašto.** `python -m unittest discover` ne nalazi paket bez instalacije.
**Cena.** Lako je zaboraviti `[dev]`; ništa to ne hvata automatski.

## ADR-033 — Tabela slojeva je izvršiva

**Odluka.** `tools/layer_check.py` (u gitu) parsira uvoze kroz `ast` po prepisu tabele iz
CONVENTIONS §2; `tests/test_layers.py` ga pokreće i tvrdi da imena redova u dokumentu i
alatu ostaju ista. Fajl bez reda u tabeli je nalaz, ne tišina. `__init__.py` uvozi samo
stdlib; uvoz je uvek pun put (`from chess.core.types import Piece`).
**Zašto.** Kršenje granice hvata suite, ne asistent koji se seti; fasada u `__init__.py`
bi pravila ivicu u grafu zavisnosti koju tabela ne opisuje.
**Cena.** Nov modul traži nov red u tabeli u istom commitu. Vezana su imena redova, ne
semantika ćelija.

## ADR-034 — `capture` i `promotion` su uvek serverski podaci

**Odluka.** `capture: true` na svakom potezu koji uzima, uključujući en passant;
`promotion: true` na svakom potezu koji traži promociju, u jednu od četiri figure.
**Zašto.** Kod en passanta je odredišno polje prazno — klijent koji zaključuje crta
pogrešno, a klijent koji zaključuje tačno je implementirao pravilo.
**Cena.** Jedan bool po potezu.

## ADR-035 — `ruff` ne dira `docs/`

**Odluka.** `extend-exclude = ["docs"]` u `pyproject.toml`.
**Zašto.** `ruff format` prepravlja Python blokove u Markdown-u i lomi namerno zbijene
primere; obrazac `"*.md"` ne radi (izmereno).
**Cena.** Python blokovi u dokumentaciji nemaju proveru.

## ADR-038 — Rasterizacija kroz pygame; `cairosvg` odbijen

**Odluka.** `tools/rasterize_pieces.py` pretvara 12 Cburnett SVG-ova u PNG od 80 i 32 px
kroz pygame (nanosvg). PNG ide u git; alat nije zavisnost projekta.
**Zašto.** `cairosvg` na Windows-u vuče native DLL-ove van `pip`-a; alat koji jednom
generiše resurs nije zavisnost — igraču trebaju PNG-ovi, a oni su u gitu.
**Cena.** nanosvg ne skalira crtež na platno — alat sam skalira geometriju i proverava
udeo neprovidnih piksela kroz veličine.

## ADR-039 — Tuđi materijal se čuva bajt u bajt

**Odluka.** `.gitattributes`: `-text` za `assets/pieces/svg/*.svg` i
`assets/fonts/LICENSE.txt`, `binary` za PNG i TTF. `tests/test_assets.py` proverava 12 `sha1`
vrednosti iz `assets/pieces/LICENSE.txt` i red u `.gitattributes`. Verzija i `sha256` fonta
stoje u našem `PROVENANCE.txt`, ne u tuđoj licenci.
**Zašto.** `core.autocrlf=true` menja prelaske reda pri kloniranju, pa bi zapisani heševi
bili netačni kod svakog ko klonira. Tuđ dokument se ne dopunjuje našom rečenicom.
**Cena.** `.gitattributes` se ne dira bez čitanja oba `LICENSE.txt`.

## ADR-040 — Ugovor `t()`

**Odluka.** `t()` ne baca na loš podatak: nepostojeći ključ vraća ključ, parametar koji
fali ostaje `{{ime}}`, oba uz WARNING (jednom po ključu). Baca na pogrešan poziv:
`RuntimeError` pre `load()`, `TypeError` za parametar koji nije `str`. `load()` odbija BOM,
loš JSON i dupli ključ sa `ValueError`. Zamena je `{{ime}}`; parametri su stringovi;
`utf-8-sig` se ne koristi.
**Zašto.** Prevod koji fali degradira ekran umesto da ga obori, a vidi se; greška u kodu
pada odmah. Sintaksa mora da radi isto u JavaScript-u (`str(1.0)` ≠ `String(1.0)`).
**Cena.** Bez format specifikatora; broj se formatira na pozivnom mestu.

## ADR-041 — Zatvoren skup iz protokola se čita mašinski

**Odluka.** `tests/client/test_i18n.py` parsira prvu kolonu tabele kodova iz `PROTOCOL.md`
§5 i tvrdi oba smera prema `sr.json` (`error.` + kod malim slovima). Isto važi za
`termination.*` u fazi 3. U 2.1 spona prelazi sa dokumenta na enum u `protocol/messages.py`.
**Zašto.** Dodat kod bez ključa i ključ bez koda su tihi kvarovi.
**Cena.** Oblik tabele u §5 je noseći; test tvrdi da ključ postoji, ne da je prevod tačan.

## ADR-042 — BSD-3-Clause za naš kod; `LICENSE` nosi uslove, `THIRD-PARTY.txt` obim

**Odluka.** `LICENSE` u korenu je kanonski SPDX tekst, neizmenjen osim reda o autorskim
pravima. `THIRD-PARTY.txt` nabraja direktorijume sa svojom licencom, u bloku koji čita
`tests/test_assets.py`; ne zove se `NOTICE` ni `COPYRIGHT`.
**Zašto.** Javan repo bez licence je „sva prava zadržana"; figure su pod istim uslovima,
pa copyleft ne bi imao smisla. Naša rečenica u standardnom tekstu putovala bi dalje kao
deo uslova.
**Cena.** Treći direktorijum sa tuđim materijalom obara test — namerno.

## ADR-043 — Licenca i u metapodacima paketa

**Odluka.** `license = "BSD-3-Clause"`, `license-files = ["LICENSE"]` u `pyproject.toml`;
`setuptools>=77` u `build-system.requires`, jer 76 odbija SPDX string.
**Zašto.** Wheel je nosio nula redova o licenci; klasifikator ne razlikuje 2- od 3-clause.
**Cena.** `pip show` ispisuje prazno `License:` (čita staro polje) — to je ispravno. Ako
resursi uđu u paket, `license-files` mora da poraste.

## ADR-047 — Dve mašinske kapije za ono što se u diffu ne vidi

**Odluka.** `tests/test_encoding_bytes.py` drži BOM van `assets/**/*.json`, `src/**/*.py`
i `docs/**/*.md`, nad bajtovima. `tools/check_commit_trailers.py` traži `Co-Authored-By:` i
`Claude-Session:` u lokalnoj istoriji poruka (izlaz 0/1/2).
**Zašto.** Oba kvara su jednom prošla nezapaženo; provera nad bajtovima ne deli sudbinu sa
kvarom od kog štiti.
**Cena.** Trajleri se proveravaju samo lokalno, ne u opisu PR-a.

## ADR-048 — REZ 2: proces se seče, proizvod ostaje

**Odluka.** Od 22. 9. 2026 obim je faze 0–3. Ukinuti su: dnevnik po tasku, pitanja po
tasku (ADR-021), propagacija u istom commitu kao pravilo, ⚠️ oznake i „telo se ne menja",
pravila o tekstu van gita, `POJMOVNIK.md`. Procesni ADR-ovi su spojeni ili uklonjeni.
Kapije ostaju cele i dobijaju jednu komandu, `tools/check.py`. Claude Code sam odobrava
čitanje, izmene i testove; pita za commit, push i grane.
**Zašto.** Faza 0 je potrošila više vremena na pravila o pravilima nego na proizvod, a
svaki task je vukao pun krug kroz pet dokumenata. Rok za zahtev mentora to ne dozvoljava.
**Cena.** Manje zapisa o tome kako se do odluka došlo; istorija do `4770159` to čuva.
Razumevanje se proverava obrnutim pregledom na kraju faze, ne po tasku.
