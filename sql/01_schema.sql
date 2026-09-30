-- Restaurant Guest Analytics: schema (SQLite; standard SQL)
-- All data is simulated. One upscale 90-seat NYC dinner restaurant with a bar, 16 weeks.

DROP TABLE IF EXISTS service_nights;
CREATE TABLE service_nights (
    week                    INTEGER,
    day                     TEXT,
    peak_night              INTEGER,   -- 1 = Thu, Fri or Sat
    covers                  INTEGER,
    reservations            INTEGER,
    walk_ins                INTEGER,
    waitlist                INTEGER,
    servers                 INTEGER,
    bartenders              INTEGER,
    covers_per_server       REAL,
    avg_ticket_minutes      REAL,      -- order to food on the table
    avg_drink_wait_minutes  REAL,
    bev_revenue             REAL,
    food_revenue            REAL,
    total_revenue           REAL,
    PRIMARY KEY (week, day)
);

DROP TABLE IF EXISTS guest_feedback;
CREATE TABLE guest_feedback (
    feedback_id  INTEGER PRIMARY KEY,
    week         INTEGER,
    day          TEXT,
    source       TEXT,      -- post-visit survey, Google, Resy, Instagram DM
    rating       INTEGER,   -- 1 to 5
    topic        TEXT,      -- main thing the guest talked about
    sentiment    TEXT
);

DROP TABLE IF EXISTS bar_pos_sales;
CREATE TABLE bar_pos_sales (
    week            INTEGER,
    day             TEXT,
    item            TEXT,
    category        TEXT,
    units           INTEGER,
    pos_unit_price  REAL,     -- what the POS actually charged
    pos_revenue     REAL
);

DROP TABLE IF EXISTS beverage_price_list;
CREATE TABLE beverage_price_list (
    item                  TEXT,
    category              TEXT,
    price                 REAL,     -- approved menu price
    effective_from_week   INTEGER,
    effective_to_week     INTEGER
);
