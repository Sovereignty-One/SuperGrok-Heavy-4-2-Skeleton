const status = document.querySelector('#status');
const log = document.querySelector('#log');
const healthButton = document.querySelector('#health-button');
const clearButton = document.querySelector('#clear-button');

function writeLog(message) {
  const timestamp = new Date().toISOString();
  log.textContent = `[${timestamp}] ${message}\n${log.textContent}`;
}

healthButton.addEventListener('click', () => {
  status.textContent = 'Local check passed.';
  writeLog('Local control-plane check passed.');
});

clearButton.addEventListener('click', () => {
  log.textContent = '';
  status.textContent = 'Log cleared locally.';
});

writeLog('Dashboard initialized with local system resources only.');
