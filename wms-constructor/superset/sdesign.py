"""Единая система оформления дашбордов Superset.

Здесь всё, что делает отчёты похожими друг на друга:
  THEMES        — цвета тем (тёмный, светлый, фон, палитра диаграмм);
  banner        — шапка отчёта с кнопкой «← Главная»;
  subheader     — заголовок раздела внутри отчёта;
  dashboard_css — оформление страницы отчёта (карточки графиков, таблицы);
  portal_css    — оформление главной страницы (карточки-плитки, герой);
  hero          — верхний блок главной;
  portal_card   — карточка темы со ссылкой на отчёт;
  hint_block    — блок-подсказка «как читать»;
  footer_note   — нижняя строка главной.
"""

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
DASH = lambda slug: f"/superset/dashboard/{slug}/?standalone=2"

# Простые контурные значки (рисуются currentColor, чтобы красить темой).
ICONS = {
    "Остатки": '<path d="M3 7.5 12 3l9 4.5v9L12 21 3 16.5z"/><path d="M3 7.5 12 12l9-4.5M12 12v9"/>',
    "Приходы": '<path d="M12 3v10"/><path d="m7.5 9 4.5 4.5L16.5 9"/><path d="M4 15v3.5A2.5 2.5 0 0 0 6.5 21h11a2.5 2.5 0 0 0 2.5-2.5V15"/>',
    "Расход и заказы": '<path d="M12 21V11"/><path d="m7.5 15 4.5-4.5L16.5 15"/><path d="M4 9V5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5V9"/>',
    "Задачи": '<path d="M9 5h11M9 12h11M9 19h11"/><path d="m3 5 1.6 1.6L7.2 4"/><path d="m3 12 1.6 1.6L7.2 11"/><path d="m3 19 1.6 1.6L7.2 18"/>',
    "Движение": '<path d="M3 12h6l3-6 3 12 3-6h3"/>',
    "Обмен с 1С": '<path d="M4 9a8 8 0 0 1 13.5-4.5L20 7"/><path d="M20 4v3.5h-3.5"/><path d="M20 15a8 8 0 0 1-13.5 4.5L4 17"/><path d="M4 20v-3.5h3.5"/>',
}


def banner(text, colors, back=True, size=28):
    """Баннер по центру; фиксированная высота и flex-центровка (без ползунков)."""
    d, l = colors[0], colors[1]
    link = (f'<a href="{HOME_URL}" style="position:absolute;left:16px;top:50%;transform:translateY(-50%);color:#fff;'
            f'font-size:14px;font-weight:600;text-decoration:none;background:rgba(255,255,255,.22);padding:5px 12px;border-radius:14px">← Главная</a>') if back else ""
    return (f'<div style="position:relative;display:flex;align-items:center;justify-content:center;height:56px;margin:0;color:#fff;'
            f'font-size:{size}px;font-weight:700;letter-spacing:1px;border-radius:14px;background:linear-gradient(90deg,{d},{l});'
            f'box-shadow:0 2px 8px rgba(0,0,0,.15)">{link}<span>{text}</span></div>')


def subheader(text, theme):
    d, l, tint, _ = THEMES[theme]
    return (f'<div style="display:flex;align-items:center;justify-content:center;height:38px;margin:0;color:{d};font-size:19px;font-weight:700;'
            f'background:{tint};border-left:6px solid {d};border-right:6px solid {l};border-radius:10px">{text}</div>')


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
.dashboard-component-chart-holder .header-controls{{position:absolute;right:6px;top:4px}}
/* таблицы: шапка-градиент, зебра, подсветка */
.dashboard table thead th{{background:linear-gradient(90deg,{d},{l})!important;color:#fff!important;font-weight:700}}
.dashboard table tbody tr:nth-of-type(even) td{{background:{tint}!important}}
.dashboard table tbody tr:nth-of-type(odd) td{{background:#fff!important}}
.dashboard table tbody tr:hover td{{background:{l}55!important}}
/* без ползунков у Markdown-блоков */
.dashboard-markdown,.dashboard-markdown>div,.dashboard-markdown .markdown,.dashboard-component-markdown{{overflow:hidden!important}}
.dashboard-markdown ::-webkit-scrollbar{{display:none}}
"""


PORTAL_CSS = """
body,.dashboard{background:#EEF2F8}
/* Меню Superset на портале не нужно: пользователь ходит только по ссылкам портала */
#main-menu,.navbar,.app-menu{display:none!important}
.dashboard-header-container{display:none!important}
.dashboard-content-container{background:transparent}
.dashboard-markdown,.dashboard-markdown>div,.dashboard-markdown .markdown,.dashboard-component-markdown{overflow:hidden!important}
.dashboard-markdown ::-webkit-scrollbar{display:none}
/* markdown-обёртка не должна добавлять отступы вокруг наших блоков */
.dashboard-markdown p{margin:0!important;padding:0!important}

/* --- герой ------------------------------------------------------------- */
.hm-hero{position:relative;overflow:hidden;border-radius:20px;padding:20px 28px 18px;color:#fff;
  background:linear-gradient(118deg,#16294A 0%,#274F87 46%,#3C78B8 100%);
  box-shadow:0 10px 28px rgba(18,40,74,.30)}
.hm-hero:after{content:"";position:absolute;right:-70px;top:-80px;width:270px;height:270px;border-radius:50%;background:rgba(255,255,255,.10)}
.hm-hero:before{content:"";position:absolute;right:110px;bottom:-100px;width:190px;height:190px;border-radius:50%;background:rgba(255,255,255,.07)}
.hm-hero-in{position:relative;z-index:2}
.hm-kicker{font-size:11.5px;letter-spacing:2.6px;text-transform:uppercase;font-weight:700;opacity:.82}
.hm-title{font-size:33px;font-weight:800;line-height:1.08;margin:7px 0 5px;letter-spacing:.2px}
.hm-sub{font-size:14px;opacity:.92;max-width:760px;line-height:1.35}
.hm-live{display:inline-flex;align-items:center;gap:8px;margin-top:12px;padding:5px 13px 5px 11px;border-radius:999px;
  background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.26);font-size:11.5px;font-weight:600;letter-spacing:.2px}
.hm-dot{width:8px;height:8px;border-radius:50%;background:#5BE49B;box-shadow:0 0 0 4px rgba(91,228,155,.20)}

/* --- карточки ---------------------------------------------------------- */
.hm-card{position:relative;display:block;height:100%;box-sizing:border-box;background:#fff;border:1px solid #E0E7F1;
  border-radius:16px;text-decoration:none!important;overflow:hidden;box-shadow:0 2px 10px rgba(16,40,80,.07);
  transition:transform .15s ease,box-shadow .15s ease,border-color .15s ease}
.hm-card:has(.hm-card-link){cursor:pointer}
/* ссылка-оверлей: markdown-it не пропускает div внутрь <a>, поэтому ссылка отдельная */
.hm-card-link{position:absolute;inset:0;z-index:3;border-radius:16px}
.hm-card:has(.hm-card-link):hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(16,40,80,.16);border-color:var(--l)}
.hm-card:has(.hm-card-link):hover .hm-go{gap:14px;background:var(--l);color:#fff}
.hm-card-head{display:flex;align-items:center;gap:10px;padding:13px 16px;color:#fff;
  background:linear-gradient(90deg,var(--d),var(--l))}
.hm-card-ico{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9px;background:rgba(255,255,255,.22);flex:0 0 auto}
.hm-card-ico svg{width:17px;height:17px;stroke:#fff;stroke-width:1.9;fill:none;stroke-linecap:round;stroke-linejoin:round}
.hm-card-title{font-size:19px;font-weight:800;letter-spacing:.2px;line-height:1.1}
.hm-card-count{margin-left:auto;flex:0 0 auto;font-size:10.5px;font-weight:700;letter-spacing:.3px;
  background:rgba(255,255,255,.26);padding:3px 9px;border-radius:999px;text-transform:uppercase}
.hm-card-desc{padding:10px 16px 2px;color:#4E5A6B;font-size:12.8px;line-height:1.4;min-height:52px}
.hm-card-body{padding:2px 16px 14px}
.hm-go{display:inline-flex;align-items:center;gap:8px;background:var(--tint);color:var(--d);font-weight:700;
  font-size:13.5px;padding:9px 15px;border-radius:12px;transition:gap .15s ease,background .15s ease,color .15s ease}
.hm-go svg{width:15px;height:15px;stroke:currentColor;stroke-width:2.2;fill:none;stroke-linecap:round;stroke-linejoin:round}
.hm-card.is-soon{background:#F7F8FA;border-style:dashed}
.hm-card.is-soon .hm-card-head{background:linear-gradient(90deg,#9AA6B6,#C2CAD6)}
.hm-card.is-soon .hm-go{background:#EFF1F4;color:#93A0B0}
.hm-soon-note{font-size:12.5px;color:#98A2B3;font-style:italic;padding:2px 0 4px}

/* --- подсказка и подвал ------------------------------------------------ */
.hm-hint{display:flex;gap:14px;align-items:flex-start;height:100%;box-sizing:border-box;background:#fff;
  border:1px dashed #C6D4E8;border-radius:14px;padding:14px 18px;color:#3E4A5B;font-size:13px;line-height:1.5}
.hm-hint-ico{flex:0 0 auto;width:26px;height:26px;border-radius:8px;background:#EAF3FC;display:flex;align-items:center;justify-content:center;color:#2D6CB5;font-weight:800;font-size:14px}
.hm-hint b{color:#1F3A5F}
.hm-foot{display:flex;justify-content:space-between;align-items:center;gap:16px;color:#8A94A6;font-size:11.5px;padding:2px 8px}
.hm-foot b{color:#5B6676}
"""


def portal_css():
    return PORTAL_CSS


# прежнее имя (использовалось в build_home.py и pilot_tasks.py)
home_css = portal_css


def _icon(theme):
    path = ICONS.get(theme, ICONS["Остатки"])
    return f'<svg viewBox="0 0 24 24">{path}</svg>'


def hero(title, subtitle, kicker="АО «Меридиан» · склад", live="Данные из WMS на момент открытия"):
    return (f'<div class="hm-hero"><div class="hm-hero-in">'
            f'<div class="hm-kicker">{kicker}</div>'
            f'<div class="hm-title">{title}</div>'
            f'<div class="hm-sub">{subtitle}</div>'
            f'<div class="hm-live"><span class="hm-dot"></span>{live}</div>'
            f'</div></div>')


def portal_card(theme, desc, url=None, note="Открыть отчёт"):
    """Карточка темы.

    Важно про разметку: markdown-it (рендер Markdown-блоков Superset) не
    пропускает блочные <div> внутрь <a> — он разрывает ссылку и карточка
    рассыпается в пустые абзацы. Поэтому вся карточка — <div>, а ссылкой
    служит прозрачный абсолютный <a> поверх неё (класс hm-card-link).
    """
    d, l, tint, _ = THEMES[theme]
    head = (f'<div class="hm-card-head"><span class="hm-card-ico">{_icon(theme)}</span>'
            f'<span class="hm-card-title">{theme}</span>'
            f'<span class="hm-card-count">{"готов" if url else "скоро"}</span></div>')
    if url:
        return (f'<div class="hm-card" style="--d:{d};--l:{l};--tint:{tint}">'
                f'<a class="hm-card-link" href="{url}" aria-label="{theme}"></a>'
                f'{head}<div class="hm-card-desc">{desc}</div>'
                f'<div class="hm-card-body"><span class="hm-go">{note}'
                f'<svg viewBox="0 0 24 24"><path d="M5 12h13"/>'
                f'<path d="m12.5 5.5 6.5 6.5-6.5 6.5"/></svg></span></div></div>')
    return (f'<div class="hm-card is-soon" style="--d:{d};--l:{l};--tint:{tint}">'
            f'{head}<div class="hm-card-desc">{desc}</div>'
            f'<div class="hm-card-body"><div class="hm-soon-note">Появится на этой странице</div></div></div>')


def hint_block(text):
    return (f'<div class="hm-hint"><span class="hm-hint-ico">?</span><div>{text}</div></div>')


def footer_note(left, right):
    return f'<div class="hm-foot"><div>{left}</div><div>{right}</div></div>'
