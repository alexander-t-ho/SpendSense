# Railway Volume Setup - Step by Step

Since `railway link` can be slow, here's how to set up the volume and upload your database using the Railway Dashboard.

## Step 1: Create Volume in Railway Dashboard

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Select your project** (the one with your backend service)
3. **Click on your backend service**
4. **Go to the "Volumes" tab** (in the left sidebar or top navigation)
5. **Click "Create Volume"** or "New Volume"
6. **Configure the volume**:
   - **Name**: `data`
   - **Mount Path**: `/app/data`
   - **Size**: 1GB (or more if needed)
7. **Click "Create"**
8. **Restart your service** (this will mount the volume)

## Step 2: Set Environment Variable

1. **In your service**, go to the **"Variables"** tab
2. **Click "New Variable"**
3. **Add**:
   - **Key**: `DATABASE_URL`
   - **Value**: `sqlite:////app/data/spendsense.db`
4. **Click "Save"** (this will trigger a redeploy)

## Step 3: Upload Database File

After the volume is created and mounted, upload your database:

### Option A: Using Railway Shell (Recommended)

```bash
# Open a shell in your Railway service
railway shell

# In the Railway shell:
mkdir -p /app/data
exit

# Then from your local machine, upload the file
# Note: You may need to use base64 encoding for binary files
cat data/spendsense.db | base64 | railway run sh -c "base64 -d > /app/data/spendsense.db"
```

### Option B: Using Railway Run (If Project is Accessible)

```bash
# If you can access your project without linking
railway run sh -c "mkdir -p /app/data && cat > /app/data/spendsense.db" < data/spendsense.db
```

### Option C: Using Python Script in Railway

Create a temporary endpoint or script that accepts the database file:

```bash
# Upload via a temporary API endpoint (if you create one)
curl -X POST https://web-production-ebdc6.up.railway.app/api/admin/upload-db \
  -F "file=@data/spendsense.db"
```

## Step 4: Verify Upload

After uploading, verify the database:

```bash
# Check via API
curl https://web-production-ebdc6.up.railway.app/api/stats

# Should return:
# {
#   "total_users": 151,  # 150 users + 1 admin
#   "total_accounts": 471,
#   "total_transactions": 28831
# }
```

Or check via Railway shell:

```bash
railway shell
sqlite3 /app/data/spendsense.db "SELECT COUNT(*) FROM users;"
exit
```

## Step 5: Restart Service

After uploading, restart your Railway service to ensure it picks up the new database:

1. Go to Railway Dashboard → Your Service
2. Go to "Deployments" tab
3. Click "Redeploy" or wait for automatic restart

## Alternative: Use Railway's File System Directly

If volumes don't work, Railway also supports writing to the filesystem. The default path `data/spendsense.db` should work, but it won't persist across deployments unless you use a volume.

## Troubleshooting

**If volume creation fails:**
- Check Railway's documentation for volume limits
- Ensure you're on a plan that supports volumes
- Try a smaller volume size first

**If upload fails:**
- Check that the volume is mounted: `railway run ls -la /app/data`
- Verify the mount path matches your `DATABASE_URL`
- Check Railway logs for errors

**If database doesn't appear:**
- Verify `DATABASE_URL` environment variable is set correctly
- Check that the file was uploaded: `railway run ls -lh /app/data/`
- Restart the service after uploading

## Quick Reference

- **Volume Path**: `/app/data`
- **Database Path**: `/app/data/spendsense.db`
- **Environment Variable**: `DATABASE_URL=sqlite:////app/data/spendsense.db`
- **Local Database**: `data/spendsense.db` (10MB, 150 users)




