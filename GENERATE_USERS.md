# Generate Users in Production

Since the HTTP endpoint times out, use the CLI script to generate users directly on Railway.

## Option 1: Using Railway CLI (Recommended)

```bash
# Link to your Railway project (if not already linked)
railway link

# Generate 150 users (in batches of 10)
railway run python scripts/generate_users_production.py --num-users 150 --batch-size 10

# Or generate in smaller batches if needed
railway run python scripts/generate_users_production.py --num-users 150 --batch-size 5
```

## Option 2: Using HTTP Endpoint (Small Batches)

If you want to use the HTTP endpoint, call it multiple times with very small batches:

```bash
# Generate 1 user at a time (call 150 times)
for i in {1..150}; do
  echo "Generating user batch $i..."
  curl -X POST "https://web-production-ebdc6.up.railway.app/api/admin/generate-users?num_users=1" \
    -H "Content-Type: application/json"
  sleep 2  # Wait 2 seconds between requests
done
```

## Option 3: Generate Locally and Upload Database

1. Generate users locally:
```bash
python -m ingest --num-users 150
```

2. Upload the database file to Railway (if Railway supports file uploads)

## Verification

After generating users, verify the count:

```bash
# Check total users via API
curl "https://web-production-ebdc6.up.railway.app/api/stats"
```

Or log into the admin dashboard and check the user count there.

