-- Починка прав Superset (Apache Superset 6.1.0, метабаза PostgreSQL)
--
-- Симптом, который это лечит:
--   POST /api/v1/chart/data  -> 403
--   "This endpoint requires the datasource N, database or `all_datasource_access` permission"
--
-- Причина: метабаза Superset была восстановлена из дампа без последовательностей
-- (sequence) для колонок id в таблицах прав Flask-AppBuilder. Приложение не может
-- вставить новое право и молча теряет `datasource_access` для новых наборов данных,
-- поэтому доступ есть только у того, что успело попасть в дамп.
--
-- Запуск (от root на wmssql-analytics):
--   docker exec -i superset-db psql -U superset -d superset < fix_fab_permissions.sql
--
-- Проверка после запуска:
--   docker exec superset-db psql -U superset -d superset -c \
--     "select count(*) from ab_permission_view_role where role_id=1"
--   -> должно вырасти на число наборов данных
--   затем перезапустить Superset: docker restart superset

-- 1. Вернуть последовательности таблицам прав.
DO $$
DECLARE
    t text;
    has_default text;
BEGIN
    FOREACH t IN ARRAY ARRAY['ab_view_menu','ab_permission_view','ab_permission_view_role',
                             'ab_permission','ab_role','ab_user','ab_user_role']
    LOOP
        SELECT coalesce(column_default, '') INTO has_default
        FROM information_schema.columns
        WHERE table_name = t AND column_name = 'id';

        IF has_default = '' THEN
            EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %I_id_seq', t);
            EXECUTE format('ALTER TABLE %I ALTER COLUMN id SET DEFAULT nextval(%L)', t, t || '_id_seq');
            EXECUTE format('SELECT setval(%L, coalesce((SELECT max(id) FROM %I), 1))', t || '_id_seq', t);
            RAISE NOTICE '%: последовательность привязана', t;
        END IF;
    END LOOP;
END $$;

-- 2. Выдать права datasource_access на каждый набор данных ролям Admin (1) и Public (2).
--    perm у набора — строка вида "[LV_MERIDIAN (WMS)].[dm_stock](id:10)".
DO $$
DECLARE
    ds record;
    perm_id int;
    view_id int;
    pv_id int;
BEGIN
    SELECT id INTO perm_id FROM ab_permission WHERE name = 'datasource_access' LIMIT 1;

    FOR ds IN SELECT id, perm FROM tables WHERE perm IS NOT NULL LOOP
        INSERT INTO ab_view_menu (name)
        SELECT ds.perm WHERE NOT EXISTS (SELECT 1 FROM ab_view_menu WHERE name = ds.perm);
        SELECT id INTO view_id FROM ab_view_menu WHERE name = ds.perm LIMIT 1;

        INSERT INTO ab_permission_view (permission_id, view_menu_id)
        SELECT perm_id, view_id
        WHERE NOT EXISTS (SELECT 1 FROM ab_permission_view
                          WHERE permission_id = perm_id AND view_menu_id = view_id);
        SELECT id INTO pv_id FROM ab_permission_view
        WHERE permission_id = perm_id AND view_menu_id = view_id LIMIT 1;

        INSERT INTO ab_permission_view_role (permission_view_id, role_id)
        SELECT pv_id, x
        FROM unnest(ARRAY[1, 2]) AS x
        WHERE NOT EXISTS (
            SELECT 1 FROM ab_permission_view_role pr
            WHERE pr.permission_view_id = pv_id AND pr.role_id = x
        );
    END LOOP;
END $$;
