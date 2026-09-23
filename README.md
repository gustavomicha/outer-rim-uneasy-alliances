# Uneasy Alliances — playable web version

A browser version of **Uneasy Alliances**, the fan-made cooperative expansion for *Star Wars: Outer Rim*
by Mike Schoenfeld (v2.2.01), so you can play it with your physical copy of the game without printing
and cutting 140+ cards.

**▶ Play: https://gustavomicha.github.io/outer-rim-uneasy-alliances/**

It is a single self-contained HTML file: no server, no install, no internet needed once loaded. Your game
is saved in the browser, so closing the tab doesn't lose it.

## What it does

- **Setup** — pick one of the 8 scenarios and a difficulty (Easy / Medium / Hard), name both players and
  choose their player board colors. The co-op event deck is built for you: the right number of generic
  cards are removed at random and the scenario's themed cards are shuffled in.
- **Scenario sheet** — both sides are drawn in the style of the *Unfinished Business* ambition sheets.
  Click a slot to place or remove a goal token, flip between sides A and B, and track each player's fame.
  On side B the Cooperative Objective Marker location matching your goal tokens is highlighted, and every
  "Resolve card #…" reference opens that card.
- **Co-op event deck** — draw at the end of a turn, pass the turn automatically, discard the top card when
  defeated, and browse the discard pile. Cards can be rotated 180°, sent to a player's hand or discarded.
  On themed cards, the half that does not belong to your scenario is dimmed.
- **Numbered deck (#101–148)** — search a number or click it in the grid. Numbers with two versions pick
  one at random, and your scenario's job and crew cards are highlighted.
- **Co-op job market** — top card always face up, with shuffle, top-to-bottom and gain actions.
- Undo (Ctrl/Cmd+Z), a game log, and a loss screen when the event deck runs out.

## Credits

- **Expansion design:** Mike Schoenfeld — *Uneasy Alliances* v2.2.01, shared on
  [BoardGameGeek](https://boardgamegeek.com/thread/3058093/star-wars-outer-rim-uneasy-alliances-a-fan-made-co).
  Playtesting by Michelle Schoenfeld, Kevin Schoenfeld, Randy Comstock and Tony Teshera.
- **This web version:** built with [Claude Code](https://claude.com/claude-code).
- You need the base game *Star Wars: Outer Rim* and the *Unfinished Business* expansion to play.

### One fix applied

The event card that introduces Jabba's Gammorean says "Resolve card #148", but #148 is Erskin Semaj
(Mon Mothma's aide); the card described is Jubnuck, **#143**. The app shows #143 on that card.

## Rebuilding it

`index.html` is generated from the expansion PDF, which is not included in this repo.

1. Download *Uneasy Alliances (V2.2.01)* from the BGG thread above and put the PDF in the repo root,
   keeping its name: `Uneasy Alliances - Outer Rim Cooperative (V2.2.01).pdf`.
2. Put the *Unfinished Business* rulebook PDF (`sw07_outerrim_rulebook_v2-compressed.pdf`, from the
   [Fantasy Flight Games support page](https://www.fantasyflightgames.com/en/products/star-wars-outer-rim/))
   in the root too — the page frame is taken from it.
3. `pip install pymupdf pillow`
4. `python build/build.py`

The script cuts every card out of the PDF, checks each scenario sheet's progress circles against the text
in `build/scenarios.json`, and inlines everything (cards, fonts, icons) into `index.html`.

- `build/app.html` — the app itself: one template with all the markup, styles and logic.
- `build/app_classic.html` — an earlier dark theme; add it to `TARGETS` in `build/build.py` to build it.
- `build/scenarios.json` — the text of all 16 scenario sheet sides.
- `build/assets/fonts/` — Source Sans 3, Saira Condensed and Montserrat (SIL Open Font License).

## Disclaimer

Unofficial fan project, free and non-commercial. Not affiliated with, endorsed by or sponsored by
Fantasy Flight Games, Asmodee or Lucasfilm. *Star Wars* and *Outer Rim* are trademarks of their respective
owners, and all game content remains the property of its owners. If you hold rights to any material here
and want it taken down, open an issue and it will be removed.
