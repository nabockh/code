CREATE OR REPLACE FUNCTION benchmark_aggregate (bm_id int4)
  RETURNS int4
AS
$BODY$
  DECLARE
  type_               INTEGER;
  from_               INTEGER;
  to_                 INTEGER;
  rank                VARCHAR;
  position            INTEGER;
  avaliable_ranks     VARCHAR [];
  avaliable_positions INTEGER [];
  aggregated_rank     RECORD;
  v_groups_count      INTEGER;
  v_groups_step       INTEGER;
  point1              RECORD;
  point2              RECORD;
  i                   INTEGER;
  a_point             RECORD;
  curs CURSOR (bid INTEGER) FOR
  select 
    point, 
    (select count(*) from 
                    "bm_responserange" AS "r"
                    INNER JOIN "bm_questionresponse"
                      ON "bm_questionresponse"."id" = "r"."response_id"
                    INNER JOIN "bm_question"
                      ON "bm_question"."id" = "bm_questionresponse"."question_id"
                    INNER JOIN "bm_benchmark"
                      ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
         WHERE "bm_benchmark"."id" = bid and
           point between r.min and r.max)
  from (
    SELECT
      generate_series(min(r.min), max(r.max)) AS "point"
    FROM
      "bm_responserange" AS "r"
      INNER JOIN "bm_questionresponse"
        ON "bm_questionresponse"."id" = "r"."response_id"
      INNER JOIN "bm_question"
        ON "bm_question"."id" = "bm_questionresponse"."question_id"
      INNER JOIN "bm_benchmark"
        ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
    WHERE "bm_benchmark"."id" = bid
  ) as points;
BEGIN
  DELETE FROM "bm_seriesstatistic" WHERE "benchmark_id"=bm_id;
  DELETE FROM "bm_numericstatistic" WHERE "benchmark_id"=bm_id;
  SELECT
    "bm_question"."type"
  INTO type_
  FROM "bm_question"
    INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
  WHERE "bm_benchmark"."id" = bm_id;
  IF type_ = 1
  THEN
    INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "value")
      (
        SELECT
          bm_id,
          "bm_questionchoice"."label",
          count("bm_responsechoice"."choice_id")
        FROM "bm_responsechoice"
          INNER JOIN "bm_questionresponse" ON "bm_questionresponse"."id" = "bm_responsechoice"."response_id"
          INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionresponse"."question_id"
          INNER JOIN "bm_questionchoice" ON "bm_question"."id" = "bm_questionchoice"."question_id"
          INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
        WHERE
          "bm_benchmark"."id" = bm_id AND "bm_responsechoice"."choice_id" = "bm_questionchoice"."id"
        GROUP BY "bm_questionchoice"."label"
      );
  END IF;
  IF type_ = 2
  THEN
    DROP TABLE IF EXISTS temp_aggregate_ranking;
    CREATE TEMPORARY TABLE temp_aggregate_ranking
    (
      "benchmark_id" INTEGER NOT NULL,
      "rank_title"   VARCHAR NOT NULL,
      "value"        INTEGER NOT NULL,
      "count"        INTEGER NOT NULL
    )
    ON COMMIT DELETE ROWS;

    INSERT INTO "temp_aggregate_ranking"
      (
        SELECT
          bm_id,
          "bm_questionranking"."label",
          "bm_responseranking"."value",
          count("bm_responseranking"."rank_id")
        FROM "bm_responseranking"
          INNER JOIN "bm_questionresponse" ON "bm_questionresponse"."id" = "bm_responseranking"."response_id"
          INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionresponse"."question_id"
          INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
          INNER JOIN "bm_questionranking" ON "bm_question"."id" = "bm_questionranking"."question_id"
        WHERE "bm_benchmark"."id" = bm_id AND "bm_responseranking"."rank_id" = "bm_questionranking"."id"
        GROUP BY "bm_questionranking"."label", "bm_responseranking"."value"
        ORDER BY "bm_questionranking"."label", "bm_responseranking"."value"
      );

    SELECT
      array_agg("bm_questionranking".label)
    INTO avaliable_ranks
    FROM "bm_questionranking"
      INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionranking"."question_id"
      INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
    WHERE "bm_benchmark"."id" = bm_id;

    SELECT
      array_agg("bm_questionranking".order - 1)
    INTO avaliable_positions
    FROM "bm_questionranking"
      INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionranking"."question_id"
      INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
    WHERE "bm_benchmark"."id" = bm_id;

    FOREACH rank IN ARRAY avaliable_ranks LOOP
      FOREACH position IN ARRAY avaliable_positions LOOP
        SELECT
          *
        INTO aggregated_rank
        FROM "temp_aggregate_ranking"
        WHERE "rank_title" = rank AND "value" = position;
        IF NOT FOUND
        THEN
          INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
          VALUES (bm_id, rank, position + 1, 0);
        ELSE
          INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
          VALUES (aggregated_rank.benchmark_id, aggregated_rank.rank_title, aggregated_rank.value + 1,
                  aggregated_rank.count);
        END IF;
      END LOOP;
    END LOOP;
  END IF;
  IF type_ = 3
  THEN
    SELECT
      bm_id as "benchmark_id",
      min("rn".value),
      max("rn".value),
      avg("rn".value),
      stddev("rn".value),
      count("rn".value)
    INTO a_point
    FROM "bm_responsenumeric" AS "rn"
      INNER JOIN "bm_questionresponse" ON "bm_questionresponse"."id" = "rn"."response_id"
      INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionresponse"."question_id"
      INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
    WHERE "bm_benchmark"."id" = bm_id;
    INSERT INTO "bm_numericstatistic" ("benchmark_id", "min", "max", "avg", "sd")
      VALUES (
        a_point.benchmark_id, a_point.min, a_point.max, a_point.avg, a_point.stddev
      );

    v_groups_count := LEAST(10, a_point.count);
    INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "value")
      (
        WITH ranges AS (
          SELECT
            "r_min"::text||'-'||"r_max"::text as "range",
            r_min,
            r_max
          FROM (
            SELECT lag("lowest", 1, -1) over(order by "lowest") + 1 as "r_min", greatest("lowest", "highest") as "r_max" from (
              SELECT DISTINCT
                lowest, highest
              FROM (SELECT
                      count("response_id"),
                      min("value") AS "lowest",
                      max("value") AS "highest",
                      "r_rank"
                    FROM (SELECT "rn"."response_id", "rn"."value",
                                 ntile(v_groups_count) OVER (ORDER BY "value") AS "r_rank"
                           FROM bm_responsenumeric rn
                              INNER JOIN "bm_questionresponse" ON "bm_questionresponse"."id" = "rn"."response_id"
                              INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionresponse"."question_id"
                              INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
                           WHERE "bm_benchmark"."id" = bm_id
                         ) AS ranked
                    GROUP BY ranked.r_rank
                    ORDER BY "lowest"
                   ) AS uniq
              ) as range
            ) AS s)
        SELECT
          bm_id,
          r.range,
          count(rn.value)
        FROM ranges r
          INNER JOIN bm_responsenumeric rn ON rn.value BETWEEN r.r_min AND r.r_max
          INNER JOIN "bm_questionresponse" ON "bm_questionresponse"."id" = "rn"."response_id"
          INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionresponse"."question_id"
          INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
        WHERE "bm_benchmark"."id" = bm_id
        GROUP BY r.range
      );

  END IF;
  IF type_ = 4
  THEN
    INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "value")
      (
        SELECT
          bm_id,
          CASE WHEN "bm_responseyesno"."value" THEN 'Yes' ELSE 'No' END,
          count(1)
        FROM "bm_responseyesno"
          INNER JOIN "bm_questionresponse" ON "bm_questionresponse"."id" = "bm_responseyesno"."response_id"
          INNER JOIN "bm_question" ON "bm_question"."id" = "bm_questionresponse"."question_id"
          INNER JOIN "bm_benchmark" ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
        WHERE
          "bm_benchmark"."id" = bm_id
        GROUP BY "bm_responseyesno"."value"
      );
  END IF;
  IF type_ = 5
  THEN
    i := 0;
    FOR a_point IN curs(bm_id) LOOP
      IF i = 0
      THEN
        i := 1;
        point1 := a_point;
        point2 := point1;
      ELSE
        IF a_point.count != point1.count 
        THEN
          IF point2.count = 0
          THEN
            INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
            VALUES (bm_id, point2.point, point2.point, point2.count);  
            point1 := a_point;
          ELSE
            IF a_point.count > point1.count
            THEN
              point2 = a_point;
            END IF; 
            INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
            VALUES (bm_id, point1.point, point2.point, point1.count);
            IF a_point.count < point1.count 
            THEN
              point1 := point2;
              point1.count := a_point.count;
            ELSE
              point1 := a_point;
            END IF;
          END IF;
        END IF;
        point2 := a_point;
      END IF;
    END LOOP;
    INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
    VALUES (bm_id, point1.point, point2.point, point2.count);
  END IF;
  RETURN bm_id;
END;
$BODY$
LANGUAGE plpgsql VOLATILE;
