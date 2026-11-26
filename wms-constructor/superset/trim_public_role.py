#!/usr/bin/env python3
"""Оставляет роли Public (анонимный просмотр) только права просмотра дашбордов. Выполнять ВНУТРИ контейнера:
  docker exec -i superset python - < trim_public_role.py
Идемпотентно. После `superset init` с PUBLIC_ROLE_LIKE права могут вернуться: в конфиге стоит PUBLIC_ROLE_LIKE = None."""
import re
from superset.app import create_app

app = create_app()
REMOVE_VIEWS = {"Explore", "ExploreFormDataRestApi", "ExplorePermalinkRestApi", "Database", "Datasource", "SavedQuery", "RowLevelSecurity",
                "CssTemplate", "Tag", "TagView", "UserRegistrationsRestAPI", "ResetMyPasswordView", "SwaggerView", "OpenApi", "user", "Log"}
REMOVE_PAIRS = {("Chart", "export"), ("Chart", "tag"), ("Chart", "write"), ("CurrentUserRestApi", "write"),
                ("Dashboard", "cache_dashboard_screenshot"), ("Dashboard", "delete_embedded"), ("Dashboard", "export"), ("Dashboard", "export_as_example"),
                ("Dashboard", "put_chart_customizations"), ("Dashboard", "tag"), ("Dashboard", "write"), ("Dashboard", "view_query"), ("Dashboard", "get_embedded"),
                ("DashboardPermalinkRestApi", "write"), ("SQLLab", "export_streaming_csv"), ("Theme", "export"), ("Theme", "write"),
                ("Superset", "csv"), ("Superset", "explore"), ("Superset", "explore_json"), ("Superset", "share_chart"), ("Superset", "share_dashboard"),
                ("Superset", "file_handler"), ("Superset", "fetch_datasource_metadata"), ("Superset", "slice")}
with app.app_context():
    from superset import db
    role = app.appbuilder.sm.find_role("Public")
    drop = [pv for pv in list(role.permissions)
            if pv.permission.name == "menu_access" or pv.view_menu.name in REMOVE_VIEWS
            or (pv.view_menu.name, pv.permission.name.replace("can_", "")) in REMOVE_PAIRS]
    for pv in drop: role.permissions.remove(pv)
    db.session.merge(role); db.session.commit()
    print("удалено прав у Public:", len(drop), "| осталось:", len(app.appbuilder.sm.find_role("Public").permissions))
