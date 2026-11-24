"""Status presentation; values never authorize publication by themselves."""
from html import escape

STATES = {'SUPPORTED':'supported', 'QUALIFIED':'qualified',
          'INCONCLUSIVE':'inconclusive', 'NOT ESTIMABLE':'not-estimable',
          'BLOCKED':'blocked'}

def status_badge(st, status: str, *, note: str = '') -> None:
    key = str(status).upper().replace('_',' ')
    if key not in STATES:
        key='BLOCKED'
    label = key if not note else f'{key} · {note}'
    st.markdown(f'<span class="v2-status v2-status--{STATES[key]}">{escape(label)}</span>',
                unsafe_allow_html=True)
