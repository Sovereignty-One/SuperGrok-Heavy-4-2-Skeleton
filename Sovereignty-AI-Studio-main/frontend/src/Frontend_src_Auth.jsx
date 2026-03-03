import { useState } from 'react';

function Auth({ onLogin }) {
  const = useState("");
  const = useState("");
  const = useState("");

  const handleSign = async () => {
    // Simulate: generate sig locally (real would be wasm)
    const payload = `${Date.now()}:admin`;
    const kp = await loadPQCrypto(); // from your loader
    const signature = await kp.dilithium.sign(new TextEncoder().encode(payload), kp.privateKey);
    setSig(signature.hex());
  };

  const login = async () => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ pubkey, signature: sig, totp_code: totp })
    });

    if (res.ok) {
      const { token } = await res.json();
      onLogin(token);  // pass to App, store in state
    } else {
      alert("Login failed");
    }
  };

  return (
    <div>
      <input placeholder="Pubkey hex" onChange={e => setPubkey(e.target.value)} />
      <button onClick={handleSign}>Sign Payload</button>
      <input placeholder="TOTP Code" onChange={e => setTotp(e.target.value)} />
      <button onClick={login}>Log In</button>
    </div>
  );
}
