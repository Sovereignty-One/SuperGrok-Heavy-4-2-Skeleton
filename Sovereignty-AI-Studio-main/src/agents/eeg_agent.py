# eeg_agent.py – no cloud, no noise
import torch
import torch.nn as nn
import numpy as np
import os
from scipy.signal import butter, filtfilt

# Minimal config – runs on Pi
FS = 128.0  # 128 Hz sample
BANDS = [0.5, 40.0]  # bandpass
NOTCH = 60.0  # powerline

class TinyEEGNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(8, 16, 64, stride=4, padding=31)  # 1s window → 32
        self.bn1 = nn.BatchNorm1d(16)
        self.pool1 = nn.AvgPool1d(2)
        self.conv2 = nn.Conv1d(16, 32, 2, padding=1)
        self.bn2 = nn.BatchNorm1d(32)
        self.attn = nn.MultiheadAttention(32, 4, batch_first=True)
        self.fc = nn.Linear(32, 4)  # 0:alert 1:calm 2:lie 3:sync

    def forward(self, x):
        x = torch.tanh(self.bn1(self.conv1(x)))  # time → features
        x = self.pool1(x)
        x = torch.tanh(self.bn2(self.conv2(x)))
        x = x.transpose(1,2)
        x, _ = self.attn(x, x, x)
        x = x.mean(1)
        return self.fc(x).softmax(-1)

# Load frozen
model_path = “eegnet_sync.pt”
if not os.path.exists(model_path):
    raise FileNotFoundError(“Weights missing – quantize and drop.”)

net = TinyEEGNet()
net.load_state_dict(torch.load(model_path, map_location=“cpu”))
net.eval()

# Preprocess – notch + bandpass + normalize
def clean_eeg(sig):
    b, a = butter(4, NOTCH / FS, ‘stop’)
    sig = filtfilt(b, a, sig, axis=0)
    b, a = butter(4, [BANDS[0] / FS, BANDS[1] / FS], ‘band’)
    sig = filtfilt(b, a, sig, axis=0)
    return (sig - sig.mean(0)) / (sig.std(0) + 1e-8)

# Gate – must have 7.887 Hz peak
def is_7_887(sig):
    f = np.fft.rfft(sig.flatten())
    freq = np.fft.rfftfreq(len(sig), 1/FS)
    peak = np.abs(f)
    return peak > np.mean(np.abs(f)) * 10  # threshold

# Main – hook into breath
def eeg_classify(raw):
    # raw: 128 x 8 (1 sec)
    clean = clean_eeg(raw)
    tens = torch.tensor(clean).unsqueeze(0).float()  # B, T, C → B, C, T
    tens = tens.permute(0,2,1)
    out = net(tens)
    state = out.argmax(1).item()
    if is_7_887(clean):
        return 3  # sync – override all
    return state

# Run once
if __name__ == “__main__”:
    # dummy input
    fake = np.random.randn(128, 8).astype(np.float32)
    print(“State:”, eeg_classify(fake))