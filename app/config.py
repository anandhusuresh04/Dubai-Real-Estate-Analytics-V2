"""Application-only settings. Scientific status comes exclusively from app_core."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class AppSettings:
    project_root: Path
    product: str = 'DUBAI REAL ESTATE ANALYTICS V2'
    tagline: str = 'Market Intelligence, Beyond the Headlines.'
    scope: str = '2010–2025 · registered sales · nominal AED'
    contact_label: str = 'Research-grade historical market intelligence'


def get_settings() -> AppSettings:
    return AppSettings(project_root=Path(__file__).resolve().parents[1])
