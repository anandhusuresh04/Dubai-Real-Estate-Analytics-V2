"""Guard the editorial redesign against returning to empty default Streamlit scaffolding."""
from html import escape
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from app.content import MODULE_DESCRIPTIONS, GUIDES
from app.navigation import PAGES
from app.components.layout import _module_card, _context_card, render_shell
from app.components.header import page_header
from app.runtime import ReleaseView
from app.theme.styles import CSS
from test_phase2_skeleton import FakeStreamlit, text_of


def test_modules_are_specific_and_no_empirical_fixtures():
    assert set(MODULE_DESCRIPTIONS)=={page.key for page in PAGES}
    assert all(len(MODULE_DESCRIPTIONS[page.key])==len(page.sections) for page in PAGES)
    assert all(len(desc)>35 for descriptions in MODULE_DESCRIPTIONS.values() for desc in descriptions)
    assert all('not an investment forecast' not in desc.lower() for descriptions in MODULE_DESCRIPTIONS.values() for desc in descriptions)


def test_research_module_cards_are_finished_layout_not_dashed_placeholders():
    rendered=_module_card(1,'Market structure','Future module; no result claimed.')
    assert 'PLANNED · PHASE 3' in rendered
    assert 'v2-module' in rendered
    assert 'dash' not in rendered
    assert 'role="group"' not in rendered


def test_page_context_and_titles_escape_html():
    st=FakeStreamlit()
    page_header(st,'<script>','<svg>',page_number=2)
    assert '<script>' not in text_of(st)
    assert '&lt;script&gt;' in text_of(st)
    assert '02 / 06' in text_of(st)
    assert '&lt;unsafe&gt;' in _context_card('<unsafe>',GUIDES['market_structure'])
    assert '&lt;img&gt;' in _module_card(1,'<img>','No chart.')


def test_fail_closed_release_is_prominent_and_not_a_success_state(monkeypatch):
    monkeypatch.setattr('app.components.layout.check_release',
                        lambda root:ReleaseView(False,'UNAVAILABLE','No validated artifacts'))
    st=FakeStreamlit()
    render_shell(st,PAGES[0]);html=text_of(st)
    assert 'Publication access restricted' in html
    assert 'Research figures withheld' not in html or 'unverified' in html
    assert 'No validated artifacts' in html
    assert 'v2-modules' in html
    assert 'Research question' in html
    assert 'BLOCKED' in html
    assert 'Validated research foundation' not in html


def test_approved_release_explicitly_remains_qualified(monkeypatch):
    monkeypatch.setattr('app.components.layout.check_release',
                        lambda root:ReleaseView(True,'APPROVED_WITH_QUALIFICATIONS','Qualified',15,36))
    st=FakeStreamlit()
    render_shell(st,PAGES[1]);html=text_of(st)
    assert 'Validated research foundation' in html
    assert 'claim-specific permissions remain mandatory' in html
    assert 'QUALIFIED' in html
    assert 'APPROVED WITHOUT RESTRICTIONS' not in html


def test_mobile_and_reduced_motion_treatment():
    assert '@media (max-width: 720px)' in CSS
    assert 'grid-template-columns:1fr' in CSS
    assert 'prefers-reduced-motion' in CSS
    assert '[aria-current="page"]' in CSS
    assert 'focus:outline-none' not in CSS
