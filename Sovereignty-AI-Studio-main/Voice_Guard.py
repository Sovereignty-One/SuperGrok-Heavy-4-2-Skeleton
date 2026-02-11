# voice_guard.py – deepfake check, offline only
import librosa
import numpy as np
from models import load_detector  # from soundproofai gutted

def is_deepfake(file):
    # load audio raw
    y, sr = librosa.load(file, sr=16000, duration=5)  # 5 sec clip
    # features: mfcc, chroma, spectral contrast
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    spec = librosa.feature.spectral_contrast(y=y, sr=sr)

    X = np.stack((mfcc.mean(1), chroma.mean(1), spec.mean(1)))

    detector = load_detector()  # local .h5 model
    score = detector.predict(X.reshape(1, -1))[0]

    return score > 0.7  # 70% = fake
