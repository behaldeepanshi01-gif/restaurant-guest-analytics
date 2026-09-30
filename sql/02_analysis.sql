-- Restaurant Guest Analytics: analysis queries
-- The fix went live in week 11. "Before" = weeks 7-10, "After" = weeks 12-16.

-- Q1. Engagement vs satisfaction, week by week: is the room getting fuller while guests get less happy?
SELECT n.week,
       SUM(n.covers)                                   AS covers,
       SUM(n.reservations)                             AS reservations,
       SUM(n.waitlist)                                 AS waitlist,
       f.responses,
       f.avg_rating,
       f.pct_4_or_5_stars
FROM service_nights n
JOIN (SELECT week,
             COUNT(*)                                          AS responses,
             ROUND(AVG(rating), 2)                             AS avg_rating,
             ROUND(100.0 * AVG(CASE WHEN rating >= 4 THEN 1 ELSE 0 END), 1) AS pct_4_or_5_stars
      FROM guest_feedback GROUP BY week) f ON f.week = n.week
GROUP BY n.week
ORDER BY n.week;

-- Q2. Where does the rating break? Rating by how many covers each server carried that night
SELECT CASE WHEN n.covers_per_server <= 26 THEN '1. Up to 26'
            WHEN n.covers_per_server <= 30 THEN '2. 26-30'
            WHEN n.covers_per_server <= 34 THEN '3. 30-34'
            ELSE '4. Over 34' END                     AS covers_per_server_band,
       COUNT(DISTINCT n.week || n.day)                 AS nights,
       ROUND(AVG(n.avg_ticket_minutes), 1)             AS avg_ticket_minutes,
       COUNT(f.feedback_id)                            AS responses,
       ROUND(AVG(f.rating), 2)                         AS avg_rating
FROM service_nights n
JOIN guest_feedback f ON f.week = n.week AND f.day = n.day
GROUP BY covers_per_server_band
ORDER BY covers_per_server_band;

-- Q3. What are unhappy guests (1 to 3 stars) talking about? Before vs after the fix
SELECT topic,
       ROUND(100.0 * SUM(CASE WHEN week BETWEEN 7 AND 10 THEN 1 ELSE 0 END)
             / (SELECT COUNT(*) FROM guest_feedback WHERE rating <= 3 AND week BETWEEN 7 AND 10), 1) AS pct_of_complaints_before,
       ROUND(100.0 * SUM(CASE WHEN week >= 12 THEN 1 ELSE 0 END)
             / (SELECT COUNT(*) FROM guest_feedback WHERE rating <= 3 AND week >= 12), 1)            AS pct_of_complaints_after
FROM guest_feedback
WHERE rating <= 3
GROUP BY topic
ORDER BY pct_of_complaints_before DESC;

-- Q4. Before vs after the fix
WITH p AS (
    SELECT n.*, CASE WHEN n.week BETWEEN 7 AND 10 THEN 'Before (wk 7-10)'
                     WHEN n.week >= 12 THEN 'After (wk 12-16)' END AS period
    FROM service_nights n
)
SELECT p.period,
       ROUND(AVG(p.covers), 0)                             AS covers_per_night,
       ROUND(AVG(p.covers_per_server), 1)                  AS covers_per_server,
       ROUND(AVG(p.avg_ticket_minutes), 1)                 AS ticket_minutes,
       ROUND(AVG(p.avg_drink_wait_minutes), 1)             AS drink_wait_minutes,
       ROUND(SUM(p.total_revenue) / SUM(p.covers), 2)      AS revenue_per_cover,
       (SELECT ROUND(AVG(f.rating), 2) FROM guest_feedback f
         WHERE (p.period LIKE 'Before%' AND f.week BETWEEN 7 AND 10)
            OR (p.period LIKE 'After%'  AND f.week >= 12))  AS avg_rating
FROM p
WHERE p.period IS NOT NULL
GROUP BY p.period
ORDER BY p.period DESC;

-- Q5. Bar POS vs approved beverage price list: is the POS charging what it should? (weekly)
WITH chk AS (
    SELECT s.week, s.item, s.category, s.units, s.pos_unit_price, p.price AS approved_price,
           s.units * (p.price - s.pos_unit_price) AS revenue_gap
    FROM bar_pos_sales s
    JOIN beverage_price_list p
      ON p.item = s.item AND s.week BETWEEN p.effective_from_week AND p.effective_to_week
)
SELECT week,
       ROUND(SUM(revenue_gap), 0)                                AS revenue_gap,
       SUM(CASE WHEN revenue_gap > 0 THEN units ELSE 0 END)      AS undercharged_drinks,
       COUNT(DISTINCT CASE WHEN revenue_gap > 0 THEN item END)   AS items_affected
FROM chk
GROUP BY week
HAVING SUM(revenue_gap) <> 0
ORDER BY week;

-- Q6. Which drinks? (the gap sits only on spirits: wine, beer and zero-proof are fine)
WITH chk AS (
    SELECT s.item, s.category, s.units, s.pos_unit_price, p.price AS approved_price,
           s.units * (p.price - s.pos_unit_price) AS revenue_gap
    FROM bar_pos_sales s
    JOIN beverage_price_list p
      ON p.item = s.item AND s.week BETWEEN p.effective_from_week AND p.effective_to_week
)
SELECT category, item,
       MIN(pos_unit_price)        AS pos_price_charged,
       MAX(approved_price)        AS approved_price,
       SUM(units)                 AS drinks_undercharged,
       ROUND(SUM(revenue_gap), 0) AS revenue_gap
FROM chk
WHERE revenue_gap > 0
GROUP BY category, item
ORDER BY revenue_gap DESC;

-- Q7. What did the fixes cost, and what did they bring back? (per 4 weeks, after the fix)
--     Staff cost assumptions: $220 per server shift, $240 per bartender shift (wages, tip share, taxes)
WITH base AS (   -- staffing before the fix, by day of week
    SELECT day, MAX(servers) AS base_servers, MAX(bartenders) AS base_bartenders
    FROM service_nights WHERE week < 11 GROUP BY day
),
extra AS (
    SELECT SUM(n.servers - b.base_servers)       AS extra_server_shifts,
           SUM(n.bartenders - b.base_bartenders) AS extra_bartender_shifts,
           COUNT(DISTINCT n.week)                AS weeks
    FROM service_nights n JOIN base b ON b.day = n.day
    WHERE n.week >= 12
),
gap AS (         -- spirits revenue the POS was losing each week before the fix
    SELECT SUM(s.units * (p.price - s.pos_unit_price)) / COUNT(DISTINCT s.week) AS weekly_gap
    FROM bar_pos_sales s
    JOIN beverage_price_list p
      ON p.item = s.item AND s.week BETWEEN p.effective_from_week AND p.effective_to_week
    WHERE s.week BETWEEN 6 AND 10
)
SELECT ROUND(4.0 * e.extra_server_shifts / e.weeks, 1)                                    AS extra_server_shifts,
       ROUND(4.0 * e.extra_bartender_shifts / e.weeks, 1)                                 AS extra_bartender_shifts,
       ROUND(4.0 * (e.extra_server_shifts * 220 + e.extra_bartender_shifts * 240) / e.weeks, 0) AS extra_staff_cost,
       ROUND(4.0 * g.weekly_gap, 0)                                                        AS spirits_revenue_protected,
       ROUND(100.0 * g.weekly_gap / ((e.extra_server_shifts * 220 + e.extra_bartender_shifts * 240) / e.weeks), 0)
                                                                                           AS pct_of_staff_cost_covered
FROM extra e, gap g;
