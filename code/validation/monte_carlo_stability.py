import numpy as np
from scipy.stats import spearmanr
import sys

# Baseline WASPAS skorları (Aşama II'den alınır)
baseline_scores = {'S1':0.832,'S2':0.637,'S3':0.734,'S4':0.691,'S5':0.799}
baseline_rank   = sorted(baseline_scores, key=baseline_scores.get, reverse=True)
print(f"Baseline Rank: {baseline_rank}")

N = 10_000

for sigma_rel in [0.05, 0.10, 0.15, 0.20]:
    si_count = 0
    rpr_count = 0
    
    for _ in range(N):
        perturbed = { k: v*(1 + np.random.normal(0, sigma_rel))
                      for k, v in baseline_scores.items() }
        rank = sorted(perturbed, key=perturbed.get, reverse=True)
        if rank[0] == baseline_rank[0]:
            si_count += 1
        if rank == baseline_rank:
            rpr_count += 1
            
    SI  = si_count / N
    RPR = rpr_count  / N
    
    cert = "GECERLI" if (SI>=0.90 and RPR>=0.85) else "BASARISIZ"
    print(f"sigma = {sigma_rel*100:0.0f}% | SI = {SI:.3f} | RPR = {RPR:.3f} | Sertifika: {cert}")
