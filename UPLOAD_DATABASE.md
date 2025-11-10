# Upload Database to Railway

Your local database already has **150 users, 471 accounts, and 28,831 transactions**! 

## Option 1: Use Railway CLI to Upload Database

Railway uses persistent volumes for file storage. Here's how to upload your database:

### Step 1: Link to Railway Project

```bash
railway link
# Select your project when prompted
```

### Step 2: Upload Database File

Since Railway uses volumes, you can copy the database file directly:

```bash
# Method 1: Use Railway CLI to copy file
railway run sh -c "mkdir -p data && cat > data/spendsense.db" < data/spendsense.db

# Method 2: Use the upload script
./scripts/upload_db_to_railway.sh
```

### Step 3: Verify Upload

```bash
# Check if database was uploaded
railway run sqlite3 data/spendsense.db "SELECT COUNT(*) FROM users;"
```

## Option 2: Use Railway Volume (Recommended)

Railway supports persistent volumes. If you haven't set one up:

1. **Go to Railway Dashboard** → Your Service → **Volumes**
2. **Create a new volume** named `data` with path `/app/data`
3. **Restart your service** to mount the volume
4. **Upload the database** using Railway CLI:

```bash
railway run sh -c "cat > /app/data/spendsense.db" < data/spendsense.db
```

## Option 3: Set DATABASE_URL Environment Variable

If Railway has a volume mounted, set the environment variable:

1. Go to Railway Dashboard → Your Service → **Variables**
2. Add: `DATABASE_URL=sqlite:////app/data/spendsense.db` (or wherever your volume is mounted)

## Verify After Upload

After uploading, verify the users are accessible:

```bash
# Check stats endpoint
curl https://web-production-ebdc6.up.railway.app/api/stats

# Should return:
# {
#   "total_users": 151,  # 150 users + 1 admin
#   "total_accounts": 471,
#   "total_transactions": 28831
# }
```

## Important Notes

- **Database size**: Your database is ~10MB, which should upload fine
- **Backup**: Railway volumes persist data, but consider backing up important data
- **Restart**: After uploading, restart your Railway service to ensure it picks up the new database

