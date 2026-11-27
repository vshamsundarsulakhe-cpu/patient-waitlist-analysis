"""Clean and combine the raw Inpatient / Outpatient waitlist files into one table.

Run from the repo root:  python src/clean_data.py
Output: data/clean/waitlist_clean.csv
"""
import glob
import os

import pandas as pd

RAW = "data/raw"
OUT = "data/clean/waitlist_clean.csv"

BAND_ORDER = ["0-3 Months", "3-6 Months", "6-9 Months", "9-12 Months",
              "12-15 Months", "15-18 Months", "18+ Months"]


def load_inpatient():
    frames = []
    for f in sorted(glob.glob(f"{RAW}/IN_WL *.csv")):
        d = pd.read_csv(f, encoding="utf-8-sig")
        d = d.loc[:, ~d.columns.str.startswith("Unnamed")]  # 2018 file has a trailing empty column
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    return d.rename(columns={"Specialty_Name": "Specialty"})


def load_outpatient():
    frames = [pd.read_csv(f, encoding="utf-8-sig") for f in sorted(glob.glob(f"{RAW}/Op_WL *.csv"))]
    d = pd.concat(frames, ignore_index=True)
    d = d.rename(columns={"Speciality": "Specialty"})
    d["Case_Type"] = "Outpatient"  # outpatient files have no case type column
    return d


def main():
    inp, outp = load_inpatient(), load_outpatient()
    raw_rows = len(inp) + len(outp)

    cols = ["Archive_Date", "Specialty_HIPE", "Specialty", "Case_Type",
            "Adult_Child", "Age_Profile", "Time_Bands", "Total"]
    df = pd.concat([inp[cols], outp[cols]], ignore_index=True)

    # trim all text columns
    for c in ["Specialty", "Case_Type", "Adult_Child", "Age_Profile", "Time_Bands"]:
        df[c] = df[c].astype("string").str.strip()

    # standardise labels
    df["Time_Bands"] = df["Time_Bands"].replace({"18 Months +": "18+ Months"})
    df["Adult_Child"] = df["Adult_Child"].replace({"": pd.NA})

    # types
    df["Archive_Date"] = pd.to_datetime(df["Archive_Date"], format="%d-%m-%Y")
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce")

    # drop rows that cannot be used (missing band / age / count)
    before = len(df)
    df = df.dropna(subset=["Time_Bands", "Age_Profile", "Total"])
    dropped = before - len(df)

    # specialty group mapping
    mp = pd.read_csv(f"{RAW}/Mapping_Specialty.csv")
    mp["Specialty"] = mp["Specialty"].str.strip()
    mp = mp.rename(columns={"Specialty Group": "Specialty_Group"})
    df = df.merge(mp, on="Specialty", how="left")
    df["Specialty_Group"] = df["Specialty_Group"].fillna("Other / Unmapped")

    # helper columns
    df["Year"] = df["Archive_Date"].dt.year
    df["Month"] = df["Archive_Date"].dt.to_period("M").astype(str)
    df["Band_Order"] = df["Time_Bands"].map({b: i + 1 for i, b in enumerate(BAND_ORDER)})
    df["Long_Wait_12m_Plus"] = df["Band_Order"] >= 5  # 12+ months

    df = df.sort_values(["Archive_Date", "Case_Type", "Specialty"]).reset_index(drop=True)
    os.makedirs("data/clean", exist_ok=True)
    df.to_csv(OUT, index=False)

    print(f"Raw rows: {raw_rows:,} | dropped (missing band/age/total): {dropped:,} | clean rows: {len(df):,}")
    print("Case types:", df["Case_Type"].value_counts().to_dict())
    print("Time bands:", sorted(df["Time_Bands"].unique(), key=BAND_ORDER.index))
    print("Unmapped specialties:", sorted(df.loc[df.Specialty_Group == "Other / Unmapped", "Specialty"].unique()))
    print("Date range:", df.Archive_Date.min().date(), "->", df.Archive_Date.max().date())


if __name__ == "__main__":
    main()
