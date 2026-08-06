import { PostQuantumCrypto } from './services/crypto.js';

const status = document.querySelector('#status');
const log = document.querySelector('#log');
const healthButton = document.querySelector('#health-button');
const clearButton = document.querySelector('#clear-button');

function writeLog(message) {
  const timestamp = new Date().toISOString();
  log.textContent = `[${timestamp}] ${message}\n${log.textContent}`;
}

healthButton.addEventListener('click', async () => {
  status.textContent = 'Running local check…';
  try {
    const proof = await PostQuantumCrypto.sha3_512('supergrok-local-health-' + Date.now());
    status.textContent = 'Local check passed.';
    writeLog('Local control-plane check passed. SHA-512 proof: ' + proof.slice(0, 16) + '…');
  } catch (err) {
    status.textContent = 'Local check failed: ' + err.message;
    writeLog('ERROR: ' + err.message);
  }
});

clearButton.addEventListener('click', () => {
  log.textContent = '';
  status.textContent = 'Log cleared locally.';
});

writeLog('Dashboard initialized with local system resources only.');
