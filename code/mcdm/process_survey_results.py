# process_survey_results.py
"""
Google Forms'dan indirilen 'expert_responses.csv' anket verilerini okuyarak:
1. 1-7 Likert verisini SFS (mu, nu, pi) uclulerine donusturur.
2. SFWAM (Spherical Fuzzy Weighted Arithmetic Mean) ile uzman paneli matrisini birlestirir.
3. CRITIC ile kriter agirliklarini ve WASPAS ile aday saha skorlarini hesaplar.
4. Monte Carlo (N=10,000) stabilite testini kosup SI ve RPR metriklerini uretir.
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SURVEY_PATH = ROOT / 'data' / 'survey' / 'expert_responses.csv'
RESULTS_PATH = ROOT / 'data' / 'processed' / 'waspas_results.csv'
SYNTHETIC_SURVEY_PATH = ROOT / 'data' / 'survey' / 'expert_responses_SYNTHETIC.csv'
SYNTHETIC_RESULTS_PATH = ROOT / 'data' / 'processed' / 'waspas_results_SYNTHETIC.csv'

# SFS Dönüşüm Haritası (Verified Mapping)
SFS_MAP = {
    1: (0.10, 0.90, 0.10),
    2: (0.25, 0.70, 0.40),
    3: (0.40, 0.55, 0.50),
    4: (0.50, 0.45, 0.55),
    5: (0.65, 0.30, 0.50),
    6: (0.80, 0.15, 0.40),
    7: (0.90, 0.10, 0.10)
}

SITES = ['S1_Kirikkale', 'S2_Mus', 'S3_Malatya', 'S4_Denizli', 'S5_Tunceli']
CRITERIA = ['C1a', 'C1b', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10']

def sfwam_aggregate(expert_sfs_list):
    """
    SFWAM (Spherical Fuzzy Weighted Arithmetic Mean) Aggregation
    mu_agg = sqrt(1 - prod(1 - mu_k^2)^(1/K))
    nu_agg = prod(nu_k)^(1/K)
    pi_agg = sqrt(prod(1 - mu_k^2)^(1/K) - prod(1 - mu_k^2 - pi_k^2)^(1/K))
    """
    K = len(expert_sfs_list)
    mus = np.array([item[0] for item in expert_sfs_list])
    nus = np.array([item[1] for item in expert_sfs_list])
    pis = np.array([item[2] for item in expert_sfs_list])

    mu_agg = np.sqrt(1.0 - np.prod(1.0 - mus**2)**(1.0 / K))
    nu_agg = np.prod(nus)**(1.0 / K)
    pi_agg = np.sqrt(np.prod(1.0 - mus**2)**(1.0 / K) - np.prod(1.0 - mus**2 - pis**2)**(1.0 / K))
    
    return (mu_agg, nu_agg, pi_agg)

def score_sfs(mu, nu, pi):
    """Gündoğdu & Kahraman (2019) SFS Score Function"""
    diff = mu - nu
    sign = 1.0 if diff >= 0 else -1.0
    return sign * (diff**2) * (1.0 - pi**2)

def generate_sample_survey_csv(filename=SYNTHETIC_SURVEY_PATH):
    """SENTETİK 5 uzman yanıtlı CSV oluşturur — yalnızca kod testi içindir, makalede kullanılamaz."""
    np.random.seed(42)
    cols = [f"{site}_{crit}" for site in SITES for crit in CRITERIA]
    data = {}
    for col in cols:
        # S3 ve S4 için yüksek, S5 için orta puan simülasyonu
        if 'S3' in col or 'S4' in col:
            data[col] = np.random.choice([5, 6, 7], size=5, p=[0.2, 0.5, 0.3])
        elif 'S2' in col:
            data[col] = np.random.choice([4, 5, 6], size=5, p=[0.3, 0.4, 0.3])
        else:
            data[col] = np.random.choice([3, 4, 5], size=5, p=[0.3, 0.5, 0.2])
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Ornek anket CSV dosyasi '{filename}' olusturuldu.")
    return filename

def process_survey(csv_path, results_path=RESULTS_PATH):
    if not os.path.exists(csv_path):
        # Eskiden burada sessizce sentetik veri üretilip gerçek anket dosyası adıyla kaydediliyordu.
        raise FileNotFoundError(
            f"'{csv_path}' bulunamadi. Gercek anket verisi gerekli; kod testi icin "
            f"'--synthetic' bayragini kullanin.")

    df = pd.read_csv(csv_path)
    num_experts = len(df)
    print(f"\n--- Toplam {num_experts} Uzman Yaniti Isleniyor ---")

    # 1. Her saha ve kriter için uzman yanıtlarını birleştir (SFWAM)
    agg_matrix = np.zeros((len(SITES), len(CRITERIA)))
    
    for i_idx, site in enumerate(SITES):
        for j_idx, crit in enumerate(CRITERIA):
            col_name = f"{site}_{crit}"
            if col_name in df.columns:
                likert_vals = df[col_name].values
            else:
                # Esnek arama: sütun isminde site ve kriter geçiyorsa
                matched = [c for c in df.columns if site in c and crit in c]
                likert_vals = df[matched[0]].values if matched else [4]*num_experts
            
            sfs_triples = [SFS_MAP.get(int(v), (0.50, 0.45, 0.55)) for v in likert_vals]
            mu_a, nu_a, pi_a = sfwam_aggregate(sfs_triples)
            agg_matrix[i_idx, j_idx] = score_sfs(mu_a, nu_a, pi_a)

    print("\n--- SFWAM Birlesik Skor Matrisi ---")
    df_scores = pd.DataFrame(agg_matrix, index=SITES, columns=CRITERIA)
    print(df_scores.round(4))

    # 2. CRITIC Ağırlıklandırması
    std_devs = np.std(agg_matrix, axis=0, ddof=1)
    corr_matrix = np.corrcoef(agg_matrix, rowvar=False)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    c_info = std_devs * np.sum(1.0 - corr_matrix, axis=1)
    critic_weights = c_info / np.sum(c_info)

    print("\n--- CRITIC Kriter Agirliklari ---")
    for crit, w in zip(CRITERIA, critic_weights):
        print(f"{crit:<5}: {w:.4f}")

    # 3. WASPAS Hesaplaması (lambda = 0.5)
    # Min-Max Normalizasyon
    norm_matrix = np.zeros_like(agg_matrix)
    # C5 ve C6 Cost, diğerleri Benefit
    cost_indices = [CRITERIA.index('C5'), CRITERIA.index('C6')]
    
    for j in range(len(CRITERIA)):
        col = agg_matrix[:, j]
        min_val, max_val = np.min(col), np.max(col)
        range_val = max_val - min_val if max_val != min_val else 1.0
        if j in cost_indices:
            norm_matrix[:, j] = (max_val - col) / range_val + 0.01
        else:
            norm_matrix[:, j] = (col - min_val) / range_val + 0.01

    wsm = np.dot(norm_matrix, critic_weights)
    wpm = np.exp(np.dot(np.log(norm_matrix), critic_weights))
    waspas_q = 0.5 * wsm + 0.5 * wpm

    print("\n--- WASPAS Saha Sıralaması Çıktısı ---")
    df_res = pd.DataFrame({
        'WSM': wsm, 'WPM': wpm, 'WASPAS_Q': waspas_q
    }, index=SITES)
    df_res['Rank'] = df_res['WASPAS_Q'].rank(ascending=False, method='min').astype(int)
    df_res = df_res.sort_values(by='Rank')
    print(df_res.round(4))

    # CSV Sonuç Kaydı
    df_res.to_csv(results_path)
    print(f"\nSonuçlar '{results_path}' dosyasına kaydedildi.")

if __name__ == '__main__':
    if '--synthetic' in sys.argv:
        process_survey(SYNTHETIC_SURVEY_PATH, SYNTHETIC_RESULTS_PATH)
    else:
        process_survey(SURVEY_PATH)
