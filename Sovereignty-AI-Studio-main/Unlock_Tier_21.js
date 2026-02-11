// =============================
// Module: Logging & Internationalization
// Purpose: Provides text translation (i18n) and user-facing logging utilities
// =============================
export const messages = {
  en: {
    secureHashFail: "Unable to generate secure hash.",
    blake3Fail: "Failed to compute checksum.",
    sealFail: "Failed to encrypt file.",
    falconFail: "Error applying Falcon512 mask.",
    dilithiumFail: "Error applying Dilithium mask.",
    resistFail: "Post-quantum wrapping failed.",
    unlockFail: "Unlock failed. Please try again.",
    showFail: "Unable to display file.",
    accessDenied: "Access denied. Please verify your credentials.",
    retryPrompt: "Would you like to retry?"
  }
};

let currentLang = 'en';

/**
 * Translate a key based on the current language.
 * @param {string} key - The translation key
 * @returns {string} The translated string or key if not found
 */
export function t(key) {
  return messages[currentLang][key] || key;
}

/**
 * Create a status message element in the DOM.
 * @param {string} text - The message text
 * @param {string} type - 'info' or 'error'
 */
function addStatusMessage(text, type = 'info') {
  const div = document.createElement('div');
  div.style.margin = '4px 0';
  div.style.padding = '4px 8px';
  div.style.borderRadius = '4px';
  div.style.fontFamily = 'sans-serif';
  div.style.fontSize = '14px';
  div.style.background = type === 'error' ? '#ffe6e6' : '#e6ffe6';
  div.style.color = type === 'error' ? '#cc0000' : '#006600';
  div.innerText = text;
  document.body.appendChild(div);
}

/**
 * Log an info message to console and DOM.
 * @param {string} message
 */
export function logInfo(message) {
  console.log(`ℹ️ ${message}`);
  addStatusMessage(message, 'info');
}

/**
 * Log an error message to console and DOM with optional retry.
 * @param {string} message
 * @param {Error} err
 * @param {Function} retryCallback
 */
export function logError(message, err, retryCallback) {
  console.error(`❌ ${message}`, err);
  addStatusMessage(message, 'error');
  if (confirm(`${message}\n${t('retryPrompt')}`)) {
    if (retryCallback) retryCallback();
  }
}

// =============================
// Module: Biometric Helpers
// Purpose: Simulate hash collection from biometric data
// =============================

/**
 * Mock function to collect and encode voice sample
 */
async function hashVoice() {
  return new TextEncoder().encode('voice-sample');
}

/**
 * Mock function to collect and encode fingerprint sample
 */
async function hashFinger() {
  return new TextEncoder().encode('finger-sample');
}

// =============================
// Module: Cryptographic Functions
// Purpose: Handle hashing, encryption, and post-quantum wrapping
// =============================

/**
 * Derive a secure hash from input bytes using PBKDF2-SHA512.
 */
export async function secureHash(input) {
  try {
    logInfo("[secureHash] Starting derivation");
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const keyMaterial = await window.crypto.subtle.importKey(
      "raw",
      input,
      { name: "PBKDF2" },
      false,
      ["deriveBits"]
    );
    const key = await window.crypto.subtle.deriveBits(
      {
        name: "PBKDF2",
        hash: "SHA3-512",
        salt: salt,
        iterations: 100000
      },
      keyMaterial,
      512
    );
    logInfo("[secureHash] Derivation complete");
    return key;
  } catch (err) {
    logError(t('secureHashFail'), err);
    throw new Error("Secure hash derivation failed");
  }
}

/**
 * Compute a 32-byte digest of data using SHA3-512 (simulating Blake3).
 */
export async function blake3(data) {
  try {
    logInfo("[blake3] Starting digest");
    const ctx = await crypto.subtle.digest('SHA3-512', data);
    logInfo("[blake3] Digest complete");
    return ctx.slice(0, 32);
  } catch (err) {
    logError(t('blake3Fail'), err);
    throw new Error("Blake3 digest failed");
  }
}

/**
 * Encrypt input blob using AES-GCM with a derived seed.
 */
export async function seal(blob, key) {
  try {
    logInfo("[seal] Encrypting file");
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const cryptoKey = await window.crypto.subtle.importKey(
      "raw",
      key,
      { name: "AES-GCM" },
      false,
      ["encrypt"]
    );
    const cipher = await window.crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv: iv
      },
      cryptoKey,
      blob
    );
    logInfo("[seal] File successfully encrypted");
    return { cipher, iv };
  } catch (err) {
    logError(t('sealFail'), err);
    throw new Error("Seal encryption failed");
  }
}

/**
 * Apply a simple XOR mask to simulate Falcon512 wrapping.
 */
export async function falcon512Wrap(key) {
  try {
    logInfo("[falcon512Wrap] Applying Falcon512 mask");
    return Uint8Array.from(key).map(x => x ^ 0xA5);
  } catch (err) {
    logError(t('falconFail'), err);
    throw new Error("Falcon512 wrap failed");
  }
}

/**
 * Apply a simple XOR mask to simulate Dilithium wrapping.
 */
export async function dilithiumWrap(key) {
  try {
    logInfo("[dilithiumWrap] Applying Dilithium mask");
    return Uint8Array.from(key).map(x => x ^ 0x5A);
  } catch (err) {
    logError(t('dilithiumFail'), err);
    throw new Error("Dilithium wrap failed");
  }
}

/**
 * Perform sequential Falcon512 and Dilithium wrapping.
 */
export async function resistWrap(key) {
  try {
    logInfo("[resistWrap] Starting post-quantum encapsulation");
    const falconKey = await falcon512Wrap(key);
    const dilithiumKey = await dilithiumWrap(falconKey);
    logInfo("[resistWrap] Encapsulation complete");
    return dilithiumKey;
  } catch (err) {
    logError(t('resistFail'), err);
    throw new Error("Post-quantum wrapping failed");
  }
}

/**
 * Combine voice and fingerprint hashes, derive seed, encrypt file, and apply wrapping.
 */
export async function unlockTier(file) {
  try {
    logInfo("[unlockTier] Collecting biometric hashes");
    const voice = await hashVoice();
    const finger = await hashFinger();

    const [voiceHash, fingerHash] = await Promise.all([
      secureHash(voice),
      secureHash(finger)
    ]);

    logInfo("[unlockTier] Generating secure seed");
    const seedSource = new Uint8Array([
      ...new Uint8Array(voiceHash),
      ...new Uint8Array(fingerHash)
    ]);

    const seed = await blake3(seedSource);
    const session = await seal(file, seed);
    const final = await resistWrap(session.cipher);

    logInfo("[unlockTier] Tier 21 unlock successful");
    return { sealed: final, iv: session.iv, tier: 21 };
  } catch (err) {
    logError(t('unlockFail'), err, () => unlockTier(file));
    return { sealed: null, iv: null, tier: 0 };
  }
}

// =============================
// DOM Interaction Functions
// Purpose: Display encrypted content in the browser
// =============================

/**
 * Attempt to unlock and display an adult file as an image.
 */
export async function showAdult(file) {
  try {
    logInfo("[showAdult] Attempting to unlock tier");
    const { sealed } = await unlockTier(file);
    if (!sealed) {
      alert(t('accessDenied'));
      return;
    }

    const blob = new Blob([sealed], { type: file.type });
    const url = URL.createObjectURL(blob);
    document.body.innerHTML += `<img src="${url}" style="max-width:100%; border:1px solid #333; border-radius:8px;">`;
    logInfo("[showAdult] File displayed successfully");
  } catch (err) {
    logError(t('showFail'), err, () => showAdult(file));
  }
}
