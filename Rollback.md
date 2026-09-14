# Rollback

## The way back out

- **Version Control:** All changes must be atomic commits.
- **Reverting:** If core logic breaks, revert to the last known good commit of `code/main.py`.
- **Data integrity:** Since `dataset/` is read-only, there is no need to rollback data. Simply delete `output.csv` and rerun the previous commit's `main.py`.
