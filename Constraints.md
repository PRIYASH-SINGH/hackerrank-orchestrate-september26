# Constraints

## What's off-limits

- **No external API calls** for live market data, banking access, or exchange rates. Must strictly use `dataset/exchange_rates.csv`.
- **No modification of `dataset/` files.** Treat all inputs as read-only.
- **Deterministic output required.** Avoid random non-seeded logic.
- **No hardcoded labels.** Do not try to reverse engineer `sample_requests.csv`.
- **Do not treat blank amounts as zero.** Must look up images in `images.csv` for amounts.
- **Output strictly 8 columns.** No extra columns in `output.csv`.
