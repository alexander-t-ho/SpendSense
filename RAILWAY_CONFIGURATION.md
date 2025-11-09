# Railway Configuration Guide - Step by Step

## How to Configure Root Directory and Start Command in Railway

### Step 1: Access Your Service Settings

1. **Go to Railway Dashboard**: [railway.app](https://railway.app)
2. **Select your project** (or create a new one)
3. **Click on your service** (the backend service you created)
4. **Click on the "Settings" tab** (top navigation bar)

### Step 2: Configure Root Directory

1. In the Settings page, scroll down to find **"Root Directory"** section
2. **Leave it empty** or set it to `/` (forward slash)
   - This tells Railway to use the repository root as the working directory
   - Since your `api/` folder is at the root level, this is correct
3. If the field is empty, Railway defaults to root directory - that's perfect!

**Note**: Root Directory should be `/` or left empty because:
- Your `api/main.py` is at `api/main.py` (relative to root)
- Your `requirements.txt` is at the root
- Your `railway.json` is at the root

### Step 3: Configure Start Command

1. In the same Settings page, scroll to find **"Start Command"** section
2. **Enter the following command**:
   ```
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
3. Click **"Save"** or the changes will auto-save

**What this command does**:
- `uvicorn` - The ASGI server for FastAPI
- `api.main:app` - Points to your FastAPI app in `api/main.py`
- `--host 0.0.0.0` - Makes the server accessible from outside the container
- `--port $PORT` - Uses Railway's dynamically assigned port

### Alternative: Using railway.json (Already Configured!)

**Good news!** Your project already has a `railway.json` file that configures this automatically:

```json
{
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

If `railway.json` exists, Railway will use it automatically. However, you can still override it in the dashboard if needed.

### Step 4: Verify Configuration

After setting these values:

1. **Check the Deployments tab** - Railway should start a new deployment
2. **Check the Logs tab** - You should see:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:XXXX (Press CTRL+C to quit)
   ```

### Troubleshooting

**If you see "Module not found" errors:**
- Make sure Root Directory is `/` (root)
- Verify your `requirements.txt` includes all dependencies
- Check that `api/main.py` exists at the correct path

**If the service won't start:**
- Check the Logs tab for error messages
- Verify the Start Command is exactly: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Make sure Python is detected (Railway auto-detects from `requirements.txt`)

**If you can't find the settings:**
- Make sure you're in the **Settings** tab (not Deployments or Metrics)
- The Root Directory and Start Command are usually in the **"Deploy"** section of Settings

### Visual Guide (Where to Click)

```
Railway Dashboard
├── Your Project
    ├── Your Service (Backend)
        ├── [Deployments Tab] ← Check deployment status here
        ├── [Metrics Tab] ← Monitor performance
        ├── [Settings Tab] ← **CLICK HERE**
        │   ├── General
        │   ├── Deploy
        │   │   ├── Root Directory: `/` or empty
        │   │   └── Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
        │   ├── Variables ← Add CORS_ORIGINS here
        │   └── Networking
        └── [Logs Tab] ← Check for errors
```

### Quick Checklist

- [ ] Root Directory: `/` or empty
- [ ] Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- [ ] Environment Variable `CORS_ORIGINS` added (in Variables section)
- [ ] Deployment is running (check Deployments tab)
- [ ] Logs show "Uvicorn running" (check Logs tab)

### Need Help?

If you're still having issues:
1. Check the Railway logs for specific error messages
2. Verify your `requirements.txt` has all dependencies
3. Make sure your code is pushed to GitHub (Railway pulls from there)
4. Try redeploying: Settings → Deploy → "Redeploy"

