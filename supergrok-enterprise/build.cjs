const fs = require('node:fs');
const path = require('node:path');

const root = __dirname;
const dist = path.join(root, 'dist');

if (fs.existsSync(dist)) fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });
fs.cpSync(path.join(root, 'index.html'), path.join(dist, 'index.html'));
fs.cpSync(path.join(root, 'src'), path.join(dist, 'src'), { recursive: true });
fs.cpSync(path.join(root, 'nginx.conf'), path.join(dist, 'nginx.conf'));

console.log(`Local frontend copied to ${dist}`);
