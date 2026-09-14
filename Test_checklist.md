# Test Checklist

## Proof, not claims

- [ ] `output.csv` generated successfully in the root directory.
- [ ] `output.csv` has exactly 251 rows (1 header + 250 requests).
- [ ] `output.csv` contains exactly the 8 required columns in the correct order.
- [ ] `0 <= amount_safe_to_pay <= requested_amount` for all rows.
- [ ] Blank amounts in `financial_events.csv` are properly resolved using `images.csv`.
- [ ] `affordable_now` correctly sets `earliest_date_for_full_payment` to `request_date`.
- [ ] `partial_payment` correctly limits to 2 payments adding up to `requested_amount`.
- [ ] Installment plans perfectly match a supplied `payment_option_id`.
- [ ] Evaluated against `dataset/sample_requests.csv` to ensure decision logic alignment.
