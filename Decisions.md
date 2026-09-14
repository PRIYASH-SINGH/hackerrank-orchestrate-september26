# Decisions

## Why, not just what

- **Data Handling:** Using Python's built-in `csv` module for data ingestion, moving away from `pandas` to keep the evaluation lightweight and strictly typed when iterating row-by-row.
- **Core Logic Iteration:** We start by reading all datasets into memory to provide global context to the agent. A request-by-request loop isolates the evaluation for each request to avoid state bleed.
- **Modularity:** Separated data ingestion from decision logic, introducing `FinancialForecaster` to neatly encapsulate the projection of 90-day cash flows (recurring events, confirmed future events, exchange rates).
- **Exchange Rates:** Lookups match on the `YYYY-MM` prefix of `rate_date`, now using a Breadth-First Search (BFS) graph traversal to dynamically compute transitive exchange rates (e.g., USD -> EUR -> ZAR) when direct conversions are not explicitly present.
- **Recurring Events Definition:** For V2, events are treated as recurring if they have multiple `settled` instances. To prevent projecting arbitrary expenses, we strengthened the heuristic by verifying the interval variance is tight (max minus min interval difference <= 10 days over at least 3 occurrences) or that the event fundamentally represents a `subscription` or `debt_payment`.
- **Pending Cash Flows:** Future event handling now projects `pending` credits in addition to debits and scheduled transactions, preventing overly pessimistic forecasting when expected income is verified as pending.
- **Hybrid AI Engine (V3):** We separated the complex 90-day balance forecasting logic (which LLMs struggle to do deterministically without error) from the reasoning logic (which deterministic scripts struggle to do effectively, given subjective multi-variable personalization elements).
  - *Data Pre-processing:* Google GenAI SDK handles multi-modal OCR (extracting missing values from `images.csv`) and message intent parsing (`messages.csv`) before the forecast model runs. Both use strict Pydantic parsing (`ImageOCRResult`, `EventUpdate`).
  - *Final Decision:* The final personalized determination combines the deterministic 90-day `min_projected_balance` with the user's `financial_priorities` via GenAI, ensuring the final output dynamically generates and conforms exactly to the required output schema `FinalRecommendation`.
  - *Strict API Verification:* Removed graceful fallback dummy responses for GenAI calls. If the `GEMINI_API_KEY` is absent or invalid, the pipeline throws a hard error in compliance with the instruction to not hallucinate API responses.
  - *SDK Upgrade:* Upgraded from the deprecated `google.generativeai` to the new `google-genai` official SDK.
  - *Unlinked Message Processing:* Added matching for messages without a `related_event_id` utilizing the Pydantic field `target_event_keyword` to extract intent and find target events by description.
