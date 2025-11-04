# SpendSense: Product Requirements Document (PRD)

**Project**: From Plaid to Personalized Learning  
**Version**: 2.0  
**Date**: November 2024  
**Status**: Phase 1 & 2 Complete, Phase 3+ Pending

---

## Executive Summary

SpendSense is an explainable, consent-aware financial education platform that transforms Plaid transaction data into personalized insights and learning recommendations. The system detects behavioral patterns, assigns user personas, and delivers educational content with strict guardrails around eligibility, tone, and regulatory compliance.

**Core Principle**: Financial AI must be explainable and auditable. Every recommendation needs a clear rationale that cites specific data points.

---

## Project Overview

**Type**: Individual or small team project  
**Timeline**: No strict deadline (estimated 10-11 weeks for full implementation)  
**Goal**: Build a complete proof-of-concept system demonstrating:
- Behavioral pattern detection
- Persona-based personalization
- Consent-aware recommendations
- Operator oversight capabilities
- Full evaluation metrics

---

## Technology Stack

### Core Stack
- **Frontend**: React (TypeScript) with modern UI framework
- **Backend**: Python 3.11+ with FastAPI
- **Storage**:
  - SQLite for relational data (users, accounts, transactions, consent)
  - Parquet files for analytics (behavioral signals, features)
  - JSON for configs and logs
- **AWS**: Lambda functions for serverless compute

### Additional Tools
- Pandas/NumPy for data processing
- Polars for fast Parquet operations
- Pydantic for data validation
- SQLAlchemy for ORM
- pytest for testing
- React Query for data fetching
- Tailwind CSS for styling
- Vite for frontend build tool

---

## Core Requirements

### 1. Data Ingestion (Plaid-Style)

#### Requirements
- Generate synthetic data matching Plaid's structure
- 50-100 synthetic users (configurable, default 5 for testing)
- No real PII—use fake names, masked account numbers
- Diverse financial situations
- Ingest from CSV/JSON (no live Plaid connection required)

#### Data Structure

**Accounts:**
- `account_id` (12-digit numeric)
- `type/subtype` (checking, savings, credit card, money market, HSA)
- `balances`: available, current, limit
- `iso_currency_code`
- `holder_category` (exclude business accounts)
- Loan-specific fields: `interest_rate`, `next_payment_due_date`
- Credit card fields: `amount_due`, `minimum_payment_due`

**Transactions:**
- `account_id`
- `date`
- `amount` (negative for expenses, positive for income/returns)
- `merchant_name` or `merchant_entity_id`
- `payment_channel` (in store, online, other)
- `personal_finance_category` (primary/detailed)
- `pending` status (resolves within 24-48 hours)
- Returns/partial returns supported
- Interest charges for credit cards

**Liabilities:**
- **Credit Cards:**
  - APRs (type/percentage)
  - `minimum_payment_amount`
  - `last_payment_amount` (supports minimum-payment-only detection)
  - `is_overdue`
  - `next_payment_due_date`
  - `last_statement_balance`
  - `amount_due`
  - `minimum_payment_due`
- **Mortgages/Student Loans:**
  - `interest_rate`
  - `next_payment_due_date`

#### Deliverables
- ✅ Synthetic data generator (`ingest/generator.py`)
- ✅ Data loader (`ingest/loader.py`)
- ✅ SQLite database schema (`ingest/schema.py`)
- ✅ CSV export including `transactions_final.csv` format
- ✅ Realistic transaction amounts based on `transactions_final.csv` analysis
- ✅ Credit limit and balance threshold enforcement
- ✅ Pending transactions (24-48 hours only)
- ✅ Returns/partial returns
- ✅ Interest charges and payment patterns

---

### 2. Behavioral Signal Detection

Compute signals per time window (30-day and 180-day):

#### Subscriptions
- Recurring merchants (≥3 in 90 days with monthly/weekly cadence)
- Monthly/weekly cadence identification
- Monthly recurring spend
- Subscription share of total spend
- Periodic transactions (every 30 days, monthly, or bi-monthly)
- Expenses only (negative amounts)

#### Savings
- Net inflow to savings-like accounts (savings, money market, cash management, HSA)
- Growth rate calculation
- Emergency fund coverage = savings balance / average monthly expenses

#### Credit
- Utilization calculation = balance / limit
- Utilization flags (≥30%, ≥50%, ≥80%)
- Minimum-payment-only detection
- Interest charge detection (INTEREST CHARGE transactions)
- Overdue status tracking (from `liability.is_overdue`)

#### Income Stability
- Payroll ACH detection
- Payment frequency analysis
- Cash-flow buffer calculation (months)

#### Deliverables
- ✅ Feature pipeline (`features/pipeline.py`)
- ✅ Subscription detection (`features/subscriptions.py`)
- ✅ Savings analysis (`features/savings.py`)
- ✅ Credit utilization (`features/credit.py`)
- ✅ Income stability (`features/income.py`)
- ✅ Time windows (30d, 180d) working
- ⏳ Parquet storage for analytics

---

### 3. Persona Assignment (Maximum 5)

Assign each user to a persona based on detected behaviors:

#### Persona 1: High Utilization
**Criteria:**
- Any card utilization ≥50% OR
- Interest charges > 0 OR
- Minimum-payment-only OR
- `is_overdue` = true

**Primary Focus:**
- Reduce utilization and interest
- Payment planning and autopay education

#### Persona 2: Variable Income Budgeter
**Criteria:**
- Median pay gap > 45 days AND
- Cash-flow buffer < 1 month

**Primary Focus:**
- Percent-based budgets
- Emergency fund basics
- Smoothing strategies

#### Persona 3: Subscription-Heavy
**Criteria:**
- Recurring merchants ≥3 AND
- (Monthly recurring spend ≥$50 in 30d OR subscription spend share ≥10%)

**Primary Focus:**
- Subscription audit
- Cancellation/negotiation tips
- Bill alerts

#### Persona 4: Savings Builder
**Criteria:**
- Savings growth rate ≥2% over window OR
- Net savings inflow ≥$200/month, AND
- All card utilizations < 30%

**Primary Focus:**
- Goal setting
- Automation
- APY optimization (HYSA/CD basics)

#### Persona 5: [Custom Persona]
**To be defined:**
- Clear criteria based on behavioral signals
- Rationale for why this persona matters
- Primary educational focus
- Prioritization logic if multiple personas match

#### Deliverables
- ⏳ Persona assignment logic (`personas/assigner.py`)
- ⏳ Prioritization system (if multiple personas match)
- ⏳ Decision traces (`personas/traces.py`)
- ⏳ Persona definitions (`personas/definitions.py`)

---

### 4. Personalization & Recommendations

Output per user per window:
- **3-5 education items** mapped to persona/signals
- **1-3 partner offers** with eligibility checks
- **Every item includes**: "because" rationale citing concrete data
- **Plain-language explanations** (no jargon)

#### Example Rationale Format
> "We noticed your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score and reduce interest charges of $87/month."

#### Education Content Examples
- Articles on debt paydown strategies
- Budget templates for variable income
- Subscription audit checklists
- Emergency fund calculators
- Credit utilization explainers

#### Partner Offer Examples
- Balance transfer credit cards (if credit utilization high)
- High-yield savings accounts (if building emergency fund)
- Budgeting apps (if variable income)
- Subscription management tools (if subscription-heavy)

#### Deliverables
- ⏳ Recommendation engine (`recommend/generator.py`)
- ⏳ Education content catalog (`recommend/content_catalog.py`)
- ⏳ Partner offers catalog (`recommend/offers_catalog.py`)
- ⏳ Rationale generation (`recommend/rationales.py`)
- ⏳ Content-to-persona mapping

---

### 5. Consent, Eligibility & Tone Guardrails

#### Consent
- ✅ Require explicit opt-in before processing data
- ✅ Allow users to revoke consent at any time
- ✅ Track consent status per user (`consents` table)
- ✅ No recommendations without consent

#### Eligibility
- ⏳ Don't recommend products user isn't eligible for
- ⏳ Check minimum income/credit requirements
- ⏳ Filter based on existing accounts
- ⏳ Avoid harmful suggestions (no payday loans, predatory products)

#### Tone
- ⏳ No shaming language
- ⏳ Empowering, educational tone
- ⏳ Avoid judgmental phrases like "you're overspending"
- ⏳ Use neutral, supportive language

#### Disclosure
Every recommendation must include:
> "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."

#### Deliverables
- ✅ Consent tracking (`ingest/schema.py`)
- ⏳ Consent management (`guardrails/consent.py`)
- ⏳ Eligibility checks (`guardrails/eligibility.py`)
- ⏳ Tone validation (`guardrails/tone.py`)
- ⏳ Disclosure system (`guardrails/disclosure.py`)

---

### 6. Operator View

Build a simple interface for human oversight:
- ⏳ View detected signals for any user (30d, 180d)
- ⏳ See short-term (30d) and long-term (180d) persona assignments
- ⏳ Review generated recommendations with rationales
- ⏳ Approve or override recommendations
- ⏳ Access decision trace (why this recommendation was made)
- ⏳ Flag recommendations for review

#### Deliverables
- ⏳ Operator dashboard (`ui/operator/`)
- ⏳ Recommendation approval workflow
- ⏳ Decision trace viewer
- ⏳ Signal summary view
- ⏳ User list with personas

---

### 7. Evaluation & Metrics

Build an evaluation system that measures:
- **Coverage**: % of users with assigned persona and ≥3 detected behaviors
- **Explainability**: % of recommendations with plain-language rationales
- **Relevance**: manual review or simple scoring of education-persona fit
- **Latency**: time to generate recommendations (should be fast on laptop)
- **Fairness**: basic demographic parity check if synthetic data includes demographics

#### Output
- JSON/CSV metrics file
- Brief summary report (1-2 pages)
- Per-user decision traces

#### Deliverables
- ⏳ Evaluation harness (`eval/harness.py`)
- ⏳ Metrics calculation (`eval/metrics.py`)
- ⏳ Report generation (`eval/reports.py`)

---

## Implementation Phases

### ✅ Phase 1: Foundation & Data Generation (Week 1-2) - COMPLETE

**Goal**: Establish project structure and generate synthetic Plaid-style data

**Deliverables:**
- ✅ Project scaffolding with modular structure
- ✅ Synthetic data generator (supports 50-100 users, default 5)
- ✅ Data validation and schema enforcement
- ✅ SQLite database schema design
- ✅ Initial documentation
- ✅ CSV export including `transactions_final.csv` format
- ✅ Realistic transaction amounts based on `transactions_final.csv`
- ✅ Credit limit and balance threshold enforcement
- ✅ Pending transactions (24-48 hours only)
- ✅ Returns/partial returns
- ✅ Interest charges and payment patterns
- ✅ Frontend dashboard with account cards and transaction tables

**Tasks Completed:**
- ✅ Set up project structure (ingest/, features/, personas/, recommend/, guardrails/, ui/, eval/, docs/)
- ✅ Created SQLite schema for accounts, transactions, liabilities
- ✅ Built synthetic data generator with:
  - Account types (checking, savings, credit, money market, HSA)
  - Transaction generation with realistic patterns
  - Liability data (credit cards with APRs, mortgages, student loans)
  - Diverse financial situations (6 profiles)
- ✅ Implemented data ingestion pipeline (CSV/JSON → SQLite)
- ✅ Data validation and quality checks
- ✅ 12-digit account IDs
- ✅ Matching names/emails
- ✅ Multiple credit cards per user (1-3)
- ✅ Loan-specific fields in Account model

**Key Files:**
- `ingest/generator.py` - Synthetic data generator
- `ingest/schema.py` - Database models
- `ingest/loader.py` - Data ingestion pipeline
- `data/synthetic/transactions_final.csv` - Rich CSV output for Phase 2

**Success Criteria:**
- ✅ 50-100 users supported (configurable, default 5)
- ✅ All Plaid fields represented
- ✅ Data passes validation checks
- ✅ No real PII present

---

### ✅ Phase 2: Behavioral Signal Detection (Week 2-3) - COMPLETE

**Goal**: Compute behavioral signals from transaction data

**Deliverables:**
- ✅ Feature engineering pipeline
- ✅ Signal detection for subscriptions, savings, credit, income
- ✅ Time-window aggregation (30-day, 180-day)
- ⏳ Parquet storage for analytics

**Tasks Completed:**
- ✅ Subscriptions Detection:
  - Recurring merchant detection (≥3 occurrences in 90 days)
  - Monthly/weekly cadence identification
  - Subscription spend calculation
  - Share of total spend metric
- ✅ Savings Analysis:
  - Net inflow to savings accounts
  - Growth rate calculation
  - Emergency fund coverage (savings / avg monthly expenses)
- ✅ Credit Analysis:
  - Utilization calculation (balance / limit)
  - Utilization flags (≥30%, ≥50%, ≥80%)
  - Minimum-payment-only detection
  - Interest charge detection
  - Overdue status tracking
- ✅ Income Stability:
  - Payroll ACH detection
  - Payment frequency analysis
  - Cash-flow buffer calculation (months)

**Key Files:**
- `features/subscriptions.py` - Subscription detection
- `features/savings.py` - Savings analysis
- `features/credit.py` - Credit utilization
- `features/income.py` - Income stability
- `features/pipeline.py` - Orchestrates all feature computation
- `data/features/` - Parquet files (pending)

**Success Criteria:**
- ✅ All signals computed correctly
- ✅ Time windows (30d, 180d) working
- ⏳ Parquet files generated and queryable
- ✅ Performance: <2 seconds per user

---

### ✅ Phase 3: Persona Assignment System (Week 3-4) - COMPLETE ✅

**Completed Features:**
- ✅ 5 persona definitions with risk levels
- ✅ Persona assignment logic with prioritization
- ✅ Risk-based persona selection (higher risk selected when multiple match)
- ✅ Decision trace logging
- ✅ API endpoints for persona retrieval
- ✅ Admin dashboard display of persona and risk levels
- ✅ User detail page with persona/risk analysis
- ✅ Income calculation from payroll transactions (180-day, scaled to yearly)
- ✅ Loan payments as negative transactions (mortgages, student loans)
- ✅ Even persona distribution (10 users per persona for 50 users)
- ✅ Income distribution: Median ~$63K, Minimum ~$28K

**Goal**: Assign users to personas based on behavioral signals

**Deliverables:**
- ✅ 5 persona definitions with clear criteria
- ✅ Persona assignment logic
- ✅ Prioritization rules for multi-persona matches
- ✅ Decision trace logging
- ✅ API endpoints for persona assignment

**Tasks Completed:**
- ✅ Persona 1: High Utilization
  - Criteria: utilization ≥50% OR interest > 0 OR min-payment-only OR overdue
  - Focus: Reduce utilization, payment planning
  - Priority: CRITICAL (5)
- ✅ Persona 2: Variable Income Budgeter
  - Criteria: median pay gap > 45 days AND cash-flow buffer < 1 month
  - Focus: Percent-based budgets, emergency fund
  - Priority: HIGH (4)
- ✅ Persona 3: Subscription-Heavy
  - Criteria: ≥3 recurring merchants AND (≥$50/month OR ≥10% of spend)
  - Focus: Subscription audit, cancellation tips
  - Priority: MEDIUM (3)
- ✅ Persona 4: Savings Builder
  - Criteria: savings growth ≥2% OR net inflow ≥$200/month AND all utilizations < 30%
  - Focus: Goal setting, automation, HYSA
  - Priority: LOW (2)
- ✅ Persona 5: Balanced/Stable
  - Criteria: Low utilization, stable income, moderate subscriptions, steady savings
  - Focus: Maintenance, optimization, long-term planning
  - Priority: MINIMAL (1)
- ✅ Implement prioritization logic for conflicts (highest priority wins)
- ✅ Create decision trace logging (JSON files + JSONL log)
- ✅ API endpoints: `GET /api/personas/{user_id}` and `GET /api/personas`

**Key Files:**
- ✅ `personas/definitions.py` - Persona criteria with matching logic
- ✅ `personas/assigner.py` - Assignment logic with prioritization
- ✅ `personas/traces.py` - Decision logging system
- ✅ `api/main.py` - Persona assignment endpoints

**Success Criteria:**
- ✅ All 5 personas defined with clear criteria
- ✅ 100% of users assigned to at least one persona (defaults to balanced_stable)
- ✅ Prioritization logic handles conflicts (highest priority persona selected as primary)
- ✅ Decision traces stored for audit (JSON files in `data/persona_traces/`)

---

### ✅ Phase 4: Recommendation Engine (Week 4-5) - COMPLETE ✅

**Goal**: Generate personalized recommendations with rationales

**Completed Features:**
- ✅ Education content catalog (18 items)
- ✅ Partner offer catalog (8 items)
- ✅ Recommendation generation logic
- ✅ Plain-language rationale generation
- ✅ Content-to-persona mapping
- ✅ API endpoint: `GET /api/recommendations/{user_id}`
- ✅ Frontend component: RecommendationsSection
- ✅ Integration with user detail page

**Deliverables:**
- ✅ Education content catalog (18 items mapped to personas and signals)
- ✅ Partner offer catalog (8 items with eligibility criteria)
- ✅ Recommendation generation logic (3-5 education items, 1-3 partner offers)
- ✅ Plain-language rationale generation (cites specific data points)
- ✅ Content-to-persona mapping (all 5 personas covered)

**Tasks Completed:**
- ✅ Education Content:
  - Created content catalog with 18 items (articles, templates, calculators)
  - Mapped content to personas and signals
  - Content stored in Python dataclasses
- ✅ Partner Offers:
  - Created offer catalog with 8 items and eligibility criteria
  - Mapped offers to personas
  - Stored eligibility requirements (credit score, income, utilization, etc.)
- ✅ Recommendation Logic:
  - Generates 3-5 education items per user
  - Generates 1-3 partner offers per user
  - Creates plain-language rationales citing data
  - Format: "We noticed [specific data point] because [reason]"
- ✅ Rationale Generation:
  - Template-based rationale builder
  - Dynamic data insertion from user features
  - Plain-language explanations with specific data citations

**Key Files:**
- ✅ `recommend/content_catalog.py` - Education content (18 items)
- ✅ `recommend/offers_catalog.py` - Partner offers (8 items)
- ✅ `recommend/generator.py` - Recommendation logic
- ✅ `recommend/rationales.py` - Rationale builder
- ✅ `api/main.py` - Recommendations endpoint
- ✅ `ui/src/components/RecommendationsSection.tsx` - Frontend component

**Success Criteria:**
- ✅ 100% of recommendations have rationales
- ✅ Rationales cite specific data points (utilization %, subscription counts, income gaps, etc.)
- ✅ Plain language (no jargon)
- ✅ Content relevant to assigned persona

---

### ⏳ Phase 5: Guardrails & Compliance (Week 5-6) - PENDING

**Goal**: Implement consent, eligibility, and tone guardrails

**Deliverables:**
- ✅ Consent management system (schema)
- ⏳ Eligibility checking
- ⏳ Tone validation
- ⏳ Regulatory disclosures

**Tasks:**
- ✅ Consent Management:
  - ✅ Track consent status per user
  - ⏳ Opt-in/opt-out functionality
  - ⏳ Consent revocation
  - ⏳ No recommendations without consent
- ⏳ Eligibility Checks:
  - Income requirements validation
  - Credit score requirements
  - Existing account filtering
  - Harmful product filtering (no payday loans)
- ⏳ Tone Validation:
  - Language pattern detection
  - Shaming language detection
  - Empowering tone enforcement
  - Neutral, supportive language checks
- ⏳ Disclosures:
  - Standard disclaimer on all recommendations
  - "Not financial advice" messaging

**Key Files:**
- `guardrails/consent.py` - Consent tracking
- `guardrails/eligibility.py` - Eligibility checks
- `guardrails/tone.py` - Tone validation
- `guardrails/disclosure.py` - Disclaimers

**Success Criteria:**
- ✅ Consent tracked and enforced (schema ready)
- ⏳ No ineligible offers recommended
- ⏳ No shaming language detected
- ⏳ Disclaimers on all recommendations

---

### ⏳ Phase 6: API & Backend (Week 6-7) - PARTIALLY COMPLETE

**Goal**: Build FastAPI REST API with all endpoints, including Origin-like insights

**Deliverables:**
- ✅ Complete REST API (core endpoints)
- ✅ Endpoint documentation (OpenAPI/Swagger)
- ✅ Error handling
- ✅ Data validation
- ⏳ Insights API endpoints (Origin-like features)

**Tasks:**
- ✅ API Endpoints:
  - ✅ `GET /api/stats` - Overall statistics
  - ✅ `GET /api/users` - User listing
  - ✅ `GET /api/profile/{user_id}` - Get behavioral profile with transactions
  - ✅ `GET /api/correlation` - Correlation analysis
  - ✅ `GET /api/correlation/groups` - Group correlations
  - ✅ `GET /api/features/parquet` - Read features from Parquet
  - ⏳ `POST /users` - Create user
  - ⏳ `POST /consent` - Record consent
  - ⏳ `GET /recommendations/{user_id}` - Get recommendations
  - ⏳ `POST /feedback` - Record user feedback
  - ⏳ `GET /operator/review` - Operator approval queue
  - ⏳ `GET /health` - Health check
  - ⏳ `GET /signals/{user_id}` - Get computed signals
  - ⏳ `GET /personas/{user_id}` - Get persona assignment
  - ⏳ `PUT /recommendations/{recommendation_id}/approve` - Approve recommendation
- ⏳ Insights API Endpoints (Origin-like features):
  - ⏳ `GET /api/insights/{user_id}/weekly-recap?week_start=YYYY-MM-DD` - Weekly spending recap
  - ⏳ `GET /api/insights/{user_id}/spending-analysis?months=6` - 6-month spending analysis
  - ⏳ `GET /api/insights/{user_id}/suggested-budget` - AI-suggested monthly budget
  - ⏳ `GET /api/insights/{user_id}/budget-history?months=6` - Budget history for charts
  - ⏳ `GET /api/insights/{user_id}/budget-tracking?month=YYYY-MM` - Budget tracking status
  - ⏳ `GET /api/insights/{user_id}/net-worth?period=week|month` - Net worth calculation
  - ⏳ `GET /api/insights/{user_id}/net-worth-history?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Net worth trends
- ✅ Data Models:
  - ✅ Pydantic models for request/response
  - ✅ SQLAlchemy models for database
- ⏳ Insights Backend Modules:
  - ⏳ `insights/weekly_recap.py` - Weekly spending recaps
  - ⏳ `insights/spending_analysis.py` - 6-month analysis
  - ⏳ `insights/budget_calculator.py` - Budget suggestions
  - ⏳ `insights/budget_tracker.py` - Budget tracking
  - ⏳ `insights/net_worth_tracker.py` - Net worth calculations
- ✅ Error Handling:
  - Custom exception classes
  - Proper HTTP status codes
  - Error message formatting

**Key Files:**
- `api/main.py` - FastAPI app
- `api/routes/` - Route handlers (pending)
- `api/models/` - Pydantic models (pending)
- `api/middleware/` - Middleware (pending)
- `insights/` - Insight computation modules (new)

**Success Criteria:**
- ✅ Core endpoints implemented
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Error handling working
- ✅ Response time <5 seconds
- ⏳ Insights endpoints returning data in <2 seconds

---

### ⏳ Phase 7: Operator View (Week 7-8) - PENDING

**Goal**: Build oversight interface for human operators

**Deliverables:**
- ⏳ Operator dashboard
- ⏳ Signal review interface
- ⏳ Recommendation approval system
- ⏳ Decision trace viewer

**Tasks:**
- ⏳ Dashboard Components:
  - User list with personas
  - Signal summary view
  - Recommendation queue
  - Approval/override interface
- ⏳ Features:
  - View all detected signals (30d, 180d)
  - See persona assignments
  - Review recommendations with rationales
  - Approve or override recommendations
  - View decision traces
  - Flag for review
- ⏳ UI Implementation:
  - React components for operator view
  - Data tables and filters
  - Action buttons (approve/reject/override)

**Key Files:**
- `ui/operator/` - Operator view components
- `ui/components/` - Shared components
- `api/routes/operator.py` - Operator endpoints

**Success Criteria:**
- ⏳ All signals visible
- ⏳ Can approve/override recommendations
- ⏳ Decision traces accessible
- ⏳ Intuitive interface

---

### ⏳ Phase 8: Evaluation & Metrics (Week 8-9) - PENDING

**Goal**: Build evaluation harness and generate metrics

**Deliverables:**
- ⏳ Evaluation system
- ⏳ Metrics calculation
- ⏳ Report generation
- ⏳ Performance benchmarks

**Tasks:**
- ⏳ Metrics Calculation:
  - Coverage: % users with persona + ≥3 behaviors
  - Explainability: % recommendations with rationales
  - Relevance: Education-persona fit scoring
  - Latency: Time to generate recommendations
  - Fairness: Demographic parity checks
- ⏳ Evaluation Harness:
  - Automated metric calculation
  - Per-user decision traces
  - JSON/CSV output
  - Summary report generation
- ⏳ Testing:
  - Unit tests (≥10 tests)
  - Integration tests
  - Performance tests

**Key Files:**
- `eval/metrics.py` - Metric calculations
- `eval/harness.py` - Evaluation runner
- `eval/reports.py` - Report generation
- `tests/` - Test suite

**Success Criteria:**
- ⏳ 100% coverage target met
- ⏳ 100% explainability target met
- ⏳ Latency <5 seconds
- ⏳ ≥10 passing tests
- ⏳ Evaluation report generated

---

### ✅ Phase 9: Frontend & User Experience (Week 9-10) - PARTIALLY COMPLETE

**Goal**: Build user-facing interface with Origin-like insights and dashboard separation

**Deliverables:**
- ✅ User dashboard (admin view - sees all users)
- ⏳ User dashboard (end-user view - sees only own account)
- ⏳ Operator dashboard (admin view - oversight features)
- ⏳ Origin-like insight components
- ⏳ Personalized content feed
- ⏳ Consent management UI
- ⏳ Recommendation display

**Tasks Completed:**
- ✅ Dashboard Structure:
  - ✅ Main dashboard (admin view - all users)
  - ✅ User detail page with accounts and transactions
  - ✅ Account cards with masked IDs and utilization colors
  - ✅ Transaction tables with grouping and sorting
- ✅ Components:
  - ✅ AccountCard - Account display
  - ✅ TransactionTable - Transaction display
  - ✅ FeatureCard - Feature visualization
  - ✅ CollapsibleAccountCard - Collapsible account view
- ✅ UX Features:
  - ✅ Responsive design
  - ✅ Loading states
  - ✅ Error handling
  - ✅ 30/180 day transaction window selector
  - ⏳ Accessibility

**Tasks Remaining:**
- ✅ Dashboard Separation:
  - ✅ Create `ui/src/pages/user/UserDashboard.tsx` - End-user view (restricted to own account)
  - ✅ Create `ui/src/pages/operator/OperatorDashboard.tsx` - Admin/operator view (all users + oversight)
  - ✅ Update routing to support both views
  - ⏳ Add role-based access control (admin vs user) - TODO: Add authentication/role context
- ⏳ Origin-like Insight Components:
  - ⏳ WeeklyRecapCard - Weekly spending recaps with daily breakdown
  - ⏳ SpendingAnalysisCard - 6-month spending analysis with 3 key insights
  - ⏳ SuggestedBudgetCard - AI-suggested budget with historical chart
  - ⏳ BudgetTrackingCard - Budget tracking with circular gauge and category progress
  - ⏳ NetWorthRecapCard - Net worth trends with line chart
- ⏳ User Dashboard Features:
  - ⏳ Personalized insights feed
  - ⏳ Behavioral signals visualization
  - ⏳ Persona display (pending persona assignment)
  - ⏳ Recommendations feed
  - ⏳ Consent toggle
  - ⏳ Educational content viewer
- ⏳ Frontend Dependencies:
  - ⏳ Install Recharts for charting (bar charts, line charts, radial gauges)
  - ⏳ Install python-dateutil (backend) for date manipulation

**Key Files:**
- `ui/src/pages/Dashboard.tsx` - Main dashboard (admin view)
- `ui/src/pages/UserDetail.tsx` - User detail page
- `ui/src/pages/user/UserDashboard.tsx` - End-user dashboard (new)
- `ui/src/pages/operator/OperatorDashboard.tsx` - Operator dashboard (new)
- `ui/src/components/AccountCard.tsx` - Account display
- `ui/src/components/TransactionTable.tsx` - Transaction display
- `ui/src/components/FeatureCard.tsx` - Feature visualization
- `ui/src/components/WeeklyRecapCard.tsx` - Weekly recap (new)
- `ui/src/components/SpendingAnalysisCard.tsx` - Spending analysis (new)
- `ui/src/components/SuggestedBudgetCard.tsx` - Budget suggestion (new)
- `ui/src/components/BudgetTrackingCard.tsx` - Budget tracking (new)
- `ui/src/components/NetWorthRecapCard.tsx` - Net worth recap (new)

**Success Criteria:**
- ✅ Beautiful, modern UI
- ✅ Responsive design
- ⏳ Dashboard separation (admin vs user views)
- ⏳ All Origin-like insights components functional
- ⏳ All features accessible
- ✅ Fast load times

---

### ⏳ Phase 10: AWS Lambda Integration & Deployment (Week 10-11) - PENDING

**Goal**: Deploy to AWS Lambda and finalize

**Deliverables:**
- ⏳ Lambda function deployment
- ⏳ Serverless configuration
- ⏳ Documentation completion
- ⏳ Final testing

**Tasks:**
- ⏳ Lambda Setup:
  - Package FastAPI for Lambda
  - Configure API Gateway
  - Set up environment variables
  - Deploy functions
- ⏳ Documentation:
  - Complete README
  - API documentation
  - Setup instructions
  - Decision log
- ⏳ Final Polish:
  - Code review
  - Performance optimization
  - Security audit
  - Documentation review

**Key Files:**
- `deploy/` - Deployment scripts
- `README.md` - Complete documentation
- `docs/decisions.md` - Decision log
- `requirements.txt` - Dependencies

**Success Criteria:**
- ⏳ Lambda functions deployed
- ✅ One-command setup working
- ⏳ All documentation complete
- ✅ System runs locally

---

## Project Structure

```
SpendSense/
├── .cursorrules                    # Main cursor rules
├── .cursorrules/                   # Agent-specific rules
│   ├── architect.md
│   ├── frontend.md
│   └── backend.md
├── ingest/                         # Data ingestion
│   ├── generator.py               # ✅ Synthetic data generator
│   ├── loader.py                  # ✅ Data ingestion pipeline
│   ├── schema.py                  # ✅ Database models
│   └── __main__.py                # ✅ CLI entry point
├── features/                       # Signal detection
│   ├── subscriptions.py           # ✅ Subscription detection
│   ├── savings.py                 # ✅ Savings analysis
│   ├── credit.py                  # ✅ Credit utilization
│   ├── income.py                  # ✅ Income stability
│   └── pipeline.py                # ✅ Feature orchestration
├── personas/                       # Persona assignment
│   ├── definitions.py             # ⏳ Persona criteria
│   ├── assigner.py                # ⏳ Assignment logic
│   └── traces.py                  # ⏳ Decision logging
├── recommend/                      # Recommendation engine
│   ├── generator.py               # ⏳ Recommendation logic
│   ├── rationales.py              # ⏳ Rationale builder
│   ├── content_catalog.py         # ⏳ Education content
│   └── offers_catalog.py          # ⏳ Partner offers
├── guardrails/                     # Compliance
│   ├── consent.py                 # ⏳ Consent tracking
│   ├── eligibility.py             # ⏳ Eligibility checks
│   ├── tone.py                    # ⏳ Tone validation
│   └── disclosure.py              # ⏳ Disclaimers
├── api/                           # FastAPI backend
│   ├── main.py                    # ✅ FastAPI app
│   ├── routes/                    # ⏳ Route handlers
│   ├── models/                    # ⏳ Pydantic models
│   └── middleware/                # ⏳ Middleware
├── ui/                            # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx      # ✅ Main dashboard
│   │   │   └── UserDetail.tsx     # ✅ User detail page
│   │   ├── components/
│   │   │   ├── AccountCard.tsx    # ✅ Account display
│   │   │   ├── TransactionTable.tsx # ✅ Transaction display
│   │   │   └── FeatureCard.tsx    # ✅ Feature visualization
│   │   └── services/
│   │       └── api.ts             # ✅ API client
│   ├── user/                      # ⏳ User-facing components
│   ├── operator/                  # ⏳ Operator view
│   └── shared/                    # ⏳ Shared components
├── eval/                          # Evaluation
│   ├── metrics.py                 # ⏳ Metric calculations
│   ├── harness.py                 # ⏳ Evaluation runner
│   └── reports.py                 # ⏳ Report generation
├── tests/                         # Test suite
├── data/                          # Data storage
│   ├── synthetic/                 # ✅ Generated data
│   │   └── transactions_final.csv # ✅ Rich CSV output
│   ├── features/                  # ⏳ Parquet files
│   └── catalogs/                  # ⏳ Content/offer JSON
├── docs/                          # Documentation
│   ├── personas.md                # ⏳ Persona documentation
│   ├── decisions.md               # ✅ Decision log
│   ├── schema.md                  # ✅ Schema documentation
│   ├── phase1_summary.md          # ✅ Phase 1 summary
│   ├── phase2_summary.md          # ✅ Phase 2 summary
│   └── phase1_prd_compliance.md   # ✅ Compliance check
├── deploy/                        # ⏳ Deployment scripts
├── requirements.txt               # ✅ Python dependencies
├── ui/package.json                # ✅ Frontend dependencies
├── README.md                      # ✅ Project overview
└── plan.plan.md                   # ✅ This PRD document
```

**Legend**: ✅ Complete | ⏳ Pending

---

## Success Criteria

### Category Metrics
| Category | Metric | Target |
|----------|--------|--------|
| Coverage | Users with assigned persona + ≥3 behaviors | 100% |
| Explainability | Recommendations with rationales | 100% |
| Latency | Time to generate recommendations per user | <5 seconds |
| Auditability | Recommendations with decision traces | 100% |
| Code Quality | Passing unit/integration tests | ≥10 tests |
| Documentation | Schema and decision log clarity | Complete |

### Additional Requirements
- ✅ All personas have clear, documented criteria (pending implementation)
- ⏳ Guardrails prevent ineligible offers
- ⏳ Tone checks enforce "no shaming" language
- ✅ Consent is tracked and enforced (schema ready)
- ⏳ Operator view shows all signals and can override
- ⏳ Evaluation report includes fairness analysis
- ✅ System runs locally without external dependencies

---

## Data Output Format

### transactions_final.csv
Generated CSV matches the structure of the reference `transactions_final.csv` with all columns:

**Columns:**
- `transaction_id` - Unique transaction identifier
- `timestamp` - Full timestamp
- `date` - Date only
- `time` - Time only
- `customer_id` - User identifier (CUST000001, etc.)
- `merchant_id` - Merchant identifier (MERCH000000, etc.)
- `merchant_category` - Category (groceries, restaurant, utilities, etc.)
- `transaction_type` - Type (purchase, refund, transfer, fee, deposit, withdrawal)
- `payment_method` - Method (credit_card, debit_card, digital_wallet, bank_transfer, cash)
- `amount` - Transaction amount (positive, sign in transaction_type)
- `amount_category` - Size category (small, medium, large, very_large, extra_large)
- `status` - Status (approved, pending, declined)
- `account_balance` - Running balance after transaction
- `account_id` - Account identifier (12-digit, last 4 shown on dashboard)
- `hour` - Hour of day (0-23)
- `day_of_week` - Day name (Monday, Tuesday, etc.)
- `month` - Month number (1-12)
- `month_name` - Month name (January, February, etc.)
- `quarter` - Quarter (1-4)
- `year` - Year

**Unique Identifiers:**
- `customer_id`: Maps to dashboard users (CUST000001, CUST000002, etc.)
- `account_id`: 12-digit account IDs (last 4 digits shown on dashboard as `********3749`)
- `merchant_id`: Consistent merchant identifiers

---

## Risk Mitigation

### Data Quality
- ✅ Implement robust validation and synthetic data checks
- ✅ Realistic transaction amounts based on real-world patterns
- ✅ Credit limit and balance enforcement
- ⏳ Add data quality reports

### Performance
- ✅ Optimize feature computation (currently <2 seconds per user)
- ⏳ Use Parquet for analytics storage
- ⏳ Implement caching for recommendations

### Compliance
- ✅ Strict guardrails (schema ready)
- ⏳ Regular audits
- ⏳ Legal review
- ✅ "Not financial advice" disclaimer

### Explainability
- ⏳ Template-based rationales
- ⏳ Decision traces
- ⏳ Plain-language explanations

### User Trust
- ✅ Clear consent tracking
- ⏳ Transparent recommendations
- ⏳ No shaming language enforcement

---

## Current Status

### ✅ Completed (Phase 1 & 2, Partial Phase 6 & 9)
- ✅ Project structure and scaffolding
- ✅ Database schema with all required tables
- ✅ Synthetic data generator with realistic patterns
- ✅ Credit limit and balance enforcement
- ✅ Transaction amount patterns from `transactions_final.csv`
- ✅ Pending transactions (24-48 hours)
- ✅ Returns and interest charges
- ✅ Payment pattern detection
- ✅ Frontend dashboard
- ✅ Backend API (core endpoints)
- ✅ Feature pipeline for behavioral signals
- ✅ CSV export in `transactions_final.csv` format
- ✅ Account cards with masked IDs and utilization colors
- ✅ Transaction tables grouped by account
- ✅ User detail pages with accounts and transactions

### ⏳ In Progress / Pending
- ⏳ Persona assignment system (Phase 3)
- ⏳ Recommendation engine (Phase 4)
- ⏳ Guardrails implementation (Phase 5)
- ⏳ Operator view (Phase 7)
- ⏳ Evaluation harness (Phase 8)
- ⏳ AWS Lambda deployment (Phase 10)
- ⏳ Money market account generation
- ⏳ Parquet storage for analytics
- ⏳ Additional API endpoints
- ⏳ Test suite (≥10 tests)

---

## Key Decisions

1. **12-Digit Account IDs**: All accounts use 12-digit numeric IDs for realism
2. **Loan Fields in Account Model**: Interest rates and payment dates stored directly in Account for easier access
3. **Multiple Credit Cards**: Users can have 1-3 credit cards
4. **30-Day Transactions**: Generator creates transactions for last 30 days only
5. **Matching Names/Emails**: User emails derived from their names for realism
6. **Frontend Masking**: Account IDs shown as `********XXXX` for security/privacy
7. **Realistic Amounts**: Transaction amounts based on `transactions_final.csv` analysis
8. **Credit Limit Enforcement**: Transactions respect credit limits with $100 buffer
9. **Pending Transactions**: Only recent transactions (24-48 hours) are pending
10. **CSV Output**: Generates `transactions_final.csv` with all columns plus unique identifiers
11. **FastAPI Backend**: Fast, modern Python API framework
12. **React Frontend**: Modern, component-based UI with TypeScript
13. **SQLite for Development**: Local database for fast iteration
14. **Parquet for Analytics**: Efficient columnar storage for feature data (pending)

---

## To-Dos

- [x] Copy BMAD_Cursor files: rename cursorrules-main.cursorrules to .cursorrules, create .cursorrules/ folder, copy agent files (architect.md, frontend.md, backend.md)
- [x] Create modular project structure (ingest/, features/, personas/, recommend/, guardrails/, api/, ui/, eval/, docs/)
- [x] Design and implement SQLite schema for accounts, transactions, liabilities, users, consent
- [x] Build synthetic data generator for 50-100 users with diverse financial situations matching Plaid structure
- [x] Implement behavioral signal detection: subscriptions, savings, credit, income stability with 30d/180d windows
- [ ] Define 5 personas (4 specified + 1 custom), implement assignment logic with prioritization and decision traces
- [ ] Build recommendation engine with education content catalog, partner offers, and plain-language rationale generation
- [ ] Implement consent management, eligibility checks, tone validation, and regulatory disclosures
- [ ] Build FastAPI REST API with all required endpoints (users, consent, profile, recommendations, feedback, operator)
- [ ] Create operator dashboard with signal review, recommendation approval, and decision trace viewer
- [ ] Build evaluation harness with metrics calculation (coverage, explainability, relevance, latency, fairness) and report generation
- [x] Build React user interface with personalized dashboard, recommendations feed, and consent management
- [ ] Deploy FastAPI to AWS Lambda, complete documentation, and finalize for production
- [ ] Add money market account generation
- [ ] Implement Parquet storage for analytics
- [ ] Create test suite with ≥10 tests
- [ ] Add data validation and quality reports

---

## Next Steps

1. **Complete Phase 3**: Implement persona assignment system
2. **Complete Phase 4**: Build recommendation engine with rationales
3. **Complete Phase 5**: Implement guardrails (eligibility, tone, consent UI)
4. **Complete Phase 6**: Finish remaining API endpoints
5. **Complete Phase 7**: Build operator view
6. **Complete Phase 8**: Evaluation harness and metrics
7. **Complete Phase 10**: AWS Lambda deployment
8. **Enhancements**: Money market accounts, validation checks, test suite, Parquet storage

---

## Origin-like Data Insights Integration Subtask

### Overview
Integrate Origin-inspired features to enhance end-user experience with digestible financial insights, visualizations, and actionable summaries. This subtask prepares the foundation for Phase 3+ (Personas, Recommendations) by adding data aggregation, historical tracking, and user-facing insight generation.

### Integration Phase Recommendation

**Best Phase: Phase 9 (Frontend & User Experience) - Backend work in Phase 6, Frontend work in Phase 9**

**Rationale:**
- Origin insights are user-facing content that enhances the user dashboard experience
- These insights provide the foundation for Phase 4's recommendation engine (recommendations can reference insights)
- Backend insight computation can be integrated alongside Phase 6 (API & Backend) 
- Frontend components align with Phase 9's user experience goals
- Separates user dashboard (insights) from admin/operator dashboard (oversight)

**Timeline:**
- Backend work: Weeks 6-7 (parallel with Phase 6 API completion)
- Frontend work: Weeks 9-10 (integrated into Phase 9)

### Dashboard Separation Strategy

#### User Dashboard (`/user/*` or `/dashboard`)
**Purpose**: End-user financial insights and personalized recommendations  
**Features**:
- Weekly spending recaps
- 6-month spending analysis
- Suggested budgets
- Budget tracking
- Net worth trends
- Deep recaps
- Personalized recommendations (Phase 4)
- Consent management
- **Restriction**: User can only see their own account data

**Location**: `ui/src/pages/user/UserDashboard.tsx` (new)

#### Admin/Operator Dashboard (`/operator/*` or `/dashboard?role=admin`)
**Purpose**: Human oversight, signal review, recommendation approval  
**Features**:
- User list with personas (from Phase 3)
- Signal summary view (30d, 180d)
- Recommendation approval queue
- Decision trace viewer
- Override capabilities
- System metrics and health
- **Access**: Admin can see all users and their data

**Location**: `ui/src/pages/operator/OperatorDashboard.tsx` (new)

**Note**: Admin and user have the same experience/interface, but admin can see all users whereas user is restricted to only their account.

### Features to Integrate

1. **Weekly Spending Recaps** - Daily breakdowns, top categories, week-over-week changes
2. **6-Month Spending Analysis** - Income stability, spending tightness, buffer status
3. **AI-Suggested Budget** - Monthly budget recommendations with historical charts
4. **Budget Tracking** - Progress gauges, category breakdowns, budget vs. actual
5. **Deep Recaps (Net Worth)** - Net worth trends, portfolio performance, contextual explanations
6. **User Feedback Mechanism** - Like/dislike buttons for personalization

### Database Schema Changes

- New table: `budgets` - User-defined and suggested budgets
- New table: `net_worth_history` - Historical net worth snapshots
- New table: `user_feedback` - User feedback on insights and recommendations

### Tools & Dependencies

**New Python Packages:**
- `python-dateutil` - Enhanced date parsing and manipulation
- `numpy` - Statistical calculations (percentiles, medians)

**New Frontend Packages:**
- `recharts` - Comprehensive React charting library for bar charts, line charts, radial gauges

### Implementation Plan

**Phase 1: Foundation (Week 1)**
- Database schema extensions
- Backend infrastructure (`insights/` module)
- Weekly recap implementation

**Phase 2: Analysis Features (Week 2)**
- 6-month spending analysis
- Net worth tracking with historical snapshots

**Phase 3: Budget Features (Week 3)**
- Budget calculator and suggestion algorithm
- Budget tracking with progress visualization

**Phase 4: User Experience & Feedback (Week 4)**
- User feedback system
- Deep recaps integration
- Frontend polish and responsive design

### Success Criteria

- All 5 insight types functional (weekly recap, 6-month analysis, budget suggestion, budget tracking, net worth)
- Historical data tracking working (net worth history)
- User feedback system operational
- Frontend visualizations rendering correctly
- API endpoints returning data in <2 seconds
- No breaking changes to existing functionality
- Dashboard separation working (admin sees all users, user sees only own account)

---

## Contact

For questions or clarifications: Bryce Harris - bharris@peak6.com

---

## License & Disclaimer

**This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.**

This project is for educational purposes. See LICENSE file for details.
