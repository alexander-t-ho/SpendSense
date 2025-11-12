# Login Credentials

## Admin Login

**Email/Username**: `admin@spendsense.com`  
**Password**: `123456`

## Regular Users

All users in the database use the same default password:
**Password**: `123456`

**Username**: Use the user's email address

## Testing Login

### Via API (curl)
```bash
curl -X POST https://web-production-d242.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@spendsense.com","password":"123456"}'
```

### Via Frontend
1. Go to: `https://spend-sense-o3df.vercel.app/login`
2. Enter email: `admin@spendsense.com`
3. Enter password: `123456`
4. Click "Continue"

## Reset Admin Password

If admin password doesn't work, reset it:
```bash
curl -X POST https://web-production-d242.up.railway.app/api/admin/create-admin
```

This will create/update the admin user with password `123456`.

## Troubleshooting 401 Errors

If you get a 401 "Unauthorized" error:

1. **Check credentials are correct**:
   - Email: `admin@spendsense.com`
   - Password: `123456`

2. **Verify admin user exists**:
   ```bash
   curl https://web-production-d242.up.railway.app/api/stats
   ```

3. **Reset admin password**:
   ```bash
   curl -X POST https://web-production-d242.up.railway.app/api/admin/create-admin
   ```

4. **Check VITE_API_URL is set in Vercel**:
   - Should be: `https://web-production-d242.up.railway.app`
   - Must redeploy Vercel after setting

5. **Check browser console** for detailed error messages

