*===========================================================
* WVS - Mixed Effects Models
* Author: Olena Bedasheva
* Date: 2023
*
* NOTE: Data cleaning is done in Python (wvs_cleaning.py)
* This do file runs all statistical models on the final
* merged dataset produced by the Python script.
*===========================================================

use all_waves_lviv.dta, clear

*-----------------------------------------------------------
* PRELIMINARY CHECKS
*-----------------------------------------------------------

* fix Italy authocracy duration (manual correction)
replace authocrdur=22 if S003==380
replace logdictator=log(authocrdur+1) if S003==380

* correlation checks
cor logdictator gdplog
* -0.5216
cor logdictator democra_new
* -0.4776
cor logdictator stat
* 0.5589
cor logdictator corp
* 0.1227

drop democracy_duration


*===========================================================
* MAIN MODELS — Total membership (totalorg)
* 3-level structure: individuals > country-year > country
*===========================================================

* Model 1 — dictatorship duration only (logged)
eststo est5: mixed totalorg logdictator ///
    || alpha3: || isoyear:

* Model 2 — dictatorship + individual level controls (no education)
eststo est6: mixed totalorg logdictator ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* Model 3 — dictatorship + democracy + GDP + independence + individual controls
eststo est7: mixed totalorg logdictator democra_new gdplog log_indep ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* Model 4 — dichotomous DV, logistic (only 2-level: works, 3-level does not converge)
eststo est12: melogit totalorg2 logdictator log_indep gdplog democra_new ///
    income employed age_years age2 gender marital ///
    || isoyear:

* export main table
esttab est5 est6 est7 est12 using dictatorship_dur.rtf, ///
    compress se r2 ar2 label ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title(Regression table\label{tab1})


*===========================================================
* ROBUSTNESS CHECKS — Appendix models
*===========================================================

* Model: only democracies
eststo est9: mixed totalorg logdictator gdplog log_indep ///
    income employed age_years age2 gender marital ///
    if democra_new==1 ///
    || alpha3: || isoyear:

* Model: active membership only (totalACTIVE instead of totalorg)
eststo est10: mixed totalACTIVE logdictator gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* Model: dictatorship in years (not logged)
eststo est11: mixed totalorg authocrdur gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* Model: with institutions (stat and corp) — appendix
eststo est13: mixed totalorg logdictator log_indep democra_new gdplog stat corp ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* export appendix table
esttab est10 est11 est13 est9 using APPENDIX.rtf, ///
    compress se r2 ar2 label ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title(Regression table\label{tab1})


*===========================================================
* DICTATORSHIP REGIME TYPES
*===========================================================

* personal dictatorship (logged)
eststo est1: mixed totalorg log_personal gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* personal dictatorship (count)
eststo est2: mixed totalorg count_personal gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* military dictatorship (logged)
eststo est3: mixed totalorg log_military gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* military dictatorship (count)
eststo est4: mixed totalorg count_military gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* party dictatorship (logged)
eststo est5: mixed totalorg log_party gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* party dictatorship (count)
eststo est6: mixed totalorg count_party gdplog log_indep democra_new ///
    income employed age_years age2 gender marital ///
    || alpha3: || isoyear:

* export regime types table
esttab est1 est2 est3 est4 est5 est6 using dictTYPES.rtf, ///
    compress se r2 ar2 label ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title(Regression table\label{tab1})


*===========================================================
* REGIME TYPES — DEMOCRACIES ONLY
*===========================================================

eststo est7:  mixed totalorg log_personal  gdplog log_indep income employed age_years age2 gender marital if democra_new==1 || alpha3: || isoyear:
eststo est8:  mixed totalorg count_personal gdplog log_indep income employed age_years age2 gender marital if democra_new==1 || alpha3: || isoyear:
eststo est9:  mixed totalorg log_military   gdplog log_indep income employed age_years age2 gender marital if democra_new==1 || alpha3: || isoyear:
eststo est10: mixed totalorg count_military gdplog log_indep income employed age_years age2 gender marital if democra_new==1 || alpha3: || isoyear:
eststo est11: mixed totalorg log_party      gdplog log_indep income employed age_years age2 gender marital if democra_new==1 || alpha3: || isoyear:
eststo est12: mixed totalorg count_party    gdplog log_indep income employed age_years age2 gender marital if democra_new==1 || alpha3: || isoyear:

* export democracies only table
esttab est7 est8 est9 est10 est11 est12 using dicTYPes_DEMOCRACY.rtf, ///
    compress se r2 ar2 label ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title(Regression table\label{tab1})
