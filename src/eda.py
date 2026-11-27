"""Exploratory analysis: prints key findings and saves charts to images/. Run from repo root: python src/eda.py"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/clean/waitlist_clean.csv", parse_dates=["Archive_Date"])
LAST, PREV, FIRST = "2021-03", "2020-03", "2018-01"
tot = lambda d: d["Total"].sum()
snap = lambda m: df[df.Month == m]

# --- headline numbers
cur, prev, first = tot(snap(LAST)), tot(snap(PREV)), tot(snap(FIRST))
print(f"Waiting Mar-2021: {cur:,} | Mar-2020: {prev:,} | YoY {100*(cur-prev)/prev:+.1f}% | since Jan-2018 {100*(cur-first)/first:+.1f}%")
s = snap(LAST); l12 = s[s.Long_Wait_12m_Plus]; l18 = s[s.Time_Bands == "18+ Months"]
p = snap(PREV); print(f"12m+: {tot(l12):,} ({100*tot(l12)/cur:.1f}%) vs {100*tot(p[p.Long_Wait_12m_Plus])/prev:.1f}% a year earlier | 18m+: {tot(l18):,} ({100*tot(l18)/cur:.1f}%)")
print("\nCase type share:\n", (s.groupby("Case_Type")["Total"].sum() / cur * 100).round(1).to_string())
print("\n12m+ share by case type:")
for c, g in s.groupby("Case_Type"): print(f"  {c}: {100*tot(g[g.Long_Wait_12m_Plus])/tot(g):.1f}%")
print("\nAge mix of 12m+ waiters:\n", (l12.groupby("Age_Profile")["Total"].sum() / tot(l12) * 100).round(1).to_string())
sp = s.groupby("Specialty").apply(lambda g: pd.Series({"waiting": tot(g), "pct12": 100*tot(g[g.Long_Wait_12m_Plus])/tot(g)}), include_groups=False)
print("\nTop 5 specialties:\n", sp.sort_values("waiting", ascending=False).head(5).round(1).to_string())
print("\nTop 3 = share of list:", round(100*sp.sort_values("waiting", ascending=False).head(3).waiting.sum()/cur, 1), "%")

# --- charts
m = df.groupby(["Month", "Case_Type"])["Total"].sum().unstack()
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
m["Outpatient"].plot(ax=ax[0], color="#257de0", lw=2, title="Outpatient waitlist"); m[["Day Case", "Inpatient"]].plot(ax=ax[1], color=["#f47230", "#00b894"], lw=2, title="Day case & inpatient waitlists")
for a in ax: a.set_xlabel(""); a.grid(alpha=.25); a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig("images/eda_trend.png", dpi=130); plt.close()

b = s.groupby("Time_Bands")["Total"].sum().reindex(["0-3 Months","3-6 Months","6-9 Months","9-12 Months","12-15 Months","15-18 Months","18+ Months"])
b.plot.bar(color="#257de0", figsize=(7, 4), title="Patients waiting by time band (Mar 2021)"); plt.xticks(rotation=30, ha="right"); plt.xlabel(""); plt.gca().spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig("images/eda_time_bands.png", dpi=130); plt.close()
