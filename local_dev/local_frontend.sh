#!/bin/bash
set -e # exit on error

echo "Starting Frontend Dev Server..."

cd frontend

if [[ -d "node_modules" ]]; then
    echo "node_modules directory exists"
else
    echo "node_modules directory does not exist"
    npm install
    npm run prepare
fi

npm run dev
