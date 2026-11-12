import matplotlib.pyplot as plt
from rpp_gh2_model import solve_rpp

thetas = [0.75, 0.80, 0.85, 0.90, 0.95]
costs = []
print("Theta vs Maliyet:")
for th in thetas:
    cost, opened, flows = solve_rpp(th)
    costs.append(cost)
    print(f"theta={th:.2f} | Açılan: {opened} | Maliyet: {cost:.2f} M$")

plt.plot(thetas, costs, 'o-', color='#1F4E79', linewidth=2)
plt.axvline(0.85, color='red', ls='--', label='Önerilen θ=0.85')
plt.xlabel('Olasılık Güven Düzeyi (θ)')
plt.ylabel('Beklenen Toplam Maliyet (M$)')
plt.title('Robustluk–Maliyet Sınırı (Cost-Risk Frontier)')
plt.legend(); plt.grid(True); plt.tight_layout()
plt.savefig('cost_frontier.png', dpi=300)
print("Grafik 'cost_frontier.png' olarak kaydedildi.")
