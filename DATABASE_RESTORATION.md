# Database Restoration Guide

## ✅ Database Restored!

Your database with 150 users has been uploaded to Railway:
- **Users**: 150
- **Accounts**: 471
- **Transactions**: 28,831
- **Liabilities**: 195

## ⚠️ Important: Railway Containers are Ephemeral

**Problem**: Railway containers are recreated on each deployment, which wipes the database file.

**Current Status**: Database is uploaded and working, but will be lost on next Railway redeploy.

## 🔄 How to Restore Database After Railway Redeploy

### Option 1: Re-upload Database (Quick Fix)

```bash
curl -X POST https://web-production-d242.up.railway.app/api/admin/upload-database \
  -F "file=@data/spendsense.db"
```

### Option 2: Generate Users via API (Slower but Automated)

The API endpoint can generate users in batches:

```bash
# Generate 1 user at a time (call 150 times)
for i in {1..150}; do
  curl -X POST "https://web-production-d242.up.railway.app/api/admin/generate-users?num_users=1"
  echo "Generated user $i/150"
done
```

**Note**: This is slow (1-2 users per call) but works if you don't have the database file.

### Option 3: Set Up Railway Volume (Permanent Solution) ⭐ RECOMMENDED

To make the database persist across deployments:

1. **Railway Dashboard** → Your project → Your service
2. **Volumes** tab → **Create Volume**
3. Configure:
   - Name: `data`
   - Mount Path: `/app/data`
   - Size: 1GB (or more)
4. **Set Environment Variable**:
   - Key: `DATABASE_PATH`
   - Value: `/app/data/spendsense.db`
5. **Upload database to volume**:
   ```bash
   railway run sh -c "mkdir -p /app/data && cat > /app/data/spendsense.db" < data/spendsense.db
   ```

After this, the database will persist across deployments!

## 📊 Current Database Stats

- **Total Users**: 150
- **Total Accounts**: 471  
- **Total Transactions**: 28,831
- **Total Liabilities**: 195

## 🔍 Verify Database

```bash
# Check stats
curl https://web-production-d242.up.railway.app/api/stats

# List users
curl "https://web-production-d242.up.railway.app/api/users?limit=10"
```

## 🎯 Recommended Action

**Set up a Railway Volume** (Option 3) to prevent database loss on each deployment. This is the permanent solution.

