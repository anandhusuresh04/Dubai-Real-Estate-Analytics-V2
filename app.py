"""Dubai RE Analytics V2 — six-page scientific dashboard shell.

Run from repository root: streamlit run app.py
No transaction data, notebook, or statistical model is evaluated by this entry point.
"""
from app.config import get_settings
from app.navigation import register_pages
from app.runtime import check_release
from app.theme.styles import apply_theme
from app.theme.phase3 import apply_phase3_theme


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title='Dubai RE Analytics V2 | Research Intelligence',
        page_icon='🏙️', layout='wide',
        initial_sidebar_state='expanded', menu_items={
            'About': 'Frozen historical Dubai registered-sales research, 2010–2025. No investment advice.'
        },
    )
    apply_theme(st)
    apply_phase3_theme(st)
    settings = get_settings()
    release = check_release(settings.project_root)
    with st.sidebar:
        st.markdown('<div class="v2-sidebar-brand">DUBAI RE ANALYTICS <span style="color:#7BD2C4">V2</span></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="v2-sidebar-caption">A research intelligence platform for the '
                    'Dubai registered-sales market.</div>', unsafe_allow_html=True)
        if release.authorized:
            st.markdown('<div class="v2-sidebar-meta"><strong><span class="v2-sidebar-dot"></span>'
                        'Research release: approved with qualifications</strong>'
                        'Historical scope: 2010–2025<br>Registered sales · Nominal AED<br>'
                        'Observational evidence · No live listings</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="v2-sidebar-meta"><strong><span class="v2-sidebar-dot v2-sidebar-dot--off"></span>'
                        '🔒 Research figures withheld — release unverified</strong>'
                        'Historical scope: 2010–2025<br>Registered sales · Nominal AED</div>', unsafe_allow_html=True)
    pages = register_pages(st, settings.project_root)
    navigation = st.navigation(pages, position='sidebar')
    navigation.run()


if __name__ == '__main__':
    main()
