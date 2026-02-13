// apps/frontend/server.js
const http = require('http');
const { spawn } = require('child_process');

const server = http.createServer((req, res) => {
  if (req.url === '/intent') {
    const py = spawn('python3', );
    let data = '';
    py.stdout.on('data', (chunk) => data += chunk);
    py.on('close', () => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(data);  // JSON from Python → straight to client
    });
  } else {
    res.end('Sovereignty live.');
  }
});

server.listen(3000, () => {
  console.log('Node frontend on 3000 → talks to Python sovereign core');
});
