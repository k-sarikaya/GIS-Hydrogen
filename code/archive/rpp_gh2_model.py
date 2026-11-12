from pyomo.environ import *
import numpy as np

# ── 1. VERİ TANIMLAMALARI ─────────────────────────────────────
I = ['S1','S2','S3','S4','S5']
J = ['D1','D2','D3','D4','D5','D6','D7','D8']

d_tfn = {
  'D1':(3500,5000,7200), 'D2':(2100,3200,4800), 'D3':(1400,2100,3100),
  'D4':(1800,2700,4000), 'D5':(2800,4200,6000), 'D6':(900,1400,2100),
  'D7':(600,1000,1600),  'D8':(800,1200,1800),
}

cap_tfn = {'S1':(4000,8500,13000),'S2':(3200,7000,11500),
           'S3':(4200,9000,14000),'S4':(3500,7500,12000),'S5':(4500,9500,15000)}

dist = {
  ('S1','D1'):320,('S1','D2'):162,('S1','D3'):168,('S1','D4'):248,
  ('S1','D5'):248,('S1','D6'):294,('S1','D7'):312,('S1','D8'):390,
  ('S2','D1'):490,('S2','D2'):0,  ('S2','D3'):205,('S2','D4'):328,
  ('S2','D5'):342,('S2','D6'):311,('S2','D7'):418,('S2','D8'):480,
  ('S3','D1'):395,('S3','D2'):205,('S3','D3'):0,  ('S3','D4'):420,
  ('S3','D5'):395,('S3','D6'):148,('S3','D7'):255,('S3','D8'):310,
  ('S4','D1'):298,('S4','D2'):215,('S4','D3'):280,('S4','D4'):198,
  ('S4','D5'):168,('S4','D6'):385,('S4','D7'):412,('S4','D8'):465,
  ('S5','D1'):480,('S5','D2'):311,('S5','D3'):148,('S5','D4'):545,
  ('S5','D5'):508,('S5','D6'):80, ('S5','D7'):198,('S5','D8'):175,
}

c_truck_tfn = (0.0028, 0.0038, 0.0052)
c_pipe_tfn  = (0.0008, 0.0014, 0.0022)

f_tfn = {'S1':(18,25,32),'S2':(20,27,35),'S3':(17,24,31),
         'S4':(21,28,36),'S5':(22,30,38)}

def tfn_ev(a,b,c): return (a + 4*b + c) / 6
def tfn_var(a,b,c): return ((c-a)**2 + (b-a)*(b-c)) / 18
def demand_threshold(a,b,c,th): return th * b + (1-th) * a

d_ev  = {j: tfn_ev(*d_tfn[j])  for j in J}
d_var = {j: tfn_var(*d_tfn[j]) for j in J}

ct_ev = tfn_ev(*c_truck_tfn)
cp_ev = tfn_ev(*c_pipe_tfn)
ct_var= tfn_var(*c_truck_tfn)

def solve_rpp(theta=0.85):
    d_thr = {j: demand_threshold(*d_tfn[j],theta) for j in J}

    model = ConcreteModel()
    model.I = Set(initialize=I)
    model.J = Set(initialize=J)

    model.x = Var(model.I, domain=Binary)
    model.y = Var(model.I, model.J, domain=NonNegativeReals)
    model.delta = Var(model.J, domain=NonNegativeReals)

    omega1, omega2, penalty = 0.5, 0.5, 1000.0

    def objective_rule(m):
        fixed_cost = sum(tfn_ev(*f_tfn[i]) * 1e6 * m.x[i] for i in I)
        transport_ev = sum(
            m.y[i,j] * 1000 * dist[i,j] * (ct_ev if dist[i,j]<200 else cp_ev)
            for i in I for j in J)
        transport_var = omega2 * sum(
            m.y[i,j] * 1000 * dist[i,j] * ct_var
            for i in I for j in J)
        viol_penalty = penalty * 1000 * sum(m.delta[j] for j in J)
        return omega1*(fixed_cost + transport_ev) + transport_var + viol_penalty
    
    model.OBJ = Objective(rule=objective_rule, sense=minimize)

    def demand_rule(m, j):
        return sum(m.y[i,j] for i in I) + m.delta[j] >= d_thr[j]
    model.demand_con = Constraint(model.J, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.y[i,j] for j in J) <= cap_tfn[i][1] * m.x[i]
    model.cap_con = Constraint(model.I, rule=capacity_rule)

    model.min_fac = Constraint(expr=sum(model.x[i] for i in I) >= 2)

    solver = SolverFactory('highs')
    result = solver.solve(model, tee=False)

    total_cost = value(model.OBJ) / 1e6
    opened = [i for i in I if value(model.x[i]) > 0.5]
    flows = []
    for i in I:
        for j in J:
            if value(model.y[i,j]) > 0.01:
                flows.append((i, j, value(model.y[i,j])))
    
    return total_cost, opened, flows

if __name__ == '__main__':
    cost, opened, flows = solve_rpp(0.85)
    print('\n=== SONUÇLAR (theta=0.85) ===')
    print('Açılan tesisler:', opened)
    print('Toplam maliyet (M$):', round(cost, 2))
    for i, j, flow in flows:
        print(f'  {i} -> {j}: {flow:.0f} t/yil')
