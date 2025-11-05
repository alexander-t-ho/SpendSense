# Local Development - Quick Start

## Prerequisites
- Python 3.9+ installed
- Node.js and npm installed

## Start Backend (Port 8000)

```bash
cd /Users/alexho/SpendSense
./start_backend.sh
```

Or manually:
```bash
cd /Users/alexho/SpendSense
source venv/bin/activate  # or: python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

## Start Frontend (Port 3000)

Open a **new terminal window** and run:

```bash
cd /Users/alexho/SpendSense/ui
npm install  # First time only
npm run dev
```

## Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Quick Commands

### Start Both Servers (in separate terminals)

**Terminal 1 - Backend:**
```bash
cd /Users/alexho/SpendSense && ./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
cd /Users/alexho/SpendSense/ui && npm run dev
```

### Stop Servers

Press `Ctrl+C` in each terminal window to stop the servers.

### Check if Servers are Running

```bash
# Check backend
curl http://localhost:8000/

# Check frontend
curl http://localhost:3000/
```
