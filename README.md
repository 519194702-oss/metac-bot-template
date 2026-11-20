# xiaoqi-forecaster

A forecasting bot for the [Metaculus FutureEval](https://www.metaculus.com/futureeval/) Bot Tournament (Fall 2026 season + bi-weekly MiniBench). Personal hobbyist bot, open source (MIT).

Built from the official [Metaculus template bot](https://github.com/Metaculus/metac-bot-template). Changes from the template:

- **Pinned models via env vars** — `DEFAULT_MODEL` (default `openrouter/openai/gpt-5.2:online`, a web-search-enabled model), `PARSER_MODEL` (default `openrouter/openai/gpt-4o-mini`, cheap reformatting only).
- **Research** — AskNews when `ASKNEWS_CLIENT_ID`/`ASKNEWS_SECRET` are set, otherwise a web-search-enabled model via SmartSearcher.
- **`--dry-run` / `DRY_RUN=1`** — run the full pipeline without publishing anything to Metaculus.
- Forecasting prompts are unchanged from the official template (Metaculus's own battle-tested prompts).

## Current status (verified 2026-11-19)

- **Fall 2026 Bot Tournament**: Sep 28, 2026 – Jan 6, 2027, **$50,000 prize pool**, ~300–400 questions. New bots can join mid-season (you start at 0, mid-leaderboard).
- **MiniBench** (current round): Nov 16 – Dec 4, 2026, **$1,000 per round**, ~60 questions. New rounds start Monday every other week. Most questions launch in the first few days of a round — join early.
- **Market Pulse**: ~$7,000/quarter, bots eligible (needs continuous forecast updates; not enabled here).
- Scoring is a log-based spot peer score (only your last forecast before a question closes counts).
- Questions stay open ~3 hours each, in batches of up to ~10 — the bot polls every 20 minutes via GitHub Actions.

## Rules that matter (from the [official resources page](https://www.metaculus.com/notebooks/38928/ai-benchmark-resources/) and [tournament rules](https://www.metaculus.com/notebooks/28751/q1-ai-forecasting-benchmark-rules/))

- **Prize eligibility**: hobbyist/personal bots ARE eligible. Commercial bots (built for a for-profit entity with 3+ people) are only eligible if fully open source. This bot is personal + open source, so it qualifies on both counts.
- **No human in the loop**: the bot must forecast via API on its own. You may not preview its forecasts on open questions and then tweak it, or re-run it because you dislike a forecast. Test only on closed questions or the bot-testing-area.
- **One forecast per question** in bot-only tournaments; only the last forecast before close counts.
- **Comments required**: the bot must leave a (private) comment with reasoning on every question it forecasts. Comments are made public after questions close.
- **If you win**: you must provide your code or a description of how the bot works, and agree to an inspection (demo it on new questions). Prize recipients must verify identity, nationality, and residency; payouts are not made where prohibited by US law. Taxes are the recipient's responsibility.
- **Entry form**: all participants must fill out the first section of the [participation form](https://forms.gle/aQdYMq9Pisrf1v7d8) (3 required questions: demographics + motivation). The same form is the application for free LLM credits.
- **Season-end survey**: commercial bots are explicitly required to complete it; whether it gates hobbyist prizes is not spelled out in the rules I read — fill it in when it arrives, to be safe.
- **Prize split**: the exact dollar split by rank is not published on the rules pages I read — allocation follows the Tournament Scoring Rules (weighted Peer Score) and depends on rank/performance. Unclaimed prizes may be forfeited after 30 days.
- **Eligibility**: 18+, open worldwide except Cuba, Iran, Syria, North Korea, Russia, and Ukraine (Crimea/DNR/LNR). China is not excluded.

## Free LLM / search credits

- **Donated LLM credits** (OpenAI/Anthropic/Google via OpenRouter): apply in the participation form. Selective — not everyone gets them. Fall 2026 uses incremental funding: ~$100 initially, more added automatically for above-average MiniBench performance (first MiniBench only, once per bot maker). Open-source bots can earn 2.5x more from performance grants.
- **AskNews search**: free for every registered bot maker — 1k calls/month, 4k total per tournament, 5M tokens. Sign up with the same email as your Metaculus account, then ask for the free tier (see `USER_STEPS.md`).
- Typical bot cost is $0.10–$3 per question; a season can run $50–$1,000+ depending on models. Budget the donated credits and check usage often.

## Quick start (GitHub Actions — no local setup needed)

1. **Fork** this repo on GitHub (or fork the upstream template and push this code to it).
2. **Add secrets** — Settings → Secrets and variables → Actions → New repository secret:
   - `METACULUS_TOKEN` — from Metaculus Settings → My Forecasting Bots → Create Bot.
   - `OPENROUTER_API_KEY` — the donated key from the participation form (or your own OpenRouter key).
   - Optional: `ASKNEWS_CLIENT_ID`, `ASKNEWS_SECRET`, `PERPLEXITY_API_KEY`, `EXA_API_KEY`.
3. **Enable Actions** — Actions tab → "I understand my workflows, go ahead and enable them".
4. **Smoke test** — Actions → Test Bot → Run workflow. It forecasts on the unscored bot-testing-area tournament. After ~3–5 min, switch to your bot account on Metaculus and check the forecasts landed.
5. **Fill out the participation form** before submitting live forecasts.
6. Done — the `Forecast on new AI tournament questions` workflow runs every 20 minutes on the Fall tournament + MiniBench. Pause it via Actions → … → Disable workflow.

## Run locally

```bash
uv sync
cp .env.template .env   # fill in METACULUS_TOKEN + OPENROUTER_API_KEY
uv run python main.py --mode test_questions --dry-run   # smoke test, publishes nothing
uv run python main.py --mode tournament                  # live: Fall 2026 + MiniBench
uv run python main.py --mode metaculus_cup               # practice vs humans (no prizes)
```

Run tests (offline, stubbed LLM, no account needed):

```bash
uv run python -m unittest discover -s tests -v
```

## How it works

For each open question: 1 research report (AskNews or web-search model) → 5 independent forecasts → aggregated prediction → published with a private reasoning comment. Handles binary, multiple-choice, numeric, date, and conditional questions. Skips questions already forecasted. One question at a time (`_max_concurrent_questions = 1`) to respect rate limits.

## Files

- `main.py` — the bot (only file you normally need to touch).
- `bot_helpers.py` — env validation, banners.
- `main_with_no_framework.py` — single-file reference implementation (upstream template, unmodified).
- `tests/test_bot_local.py` — offline unit tests.
- `.github/workflows/` — `run_bot_on_tournament.yaml` (every 20 min), `test_bot.yaml` (manual smoke test), `run_bot_on_metaculus_cup.yaml` (every 2 days), `review_bot.yaml` (weekly self-review, off by default).
- `../USER_STEPS.md` — exact steps for the human (registration, form drafts, secrets).

## Cost control

- Parser uses the cheap model; only the reasoning model is frontier-class.
- 5 predictions per question is the template default (ensemble improves peer score); lower `predictions_per_research_report` in `main.py` if credits run low.
- Check donated-credit balance via OpenRouter's API (`limit_remaining`) or by emailing ben@metaculus.com.
