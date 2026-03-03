# SuperGrok Enterprise - Installation Guide

## 📋 Prerequisites

Before installation, ensure you have:

- **Node.js 18+** and npm (Download from https://nodejs.org/)
- **Git** (Download from https://git-scm.com/)
- **Modern browser** (Chrome 89+, Firefox 88+, Safari 14.1+, Edge 89+)
- **4GB RAM** minimum
- **100MB disk space**

## 🚀 Quick Start (3 Steps)

### Step 1: Extract Files

Extract the `supergrok-enterprise` folder to your desired location.

### Step 2: Install Dependencies

```bash
cd supergrok-enterprise
npm install
```

This will install all required packages (~250MB).

### Step 3: Start Development Server

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

**That's it! You're running SuperGrok Enterprise.**

---

## 📦 Production Deployment

### Option 1: Build and Deploy (Recommended)

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The `dist/` folder contains optimized production files. Deploy this folder to any static hosting service.

### Option 2: Docker Deployment

```bash
# Build Docker image
docker build -t supergrok-enterprise .

# Run container
docker run -p 3000:80 supergrok-enterprise

# Or use docker-compose
docker-compose up -d
```

Access at http://localhost:3000

### Option 3: Automated Deployment Script

```bash
# Make script executable (Linux/Mac)
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

This script will:
- Check prerequisites
- Install dependencies
- Run linter
- Build production bundle
- Test the build
- Show deployment options

---

## 🌐 Hosting Options

### Vercel (Easiest)

```bash
npm install -g vercel
vercel deploy
```

### Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### AWS S3 + CloudFront

```bash
# Install AWS CLI
# Configure credentials: aws configure

# Sync to S3
aws s3 sync dist/ s3://your-bucket-name/

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Nginx (Self-Hosted)

```bash
# Build
npm run build

# Copy to nginx root
sudo cp -r dist/* /var/www/html/

# Restart nginx
sudo systemctl restart nginx
```

### Apache (Self-Hosted)

```bash
# Build
npm run build

# Copy to apache root
sudo cp -r dist/* /var/www/html/

# Create .htaccess for SPA routing
cat > dist/.htaccess << EOF
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
EOF

# Restart apache
sudo systemctl restart apache2
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in root:

```env
VITE_API_URL=https://api.your-domain.com
VITE_APP_NAME=SuperGrok Enterprise
VITE_VERSION=1.0.0
```

### Custom Branding

Edit `src/App.jsx`:

```javascript
// Line 185: Change title
<h1 className="text-4xl font-bold text-white mb-2">
  🧠 Your Company Name
</h1>
```

Edit `tailwind.config.js` for colors:

```javascript
theme: {
  extend: {
    colors: {
      primary: '#your-color',
    }
  }
}
```

---

## 🐛 Troubleshooting

### Issue: `npm install` fails

**Solution:**
```bash
# Clear cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Issue: Port 3000 already in use

**Solution:**
```bash
# Use different port
npm run dev -- --port 3001
```

Or kill process on port 3000:
```bash
# Linux/Mac
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Issue: Build fails with memory error

**Solution:**
```bash
# Increase Node memory
NODE_OPTIONS=--max-old-space-size=4096 npm run build
```

### Issue: Crypto operations not working

**Possible causes:**
1. Not using HTTPS (required for Web Crypto API in production)
2. Older browser without Web Crypto support
3. Browser privacy settings blocking crypto

**Solution:**
- Use localhost for development (http://localhost works)
- Deploy with HTTPS in production
- Update browser to latest version
- Check browser console for errors

### Issue: Voice input not working

**Requirements:**
- HTTPS connection (or localhost)
- Microphone permissions granted
- Chrome or Edge browser (best support)

**Solution:**
```bash
# Check microphone access in browser settings
# Try localhost instead of 127.0.0.1
# Grant microphone permissions when prompted
```

---

## 📊 Performance Optimization

### 1. Enable Production Mode

Always build with production mode:
```bash
npm run build
```

Never use `npm run dev` in production.

### 2. Enable Server Compression

**Nginx:**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

**Apache:**
```apache
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript
</IfModule>
```

### 3. Use CDN

Upload `dist/assets/*` to CDN and update paths.

### 4. Enable HTTP/2

Configure your web server for HTTP/2.

### 5. Implement Caching

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 🔒 Security Checklist

- [ ] Deploy with HTTPS
- [ ] Configure Content Security Policy headers
- [ ] Enable CORS properly
- [ ] Set secure cookie flags
- [ ] Implement rate limiting
- [ ] Enable HTTP Strict Transport Security (HSTS)
- [ ] Regular dependency updates: `npm audit fix`
- [ ] Monitor logs for suspicious activity

---

## 📱 Mobile Deployment

### iOS (TestFlight)

Use Capacitor:
```bash
npm install @capacitor/cli @capacitor/core @capacitor/ios
npx cap init
npx cap add ios
npm run build
npx cap copy
npx cap open ios
```

### Android (Google Play)

```bash
npm install @capacitor/cli @capacitor/core @capacitor/android
npx cap init
npx cap add android
npm run build
npx cap copy
npx cap open android
```

---

## 🔄 Updates

### Update Dependencies

```bash
# Check for updates
npm outdated

# Update all (careful!)
npm update

# Update specific package
npm install package-name@latest
```

### Update SuperGrok

```bash
# Pull latest changes
git pull origin main

# Install new dependencies
npm install

# Rebuild
npm run build
```

---

## 📞 Support

### Getting Help

1. Check this guide
2. Check README.md
3. Search GitHub Issues
4. Create new issue with:
   - Error message
   - Steps to reproduce
   - Browser/OS version
   - Screenshot if applicable

### Common Commands

```bash
# Development
npm run dev              # Start dev server
npm run build           # Build production
npm run preview         # Preview production build
npm run lint            # Run linter

# Docker
docker build -t supergrok .        # Build image
docker run -p 3000:80 supergrok   # Run container
docker-compose up -d               # Run with compose
docker-compose logs -f             # View logs

# Deployment
./deploy.sh             # Automated deployment
vercel deploy          # Deploy to Vercel
netlify deploy --prod  # Deploy to Netlify
```

---

## ✅ Verification

After installation, verify:

1. ✅ Dashboard loads at http://localhost:3000
2. ✅ All tabs are accessible
3. ✅ Can generate SHA3-512 hash
4. ✅ Can generate QR keys
5. ✅ Can export backend files
6. ✅ Logs show system activity
7. ✅ No console errors

Test cryptography:
1. Go to "Crypto Tools" tab
2. Enter "test" in SHA3-512 input
3. Click "Generate SHA3-512"
4. Should see hash output

Test key generation:
1. Go to "QR Keys" tab
2. Click "Generate Post-Quantum Key"
3. Should see key with Falcon-512, ChaCha20, Dilithium3

---

## 🎓 Next Steps

1. **Explore Features**: Try all tabs and features
2. **Customize**: Edit colors, branding, content
3. **Deploy**: Choose hosting option and deploy
4. **Monitor**: Set up logging and monitoring
5. **Scale**: Add load balancing if needed

---

**Need help? Create an issue on GitHub with detailed information about your problem.**

**Ready for production? Run `./deploy.sh` to prepare your deployment.**
