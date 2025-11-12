# Setting API Keys via CLI

## Quick Setup

### Option 1: Set for Current Session Only
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Option 2: Add to .env File (Recommended - Persists)
```bash
# Edit the .env file
nano .env
# OR
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

### Option 3: Set Using OpenRouter (Alternative)
```bash
export OPENROUTER_API_KEY="your-openrouter-key-here"
# OR add to .env file
echo "OPENROUTER_API_KEY=your-openrouter-key-here" >> .env
```

## Verify Your Key is Set

```bash
# Check if key is set
echo $OPENAI_API_KEY

# Or check both
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:+SET}"
```

## Restart Backend After Setting Key

After setting the key, restart your backend server:

```bash
# Stop the current backend (Ctrl+C if running in foreground)
# Then restart:
./start_backend.sh
```

## Using .env File (Already Configured)

The `start_backend.sh` script now automatically loads environment variables from `.env` file if it exists.

1. Edit `.env` file:
   ```bash
   nano .env
   ```

2. Add your key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. Restart backend - it will automatically load the key!

## Get Your API Key

- **OpenAI**: https://platform.openai.com/api-keys
- **OpenRouter**: https://openrouter.ai/keys

