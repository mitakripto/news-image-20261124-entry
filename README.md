# One Page of World News — Tuesday 24 November 2026

My entry for the make.fun bounty
[news-image-20261124](https://make.fun/bounty/news-image-20261124):
the whole of 24 November 2026's world news, summed up in a single image.

The page is a broadsheet drawn in a George Orwell 1984 poster register
crossed with Bioshock art deco — deep-sea teal and gold, propaganda red,
numbered stories, heavy rules, one small watching eye. It carries 60
stories from 7 regions, each one reported on 24 November 2026 — three
illustrated leads, ten illustrated cards, and 47 numbered briefs.
Leading the page: a US jury finding Huawei guilty of trade secrets and
bank fraud, Iran's claim that four tankers hit mines in the Strait of
Hormuz, and Ukraine acknowledging strikes on Russian ships in the Gulf
of Finland and off Libya.

Every story is colour-coded by continent. A bar under the masthead gives
each region's count, every story's number badge wears its region's
colour, and the pins on the dotted world map match. Every drawn story
carries a status tag — CONFIRMED, REPORTED or CLAIM, with a legend —
a source line, and its own small illustration with the story's number
or verdict set large; the Huawei lead is drawn as scales of justice
with the 10-of-12 verdict. A THE DAY IN UTC timeline strip runs under
the stats. A DATE CHECK box names the near-misses deliberately left
out — the ICJ Myanmar ruling (Thursday 19 Nov), the 'El Chapo Isidro'
capture (Friday 20 Nov), the COP31 collapse (Sunday 22 Nov), the
Sparta II / Benghazi strike (Sunday 22 Nov), the Shenzhou-24 launch
(Wednesday 25 Nov) and Monday's Huang reinstatement — and the page
states Tuesday's news only: the Asian market follow-through (not
Monday's Nasdaq +6.51%), the Cikande toll as "26 body bags recovered",
and the Shenzhou-24 crew unveiling, not its launch.

How it is built: `draw.py` renders the 1024×1024 page with Pillow. The
render is deterministic — fixed fonts, a fixed layout, no randomness, no
network — and writes `entry.png`. `main.py` copies that file to the
grader's output, so both runs hand over identical bytes.
