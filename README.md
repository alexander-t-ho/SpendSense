# SpendSense

From Plaid to Personalized Learning

SpendSense is an explainable, consent-aware financial education platform that transforms Plaid transaction data into personalized insights and learning recommendations.

## Project Overview

SpendSense detects behavioral patterns from transaction data, assigns user personas, and delivers personalized financial education with clear guardrails around eligibility and tone.

## Technology Stack

- **Frontend**: React (TypeScript) with Tailwind CSS
- **Backend**: Python 3.11+ with FastAPI
- **Storage**: 
  - SQLite for relational data
  - Parquet for analytics
  - JSON for configs and logs
- **AWS**: Lambda functions for serverless compute

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Setup

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Generate synthetic data:
   ```bash
   python -m ingest.__main__ --num-users 100
   ```
4. Install frontend dependencies:
   ```bash
   cd ui && npm install
   ```
5. Run the backend:
   ```bash
   uvicorn api.main:app --reload
   ```
6. Run the frontend (in another terminal):
   ```bash
   cd ui && npm run dev
   ```
7. Open http://localhost:3000 in your browser

## Project Structure

```
SpendSense/
├── .cursorrules/              # Cursor agent rules
├── ingest/                    # Data ingestion
├── features/                  # Signal detection
├── personas/                  # Persona assignment
├── recommend/                 # Recommendation engine
├── guardrails/                # Compliance & guardrails
├── api/                       # FastAPI backend
├── ui/                        # React frontend
├── eval/                      # Evaluation harness
├── tests/                     # Test suite
├── data/                      # Data storage
└── docs/                      # Documentation
```

## Dashboard

The dashboard provides:
- Overview statistics (users, accounts, transactions, liabilities)
- User listing with account counts
- Detailed user profiles with:
  - Account information (checking, savings, credit cards, loans)
  - 30-day behavioral features
  - 180-day behavioral features

## Development

See [docs/decisions.md](docs/decisions.md) for architectural decisions and [docs/personas.md](docs/personas.md) for persona definitions.

## License

This project is for educational purposes. See LICENSE file for details.

## Disclaimer

**This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.**
