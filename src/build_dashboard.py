"""Build the interactive HTML dashboard (dashboard/index.html) from the clean data.

Run from the repo root:  python src/build_dashboard.py
The page is fully self-contained (no internet or libraries needed): data is embedded as JSON.
"""
import json

import pandas as pd

BAND_ORDER = ["0-3 Months", "3-6 Months", "6-9 Months", "9-12 Months",
              "12-15 Months", "15-18 Months", "18+ Months"]
AGES = ["0-15", "16-64", "65+"]
CASES = ["Outpatient", "Day Case", "Inpatient"]


def main():
    df = pd.read_csv("data/clean/waitlist_clean.csv", parse_dates=["Archive_Date"])
    months = sorted(df["Month"].unique())
    groups = sorted(df["Specialty_Group"].unique())
    specs = sorted(df["Specialty"].unique())
    spec_group = df.drop_duplicates("Specialty").set_index("Specialty")["Specialty_Group"]

    mi = {m: i for i, m in enumerate(months)}
    gi = {g: i for i, g in enumerate(groups)}
    si = {s: i for i, s in enumerate(specs)}

    a = (df.groupby(["Month", "Case_Type", "Specialty_Group", "Age_Profile", "Time_Bands"], as_index=False)["Total"].sum())
    A = [[mi[r.Month], CASES.index(r.Case_Type), gi[r.Specialty_Group], AGES.index(r.Age_Profile),
          BAND_ORDER.index(r.Time_Bands), int(r.Total)] for r in a.itertuples()]

    df["long"] = df["Long_Wait_12m_Plus"].astype(int) * df["Total"]
    b = df.groupby(["Month", "Case_Type", "Specialty"], as_index=False)[["Total", "long"]].sum()
    B = [[mi[r.Month], CASES.index(r.Case_Type), si[r.Specialty], int(r.Total), int(r.long)] for r in b.itertuples()]

    data = {"months": months, "cases": CASES, "groups": groups, "ages": AGES, "bands": BAND_ORDER,
            "specs": specs, "specGroup": [gi[spec_group[s]] for s in specs], "A": A, "B": B}

    html = open("src/dashboard_template.html", encoding="utf-8").read()
    html = html.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    with open("dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"dashboard/index.html written ({len(html)/1024:.0f} KB, {len(A):,} + {len(B):,} data rows)")


if __name__ == "__main__":
    main()
