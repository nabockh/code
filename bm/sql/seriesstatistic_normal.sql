CREATE OR REPLACE FUNCTION benchmark_aggregate(IN bm_id INTEGER)
  RETURNS INTEGER AS $$
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
  point1              INTEGER;
  point2              INTEGER;
  count1              INTEGER;
  count2              INTEGER;
  i                   INTEGER;
  a_point             RECORD;
    curs CURSOR (bid INTEGER) FOR
    SELECT
      generate_series(r.min, r.max) AS "point",
      count(1)
    FROM
      "bm_responserange" AS "r"
      INNER JOIN "bm_questionresponse"
        ON "bm_questionresponse"."id" = "r"."response_id"
      INNER JOIN "bm_question"
        ON "bm_question"."id" = "bm_questionresponse"."question_id"
      INNER JOIN "bm_benchmark"
        ON "bm_benchmark"."id" = "bm_question"."benchmark_id"
    WHERE "bm_benchmark"."id" = bid
    GROUP BY "point"
    ORDER BY "point";
BEGIN
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
      stddev("rn".value)
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
    v_groups_count := 3;
    from_ := a_point.min;
    to_ := a_point.max - from_;
    IF to_/v_groups_count = 1 THEN
      v_groups_count := 2;
    END IF;
    to_ := to_ + (v_groups_count - to_%v_groups_count);
    v_groups_step := CEIL(to_/v_groups_count::float)::INTEGER;
    INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "value")
      (
        WITH ranges AS (
          SELECT
            s::text||'-'||(s + v_groups_step - 1)::text as "range",
            s as "r_min",
            s + v_groups_step - 1 as "r_max"
          FROM generate_series(from_, to_, v_groups_step) AS s)
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
  IF type_ = 5
  THEN
    i := 0;
    FOR a_point IN curs(bm_id) LOOP
      IF i = 0
      THEN
        i := 1;
        point1 := a_point.point;
        point2 := point1;
        count1 := a_point.count;
      ELSE
        IF a_point.count != count1
        THEN
          INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
          VALUES (bm_id, point1, point2, count1);
          count1 := a_point.count;
          point1 := a_point.point;
        END IF;
        point2 := a_point.point;
        count2 := a_point.count;
      END IF;
    END LOOP;
    INSERT INTO "bm_seriesstatistic" ("benchmark_id", "series", "sub_series", "value")
    VALUES (bm_id, point1, point2, count2);
  END IF;
  RETURN bm_id;
END;
$$ LANGUAGE plpgsql;