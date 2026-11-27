"""Единая система оформления дашбордов Superset (палитры тем, баннеры, подзаголовки, CSS, карточки главной страницы)."""

THEMES = {  # тема: (тёмный, светлый, фоновый оттенок, палитра диаграмм)
    "Остатки": ("#2D6CB5", "#6FB1F0", "#EAF3FC", "t_ostatki"),
    "Приходы": ("#2E8B3E", "#7CCB80", "#EAF6EB", "t_prihody"),
    "Расход и заказы": ("#D9730D", "#F7B05E", "#FEF1E0", "t_rashod"),
    "Задачи": ("#6C3FB0", "#B08EE3", "#F3ECFB", "t_zadachi"),
    "Движение": ("#13867F", "#5CCBC2", "#E6F6F4", "t_dvizhenie"),
    "Обмен с 1С": ("#B23A48", "#EE8497", "#FCEBEE", "t_obmen"),
}
HOME_URL = "/superset/dashboard/home/?standalone=2"
NAVY = ("#1F3A5F", "#3C78B8")


def banner(text, colors, back=True, size=28):
    """Баннер по центру; фиксированная высота и flex-центровка (без ползунков)."""
    d, l = colors[0], colors[1]
    link = (f'<a href="{HOME_URL}" style="position:absolute;left:16px;top:50%;transform:translateY(-50%);color:#fff;'
            f'font-size:14px;font-weight:600;text-decoration:none;background:rgba(255,255,255,.22);padding:5px 12px;border-radius:14px">← Главная</a>') if back else ""
    # text-overflow: при узком окне длинный заголовок сжимается многоточием,
    # а не вылезает за границы баннера
    return (f'<div style="position:relative;display:flex;align-items:center;justify-content:center;height:52px;margin:0;color:#fff;'
            f'font-size:{size}px;font-weight:700;letter-spacing:1px;border-radius:14px;background:linear-gradient(90deg,{d},{l});'
            f'box-shadow:0 2px 8px rgba(0,0,0,.15);overflow:hidden">'
            f'{link}<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:0 8px">{text}</span></div>')


def subheader(text, theme):
    d, l, tint, _ = THEMES[theme]
    return (f'<div style="display:flex;align-items:center;justify-content:center;height:38px;margin:0;color:{d};font-size:19px;font-weight:700;'
            f'background:{tint};border-left:6px solid {d};border-right:6px solid {l};border-radius:10px;overflow:hidden">'
            f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:0 8px">{text}</span></div>')


def dashboard_css(theme):
    d, l, tint, _ = THEMES[theme]
    return f"""
body,.dashboard{{background:#F5F7FB}}
/* Верхнее меню Superset не нужно: из отчёта есть только возврат на главную */
#main-menu,.navbar,.app-menu{{display:none!important}}
.dashboard-header-container{{display:none!important}}
.dashboard-component-chart-holder{{border-radius:16px;border-top:4px solid {d};box-shadow:0 2px 10px rgba(0,0,0,.10);background:#fff}}
/* заголовки диаграмм по центру */
.dashboard-component-chart-holder .slice-header,.dashboard-component-chart-holder .chart-header{{position:relative;display:flex!important;justify-content:center!important}}
.dashboard-component-chart-holder .header-title,.dashboard-component-chart-holder .header-title *{{text-align:center!important;font-weight:700!important;font-size:16px!important;color:{d}!important;justify-content:center}}
/* Заголовок тахометра/графика в узком блоке: переносится на вторую строку,
   а не обрезается многоточием. Одно длинное слово («Приостановлено») разрешаем
   переносить по буквам — иначе оно всё равно вылезало за границы блока */
.dashboard-component-chart-holder .header-title{{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;height:auto!important;line-height:1.2!important;word-break:break-word!important;overflow-wrap:anywhere!important}}
.dashboard-component-chart-holder .header-title *{{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;word-break:break-word!important;overflow-wrap:anywhere!important;max-width:100%!important}}
.dashboard-component-chart-holder .header-controls{{position:absolute;right:6px;top:4px}}
/* таблицы: шапка-градиент, зебра, подсветка */
.dashboard table thead th{{background:linear-gradient(90deg,{d},{l})!important;color:#fff!important;font-weight:700}}
.dashboard table tbody tr:nth-of-type(even) td{{background:{tint}!important}}
.dashboard table tbody tr:nth-of-type(odd) td{{background:#fff!important}}
.dashboard table tbody tr:hover td{{background:{l}55!important}}
/* без ползунков у Markdown-блоков */
.dashboard-markdown,.dashboard-markdown>div,.dashboard-markdown .markdown,.dashboard-component-markdown{{overflow:hidden!important}}
.dashboard-markdown ::-webkit-scrollbar{{display:none}}
/* Markdown вставляет <p> с внешними отступами: из-за них баннер обрезался снизу */
.dashboard-markdown p,.dashboard-component-markdown p{{margin:0!important;padding:0!important;line-height:1.2!important}}
/* заголовок отчёта не выходит за границы своего блока */
.dashboard-markdown>div{{max-width:100%!important}}
"""


def home_css():
    return """
body,.dashboard{background:#F5F7FB}
/* Меню Superset на главной не нужно: пользователь ходит только по карточкам */
#main-menu,.navbar,.app-menu{display:none!important}
.dashboard-header-container{display:none!important}
.dashboard-markdown,.dashboard-markdown>div,.dashboard-markdown .markdown,.dashboard-component-markdown{overflow:hidden!important}
.dashboard-markdown ::-webkit-scrollbar{display:none}
.dashboard-markdown p,.dashboard-component-markdown p{margin:0!important;padding:0!important;line-height:1.2!important}
.dashboard-markdown>div{max-width:100%!important}
.hm-link{display:block;margin:7px 0;padding:9px 14px;border-radius:12px;text-decoration:none!important;font-weight:600;text-align:center;transition:transform .12s}
.hm-link:hover{transform:translateY(-1px);filter:brightness(.96)}
"""


def theme_card(theme, desc, items):
    """Карточка темы для главной. items: [(название, ссылка или None)]. Недоступные отчёты серые."""
    d, l, tint, _ = THEMES[theme]
    links = []
    for title, url in items:
        if url:
            links.append(f'<a class="hm-link" href="{url}" style="background:{tint};color:{d}">{title}</a>')
        else:
            links.append(f'<span class="hm-link" style="background:#F0F1F4;color:#9AA3AF;cursor:default">{title} <small>(скоро)</small></span>')
    return (f'<div style="height:100%;box-sizing:border-box;border:1px solid #E3E8F0;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.08)">'
            f'<div style="display:flex;align-items:center;justify-content:center;height:46px;color:#fff;font-size:22px;font-weight:700;background:linear-gradient(90deg,{d},{l})">{theme}</div>'
            f'<div style="padding:10px 16px 0;color:#4A5565;font-size:14px;text-align:center;min-height:56px">{desc}</div>'
            f'<div style="padding:4px 16px 14px">{"".join(links)}</div></div>')
