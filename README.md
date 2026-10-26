# Debug Toolpack (DTP) — a Game Master toolkit for Stellaris

**This mod was made entirely with AI.** Every script, interface element, texture and translation was written by an AI assistant, guided and tested in-game by the author.

DTP was built to make life easier for **game masters** running multiplayer Stellaris sessions: rule enforcement, announcements, fixing things after a desync or a mistake, and quick changes, all from one in-game window, without the console.

- Game version: **Stellaris 4.5.x**
- Languages: **English, Russian**
- Current version: see `dtp_toolpack/descriptor.mod`

## Installation

1. Download this repository (Code → Download ZIP) and unpack it.
2. Copy the `dtp_toolpack` folder **and** the `dtp_toolpack.mod` file into
   `Documents/Paradox Interactive/Stellaris/mod/`.
3. Enable **Debug Toolpack (DTP)** in the Paradox launcher.

When updating, delete the old `dtp_toolpack` folder first, so no stale files remain.

**UI Overhaul Dynamic users:** also copy `dtp_toolpack_uiod` and `dtp_toolpack_uiod.mod`, and enable the patch *together with* the base mod, loaded after UIOD and DTP. Update the patch together with the base mod — without the current patch the editor does not appear under UIOD.

## Empire & Species Editor (11.2)

A separate window that works like the game's empire designer, but for a game already in progress. Open it with **Open the empire & species editor** in the State, Government or Species section. It edits empire A.

| Tab | What it does |
|---|---|
| Ethics & authority | regular and fanatic ethics, gestalt consciousness, every authority (switching to a hive mind sets the ethic and the hive-mind trait and removes incompatible civics) |
| Civics | every civic in the game: regular, megacorp, hive mind, machine, special |
| Traditions / Ascension perks / Policies | whole tradition trees, perks, an option for every policy |
| Species traits | every species trait: organic, robotic, ascension, habitability |
| Species rights | citizenship, living standard, military service, slavery, purge — for **any species** of the empire |
| Species portrait | the species class and every portrait of that class |
| Look & name | ship set, city style, random flag, empire name (32 presets) |
| Modifiers | 36 Toolpack modifiers and 24 game modifiers, with a strength/duration calculator (strength 1 = 1%, minus = penalty) |

- The game's own rules are checked: ethic points, opposite ethics and the `potential`/`possible` requirements of civics, authorities, traits, perks, traditions and policies are read from the game files (`tools/eddata.py`).
- Anything the game normally forbids gets a red **!** and can only be set in **force mode**. A green frame means the empire already has it.
- Icons are the game's own textures.
- The editor lives in the game's bottom bar window (`main_bottom.gui`; with UIOD — `Ω_uiod_main_bottom.gui` in the UIOD patch), so `main.gui` stays under the size the game reads.

## Getting HOST status

- **New game:** the first player empire (the host, player 0) automatically becomes the HOST.
- **Single player:** *Access* section → *Become HOST*.
- **Multiplayer:** *Request status (vote)* — every player gets a For/Against window.
- The HOST can transfer the status (the other player must accept), resign, and grant other players individual rights.
- Players without any rights do not see the DTP icon or panels — even before a HOST exists. In single player the panel is always visible.

## Game Master role

When an empire becomes HOST, it is offered the **Game Master role** (a window explains it; you can decline).

- The empire becomes a special "Game Master" country type (like a Fallen Empire) with a closed "Game Master" ethic.
- Sees the whole galaxy, every fleet and empire; contact with everyone. Intel, encryption and decryption 1000.
- Research and resources ×1000, storage +1,000,000, stability +50, no pop growth.
- Not accepted into the Galactic Community and does not trigger its formation, but can see its window.
- Nobody can declare war on the GM or close borders to it; the GM itself can do anything. No megacorp/syndicate branch offices on GM planets.
- You cannot play as a normal empire with this role. Drop it any time: *Access* → *Resign Game Master role*.

## Sections

| Section | What it does |
|---|---|
| Home | current target, quick actions, number input |
| Game Master | monsters, leaders, map tools, situations, crises (incl. Cetana and the Great Khan), announcements, balance packages, all technologies, player summary, session timer, Galactic Senate, Game Rules |
| Empire | pick empire A (changed) and recipient B (receives) |
| Systems | marking systems (see below) |
| Resources / Modifiers | stockpiles, monthly income, bonuses and penalties |
| Planet / Buildings | class, size, deposits, districts, buildings, transfer |
| Fleet | repair, teleport, transfer, delete, **Fleet Builder** (type, count 1–100, spawn point); "+ N ships" button in the game's fleet window |
| State / Government / Species | technologies, edicts, cooldowns, force mode and the **Empire & Species Editor** |
| Diplomacy | relations, trust, borders, truces, vassals, war, **White Peace A ↔ B** |
| Access | HOST status, player rights, Game Master role |
| Log | every action by every player, built-in self-tests |

## Systems: marks

- **Red markers** — every marked system gets a red "● MARKED" label on the galaxy map (visible to all players; can be switched off). Removing the mark removes the label.
- **Marker Ship** — a cloaked HOST ship (cloaking 1000) with extreme speed and an instant jump drive. Right-click any system on the galaxy map: every system it enters is marked. *REMOVES* mode clears marks the same way.
- **Navigator**, the DTP strips in planet / star / starbase / fleet windows (Alt+M), and bulk actions on all marked systems (claims, outposts, transfer, make ownerless, expand, clear).
- The strips also have **Select** (shows "✔ Selected" once chosen), **Edit this empire** (makes the owner empire A) and **Give to this empire** (makes the owner recipient B).

## Game Rules (war ban)

- **Hard mode** — like the "Defensive Wars" policy: a banned empire cannot declare war at all (button greyed out, "GM War Ban" modifier).
- **Soft mode** — war is allowed but is a violation; the GM punishes or forgives.
- Galaxy-wide, personal or protective bans, with a term in years or indefinite, optionally covering AI empires.

## Interface

- Every section has a banner, button groups are framed, and most buttons have icons. Wherever the game has an icon (ethics, civics, authorities, traits, resources, game modifiers) its own texture is used (`interface/dtp_gameicons.gfx`); the rest are drawn by `tools/icons_dtp.py`.
- Text on icon buttons is shifted right with leading spaces so it never covers the icon (checked for both Russian and English).

## Building from source

The mod is generated by `dtp_toolpack/tools/gen3.py` (Python 3 + Pillow). The generator reads files from your own Stellaris installation (`interface`, `common`, `gfx/map`), so they are not included here:

```
python3 tools/gen3.py <out_dir> <stellaris>/interface <stellaris>/common <stellaris>/gfx/map
python3 tools/validate2.py <out_dir> <script-docs-dir> <stellaris>/interface
```

English texts come from `tools/i18n/en_map.json` (the editor's texts are written in both languages in `tools/editor3.py`).
The editor is built by `tools/editor3.py` (run from `gen3.py`) from the game data read by `tools/eddata.py`. Button keys are shortened to hashes when the files are written, so the GUI files stay small.

## Reporting bugs

Please attach `game.log` and `error.log` from `Documents/Paradox Interactive/Stellaris/logs`.

## License

[MIT](LICENSE) — you are free to use, change and redistribute this mod. Pull requests and forks are welcome.

---

Stellaris is a trademark of Paradox Interactive. This is an unofficial fan mod. Some files are modified copies of game files (as usual for Stellaris mods) and require the game to be useful.
