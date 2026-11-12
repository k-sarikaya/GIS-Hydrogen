import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from pyomo.environ import *

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / 'data' / 'processed' / 'rpp_local_results_summary.txt'
FIGURE_PATH = ROOT / 'figures' / 'Fig2_cost_frontier.png'

# ── 1. VERİ TANIMLAMALARI (Master: manuscript/manuscript.tex) ──
I = ['S1', 'S2', 'S3', 'S4', 'S5']
J = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8']

# Talep Düğümleri TFN (ton H2/yıl)
d_tfn = {
    'D1': (3500, 5000, 7200),
    'D2': (2100, 3200, 4800),
    'D3': (1200, 1900, 2800),
    'D4': (1800, 2700, 4000),
    'D5': (2800, 4200, 6000),
    'D6': (900, 1400, 2100),
    'D7': (500, 900, 1400),
    'D8': (1000, 1600, 2500),
}

# Tesis Açılış Maliyeti TFN (M$)
f_tfn = {
    'S1': (18, 25, 32),
    'S2': (20, 27, 35),
    'S3': (17, 24, 31),
    'S4': (21, 28, 36),
    'S5': (22, 30, 38)
}

# Tesis Üretim Kapasitesi TFN (ton H2/yıl)
cap_tfn = {
    'S1': (4000, 8500, 13000),
    'S2': (3200, 7000, 11500),
    'S3': (4200, 9000, 14000),
    'S4': (3500, 7500, 12000),
    'S5': (4500, 9500, 15000)
}

# Mesafe Matrisi (km) - Candidate Site x Demand Node
dist = {
    ('S1','D1'): 88,  ('S1','D2'): 162, ('S1','D3'): 268, ('S1','D4'): 61,  ('S1','D5'): 12,  ('S1','D6'): 394, ('S1','D7'): 512, ('S1','D8'): 390,
    ('S2','D1'): 530, ('S2','D2'): 348, ('S2','D3'): 225, ('S2','D4'): 528, ('S2','D5'): 492, ('S2','D6'): 211, ('S2','D7'): 11,  ('S2','D8'): 680,
    ('S3','D1'): 395, ('S3','D2'): 142, ('S3','D3'): 18,  ('S3','D4'): 385, ('S3','D5'): 360, ('S3','D6'): 148, ('S3','D7'): 255, ('S3','D8'): 410,
    ('S4','D1'): 498, ('S4','D2'): 415, ('S4','D3'): 480, ('S4','D4'): 398, ('S4','D5'): 468, ('S4','D6'): 685, ('S4','D7'): 712, ('S4','D8'): 14,
    ('S5','D1'): 480, ('S5','D2'): 311, ('S5','D3'): 148, ('S5','D4'): 545, ('S5','D5'): 508, ('S5','D6'): 72,  ('S5','D7'): 198, ('S5','D8'): 675,
}

# LCOH Üretim Maliyeti TFN ($/kg)
c_prod_tfn = (3.85, 4.45, 5.20)

# Taşıma Maliyeti TFN ($/kg per km)
c_truck_tfn = (0.0028, 0.0038, 0.0052)
c_pipe_tfn  = (0.0008, 0.0014, 0.0022)

def tfn_ev(a, b, c): return (a + 4*b + c) / 6.0
def tfn_var(a, b, c): return ((c - a)**2 + (b - a)*(b - c)) / 18.0
def demand_threshold(a, b, c, th, eta=0.5):
    return th * b + (1 - th) * a

c_prod_ev = tfn_ev(*c_prod_tfn)
c_truck_ev = tfn_ev(*c_truck_tfn)
c_pipe_ev  = tfn_ev(*c_pipe_tfn)

def solve_rpp_master(theta=0.85, eta=0.5, omega1=0.5, omega2=0.5, penalty=1000.0):
    d_thr = {j: demand_threshold(*d_tfn[j], th=theta, eta=eta) for j in J}

    model = ConcreteModel()
    model.I = Set(initialize=I)
    model.J = Set(initialize=J)

    model.x = Var(model.I, domain=Binary)
    model.y = Var(model.I, model.J, domain=NonNegativeReals)
    model.delta = Var(model.J, domain=NonNegativeReals)

    def objective_rule(m):
        fixed_cost = sum(tfn_ev(*f_tfn[i]) * 1e6 * m.x[i] for i in I)
        prod_cost = sum(m.y[i,j] * 1000.0 * c_prod_ev for i in I for j in J)
        trans_cost = sum(
            m.y[i,j] * 1000.0 * dist[i,j] * (c_truck_ev if dist[i,j] < 200 else c_pipe_ev)
            for i in I for j in J)
        exp_tc = fixed_cost + prod_cost + trans_cost
        viol_penalty = penalty * 1000.0 * sum(m.delta[j] for j in J)
        return omega1 * exp_tc + viol_penalty

    model.OBJ = Objective(rule=objective_rule, sense=minimize)

    def demand_rule(m, j):
        return sum(m.y[i,j] for i in I) + m.delta[j] >= d_thr[j]
    model.demand_con = Constraint(model.J, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.y[i,j] for j in J) <= cap_tfn[i][1] * m.x[i]
    model.cap_con = Constraint(model.I, rule=capacity_rule)

    solver = SolverFactory('highs')
    results = solver.solve(model, tee=False)

    open_sites = [i for i in I if value(model.x[i]) > 0.5]
    total_capacity = sum(cap_tfn[i][1] for i in open_sites)
    
    fixed_val = sum(tfn_ev(*f_tfn[i]) * value(model.x[i]) for i in I)
    prod_val  = sum(value(model.y[i,j]) * 1000.0 * c_prod_ev for i in I for j in J) / 1e6
    trans_val = sum(value(model.y[i,j]) * 1000.0 * dist[i,j] * (c_truck_ev if dist[i,j] < 200 else c_pipe_ev) for i in I for j in J) / 1e6
    expected_cost_m = fixed_val + prod_val + trans_val

    flows = [(i, j, value(model.y[i,j])) for i in I for j in J if value(model.y[i,j]) > 0.1]

    return expected_cost_m, open_sites, total_capacity, flows

if __name__ == '__main__':
    thetas = [0.75, 0.80, 0.85, 0.90, 0.95]
    print("=========================================================================")
    print(" LOCAL PYOMO RPP MODELI KOSUMU (MASTER VERSION: GH2_v3_PVGISCorrected)")
    print("=========================================================================")
    print(f"{'theta':<8} | {'Acilan Tesisler':<20} | {'Kapasite (t/yil)':<18} | {'E[Maliyet] (M$)':<15}")
    print("-" * 75)
    
    costs = []
    summary_lines = ["=== RPP MODELI YEREL ÇÖZÜM ÖZETİ (HiGHS / Pyomo) ===\n"]
    for th in thetas:
        cost_m, opened, cap, flows = solve_rpp_master(theta=th)
        costs.append(cost_m)
        sites_str = ", ".join(opened)
        line = f"theta={th:.2f} | Tesisler: {sites_str:<18} | Kapasite: {cap:6,d} t/yil | E[Maliyet]: ${cost_m:6.2f}M"
        print(f"{th:<8.2f} | {sites_str:<20} | {cap:<18,d} | ${cost_m:<14.2f}M")
        summary_lines.append(line)

    print("=========================================================================")
    
    # Detailed flows at baseline theta = 0.85
    cost_85, opened_85, cap_85, flows_85 = solve_rpp_master(theta=0.85)
    print("\n--- Onerilen Taban Senaryo (theta = 0.85) Akis Detaylari ---")
    print(f"{'Tesis (Origin)':<16} -> {'Talep Nod (Destination)':<25} | {'Miktar (ton H2/yil)':<20}")
    print("-" * 70)
    summary_lines.append("\n--- theta = 0.85 Akis Detaylari ---")
    for orig, dest, flow_val in flows_85:
        print(f"{orig:<16} -> {dest:<25} | {flow_val:12.1f} t/yil")
        summary_lines.append(f"{orig} -> {dest}: {flow_val:.1f} t/yil")
    
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"\nDetayli rapor '{SUMMARY_PATH}' dosyasina yazildi.")
    
    plt.figure(figsize=(8, 5))
    plt.plot(thetas, costs, 'o-', color='#1F4E79', linewidth=2.5, markersize=8, label='RPP Expected Cost ($M)')
    plt.axvline(0.85, color='red', linestyle='--', linewidth=1.5, label='Recommended Baseline (theta=0.85)')
    plt.title('Green Hydrogen SCN Cost-Risk Frontier (Pyomo / HiGHS Local Solver)', fontsize=12, fontweight='bold')
    plt.xlabel('Possibilistic Confidence Level (theta)', fontsize=11)
    plt.ylabel('Expected Total Cost (M$)', fontsize=11)
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_PATH, dpi=300)
    print(f"Grafik '{FIGURE_PATH}' olarak basariyla olusturuldu ve kaydedildi.")
