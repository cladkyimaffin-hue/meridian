"""Настройки Superset (пробная установка). Секреты берутся из переменных окружения (файл вне репозитория)."""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:%s@superset-db:5432/superset" % os.environ["SUPERSET_DB_PASS"]

_cache = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
CACHE_CONFIG = _cache
DATA_CACHE_CONFIG = _cache
FILTER_STATE_CACHE_CONFIG = _cache
EXPLORE_FORM_DATA_CACHE_CONFIG = _cache

# Просмотр без пароля: аноним получает роль Public с правами Gamma (потом ограничиваем до нужных наборов данных)
AUTH_ROLE_PUBLIC = "Public"
PUBLIC_ROLE_LIKE = "Gamma"

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
