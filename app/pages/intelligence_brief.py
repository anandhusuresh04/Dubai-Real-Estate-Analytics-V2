"""Verified Phase 3 Intelligence Brief analytics workspace."""
from app.navigation import PAGES
from app.analytics.pages import render_research_page

PAGE = next(p for p in PAGES if p.key == 'intelligence_brief')

def render(st) -> None:
    render_research_page(st, PAGE)

if __name__ == '__main__':
    import streamlit as st
    render(st)
