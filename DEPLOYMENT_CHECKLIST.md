# Vercel Deployment Checklist

## Pre-Deployment

- [ ] Backend is deployed and accessible via HTTPS
- [ ] Backend CORS is configured to allow your Vercel domain
- [ ] All environment variables are documented
- [ ] Code is committed and pushed to repository

## Vercel Configuration

- [ ] Root directory set to `ui/`
- [ ] Framework preset: Vite (auto-detected)
- [ ] Build command: `npm run build`
- [ ] Output directory: `dist`
- [ ] Install command: `npm install`

## Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

- [ ] `VITE_API_URL` = Your production backend URL (e.g., `https://spendsense-api.railway.app`)
- [ ] `VITE_WS_BASE_URL` = Your WebSocket URL (optional, e.g., `wss://spendsense-api.railway.app`)

## Post-Deployment Verification

- [ ] Site loads without errors
- [ ] Login functionality works
- [ ] API calls are successful (check browser console)
- [ ] No CORS errors
- [ ] Styling looks correct (colors, fonts, layout)
- [ ] Responsive design works on mobile
- [ ] All routes work (including refresh on sub-routes)
- [ ] Transactions load correctly
- [ ] Recommendations display (if user has consented)

## Backend CORS Configuration

Make sure your backend's `api/main.py` includes your Vercel domain:

```python
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
# Should include:
# - http://localhost:3000 (for local dev)
# - https://your-project.vercel.app (production)
# - https://your-project-*.vercel.app (preview deployments)
```

## Quick Deploy Commands

### Via Vercel CLI:

```bash
cd ui
vercel login
vercel
vercel env add VITE_API_URL
vercel --prod
```

### Via Vercel Dashboard:

1. Go to vercel.com/dashboard
2. Click "Add New Project"
3. Import your repository
4. Set root directory to `ui/`
5. Add environment variables
6. Deploy

## Troubleshooting

- **Build fails**: Check build logs in Vercel dashboard
- **API calls fail**: Verify `VITE_API_URL` is set correctly
- **CORS errors**: Update backend CORS configuration
- **404 on refresh**: Verify `vercel.json` rewrite rules are in place
- **Styling issues**: Tailwind should compile automatically, check build logs

