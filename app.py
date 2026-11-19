"""Сайт-методичка: экспериментальная оценка эффективной вязкости
неньютоновской жидкости при ударной нагрузке (Платонов М.А.).
"""

from __future__ import annotations

import io
import math
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SCHEMA_PATH = ASSETS / "schema.png"
PDF_PATH = ASSETS / "metodicheskie_rekomendatsii.pdf"

# Ускорение свободного падения — как в примере расчёта методички.
G = 9.81  # м/с²

# Формулы из раздела «6. Расчёт» методички:
#   v = √(2gh)
#   F ≈ mg + mv²/(2d)
#   η_эф ≈ F / (3π r v)
# Последняя запись — аналогия со Стоксом при средней скорости v/2:
#   F = 6π η r (v/2) = 3π η r v  ⇒  η = F / (3π r v).
# Это сравнительная оценка порядка величины, не точное значение вязкости.

SAMPLES = [
    "Вода (контрольный образец)",
    "Суспензия 50 %",
    "Суспензия 55 %",
    "Суспензия 60 %",
]

DEFAULT_H = [0.10, 0.20, 0.40, 0.60, 0.80]

COL_H = "h, м"
COL_V = "v, м/с"
COL_D = ["d₁, мм", "d₂, мм", "d₃, мм", "d₄, мм", "d₅, мм"]
COL_AVG = "d ср., мм"
COL_BOUNCE = "Отскок"

# Условные значения из примера расчёта методички (не результаты измерений).
EXAMPLE = {"m": 0.028, "r": 0.0095, "h": 0.40, "d": 0.020}


def impact_speed(h: float, g: float = G) -> float:
    return math.sqrt(2.0 * g * h)


def mean_resistance_force(m: float, v: float, d: float, g: float = G) -> float:
    return m * g + m * v**2 / (2.0 * d)


def eta_eff(force: float, r: float, v: float) -> float:
    return force / (3.0 * math.pi * r * v)


def ru(x: float, nd: int = 2) -> str:
    if x is None or not math.isfinite(x):
        return "—"
    return f"{x:.{nd}f}".replace(".", ",")


def v_from_h(h) -> float | None:
    try:
        if h is None or pd.isna(h) or float(h) < 0:
            return None
        return round(impact_speed(float(h)), 1)
    except (TypeError, ValueError):
        return None


def mean_depth(row: pd.Series) -> float | None:
    vals = []
    for col in COL_D:
        val = row.get(col)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            try:
                vals.append(float(val))
            except (TypeError, ValueError):
                pass
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


def empty_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_H: DEFAULT_H,
            COL_V: [v_from_h(h) for h in DEFAULT_H],
            **{col: [np.nan] * len(DEFAULT_H) for col in COL_D},
            COL_AVG: [np.nan] * len(DEFAULT_H),
            COL_BOUNCE: [""] * len(DEFAULT_H),
        }
    )


def with_computed(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if COL_H not in out.columns:
        return out
    out[COL_V] = out[COL_H].map(v_from_h)
    out[COL_AVG] = out.apply(mean_depth, axis=1)
    if COL_BOUNCE in out.columns:
        out[COL_BOUNCE] = out[COL_BOUNCE].fillna("").astype(str)
    return out


def tables_equal(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    if a is None or b is None or list(a.columns) != list(b.columns) or len(a) != len(b):
        return False
    try:
        pd.testing.assert_frame_equal(
            a.reset_index(drop=True),
            b.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            atol=1e-8,
            rtol=1e-8,
        )
        return True
    except AssertionError:
        return False


CSV_DECIMALS = {
    COL_H: 2,
    COL_V: 1,
    **{col: 1 for col in COL_D},
    COL_AVG: 1,
}


def to_excel_csv(df: pd.DataFrame) -> bytes:
    tmp = df.copy()
    for col in tmp.columns:
        if col == COL_BOUNCE:
            tmp[col] = tmp[col].fillna("").astype(str)
        elif col in CSV_DECIMALS:
            nd = CSV_DECIMALS[col]

            def _fmt(x, nd=nd):
                if x is None or (isinstance(x, float) and pd.isna(x)) or (isinstance(x, str) and x == ""):
                    return ""
                try:
                    return f"{float(x):.{nd}f}".replace(".", ",")
                except (TypeError, ValueError):
                    return str(x)

            tmp[col] = tmp[col].map(_fmt)
        else:
            tmp[col] = tmp[col].fillna("").astype(str)
    buf = io.StringIO()
    tmp.to_csv(buf, index=False, sep=";")
    return buf.getvalue().encode("utf-8-sig")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 920px; padding-top: 1.6rem; padding-bottom: 3rem; }
        [data-testid="stHeader"] { background: rgba(247, 243, 236, 0.9); }
        h1, h2, h3 { font-family: "Liberation Serif", "Times New Roman", Georgia, serif; color: #1a2744; }
        .hero { text-align: center; margin: 0 0 1.4rem 0; }
        .hero h1 {
            font-family: "Liberation Serif", "Times New Roman", Georgia, serif;
            font-size: 1.55rem; font-weight: 700; line-height: 1.35;
            color: #1a2744; margin: 0 0 0.55rem 0;
        }
        .hero .author { color: #3c4a5a; font-size: 1.05rem; margin: 0; }
        .purpose, .body-text {
            text-align: justify; line-height: 1.55; color: #1c2430;
            font-size: 1.02rem; margin: 0 0 1rem 0;
        }
        .purpose b { color: #1a2744; }
        .section-title {
            font-family: "Liberation Serif", "Times New Roman", Georgia, serif;
            font-size: 1.22rem; font-weight: 700; color: #1a2744;
            margin: 1.35rem 0 0.55rem 0; border-bottom: 1px solid #d5cdbf;
            padding-bottom: 0.25rem;
        }
        .kpi-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 0.4rem 0 0.8rem 0; }
        .kpi {
            flex: 1 1 180px; background: #fffdf8; border: 1px solid #d9d0c2;
            border-radius: 10px; padding: 0.7rem 0.85rem;
        }
        .kpi-label { font-size: 0.82rem; color: #5a6573; margin-bottom: 0.2rem; }
        .kpi-value { font-size: 1.35rem; font-weight: 700; color: #25415f; }
        .calc-steps {
            background: #fffdf8; border-left: 3px solid #25415f;
            padding: 0.7rem 0.9rem; margin: 0.4rem 0 0.8rem 0;
            line-height: 1.7;
        }
        .caption { text-align: center; color: #3c4a5a; font-size: 0.92rem; margin: 0.25rem 0 0.8rem 0; }
        .footnote { color: #5a6573; font-size: 0.92rem; line-height: 1.5; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "tables" not in st.session_state:
        st.session_state.tables = {name: empty_table() for name in SAMPLES}
    if "table_rev" not in st.session_state:
        st.session_state.table_rev = {name: 0 for name in SAMPLES}
    for key, val in (
        ("calc_m", EXAMPLE["m"]),
        ("calc_r", EXAMPLE["r"]),
        ("calc_h", EXAMPLE["h"]),
        ("calc_d", EXAMPLE["d"]),
    ):
        if key not in st.session_state:
            st.session_state[key] = val


def main() -> None:
    st.set_page_config(
        page_title="Методические рекомендации — Платонов М.А.",
        page_icon="🔬",
        layout="centered",
    )
    inject_css()
    init_state()

    st.markdown(
        """
        <div class="hero">
          <h1>Методические рекомендации<br>
          по экспериментальной оценке эффективной вязкости
          неньютоновской жидкости при ударной нагрузке
          в домашних условиях</h1>
          <p class="author">Платонов М.А.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_l, top_r = st.columns([3, 2])
    with top_r:
        if PDF_PATH.exists():
            st.download_button(
                label="Скачать методичку (PDF)",
                data=PDF_PATH.read_bytes(),
                file_name="Продукт_методические_рекомендации.pdf",
                mime="application/pdf",
                width='stretch',
            )

    st.markdown(
        "<p class=\"purpose\"><b>Назначение:</b> оценка эффективной вязкости водной "
        "суспензии крахмала при ударе по глубине погружения стального шарика и "
        "сравнение её поведения с поведением воды (ньютоновской жидкости).</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">1. Оборудование</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="body-text">Крахмал (кукурузный или картофельный), вода, кухонные весы; '
        "цилиндрическая ёмкость диаметром не менее 15 см; стальной шарик на нити "
        "(масса <em>m</em> и радиус <em>r</em> измеряются заранее); штатив или стойка "
        "с отметками высоты; линейка; телефон с режимом замедленной съёмки "
        "(120–240 кадров/с).</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">2. Подготовка образцов</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="body-text">Приготовить суспензии с массовой долей крахмала 50&nbsp;%, '
        "55&nbsp;% и 60&nbsp;% (массы крахмала и воды фиксируются на весах); "
        "толщина слоя — не менее 8–10 см. Контрольный образец — вода того же объёма "
        "и температуры. Перед каждым сбросом суспензию перемешивать, чтобы крахмал не оседал.</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">3. Схема установки</div>', unsafe_allow_html=True)
    if SCHEMA_PATH.exists():
        left, mid, right = st.columns([1, 8, 1])
        with mid:
            st.image(str(SCHEMA_PATH), width='stretch')
        st.markdown(
            '<p class="caption">Рис. 1. Схема установки: <em>h</em> — высота сброса, '
            "<em>d</em> — глубина погружения</p>",
            unsafe_allow_html=True,
        )
    else:
        st.error("Файл схемы не найден (assets/schema.png).")

    st.markdown('<div class="section-title">4. Порядок проведения опыта</div>', unsafe_allow_html=True)
    st.markdown(
        """
1. Установить телефон сбоку от ёмкости на уровне поверхности жидкости, линейку поместить в кадр как масштаб.
2. Сбросить шарик без начальной скорости с высот *h* = 0,10; 0,20; 0,40; 0,60; 0,80 м, записывая видео.
3. По видео определить максимальную глубину погружения *d*, время торможения *t* (от касания поверхности до остановки) и наличие отскока.
4. Выполнить не менее 5 повторов для каждой высоты и каждого образца; повторить серию в воде.
        """
    )

    st.markdown(
        '<div class="section-title">5. Таблица результатов (заполняется для каждого образца)</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Столбцы глубины оставляйте пустыми до опытов. "
        "Скорость *v* считается по формуле *v* = √(2*gh*), "
        "*d* ср. — среднее по заполненным повторам. "
        "В таблице нет результатов измерений."
    )

    sample = st.selectbox("Образец", SAMPLES, index=0)
    editor_key = f"editor_{sample}_{st.session_state.table_rev[sample]}"

    edited = st.data_editor(
        st.session_state.tables[sample],
        hide_index=True,
        num_rows="dynamic",
        width='stretch',
        key=editor_key,
        column_config={
            COL_H: st.column_config.NumberColumn(COL_H, min_value=0.0, step=0.01, format="%.2f"),
            COL_V: st.column_config.NumberColumn(
                COL_V,
                format="%.1f",
                disabled=True,
                help="Вычисляется автоматически: v = √(2gh), g = 9,81 м/с².",
            ),
            COL_D[0]: st.column_config.NumberColumn(COL_D[0], min_value=0.0, step=0.1, format="%.1f"),
            COL_D[1]: st.column_config.NumberColumn(COL_D[1], min_value=0.0, step=0.1, format="%.1f"),
            COL_D[2]: st.column_config.NumberColumn(COL_D[2], min_value=0.0, step=0.1, format="%.1f"),
            COL_D[3]: st.column_config.NumberColumn(COL_D[3], min_value=0.0, step=0.1, format="%.1f"),
            COL_D[4]: st.column_config.NumberColumn(COL_D[4], min_value=0.0, step=0.1, format="%.1f"),
            COL_AVG: st.column_config.NumberColumn(
                COL_AVG,
                format="%.1f",
                disabled=True,
                help="Среднее по заполненным значениям d₁–d₅.",
            ),
            COL_BOUNCE: st.column_config.TextColumn(COL_BOUNCE, help="Например: да / нет"),
        },
    )

    computed = with_computed(edited)
    if not tables_equal(computed, st.session_state.tables[sample]):
        st.session_state.tables[sample] = computed
        if not tables_equal(computed, edited):
            st.session_state.table_rev[sample] += 1
            st.rerun()

    btn_l, btn_r = st.columns(2)
    with btn_l:
        st.download_button(
            label="Скачать таблицу (CSV)",
            data=to_excel_csv(st.session_state.tables[sample]),
            file_name="rezultaty_{}.csv".format(
                "voda" if sample.startswith("Вода")
                else "suspenziya_{}pct".format("".join(ch for ch in sample if ch.isdigit()) or "x")
            ),
            mime="text/csv",
            width='stretch',
        )
    with btn_r:
        if st.button("Сбросить таблицу этого образца", width='stretch'):
            st.session_state.tables[sample] = empty_table()
            st.session_state.table_rev[sample] += 1
            st.rerun()

    st.markdown('<div class="section-title">6. Расчёт</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="body-text">Скорость удара: <em>v</em> = √(2<em>gh</em>). '
        "Средняя сила сопротивления (из закона сохранения энергии): "
        "<em>F</em> ≈ <em>mg</em> + <em>mv</em>²/(2<em>d</em>). "
        "Эффективная вязкость (по аналогии с формулой Стокса при средней скорости <em>v</em>/2): "
        "η<sub>эф</sub> ≈ <em>F</em> / (3π<em>rv</em>).</p>",
        unsafe_allow_html=True,
    )

    st.latex(r"v = \sqrt{2gh}")
    st.latex(r"F \approx mg + \frac{mv^{2}}{2d}")
    st.latex(r"\eta_{\mathrm{эф}} \approx \frac{F}{3\pi r v}")

    st.markdown(
        '<p class="footnote">Формула для η<sub>эф</sub> получается из закона Стокса '
        "<em>F</em> = 6πη<em>r</em>·(<em>v</em>/2) = 3πη<em>rv</em> и даёт "
        "<strong>сравнительную оценку порядка величины</strong>, а не точное значение вязкости.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("**Онлайн-калькулятор**")
    st.info(
        "В поля подставлены **условные значения из примера расчёта в методичке, "
        "это не результаты измерений**. Замените их своими данными после опытов."
    )

    def _set_example() -> None:
        st.session_state.calc_m = EXAMPLE["m"]
        st.session_state.calc_r = EXAMPLE["r"]
        st.session_state.calc_h = EXAMPLE["h"]
        st.session_state.calc_d = EXAMPLE["d"]

    c1, c2 = st.columns(2)
    with c1:
        m = st.number_input(
            "Масса шарика m, кг",
            min_value=0.0,
            step=0.001,
            format="%.3f",
            key="calc_m",
        )
        r = st.number_input(
            "Радиус шарика r, м",
            min_value=0.0,
            step=0.0001,
            format="%.4f",
            key="calc_r",
        )
    with c2:
        h = st.number_input(
            "Высота сброса h, м",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key="calc_h",
        )
        d = st.number_input(
            "Глубина погружения d, м",
            min_value=0.0,
            step=0.001,
            format="%.3f",
            help="В калькуляторе глубина в метрах (в таблице опытов — в миллиметрах): 20 мм = 0,020 м.",
            key="calc_d",
        )

    st.button(
        "Подставить условный пример из методички",
        on_click=_set_example,
    )

    if h < 0 or m < 0 or r < 0 or d < 0:
        st.error("Масса, радиус, высота и глубина не могут быть отрицательными.")
    elif d == 0 or r == 0:
        v = impact_speed(h) if h >= 0 else float("nan")
        st.markdown(
            f'<div class="kpi-row"><div class="kpi"><div class="kpi-label">Скорость удара v</div>'
            f'<div class="kpi-value">{ru(v, 2)} м/с</div></div></div>',
            unsafe_allow_html=True,
        )
        st.warning(
            "Для расчёта силы и эффективной вязкости нужны глубина погружения *d* > 0 "
            "и радиус *r* > 0."
        )
    else:
        v = impact_speed(h)
        force = mean_resistance_force(m, v, d)
        eta = eta_eff(force, r, v)
        st.markdown(
            f"""
            <div class="kpi-row">
              <div class="kpi"><div class="kpi-label">Скорость удара v</div>
                <div class="kpi-value">{ru(v, 2)} м/с</div></div>
              <div class="kpi"><div class="kpi-label">Сила сопротивления F</div>
                <div class="kpi-value">{ru(force, 1)} Н</div></div>
              <div class="kpi"><div class="kpi-label">Эффективная вязкость η<sub>эф</sub></div>
                <div class="kpi-value">{ru(eta, 0)} Па·с</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="calc-steps">
            <em>v</em> = √(2<em>gh</em>) = √(2 × {ru(G, 2)} × {ru(h, 2)}) = {ru(v, 2)}&nbsp;м/с<br>
            <em>F</em> ≈ <em>mg</em> + <em>mv</em>²/(2<em>d</em>)
              = {ru(m, 3)} × {ru(G, 2)} + {ru(m, 3)} × {ru(v, 2)}² / (2 × {ru(d, 3)})
              = {ru(force, 1)}&nbsp;Н<br>
            η<sub>эф</sub> ≈ <em>F</em> / (3π<em>rv</em>)
              = {ru(force, 1)} / (3π × {ru(r, 4)} × {ru(v, 2)})
              = {ru(eta, 0)}&nbsp;Па·с
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<p class=\"body-text\"><b>Пример расчёта (условные значения, не результат измерений):</b> "
        "m = 0,028 кг, r = 0,0095 м, h = 0,40 м, d = 0,020 м. Тогда v ≈ 2,8 м/с; "
        "F ≈ 0,028·9,81 + 0,028·2,8²/(2·0,020) ≈ 5,8 Н; "
        "η<sub>эф</sub> ≈ 5,8 / (3π·0,0095·2,8) ≈ 23 Па·с.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">7. Интерпретация результатов и ограничения метода</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="body-text">Дилатантное поведение суспензии проявляется в том, что с ростом '
        "скорости удара глубина погружения уменьшается (или появляется отскок), а η<sub>эф</sub> "
        "растёт; для воды такая зависимость отсутствует. Различия считаются значимыми, если "
        "превышают разброс повторных измерений. Формула Стокса строго применима к медленному "
        "установившемуся движению, поэтому η<sub>эф</sub> является сравнительной оценкой порядка "
        "величины, а не точным значением вязкости. Основные источники погрешностей: оседание "
        "крахмала, испарение воды, неточность определения глубины по видео, влияние дна и стенок "
        "ёмкости.</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
