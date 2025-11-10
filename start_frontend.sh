#!/bin/bash
cd "$(dirname "$0")/ui" || exit 1
[ -d "node_modules" ] || npm install --silent
npm run dev




