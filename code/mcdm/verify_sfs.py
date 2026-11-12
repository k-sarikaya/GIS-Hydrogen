# verify_sfs.py
# Spherical Fuzzy Set (SFS) 1-7 Likert Mapping & Monotonicity Verification

sfs_mapping = {
    1: ("Çok Düşük / Very Low",         0.10, 0.90, 0.10),
    2: ("Düşük / Low",                 0.25, 0.70, 0.40),
    3: ("Orta-Düşük / Fairly Low",      0.40, 0.55, 0.50),
    4: ("Orta / Medium",               0.50, 0.45, 0.55),
    5: ("Orta-Yüksek / Fairly High",    0.65, 0.30, 0.50),
    6: ("Yüksek / High",               0.80, 0.15, 0.40),
    7: ("Çok Yüksek / Very High",       0.90, 0.10, 0.10)
}

print(f"{'Puan':<5} | {'Dilsel Karşılık':<25} | {'mu':<5} | {'nu':<5} | {'pi':<5} | {'mu^2+nu^2+pi^2':<15} | {'Score':<10} | {'Geçerli mi?'}")
print("-" * 90)

scores = []
for score_val, (label, m, v, p) in sfs_mapping.items():
    sum_sq = m**2 + v**2 + p**2
    is_valid = sum_sq <= 1.0
    # Gündoğdu & Kahraman (2019) Score Function: (mu - nu)^2 * (1 - pi^2)
    # or signed score: (mu - nu) for directionality
    defuzz_score = (m - v)**2 * (1 - p**2) if m >= v else -((m - v)**2 * (1 - p**2))
    scores.append(defuzz_score)
    print(f"{score_val:<5} | {label:<25} | {m:<5.2f} | {v:<5.2f} | {p:<5.2f} | {sum_sq:<15.4f} | {defuzz_score:<10.4f} | {'EVET [OK]' if is_valid else 'HAYIR [ERR]'}")

is_strictly_increasing = all(scores[i] < scores[i+1] for i in range(len(scores)-1))
print("-" * 90)
print(f"Monotonik Artanlik Durumu: {'BASARILI (Strictly Monotonic) [OK]' if is_strictly_increasing else 'HATA [ERR]'}")
