# Railway Volume Setup - Permanent Database Storage

## ✅ Volume Created!

A Railway volume has been created:
- **Name**: `web-volume`
- **Mount Path**: `/app/data`
- **Storage**: 500MB allocated

## 🔧 Complete Setup Steps

### Step 1: Set DATABASE_PATH Environment Variable

The volume is created, but you need to set the environment variable:

**Via Railway Dashboard** (Recommended):
1. Go to [Railway Dashboard](https://railway.app)
2. Select project: **Leafly**
3. Select service: **web**
4. Go to **Variables** tab
5. Add:
   - Key: `DATABASE_PATH`
   - Value: `/app/data/spendsense.db`
6. Save

**Via CLI** (if Railway CLI supports it):
```bash
railway variables --set "DATABASE_PATH=/app/data/spendsense.db"
```

### Step 2: Restart Railway Service

After setting DATABASE_PATH, restart your Railway service:
- Railway Dashboard → Your service → Click "Restart"
- Or wait for next deployment

### Step 3: Upload Database to Volume

After restart, upload the database:

**Option A: Via Admin Endpoint** (Easiest):
```bash
curl -X POST https://web-production-d242.up.railway.app/api/admin/upload-database \
  -F "file=@data/spendsense.db"
```

**Option B: Via Railway CLI** (After service restart):
```bash
railway run sh -c "cat > /app/data/spendsense.db" < data/spendsense.db
```

### Step 4: Verify

```bash
# Check stats
curl https://web-production-d242.up.railway.app/api/stats

# Should show 150 users, 471 accounts, etc.
```

## 📋 Current Status

- ✅ Volume created: `web-volume` at `/app/data`
- ⚠️ **DATABASE_PATH** needs to be set in Railway dashboard
- ⚠️ Service needs restart after setting DATABASE_PATH
- ⚠️ Database needs to be uploaded to volume

## 🎯 Next Steps

1. **Set DATABASE_PATH** in Railway dashboard: `/app/data/spendsense.db`
2. **Restart** Railway service
3. **Upload database** using admin endpoint or CLI
4. **Verify** database persists across deployments

## 🔄 After Setup

Once complete, the database will persist across Railway deployments! No more losing data on redeploy.

