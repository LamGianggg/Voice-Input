import numpy as np
import librosa
import csv

def extract_features(file_path):
    """
    Trích xuất các đặc trưng từ file âm thanh.
    Trả về: dict chứa các giá trị đặc trưng.
    """
    y, sr = librosa.load(file_path, sr=None)

    # 1. F0 (fundamental frequency)
    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'),
                                      fmax=librosa.note_to_hz('C7'), sr=sr)
    f0_voiced = f0[voiced_flag]
    if len(f0_voiced) == 0:
        f0_mean = f0_std = f0_range = 0.0
    else:
        f0_mean = np.mean(f0_voiced)
        f0_std = np.std(f0_voiced)
        f0_range = np.max(f0_voiced) - np.min(f0_voiced)

    # 2. Energy (RMS)
    rms = librosa.feature.rms(y=y)[0]
    energy_mean = np.mean(rms)
    energy_std = np.std(rms)

    # 3. Zero-crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    zcr_mean = np.mean(zcr)
    zcr_std = np.std(zcr)

    # 4. Spectral centroid
    spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spec_cent_mean = np.mean(spec_cent)
    spec_cent_std = np.std(spec_cent)

    # 5. Spectral flux
    spectral_flux = librosa.onset.onset_strength(y=y, sr=sr)
    spectral_flux_mean = np.mean(spectral_flux)

    # 6. MFCC (13 hệ số)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_means = np.mean(mfccs, axis=1)
    mfcc_stds = np.std(mfccs, axis=1)

    # 7. Delta MFCC (bậc 1) - chỉ lấy 6 hệ số C0..C5
    delta_mfcc = librosa.feature.delta(mfccs, order=1)
    delta_means = np.mean(delta_mfcc[:6], axis=1)
    delta_stds = np.std(delta_mfcc[:6], axis=1)

    # Tạo dictionary kết quả
    features = {
        'F0_mean': f0_mean,
        'F0_std': f0_std,
        'F0_range': f0_range,
        'Energy_mean': energy_mean,
        'Energy_std': energy_std,
        'ZCR_mean': zcr_mean,
        'ZCR_std': zcr_std,
        'Spectral_centroid_mean': spec_cent_mean,
        'Spectral_centroid_std': spec_cent_std,
        'Spectral_flux_mean': spectral_flux_mean,
    }

    # MFCC mean và std
    for i in range(13):
        features[f'MFCC_C{i}_mean'] = mfcc_means[i]
        features[f'MFCC_C{i}_std'] = mfcc_stds[i]

    # Delta MFCC mean và std
    for i in range(6):
        features[f'Delta_MFCC_C{i}_mean'] = delta_means[i]
        features[f'Delta_MFCC_C{i}_std'] = delta_stds[i]

    return features

def save_features_to_csv(features, output_csv_path):
    """Lưu dictionary features vào file CSV (một dòng) không dùng pandas."""
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=features.keys())
        writer.writeheader()
        writer.writerow(features)
    return output_csv_path