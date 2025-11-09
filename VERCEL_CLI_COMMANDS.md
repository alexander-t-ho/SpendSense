# Vercel CLI Deployment Commands

Due to Node.js library issues, run these commands manually in your terminal.

## Step 1: Login to Vercel

```bash
cd /Users/alexho/SpendSense/ui
npx vercel login
# Or if you have a working node version:
/Users/alexho/.nvm/versions/node/v18.20.8/bin/vercel login
```

This will open your browser for authentication.

## Step 2: Deploy to Vercel

```bash
cd /Users/alexho/SpendSense/ui
npx vercel
# Or:
/Users/alexho/.nvm/versions/node/v18.20.8/bin/vercel
```

When prompted:
- **Set up and deploy?** → Yes
- **Which scope?** → Select your account
- **Link to existing project?** → No (or Yes if you already created one)
- **What's your project's name?** → `spendsense` (or your choice)
- **In which directory is your code located?** → `./` (current directory)
- **Want to override the settings?** → No

## Step 3: Add Environment Variable

After initial deployment, add the Railway backend URL:

```bash
npx vercel env add VITE_API_URL production
# Or:
/Users/alexho/.nvm/versions/node/v18.20.8/bin/vercel env add VITE_API_URL production
```

When prompted:
- **What's the value of VITE_API_URL?** → Enter your Railway backend URL
  - Example: `https://web-production-xxxx.up.railway.app`
- **Add VITE_API_URL to which Environments?** → Select all (Production, Preview, Development)

## Step 4: Deploy to Production

```bash
npx vercel --prod
# Or:
/Users/alexho/.nvm/versions/node/v18.20.8/bin/vercel --prod
```

This will deploy to production and give you your Vercel URL.

## Alternative: Use Vercel Dashboard

If CLI continues to have issues, use the dashboard:

1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New..." → "Project"
4. Import `alexander-t-ho/SpendSense`
5. **IMPORTANT**: Set **Root Directory** to `ui`
6. Add environment variable:
   - Name: `VITE_API_URL`
   - Value: Your Railway backend URL
7. Click "Deploy"

## After Deployment

1. Copy your Vercel URL (e.g., `https://spendsense.vercel.app`)
2. Update Railway CORS:
   ```bash
   railway login
   railway link
   railway variables --set "CORS_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app,https://your-vercel-app-*.vercel.app"
   ```
3. Test your deployment!

