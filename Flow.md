# Flow

## How execution travels

1. **Initialization (`main.py`):**
   - Load all CSV files from `dataset/` using the standard `csv` module.
   - Initialize `FinancialForecaster` with the global context (events, rates).
2. **Data Pre-processing (V3 GenAI Integration):**
   - **Multi-modal OCR:** Locate events with missing amounts, lookup the corresponding image in `images.csv`, and use Google GenAI SDK to extract the amount (`ImageOCRResult`).
   - **Intent Interpretation:** Use Google GenAI SDK to parse user intent from `messages.csv` regarding explicit event updates (cancellations, new dates, new amounts via `EventUpdate`).
   - Apply these AI-driven corrections to the in-memory events table before math operations.
3. **Request Processing Loop:**
   - Iterate over each row in `requests.csv`.
   - **Context Gathering:** Fetch user profile to define `home_currency`, `current_available_balance`, and `minimum_balance_to_keep`.
   - **90-Day Deterministic Forecast:** 
     - The `FinancialForecaster` scans `financial_events.csv` to isolate the user's historical and confirmed future events.
     - Calculates average intervals for recurring `settled` events and projects them day-by-day.
     - Layers in scheduled/pending future payments (taking care not to double count against projected recurrences).
     - Converts all cash flows to the user's `home_currency` using `exchange_rates.csv`.
     - Finds the minimum projected balance across the entire 90-day window and calculates `base_safe_amount`.
   - **GenAI Decision Engine:** 
     - Combine the request details, user profile constraints (flexible expenses, preferred payment methods), available payment options, and the deterministic 90-day safe amount.
     - Pass the context to the Google GenAI model using the strict `FinalRecommendation` Pydantic response schema to enforce the problem's exact required output layout.
4. **Output Generation:**
   - Format decisions into the exact required output schema.
   - Write to `output.csv` in the repository root.

