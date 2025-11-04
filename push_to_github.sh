#!/bin/bash

echo "🚀 PUSHING TO GITHUB..."
echo ""

# Step 1: Initialize git if needed
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Step 2: Add all files
echo ""
echo "📝 Adding files..."
git add .

# Step 3: Commit
echo ""
echo "💾 Committing changes..."
git commit -m "Initial commit: IOC Agentic System with WebSocket, AI orchestration, and multi-domain function registry"

# Step 4: Instructions for user
echo ""
echo "=========================================="
echo "🎯 NEXT STEPS - Run these commands:"
echo "=========================================="
echo ""
echo "1️⃣  Create a new repository on GitHub:"
echo "    Go to: https://github.com/new"
echo "    Name: ioc-agentic-system (or any name you want)"
echo "    Keep it PUBLIC or PRIVATE"
echo "    DO NOT add README, .gitignore, or license"
echo ""
echo "2️⃣  After creating, copy YOUR repository URL and run:"
echo ""
echo "    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo "    git branch -M main"
echo "    git push -u origin main"
echo ""
echo "=========================================="
echo ""
echo "✅ Local git setup complete!"
echo "📤 Ready to push to GitHub"

