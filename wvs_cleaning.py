"""
WVS Data Cleaning Script
========================
This script cleans and merges the World Values Survey (WVS) data
for new waves (wave 7), preparing it for multilevel analysis.

The statistical models (multilevel mixed effects) are run separately in Stata.

Author: Olena Bedasheva
Date: 2023
"""

# ==========================================
# LIBRARIES
# ==========================================
import pandas as pd       # for working with data tables
import numpy as np        # for mathematical operations
import wbdata             # for downloading World Bank data


# ==========================================
# SECTION 1 - LOADING AND FILTERING DATA
# ==========================================

# load the WVS dataset
df = pd.read_stata("WVS_TimeSeries_stata_v1_6.dta")

# keep only wave 7 (new waves)
df = df[df["S002"] == 7]

# recode country codes
df.loc[df["S003"] == 891, "S003"] = 688   # Serbia
df.loc[df["S003"] == 914, "S003"] = 70    # Bosnia

# rename year variable
df = df.rename(columns={"S020": "year"})

# sort by country and year
df = df.sort_values(["S003", "year"])

# merge with country codes file
codes = pd.read_stata("1codes.dta")
df = df.merge(codes, on="S003", how="left")

# drop rows where S002 is missing
df = df[df["S002"].notna()]


# ==========================================
# SECTION 2 - GENERATING ID VARIABLES
# ==========================================

# convert numbers to text so we can combine them
df["iso_code"] = df["S003"].astype(str)
df["year1"] = df["year"].astype(str)

# create combined country-year identifier
df["isoyear"] = df["iso_code"] + df["year1"]
df["n_isoyear"] = df["alpha2"] + df["year1"]


# ==========================================
# SECTION 3 - INDIVIDUAL LEVEL VARIABLES
# ==========================================

# income group (valid values: 1-10)
df["income"] = df["X047"].where((df["X047"] > 0) & (df["X047"] < 11))

# employment status
df["employment"] = df["X028"].where((df["X028"] > 0) & (df["X028"] < 8))

# employed = 1 if working, 0 if not working, None if missing
df["employed"] = df["employment"].apply(
    lambda x: 1 if x in [1, 2, 3] else (0 if x in [4, 5, 6, 7] else None)
)

# gender (1 = male, 2 = female)
df["gender"] = df["X001"].where(df["X001"] > 0)

# marital status (1 = married/living together, 0 = otherwise)
df["marital"] = None
df.loc[df["X007"].isin([1, 2]), "marital"] = 1
df.loc[df["X007"].isin([3, 4, 5, 6]), "marital"] = 0

# education (age at which completed education)
df["educ_year"] = df["X023"].where(df["X023"] >= 0)

# age in years
df = df.rename(columns={"X003": "age_years"})

# age squared
df["age2"] = df["age_years"] ** 2


# ==========================================
# SECTION 4 - VARIABLE LABELS
# ==========================================
# Note: Python has no built-in label system like Stata.
# We define label dictionaries for use in tables and plots.

income_labels = {
    1: "lower step", 2: "second step", 3: "third step",
    4: "fourth step", 5: "fifth step", 6: "sixth step",
    7: "seventh step", 8: "eighth step", 9: "ninth step",
    10: "highest step"
}

gender_labels = {1: "Male", 2: "Female"}

# create labeled versions of the columns (useful for plots and tables)
df["income_labeled"] = df["income"].map(income_labels)
df["gender_labeled"] = df["gender"].map(gender_labels)


# ==========================================
# SECTION 5 - ORGANISATION MEMBERSHIP (DV)
# ==========================================

# --- membership (active + inactive) ---
# dictionary: new column name → source column
orgs = {
    "social":      "A105",   # social and welfare
    "environment": "A103",   # environment
    "culture":     "A100",   # culture and education
    "prof":        "A104",   # professional
    "union":       "A101",   # union
}

# loop through each organisation and create binary variable
for name, col in orgs.items():
    df[name] = np.where(
        df[col].isin([1, 2]), 1,        # member (active or inactive) → 1
        np.where(df[col] == 0, 0,       # not a member → 0
        np.nan)                         # missing → NaN
    )

# total membership count (robust to missing values)
org_cols = list(orgs.keys())
df["totalorg"] = df[org_cols].sum(axis=1, min_count=1)

# dichotomous version: 0 = no membership, 1 = at least one
df["totalorg2"] = df["totalorg"].apply(
    lambda x: 1 if x >= 1 else (0 if x == 0 else None)
)

# verify the recode
print("Crosstab totalorg vs totalorg2:")
print(pd.crosstab(df["totalorg2"], df["totalorg"]))


# --- active membership only ---
# dictionary: new column name → source column
active_orgs = {
    "social_A":      "A105",
    "environment_A": "A103",
    "culture_A":     "A100",
    "prof_A":        "A104",
    "union_A":       "A101",
}

# loop through each organisation
for new_col, source_col in active_orgs.items():
    df[new_col] = df[source_col].apply(
        lambda x: 1 if x == 2 else (0 if x in [0, 1] else None)
        # only active members (==2) get a 1
        # inactive (==1) and non-members (==0) get 0
    )

# total active membership count
active_cols = list(active_orgs.keys())
df["totalACTIVE"] = df[active_cols].sum(axis=1, min_count=1)

# sanity check: active should always be <= total membership
print("\nCrosstab totalorg vs totalACTIVE:")
print(pd.crosstab(df["totalorg"], df["totalACTIVE"]))


# ==========================================
# SECTION 6 - KEEP RELEVANT VARIABLES
# ==========================================

keep_cols = [
    "S002", "S003", "iso_code", "year", "year1",
    "alpha2", "alpha3", "isoyear", "n_isoyear",
    "income", "employment", "employed", "gender", "marital",
    "educ_year", "age_years", "age2",
    "social", "environment", "culture", "prof", "union",
    "totalorg", "totalorg2",
    "social_A", "environment_A", "culture_A", "prof_A", "union_A",
    "totalACTIVE"
]

df = df[keep_cols]

# save intermediate dataset
df.to_stata("newwavesdata.dta", write_index=False)
print("\nSaved: newwavesdata.dta")


# ==========================================
# SECTION 7 - MERGE WITH INSTITUTIONS
# ==========================================

df = df.sort_values("alpha2")

institutions = pd.read_stata("institutions.dta")
df = df.merge(institutions, on="alpha2", how="left")

# drop rows where S003 is missing after merge
df = df[df["S003"].notna()]


# ==========================================
# SECTION 8 - YEAR OF INDEPENDENCE
# ==========================================

df = df.sort_values(["alpha3", "year"])

independence = pd.read_stata("independence.dta")
df = df.merge(independence, on="alpha3", how="left")

# convert to numeric (no need for decode/destring workaround like in Stata)
df["corrected_y_indep"] = pd.to_numeric(df["y_independence"], errors="coerce")

# manual corrections for specific countries (S003 code → correct year)
corrections = {
    250: 1816,   # France
    268: 1991,   # Georgia
    440: 1991,   # Lithuania
    222: 1875,   # El Salvador
    688: 2006,   # Serbia
    643: 1991,   # Russia
    762: 1991,   # Tajikistan
    104: 1948,   # Myanmar
}

# apply corrections using a loop
for country_code, year_value in corrections.items():
    df.loc[df["S003"] == country_code, "corrected_y_indep"] = year_value

# log of independence year
df["log_indep"] = np.log(df["corrected_y_indep"] + 1)


# ==========================================
# SECTION 9 - GDP PER CAPITA (WORLD BANK)
# ==========================================

# download GDP per capita (constant 2015 USD) from World Bank API
indicator = {"NY.GDP.PCAP.KD": "gdp"}
df_gdp = wbdata.get_dataframe(indicator, convert_date=True)
df_gdp = df_gdp.reset_index()
df_gdp = df_gdp.rename(columns={"country": "alpha3", "date": "year"})

# drop missing values
df_gdp = df_gdp.dropna(subset=["gdp"])

# keep from 1981 onwards
df_gdp = df_gdp[df_gdp["year"] >= 1981]
df_gdp = df_gdp[df_gdp["year"] <= 2020]

# log of GDP
df_gdp["gdplog"] = np.log(df_gdp["gdp"])
df_gdp["gdplog"].attrs["description"] = "GDP per capita log"

# forward fill missing values within each country
# (use previous year's value if current year is missing)
df_gdp = df_gdp.sort_values(["alpha3", "year"])
df_gdp["gdp"] = df_gdp.groupby("alpha3")["gdp"].ffill()
df_gdp["gdplog"] = df_gdp.groupby("alpha3")["gdplog"].ffill()

# save GDP data
df_gdp.to_stata("gdpdataup2020.dta", write_index=False)
print("Saved: gdpdataup2020.dta")

# merge GDP into main dataset
df = df.merge(df_gdp, on=["alpha3", "year"], how="left")

# drop specific territories not in main dataset
df = df[~df["S003"].isin([344, 446, 158])]  # Hong Kong, Macao, Taiwan

df.to_stata("newwaves_gdp_inst_indep.dta", write_index=False)
print("Saved: newwaves_gdp_inst_indep.dta")


# ==========================================
# SECTION 10 - DICTATORSHIP DURATION VARIABLES
# ==========================================

df_dict = pd.read_stata("dictatorship_years_lviv.dta")

# create logged versions of dictatorship duration variables
# (+1 avoids log(0) for countries with zero years of dictatorship)
cols_to_log = ["authocrdur", "count_personal", "count_military", "count_party"]
new_names   = ["logdictator", "log_personal",  "log_military",   "log_party"]

for old, new in zip(cols_to_log, new_names):
    df_dict[new] = np.log(df_dict[old] + 1)

df_dict.to_stata("dictatorship_with_boix.dta", write_index=False)
print("Saved: dictatorship_with_boix.dta")


# ==========================================
# SECTION 11 - APPENDING OLD AND NEW WAVES
# ==========================================

# load old waves
df_old = pd.read_stata("dataformodelsWVS.dta")

# fix independence year coding issue
df_old["corrected_y_indep"] = pd.to_numeric(df_old["y_independence"], errors="coerce")

# manual corrections for old waves too
for country_code, year_value in corrections.items():
    df_old.loc[df_old["S003"] == country_code, "corrected_y_indep"] = year_value

df_old["log_indep"] = np.log(df_old["corrected_y_indep"] + 1)

df_old.to_stata("oldwaves.dta", write_index=False)

# append new waves
df_new = pd.read_stata("newwaves_gdp_inst_indep.dta")
df_all = pd.concat([df_old, df_new], ignore_index=True)
df_all = df_all.sort_values(["S003", "year"])

# merge with dictatorship data
df_dict_merge = pd.read_stata("dictatorship_with_boix.dta")
df_all = df_all.merge(df_dict_merge, on=["S003", "year"], how="left")

# correlation checks
print("\nCorrelation checks:")
corr_vars = ["logdictator", "gdplog", "democra_new", "stat", "corp"]
corr_vars_present = [v for v in corr_vars if v in df_all.columns]
print(df_all[corr_vars_present].corr().round(4))

# save final dataset
df_all.to_stata("all_waves_lviv.dta", write_index=False)
print("\nSaved: all_waves_lviv.dta")
print("\nDone! Ready for Stata models.")
