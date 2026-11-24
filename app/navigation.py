"""Six-page, stable navigation specification; intentionally no metric calculations."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PageSpec:
    key: str
    title: str
    subtitle: str
    filename: str
    icon: str
    question: str
    sections: tuple[str, ...]

PAGES: tuple[PageSpec, ...] = (
    PageSpec('intelligence_brief','Intelligence Brief','The market story, and the strength of the evidence.',
             'intelligence_brief.py',':material/dashboard:','What matters most in the registered market?',
             ('Registered activity','Composition-aware pricing','Research findings')),
    PageSpec('market_dynamics','Market Dynamics','Registered activity, transaction mix, and geographic breadth.',
             'market_dynamics.py',':material/monitoring:','How has the registered market changed?',
             ('Historical activity','Registration composition','Geographic concentration')),
    PageSpec('price_reality','Price Reality','Observed versus matched prices and nominal purchase budgets.',
             'price_reality.py',':material/trending_up:','How much do transaction composition and selection matter?',
             ('Raw versus matched pricing','Size and mix','Budget and price tails')),
    PageSpec('community_intelligence','Community Intelligence','Evidence-qualified geographic comparisons.',
             'community_intelligence.py',':material/apartment:','Which community comparisons have enough support?',
             ('Community eligibility','Comparable price histories','Dispersion and stability')),
    PageSpec('market_structure','Market Structure','Registration differences and recorded property attributes.',
             'market_structure.py',':material/bar_chart:','How do prices vary within supported comparable groups?',
             ('Ready / Off-Plan comparisons','Property size','Bedroom support and limits')),
    PageSpec('research_reliability','Research Reliability','Provenance, robustness, uncertainty, and research permissions.',
             'research_reliability.py',':material/verified_user:','Which conclusions survive independent scrutiny?',
             ('Source integrity','Selection and sensitivity','Claim evidence and limitations')),
)

def page_files(root: Path) -> tuple[Path, ...]:
    base = Path(root) / 'app' / 'pages'
    return tuple(base / item.filename for item in PAGES)


def register_pages(st, root: Path):
    """Register exactly six pages with the native Streamlit router."""
    return [st.Page(str(path), title=spec.title, icon=spec.icon, default=(i==0))
            for i,(spec,path) in enumerate(zip(PAGES,page_files(root)))]
