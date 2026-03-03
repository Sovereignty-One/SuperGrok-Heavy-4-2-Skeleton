#!/bin/bash

# SuperGrok Enterprise Deployment Script
# Run this script to deploy the application

set -e

echo "🚀 SuperGrok Enterprise Deployment"
echo "=================================="

# Check Node.js version
echo "📦 Checking Node.js version..."
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ required. Current version: $(node -v)"
    exit 1
fi
echo "✅ Node.js version OK: $(node -v)"

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Run linter
echo "🔍 Running linter..."
npm run lint || echo "⚠️  Linter warnings present"

# Build production bundle
echo "🔨 Building production bundle..."
npm run build

# Check build success
if [ -d "dist" ]; then
    echo "✅ Build successful!"
    echo "📊 Build statistics:"
    du -sh dist
    echo ""
    echo "📁 Build files:"
    ls -lh dist/assets/*.js dist/assets/*.css 2>/dev/null || echo "No chunked assets"
else
    echo "❌ Build failed!"
    exit 1
fi

# Optional: Test build
echo "🧪 Testing production build..."
npm run preview &
PREVIEW_PID=$!
sleep 3

# Check if server is running
if curl -s http://localhost:4173 > /dev/null; then
    echo "✅ Production preview OK"
    kill $PREVIEW_PID
else
    echo "⚠️  Could not verify production preview"
    kill $PREVIEW_PID 2>/dev/null || true
fi

echo ""
echo "✅ Deployment ready!"
echo ""
echo "📝 Next steps:"
echo "1. Deploy 'dist' folder to your hosting service"
echo "2. Configure environment variables if needed"
echo "3. Set up HTTPS for production"
echo "4. Configure CORS and security headers"
echo ""
echo "🌐 Deployment options:"
echo "  - Vercel:  vercel deploy"
echo "  - Netlify: netlify deploy --prod --dir=dist"
echo "  - AWS S3:  aws s3 sync dist/ s3://your-bucket/"
echo "  - Docker:  docker build -t supergrok-enterprise ."
echo ""
echo "📚 See README.md for detailed instructions"
