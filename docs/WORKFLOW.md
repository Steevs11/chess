# WORKFLOW — kako radimo na projektu

Ovaj fajl je podsetnik za svakodnevni rad. Otvori ga kad ne znaš šta je sledeći korak.

---

## 1. Gde se šta radi

| Radnja | Gde |
|---|---|
| Arhitektura, odluke, izbor tehnologija | **claude.ai** |
| Objašnjenja, "ne razumem ovaj kod" | **claude.ai** |
| Provera da si razumeo (ti pričaš, Claude ispituje) | **claude.ai** |
| Pisanje koda, testovi, git | **Claude Code** |
| Pisanje finalne dokumentacije faze | **Claude Code** |

Razlog za podelu: Claude Code šalje celu konverzaciju sa svakim zahtevom. Duga
rasprava o arhitekturi unutar sesije za kodiranje usporava i poskupljuje svaki
kasniji zahtev.

### Predaja teksta između površina

Tekst koji planski chat sastavlja za Claude Code odvojen je od teksta upućenog
arhitekti tako da se prenosi bez ijedne izmene. Jedan odgovor traži od arhitekte
najviše jednu radnju: radnje se izvršavaju redom, a druga se izgubi dok prva traje.
Obavezuje odgovore sa claude.ai; Claude Code ne sastavlja predaju.

Razgovor sa arhitektom vodi se na srpskom, na obe površine. Jezik koda, komentara i
commit poruka je zaseban zahtev i stoji u CONVENTIONS:9–10.

Fajl iz repoa planski chat učitava sam, umesto da traži da mu se zalepi; lepi se samo ono
čiji izvor nije u gitu. Oblik reference — zakucavanje na commit SHA — stoji u
CONVENTIONS §8 „Referenciranje za pregled"; ovde je novo samo ko učitava.

Kod donet na pregled prvo se objašnjava, pa se tek onda prepravlja. Ko šta radi stoji u
PROJECT §8 i u tabeli iznad; novo je samo redosled — prepravka pre objašnjenja traži
odobrenje za ono što nije pročitano.

Nacrt odgovora na pitanja iz koraka 4 sastavlja planski chat; arhitekta ga čita, proverava
i predaje. Korak 5 ADR-021 time ostaje netaknut: odgovara arhitekta, a nacrt koji ne
prepoznaje kao svoj vraća umesto da ga preda.

Odgovor je konkretan i kratak, a kratko pitanje dobija kratak odgovor. Dužina koja ne nosi
odluku troši vreme koje ritam po tasku traži za korak 4.

Kad se od arhitekte traži da bira, traženo i opcije staju u dve do tri rečenice. Ako je u
diffu problem, umesto opcije ide STOP: izbor između dve mogućnosti od kojih nijedna ne
valja nije odluka nego prenošenje tereta.

---

## 2. Anatomija jedne sesije

```
> claude                          (iz PyCharm terminala, u korenu projekta)

> Pročitaj @docs/ROADMAP.md i @docs/PROJECT.md.
  Nastavljamo na 1.4 — rokada.

  → Claude ukratko kaže gde smo stali i šta je sledeće

> [Shift+Tab]                     → plan mod

> Implementiraj rokadu u core/movegen.py.
  Uslovi su u @docs/PROJECT.md, sekcija 7.
  Prvo napiši testove koji padaju, pa implementaciju.
  Ako je nešto dvosmisleno, pitaj umesto da pretpostaviš.

  → Claude napiše PLAN i pokaže ga. Ne dira kod.

> ┌─────────────────────────────────────────┐
  │  PROČITAJ PLAN.                         │
  │  Odobri, ili traži izmenu.              │
  └─────────────────────────────────────────┘

  → Claude piše testove → padaju → piše implementaciju
  → testovi prolaze → perft se pokreće ako je diran generator poteza
    (uslov je u CONVENTIONS §9, alat je tools/perft.py)

  → Claude objasni u 3–5 rečenica: šta je urađeno, zašto tako i koja
    alternativa je odbačena

  → Claude TEBI postavi 2–3 pitanja o napisanom kodu, o zašto a ne o šta
    (ADR-021, korak 4 — ne preskače se)

> Odgovaraš. Gde ne znaš, tražiš drugačije objašnjenje, pa opet.
  Sve što tebi nije jasno pitaš ovde.

> git diff

> ┌─────────────────────────────────────────┐
  │  PROČITAJ DIFF.                         │
  │  Ovo se ne preskače nikad.              │
  └─────────────────────────────────────────┘

> Commituj.

> Ažuriraj docs/ROADMAP.md. Ako smo doneli odluku, dopuni i DECISIONS.md.

> /clear
```

Dva uokvirena koraka su tvoja i ne preskaču se. Između njih brzo ide sve osim
pitanja iz koraka 4, koja traže tvoje vreme i takođe se ne preskaču (ADR-021).

Kad task ne piše kod — svođenje dokumenata, merenje, presuda — pitanja iz koraka 4 su o
onome što je task uradio. Korak se ne preskače zato što koda nema.

Kad se jedan fajl menja na više mesta, **sve izmene tog fajla pokazuju se pre prve**:
mesto i šta se menja. Posle toga se primenjuju onako kako alat ide. Izmena
odobrena bez uvida u ostale izgleda kao ceo plan za taj fajl.

### Kad se staje

Ritam nema bezuslovni STOP — upit na svaku komandu i svaku izmenu je već tačka
provere. Staje se na četiri mesta (ADR-046):

1. **Nalaz obara nešto što je plan proglasio odlučenim.**
2. **Nepredviđen pad testa** — neočekivana *dijagnoza* je STOP; neočekivan *broj*
   je zapis u `faza-N.md`.
3. **Tačka koju je plan unapred imenovao** — tu se staje i kad sve prolazi.
4. **Zatečeno stanje je drugačije od onog koje plan pretpostavlja.**

Na svakom STOP-u zatečeno stanje ostaje netaknuto dok se ne objasni.

---

## 3. Šta je jedan task

> **Jedan task = jedna stvar koja se završava zelenim testom i jednim commitom.**

| Jeste jedan task | Nije |
|---|---|
| implementiraj rokadu | "napravi engine" — predugačko |
| dodaj FEN parsiranje | "uradi fazu 2" — predugačko |
| napiši sat sa inkrementom | ispravi typo — prekratko, ne treba `/clear` |
| popravi bag gde perft daje 8905 umesto 8902 | |

Provera: ako ne možeš u jednoj rečenici da kažeš kada je gotovo, to su dva taska.

Podfaze iz `ROADMAP.md` (1.1, 1.2, 1.3...) su već kalibrisane kao jedan task.

---

## 4. Kada nova sesija

| Situacija | Radnja |
|---|---|
| Task završen, commitovan | provera istorije, `push`, pa `/clear` |
| Menjaš temu | `/clear` |
| Novi dan | `/clear` |
| `/context` ispod 30% slobodnog | `/clear` ili `/compact` |
| Usred taska, kontekst se puni | `/compact` (sažima i nastavlja) |
| Alat javio ažuriranje u toku taska | restartuj pre nastavka |

`/clear` briše razgovor. Ostaješ u istom terminalu i projektu.

**`push` ide posle commita i pre `/clear`-a.** Nije deo taska, jer CONVENTIONS §9 završava
na commitu. Prethode mu obe provere istorije iz CONVENTIONS §8: ignorisane putanje i
trajleri u porukama. Posle `/clear`-a nova sesija o nepushovanom commitu ne zna ništa.

**Šta se automatski učita** zavisi od verzije alata. Izmereno je i zapisano u
ADR-044, u tabeli koja nosi verziju i datum — ovde se ne prepisuje, jer bi kopija
zastarela sa prvim ažuriranjem.

**Šta se NE prenosi:** razgovor, pročitani fajlovi, sve što je dogovoreno usmeno.

> **Ako je važno, mora biti u fajlu.** Sve ostalo nestaje sa `/clear`.

---

## 5. Pre `/clear`

Kontrolna lista je **CONVENTIONS §9** — sedam stavki, plus provera koja se ne
štiklira jer se ne može odštiklirati. Ovde se ne prepisuje: dve liste istih stavki
znače da jedna sutra zaostane, a ne zna se koja.

Ta neštiklirana provera je najvažnija. Ako ne prolazi, ne prelazi dalje — traži da
ti se objasni drugačije, ili odnesi kod na claude.ai.

---

## 6. Komande

| Komanda | Kada |
|---|---|
| `Shift+Tab` | plan mod — za sve veće od jedne funkcije |
| `/clear` | između taskova |
| `/compact` | usred taska, kad se kontekst puni |

Ovo su tri mesta na kojima komanda nosi **našu** politiku. Spisak komandi svoje
verzije daje sam alat; ovde ne stoji, jer bi zastareo bez ijednog znaka (ADR-044).

---

## 7. Šablon prompta

```
Kontekst: [koji fajl, koji sloj, šta trenutno radi]
Zadatak:  [jedna konkretna stvar]
Pravila:  [šta iz docs/CONVENTIONS.md se odnosi na ovo]
Provera:  [kako znam da je gotovo]

Ako je nešto dvosmisleno, pitaj pre nego što počneš.
```

### Anti-obrasci

| Ne piši | Piši |
|---|---|
| "napravi šah" | "implementiraj generate_pawn_moves u movegen.py, uključujući dvopotezni start i en passant" |
| "popravi bug" | "perft dubina 3 vraća 8905 umesto 8902, nađi uzrok" |
| "je l' može ovako?" | "promeni ovu funkciju tako da..." |
| "dodaj testove" | "dodaj test za rokadu kad kralj prolazi kroz napadnuto polje" |

---

## 8. Na kraju faze

`docs/faze/faza-N.md` **ne nastaje na kraju faze.** Po ADR-021 dobija dva reda posle
**svakog** taska — postavljeno pitanje i da li si znao odgovor — i CONVENTIONS §9 to
vodi kao stavku gotovog taska. Na kraju faze se zato sastavlja, ne piše.

1. **claude.ai** — ispričaš celu fazu svojim rečima. Claude ispituje. Gde zapneš, tu
   se vraćaš na kod.
2. **Claude Code**, nova sesija — od zapisa po taskovima, koda, `ROADMAP.md`-a i
   `DECISIONS.md`-a sastavlja se `docs/faze/faza-N.md`.
3. Merge grane u `main` — oblik i uslov su u CONVENTIONS §8.
4. `/clear`, pa sledeća faza.

Na kraju projekta "napiši dokumentaciju" postaje sastavljanje, ne pisanje.

---

## 9. Ko šta odobrava

Šta je projektu **zabranjeno** stoji u CONVENTIONS §8. Šta izvršilac sme da pokrene
**bez pitanja** stoji u `.claude/settings.json`. To su dva različita pitanja i
nijedno se ovde ne prepisuje (ADR-044).

Ono što samo ovaj fajl može da kaže: **odobrenje ide na svaku komandu i svaku
izmenu**, ne jednom na plan. Plan odobravaš pre nego što kod postoji; svaki
pojedinačan potez posle toga odobravaš u trenutku kad se dešava.

Odobrenje bez uvida u ono što se odobrava nije odobrenje, nego potvrda tuđeg sažetka.
Zato izvršilac **izlaz svake komande čiji ishod nešto dokazuje** (testovi, kapije, brojevi,
poređenja) **prenosi doslovno** u odgovor. Pre komande koja menja fajlove pokazuje šta bi
promenila. Dug izlaz sme da skrati za redove koji se ponavljaju, nikad za zaključak.
