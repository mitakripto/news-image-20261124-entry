# The World in One Day — Tuesday 24 November 2026

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/mitakripto/news-image-20261124-entry/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/mitakripto/news-image-20261124-entry/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

My entry for the make.fun bounty [Sum up 24 November's world news in one image](https://make.fun/bounty/news-image-20261124) — join with my referral link https://make.fun/r/xavpy24p.

A single 1024×1024 front page summing up Tuesday 24 November 2026 in
60 stories across 7 regions, drawn as a cream-paper broadsheet in an
Orwell-1984 × Bioshock art-deco register: deep teal and gold, propaganda
red, serif display type.

## What's on the page

- **3 hero stories** — the US jury finding Huawei guilty on 10 counts,
  Iran's claim of four tankers hit by mines in the Strait of Hormuz, and
  Ukraine acknowledging strikes on Russian ships off Finland and Libya.
- **10 cards** — Asian markets and Bitcoin, the CAS ruling restoring
  Senegal as Africa Cup champions, Champions League Matchday 5, the Houthi
  drone on Riyadh's PIF tower, the Cikande factory fire toll, 25 hostages
  in Cartagena, Saudi strikes in Yemen, the Russian drone over Poland,
  the Shenzhou-24 crew unveiling, and the US blacklisting of Megaspeed.
- **47 one-line briefs** (stories 14–60), numbered to match the cards and
  the map pins, each colour-coded by continent.
- **A six-number stats strip** (25 hostages in Cartagena, 26 body bags at
  Cikande, 4 tankers in Hormuz, 11 wounded in Riyadh, 175 migrants missing
  off Dakar, Bitcoin at $60,406), a **continent bar with story counts**,
  a **UTC timeline** running 00:00 to 20:41, and a **dotted world map**
  with numbered pins for stories 1–13.
- **A red DATE CHECK box** listing the near-miss events deliberately left
  out, and a **tag legend**: CONFIRMED means verified by two or more
  outlets, REPORTED means carried by the day's wires, CLAIM means one
  side's account, not independently confirmed.

## Date discipline

Every story happened, or was first reported, on Tuesday 24 November 2026.
The traps are handled in the open on the page: the Nasdaq +6.51% surge was
Monday's close, not Tuesday's move; the Shenzhou-24 item is the Tuesday
crew unveiling, not Wednesday's launch; the Cikande figure is "26 body
bags recovered"; the Cartagena hostage count is 25, the president's figure;
and the Hormuz hero is tagged CLAIM because the mine claims are
unconfirmed.

## How it was built

- `python3 draw.py` renders `entry.png` (1024×1024, under 1 MiB).
- `python3 main.py [output-dir]` copies `entry.png` to the grader output.
- The drawing uses Pillow only — no network, no randomness, no external
  assets — so two runs produce byte-identical output.

## Sources

dailysummaryof.com/world/2026-11-24, horizonapp.link, Just Security Early
Edition, UEFA, CAS, Reuters, Xinhua, CoinDesk. Press time 01:30 UTC,
Wednesday 25 November 2026.
