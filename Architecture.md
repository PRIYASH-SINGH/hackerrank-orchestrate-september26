# Architecture

## The system map

- **`code/main.py`**: The entry point. Orchestrates data loading, invokes the decision engine, and writes the output.
- **Data Layer (`dataset/`)**: Read-only structured data (profiles, events, options, rates, requests).
- **Core Engine (to be implemented)**:
  - `DataLoader`: Wraps `pandas` reads.
  - `ContextBuilder`: Joins user profiles with their events, messages, and images.
  - `FinancialForecaster`: Runs the 90-day safety check and calculates available safe amount.
  - `DecisionMaker`: Applies the contest rules to choose affordability status and payment plan.
- **Output Layer**: Generates `output.csv` with exactly 8 required columns.
