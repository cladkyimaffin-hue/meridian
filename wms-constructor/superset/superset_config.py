"""Настройки Superset (пробная установка). Секреты берутся из переменных окружения (файл вне репозитория)."""
import os
import re

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:%s@superset-db:5432/superset" % os.environ["SUPERSET_DB_PASS"]

_cache = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
CACHE_CONFIG = _cache
DATA_CACHE_CONFIG = _cache
FILTER_STATE_CACHE_CONFIG = _cache
EXPLORE_FORM_DATA_CACHE_CONFIG = _cache

# Просмотр без пароля: аноним получает роль Public с правами Gamma (потом ограничиваем до нужных наборов данных)
AUTH_ROLE_PUBLIC = "Public"
PUBLIC_ROLE_LIKE = None  # права роли Public заданы вручную (только просмотр), не копировать из Gamma

# Свобода оформления: разрешаем HTML со стилями в Markdown-блоках дашбордов (создаёт только администратор)
HTML_SANITIZATION = False

BABEL_DEFAULT_LOCALE = "ru"
LANGUAGES = {"ru": {"flag": "ru", "name": "Русский"}, "en": {"flag": "us", "name": "English"}}
ROW_LIMIT = 5000
SQL_MAX_ROW = 100000
SQLLAB_TIMEOUT = 90
SUPERSET_WEBSERVER_TIMEOUT = 120

# Права на уровне дашборда: роль Public видит данные только тех дашбордов, где она указана
# Шаблоны Jinja в SQL наборов данных (периоды, фильтры)
FEATURE_FLAGS = {"DASHBOARD_RBAC": True, "ENABLE_TEMPLATE_PROCESSING": True}

# --- Режим «портал»: из отчётов нельзя уйти никуда, кроме главной ----------
# Аноним (роль Public) получает доступ только к страницам дашбордов и к тем
# вызовам API, без которых диаграммы не рисуются. Всё остальное — редакторы,
# списки, SQL Lab, API управления — закрыто на уровне приложения, поэтому
# обойти это через другой порт или прямой запрос нельзя.
#
# Список задан регулярными выражениями: префикс «/api/v1/dashboard/» закрывал
# бы и список дашбордов, а «/api/v1/chart/» — список диаграмм. Поэтому для
# каждого адреса описано ровно то, что нужно странице отчёта.
PORTAL_MODE = os.environ.get("SUPERSET_PORTAL_MODE", "1") != "0"
PORTAL_HOME = "/superset/dashboard/home/?standalone=2"
PORTAL_ALLOW = (
    # страница отчёта
    r"^/superset/dashboard/[^/]+/?$",
    # метаданные дашборда и его состав (чем нарисован отчёт)
    r"^/api/v1/dashboard/[^/]+$",
    r"^/api/v1/dashboard/[^/]+/(charts|datasets|colors)$",
    # данные диаграмм (в том числе cross-filter)
    r"^/api/v1/chart/data",
    r"^/api/v1/chart/[0-9]+/data/?$",
    r"^/api/v1/chart/[0-9]+$",
    # описания наборов не открываем: странице отчёта хватает
    # /api/v1/dashboard/<slug>/datasets (см. выше), а в /api/v1/dataset/<id>
    # лежит SQL витрины — анониму он не нужен
    # кто я и меню (фронтенд запрашивает при загрузке; у Public меню пустое)
    r"^/api/v1/me/?$",
    r"^/api/v1/menu/?$",
    # токены для POST-запросов данных
    r"^/api/v1/security/(csrf_token|guest_token|login|refresh)/?$",
    # телеметрия фронтенда и переводы — не данные
    r"^/superset/log/?",
    r"^/superset/language_pack/",
    # вход администратора (нужен, чтобы владелец мог собирать отчёты)
    r"^/login/?$",
    r"^/logout/?$",
    # статика интерфейса
    r"^/static/",
    # проверки живости
    r"^/health",
    r"^/_health",
)
# корень и «приветствие» ведут прямо на портал (без промежуточного редиректа)
PORTAL_LANDING = ("/", "/superset/welcome/", "/superset/welcome")


def _portal_allowed(path: str) -> bool:
    return any(re.match(p, path) for p in PORTAL_ALLOW)


def FLASK_APP_MUTATOR(app):  # noqa: N802 — имя задано конфигом Superset
    """Ограничивает анонимного пользователя страницами дашбордов.

    Проверка стоит на `before_request`, поэтому действует на любые адреса,
    включая прямые вызовы API. Вошедший пользователь (администратор) не
    затрагивается: сборка дашбордов и отладка работают как раньше.
    """
    if not PORTAL_MODE:
        return

    from flask import jsonify, redirect, request
    from flask_login import current_user

    @app.before_request
    def _limit_anonymous():
        # вошедший пользователь (администратор) ходит везде
        if current_user and current_user.is_authenticated:
            return None

        path = request.path or "/"
        if _portal_allowed(path):
            return None

        # всё остальное для анонима закрыто: страницы — на портал, API — отказ
        if path.startswith("/api/"):
            return jsonify({
                "message": "В режиме просмотра доступны только отчёты портала.",
                "redirect": PORTAL_HOME,
            }), 403
        return redirect(PORTAL_HOME, code=302)


# Свои цветовые палитры (для зон тахометров и графиков по темам)
EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {"id": "svetofor", "label": "Светофор (зелёный-жёлтый-красный)", "colors": ["#84BB4C", "#F9CF48", "#ED6E6E"]},
    {"id": "svetofor_rev", "label": "Светофор наоборот (красный-жёлтый-зелёный)", "colors": ["#ED6E6E", "#F9CF48", "#84BB4C"]},
    {"id": "t_ostatki", "label": "Остатки (синий)", "colors": ["#BFD9F5", "#6FB1F0", "#2D6CB5"]},
    {"id": "t_prihody", "label": "Приходы (зелёный)", "colors": ["#C9EACC", "#7CCB80", "#2E8B3E"]},
    {"id": "t_rashod", "label": "Расход (оранжевый)", "colors": ["#FBE0BC", "#F7B05E", "#D9730D"]},
    {"id": "t_zadachi", "label": "Задачи (фиолетовый)", "colors": ["#DCCBF4", "#B08EE3", "#6C3FB0"]},
    {"id": "t_dvizhenie", "label": "Движение (бирюзовый)", "colors": ["#BDEBE7", "#5CCBC2", "#13867F"]},
    {"id": "t_obmen", "label": "Обмен с 1С (красно-розовый)", "colors": ["#F8CDD5", "#EE8497", "#B23A48"]},
]
