# Local Deployment & Testing Guide

This guide will help you deploy and test SpendSense locally, including how to access Phase 8 (Evaluation & Metrics).

## Quick Start

### 1. Start Backend Server

```bash
# Option 1: Use the startup script
./start_backend.sh

# Option 2: Manual start
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will start on **http://localhost:8000**

**API Documentation**: http://localhost:8000/docs

### 2. Start Frontend Server

In a **new terminal window**:

```bash
# Option 1: Use the startup script
./start_frontend.sh

# Option 2: Manual start
cd ui && npm run dev
```

The frontend will start on **http://localhost:3000**

## Accessing Phase 8: Evaluation & Metrics

Phase 8 (Evaluation & Metrics) is accessible through the **Operator Dashboard**:

### Via UI:

1. Open http://localhost:3000 in your browser
2. Click **"Operator"** in the navigation menu (top right)
3. Click on the **"Evaluation Metrics"** tab
4. The dashboard will display:
   - Overall Score
   - Coverage Metric
   - Explainability Metric
   - Relevance Metric
   - Latency Metric
   - Fairness Metric

### Via API:

```bash
# Get evaluation metrics
curl http://localhost:8000/api/evaluation/metrics

# With latency sample size (faster for testing)
curl "http://localhost:8000/api/evaluation/metrics?latency_sample_size=5"
```

### Via CLI:

```bash
# Run full evaluation
python3 -m eval.harness

# Run with sample size (faster)
python3 -m eval.harness --latency-sample-size 5

# Output files saved to eval/results/
```

## Testing the Full System

### 1. Main Dashboard (Admin View)
- **URL**: http://localhost:3000/
- **Features**: 
  - View all users
  - System statistics
  - User listing with account counts

### 2. Operator Dashboard (Admin View)
- **URL**: http://localhost:3000/operator
- **Tabs**:
  - **Overview**: User list and statistics
  - **Recommendations**: Recommendation approval queue
  - **Signals**: Behavioral signal review
  - **Decision Traces**: Persona assignment decision traces
  - **Evaluation Metrics**: Phase 8 evaluation dashboard ⭐

### 3. User Detail Page (Admin View)
- **URL**: http://localhost:3000/user/{userId}
- **Features**:
  - User account details
  - Transaction history
  - 30-day and 180-day features
  - Financial insights (Origin-like components)
  - Recommendations (read-only)

### 4. User Dashboard (End-User View)
- **URL**: http://localhost:3000/my-dashboard/{userId}
- **Features**:
  - Own account data only
  - Interactive consent management
  - Financial insights
  - Personalized recommendations

## Phase 8 Evaluation Metrics Explained

The Evaluation Metrics dashboard shows:

### Coverage (Target: 100%)
- Percentage of users with assigned persona + ≥3 detected behaviors
- Shows total users, users with persona, and users meeting coverage criteria

### Explainability (Target: 100%)
- Percentage of recommendations with plain-language rationales
- Shows total recommendations vs. recommendations with rationales

### Relevance (Target: ≥80%)
- Education-persona fit scoring
- Shows how well recommendations match user personas

### Latency (Target: <5 seconds)
- Average time to generate recommendations per user
- Shows min, max, and average latencies

### Fairness (Target: ≥0.7)
- Demographic parity in persona distribution
- Shows persona distribution across all users
- Fairness score indicates balance

### Overall Score
- Weighted combination of all metrics
- Shows how many targets are met (e.g., "4/5")

## Troubleshooting

### Backend Not Starting
- Check if port 8000 is available: `lsof -i :8000`
- Verify Python dependencies: `pip install -r requirements.txt`
- Check database exists: `ls data/spendsense.db`

### Frontend Not Starting
- Check if port 3000 is available: `lsof -i :3000`
- Verify Node modules: `cd ui && npm install`
- Check backend is running (frontend needs backend API)

### Evaluation Metrics Not Loading
- Ensure backend is running
- Check console for errors (browser DevTools)
- Verify users have consent granted (for some metrics)
- Try refreshing the metrics

### Database Issues
- Generate synthetic data: `python3 -m ingest.__main__ --num-users 50`
- Check database file: `ls -lh data/spendsense.db`

## Next Steps

After testing locally:

1. **Phase 9**: Verify all frontend features work
2. **Phase 10**: Prepare for AWS Lambda deployment

## Useful Commands

```bash
# Generate test data
python3 -m ingest.__main__ --num-users 50

# Run evaluation (CLI)
python3 -m eval.harness --latency-sample-size 5

# Check API health
curl http://localhost:8000/

# View API docs
open http://localhost:8000/docs

# Check backend logs
# (Logs appear in terminal where backend is running)

# Check frontend logs
# (Logs appear in terminal where frontend is running)
```


