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

---

## 2. Anatomija jedne sesije

```
> claude                          (iz PyCharm terminala, u korenu projekta)

> /model opusplan                 (samo prvi put nakon instalacije)

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
  → testovi prolaze → sam pokreće perft skill

> Zašto si _rook_path_clear odvojio od _king_path_safe?

  → Claude objasni. Pitaj sve što ti nije jasno.

> git diff

> ┌─────────────────────────────────────────┐
  │  PROČITAJ DIFF.                         │
  │  Ovo je jedini korak koji se ne          │
  │  preskače nikad.                         │
  └─────────────────────────────────────────┘

> Commituj.

> Ažuriraj docs/ROADMAP.md. Ako smo doneli odluku, dopuni i DECISIONS.md.

> /clear
```

Dva uokvirena koraka su tvoja i ne preskaču se. Sve između njih ide brzo.

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
| Task završen, commitovan | `/clear` |
| Menjaš temu | `/clear` |
| Novi dan | `/clear` |
| `/context` ispod 30% slobodnog | `/clear` ili `/compact` |
| Usred taska, kontekst se puni | `/compact` (sažima i nastavlja) |

`/clear` briše razgovor. Ostaješ u istom terminalu i projektu.

**Šta se automatski učita u svaku novu sesiju:**
`CLAUDE.md` · `.claude/rules/` (kad putanja odgovara) · opisi skillova · `settings.json`

**Šta se NE prenosi:** razgovor, pročitani fajlovi, sve što je dogovoreno usmeno.

> **Ako je važno, mora biti u fajlu.** Sve ostalo nestaje sa `/clear`.

---

## 5. Kontrolna lista pre `/clear`

- [ ] Testovi prolaze
- [ ] `ruff` čist
- [ ] Pročitao sam diff
- [ ] Commitovano
- [ ] `ROADMAP.md` ažuriran
- [ ] `DECISIONS.md` dopunjen ako je doneta odluka
- [ ] Razumem šta je urađeno — mogu da objasnim naglas

Poslednja stavka je najvažnija. Ako ne prolazi, ne prelazi dalje —
pitaj Claude Code da objasni, ili donesi kod na claude.ai.

---

## 6. Komande

| Komanda | Kada |
|---|---|
| `Shift+Tab` | plan mod — za sve veće od jedne funkcije |
| `/model opusplan` | jednom, na početku |
| `/clear` | između taskova |
| `/compact` | usred taska, kad se kontekst puni |
| `/context` | kad osetiš usporenje |
| `/usage` | potrošnja u odnosu na plan |
| `/memory` | pregled i izmena CLAUDE.md |
| `/help` | spisak komandi tvoje verzije |

---

## 7. Šablon prompta

```
Kontekst: [koji fajl, koji sloj, šta trenutno radi]
Zadatak:  [jedna konkretna stvar]
Pravila:  [šta iz CLAUDE.md se odnosi na ovo]
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

1. **claude.ai** — ispričaš šta je urađeno svojim rečima. Claude ispituje.
   Gde zapneš, tu se vraćaš na kod.
2. **Claude Code**, nova sesija — task je: napiši `docs/faze/faza-N.md`.
   Claude pročita kod, `ROADMAP.md` i `DECISIONS.md` i napiše tekst na srpskom.
3. Merge grane u `main` sa `--no-ff`.
4. `/clear`, pa sledeća faza.

Na kraju projekta "napiši dokumentaciju" postaje sastavljanje, ne pisanje.

---

## 9. Šta Claude radi sam, a šta traži odobrenje

| Sam | Uz odobrenje | Nikad |
|---|---|---|
| čita i pretražuje kod | **plan** | `git push` |
| pokreće testove | `git commit` | `reset --hard`, `rebase`, `clean -fd` |
| pokreće `ruff` | `git merge` | briše ili menja test da prođe |
| poziva skillove | nova zavisnost | `pip install` bez odobrenja |
| `git add`, `status`, `diff`, `log` | fajl van dogovorene strukture | menja fajlove van plana |
| piše kod unutar odobrenog plana | izmena `CLAUDE.md` ili pravila | |

Plan odobravaš ti. Izvršavanje ide samo.
