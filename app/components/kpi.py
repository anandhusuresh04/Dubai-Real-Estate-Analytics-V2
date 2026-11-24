"""KPI presentation only: input values must already be validated upstream."""
from html import escape
from numbers import Real
import math


def display_value(value: object) -> str:
    if value is None or (isinstance(value,Real) and not math.isfinite(float(value))):
        return 'Not available'
    return str(value)


def kpi_card(st, *, label: str, value: object = None, unit: str = '', context: str = '',
             fixture: bool = False) -> None:
    """No metric calculations; fixtures get an unmistakable label."""
    v = display_value(value)
    prefix = '[SYNTHETIC FIXTURE] ' if fixture else ''
    st.markdown(
        '<div class="v2-card" role="group" aria-label="Metric card">'
        f'<div class="v2-label">{escape(prefix+label)}</div>'
        f'<div class="v2-kpi-number">{escape(v)}'
        f'<span class="v2-kpi-unit">{escape(unit)}</span></div>'
        f'<div class="v2-kpi-note">{escape(context or "No publication evidence supplied")}</div>'
        '</div>', unsafe_allow_html=True)
