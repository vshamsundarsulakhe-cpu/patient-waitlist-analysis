-- Patient Waitlist analysis queries (SQLite / standard SQL)
-- Table: waitlist  (loaded from data/clean/waitlist_clean.csv)
-- Note: each Archive_Date is a month-end snapshot, so totals are summed within ONE month to get "patients waiting".

-- Q1. Total patients waiting at each month-end
SELECT Month, SUM(Total) AS patients_waiting
FROM waitlist GROUP BY Month ORDER BY Month;

-- Q2. Latest month vs same month last year (year-on-year change)
SELECT cur.patients AS latest_month, prev.patients AS prior_year_month,
       ROUND(100.0 * (cur.patients - prev.patients) / prev.patients, 1) AS yoy_pct
FROM (SELECT SUM(Total) AS patients FROM waitlist WHERE Month = '2021-03') cur,
     (SELECT SUM(Total) AS patients FROM waitlist WHERE Month = '2020-03') prev;

-- Q3. Waitlist by case type (latest month)
SELECT Case_Type, SUM(Total) AS patients_waiting,
       ROUND(100.0 * SUM(Total) / (SELECT SUM(Total) FROM waitlist WHERE Month='2021-03'), 1) AS share_pct
FROM waitlist WHERE Month = '2021-03'
GROUP BY Case_Type ORDER BY patients_waiting DESC;

-- Q4. Top 10 specialties by patients waiting (latest month)
SELECT Specialty, SUM(Total) AS patients_waiting
FROM waitlist WHERE Month = '2021-03'
GROUP BY Specialty ORDER BY patients_waiting DESC LIMIT 10;

-- Q5. Share of patients waiting 12+ months, by specialty (latest month, specialties with 2,000+ patients)
SELECT Specialty, SUM(Total) AS patients_waiting,
       SUM(CASE WHEN Long_Wait_12m_Plus = 1 THEN Total ELSE 0 END) AS waiting_12m_plus,
       ROUND(100.0 * SUM(CASE WHEN Long_Wait_12m_Plus = 1 THEN Total ELSE 0 END) / SUM(Total), 1) AS pct_12m_plus
FROM waitlist WHERE Month = '2021-03'
GROUP BY Specialty HAVING SUM(Total) >= 2000
ORDER BY pct_12m_plus DESC LIMIT 10;

-- Q6. Time-band distribution (latest month)
SELECT Time_Bands, SUM(Total) AS patients_waiting
FROM waitlist WHERE Month = '2021-03'
GROUP BY Time_Bands, Band_Order ORDER BY Band_Order;

-- Q7. Age profile of patients waiting 12+ months (latest month)
SELECT Age_Profile, SUM(Total) AS waiting_12m_plus
FROM waitlist WHERE Month = '2021-03' AND Long_Wait_12m_Plus = 1
GROUP BY Age_Profile ORDER BY waiting_12m_plus DESC;

-- Q8. Specialty group growth: first month vs latest month
SELECT a.Specialty_Group, a.patients AS jan_2018, b.patients AS mar_2021,
       ROUND(100.0 * (b.patients - a.patients) / a.patients, 1) AS growth_pct
FROM (SELECT Specialty_Group, SUM(Total) AS patients FROM waitlist WHERE Month='2018-01' GROUP BY 1) a
JOIN (SELECT Specialty_Group, SUM(Total) AS patients FROM waitlist WHERE Month='2021-03' GROUP BY 1) b USING (Specialty_Group)
ORDER BY growth_pct DESC;

-- Q9. Month-on-month change in total waitlist (window function)
WITH m AS (SELECT Month, SUM(Total) AS patients FROM waitlist GROUP BY Month)
SELECT Month, patients,
       patients - LAG(patients) OVER (ORDER BY Month) AS change_vs_prev_month
FROM m ORDER BY Month;

-- Q10. Rank specialties within each case type (latest month)
SELECT Case_Type, Specialty, patients_waiting,
       RANK() OVER (PARTITION BY Case_Type ORDER BY patients_waiting DESC) AS rank_in_case_type
FROM (SELECT Case_Type, Specialty, SUM(Total) AS patients_waiting
      FROM waitlist WHERE Month='2021-03' GROUP BY Case_Type, Specialty)
ORDER BY Case_Type, rank_in_case_type;
