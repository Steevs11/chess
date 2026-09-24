# WORKFLOW — kako radimo

## 1. Ko šta radi

| Radnja | Gde |
|---|---|
| Arhitektura, odluke, objašnjenja, pregled diffa, debug razgovori | claude.ai (planski chat) |
| Pisanje koda i testova, git, `ROADMAP.md`, `faza-N.md` | Claude Code |
| Odluke | student |

Razgovor je na srpskom. Kod, komentari i commit poruke su na engleskom.

## 2. Jedan task

Jedan task = jedan red iz `ROADMAP.md` = jedan commit.

1. `Pročitaj @docs/ROADMAP.md (blok TRENUTNO). Radimo X.Y.` — Claude Code kaže šta će
   uraditi; plan mod (`Shift+Tab`) za sve veće od jedne funkcije.
2. Student odobri plan.
3. Claude Code piše testove, pa implementaciju; pušta `python tools/check.py`; perft ako je
   diran generator poteza.
4. Claude Code napiše **rezime u tri do pet rečenica**: šta je urađeno, zašto tako, šta je
   odbačeno.
5. Student pročita `git diff` — ceo, jednom.
6. Commit. Blok TRENUTNO u `ROADMAP.md` se ažurira u istom commitu.
7. `git push`, pa `/clear`.

Nema pitanja po tasku i nema dnevnika po tasku. Razlog odluke stoji u commit poruci ili,
ako je arhitektonska, u `DECISIONS.md`.

## 3. Kad Claude Code staje i pita

Samo na tri mesta:

1. **Nepredviđen pad testa** — pad čija dijagnoza nije ona koju plan očekuje.
2. **Nalaz koji obara nešto odlučeno** — ADR, `PROTOCOL.md`, ili tekst taska u `ROADMAP.md`.
3. **Tačka koju je plan unapred imenovao.**

Zatečeno stanje ostaje netaknuto dok se ne odluči. Sve ostalo Claude Code rešava sam i
navodi u rezimeu. Odluka se traži od studenta u dve-tri rečenice; student, ako treba,
nosi pitanje u planski chat.

## 4. Dozvole

Šta Claude Code sme bez pitanja stoji u `.claude/settings.json` (van gita): čitanje,
izmena fajlova, testovi, `ruff`, alati iz `tools/`, `git status/diff/log/add`.
**Pita** za `git commit`, `git push`, `git merge`, promenu grane i brisanje.
**Zabranjeno** je ono iz CONVENTIONS §8 („Zabranjeno").

## 5. Sesije

- `/clear` posle svakog taska i kad se menja tema; `/compact` usred taska kad se kontekst puni.
- Ako alat javi ažuriranje u toku taska, restart pre nastavka.
- Sve što je važno mora biti u fajlu — razgovor nestaje sa `/clear`.
- Planski chat na claude.ai: nov chat po fazi ili kad postane spor. Na početku chata se
  učita `ROADMAP.md` sa GitHub-a, zakucan na commit SHA.

## 6. Kraj faze

1. `python tools/check.py` zelen i checkpoint faze iz `ROADMAP.md` prošao na svežem klonu.
2. Claude Code napiše `docs/faze/faza-N.md` (do 80 redova): šta je napravljeno, kako se
   pokreće i proverava, tri do pet ključnih odluka. Bez dnevnika.
3. Merge u `main` sa `--no-ff`, push.
4. Obrnuti pregled na claude.ai: student objašnjava fazu svojim rečima, chat ispituje.
   Ne zapisuje se. Može i na kraju projekta.
