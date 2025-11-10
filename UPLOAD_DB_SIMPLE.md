# Simple Database Upload - No Railway CLI Needed!

Since `railway link` takes too long, use this simple HTTP endpoint instead.

## Step 1: Wait for Deployment

Wait for Railway to deploy the latest code (should take 1-2 minutes after the git push).

## Step 2: Upload Database via HTTP

Once deployed, simply upload your database file using curl:

```bash
curl -X POST https://web-production-ebdc6.up.railway.app/api/admin/upload-database \
  -F "file=@data/spendsense.db"
```

This will:
- Upload your local database file
- Save it to the production database path
- Verify the upload and return stats

## Step 3: Verify Upload

Check that the users are now in production:

```bash
curl https://web-production-ebdc6.up.railway.app/api/stats
```

Should return:
```json
{
  "total_users": 151,  # 150 users + 1 admin
  "total_accounts": 471,
  "total_transactions": 28831
}
```

## Step 4: Check Admin Dashboard

Log into your admin dashboard and you should see all 150 users!

## Important Notes

- **This endpoint is temporary** - Remove it after uploading for security
- **File size limit**: Railway may have a request size limit (usually 10-50MB). Your database is ~10MB, so it should work fine
- **If upload fails**: Check Railway logs for errors

## Alternative: If HTTP Upload Fails

If the HTTP upload doesn't work (e.g., file size limits), you can:

1. **Create volume via Railway Dashboard** (see `RAILWAY_VOLUME_SETUP.md`)
2. **Use Railway Shell** (if available):
   ```bash
   railway shell
   # Then manually copy the file
   ```

## Remove Endpoint After Use

After successfully uploading, remove the `/api/admin/upload-database` endpoint from `api/main.py` for security.

