-- Права на данные для анонимного просмотра (роль Public, id=2)
--
-- Симптом, который это лечит:
--   GET /api/v1/chart/{id}/data/ без входа -> 404 {"message":"Not found"}
--   Дашборд при этом открывается (200), но диаграммы пустые.
--
-- Причина: у роли Public нет права datasource_access ни на один набор данных.
-- Достаточно выдать его на наборы, которые используются в опубликованных
-- дашбордах.
--
-- Запуск:
--   docker exec -i superset-db psql -U superset -d superset < grant_public_data.sql
--
-- Проверка:
--   curl -s -o /dev/null -w '%{http_code}\n' \
--     http://192.168.12.202:8088/api/v1/chart/157/data/?format=json   -> 200

DO $$
DECLARE
    ds record;
    perm_id int;
    view_id int;
    pv_id int;
    granted int := 0;
BEGIN
    SELECT id INTO perm_id FROM ab_permission WHERE name = 'datasource_access' LIMIT 1;
    IF perm_id IS NULL THEN
        RAISE EXCEPTION 'нет права datasource_access в ab_permission';
    END IF;

    -- только наборы, на которые ссылаются диаграммы опубликованных дашбордов
    FOR ds IN
        SELECT DISTINCT t.id, t.perm
        FROM tables t
        JOIN slices s ON s.datasource_id = t.id
        JOIN dashboard_slices ds2 ON ds2.slice_id = s.id
        JOIN dashboards d ON d.id = ds2.dashboard_id
        WHERE t.perm IS NOT NULL AND d.published = true
        ORDER BY t.id
    LOOP
        INSERT INTO ab_view_menu (name)
        SELECT ds.perm
        WHERE NOT EXISTS (SELECT 1 FROM ab_view_menu WHERE name = ds.perm);
        SELECT id INTO view_id FROM ab_view_menu WHERE name = ds.perm LIMIT 1;

        INSERT INTO ab_permission_view (permission_id, view_menu_id)
        SELECT perm_id, view_id
        WHERE NOT EXISTS (
            SELECT 1 FROM ab_permission_view
            WHERE permission_id = perm_id AND view_menu_id = view_id
        );
        SELECT id INTO pv_id FROM ab_permission_view
        WHERE permission_id = perm_id AND view_menu_id = view_id LIMIT 1;

        INSERT INTO ab_permission_view_role (permission_view_id, role_id)
        SELECT pv_id, 2
        WHERE NOT EXISTS (
            SELECT 1 FROM ab_permission_view_role
            WHERE permission_view_id = pv_id AND role_id = 2
        );

        granted := granted + 1;
        RAISE NOTICE 'выдан доступ: набор % — %', ds.id, ds.perm;
    END LOOP;

    RAISE NOTICE 'итого наборов: %', granted;
END $$;

-- для сравнения: сколько прав datasource_access у Public стало
SELECT count(*) AS public_datasource_access
FROM ab_permission_view_role pvr
JOIN ab_permission_view pv ON pv.id = pvr.permission_view_id
JOIN ab_permission p ON p.id = pv.permission_id
WHERE pvr.role_id = 2 AND p.name = 'datasource_access';
