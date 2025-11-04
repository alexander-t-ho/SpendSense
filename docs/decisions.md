# Architectural Decisions

## Decision Log

This document tracks key architectural and design decisions for SpendSense.

### Decision: Technology Stack
**Date**: 2024-11-03  
**Status**: Accepted

**Context**: Need to choose technologies for quick POC implementation.

**Options Considered**:
1. Python FastAPI + React + SQLite
2. Node.js Express + React + PostgreSQL
3. Python Django + React + SQLite

**Decision**: Python FastAPI + React + SQLite

**Rationale**:
- FastAPI provides excellent async support and automatic API documentation
- React is modern and widely used for frontend
- SQLite is sufficient for POC and matches requirements
- Python ecosystem is strong for data processing (Pandas, Polars)

**Consequences**:
- Fast development and iteration
- Easy to deploy locally
- Can migrate to PostgreSQL/MySQL later if needed

---

### Decision: Data Storage Strategy
**Date**: 2024-11-03  
**Status**: Accepted

**Context**: Need to store different types of data efficiently.

**Options Considered**:
1. Single SQLite database for everything
2. SQLite + Parquet files
3. All Parquet files

**Decision**: SQLite for relational data, Parquet for analytics

**Rationale**:
- SQLite for transactional data (users, accounts, transactions)
- Parquet for analytical data (computed features, signals)
- JSON for configs and logs (human-readable, version-controlled)

**Consequences**:
- Efficient querying of relational data
- Fast analytics on Parquet files
- Easy to inspect and version configs

---

### Decision: Synthetic Data Generation
**Date**: 2024-11-03  
**Status**: Accepted

**Context**: Need realistic Plaid-style data without real PII.

**Options Considered**:
1. Use real anonymized data
2. Generate synthetic data with Faker
3. Use public datasets

**Decision**: Generate synthetic data with Faker

**Rationale**:
- No privacy concerns
- Can control diversity of financial situations
- Matches Plaid structure exactly
- Reproducible with seeds

**Consequences**:
- Full control over data characteristics
- Can test edge cases
- No real-world validation

---

### Decision: Persona Assignment Priority
**Date**: 2024-11-03  
**Status**: Proposed

**Context**: Users may match multiple personas, need prioritization logic.

**Options Considered**:
1. Single highest-priority persona
2. Multiple personas with weights
3. Persona with most severe issues first

**Decision**: TBD - Will implement priority-based assignment

**Rationale**: 
- High utilization is most urgent (financial risk)
- Variable income is urgent (cash flow risk)
- Subscription-heavy is moderate (optimization)
- Savings builder is positive (reinforcement)

**Consequences**:
- Users may see recommendations from multiple personas over time
- Priority ensures urgent issues addressed first

---

### Decision: Recommendation Rationale Format
**Date**: 2024-11-03  
**Status**: Accepted

**Context**: Need explainable recommendations with plain language.

**Options Considered**:
1. Template-based rationales
2. LLM-generated rationales
3. Hybrid approach

**Decision**: Template-based rationales with data insertion

**Rationale**:
- Ensures consistency
- Guarantees explainability
- No dependency on external APIs
- Fast and deterministic

**Consequences**:
- Rationales may be formulaic
- Can add LLM enhancement later if needed
- Easy to audit and validate

---

### Decision: Consent Model
**Date**: 2024-11-03  
**Status**: Accepted

**Context**: Need to track and enforce user consent.

**Options Considered**:
1. Binary consent (opt-in/opt-out)
2. Granular consent by feature
3. Consent with expiration

**Decision**: Binary consent with revocation support

**Rationale**:
- Simplest to implement
- Meets requirements
- Can extend to granular later
- Clear audit trail

**Consequences**:
- All-or-nothing consent
- Easy to revoke
- No partial features

---

## Future Considerations

1. **Migration to PostgreSQL**: When scaling beyond POC
2. **Caching Layer**: Redis for frequently accessed data
3. **LLM Integration**: For more natural rationale generation
4. **Real-time Updates**: WebSocket support for live data
5. **Multi-tenant Support**: If needed for production

