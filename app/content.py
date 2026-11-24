"""Static page intent and interpretation rules; NOT scientific claim authorization.

No observed numbers or market findings live in this module. Publication decisions
are exclusively owned by app_core and validated Notebook 06 artifacts.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class PageGuide:
    audience: str
    question_ids: tuple[str, ...]
    purpose: str
    selection_rule: str
    non_inference: str
    modules: tuple[str, ...]

GUIDES: dict[str, PageGuide] = {
 'intelligence_brief': PageGuide(
   'Executives, researchers and first-time visitors',
   ('RQ01','RQ04','RQ05','RQ11','RQ15'),
   'A concise entry point to the registered-sales story and the strength of each claim.',
   'Period selectors apply only to compatible descriptive counts; fixed matched-price estimates keep their original reference windows.',
   'Headline prices are neither same-property appreciation nor causal Off-Plan premiums.',
   ('Cross-research context','Evidence-qualified highlights','Guided navigation')),
 'market_dynamics': PageGuide(
   'Market analysts and strategy teams',('RQ04','RQ05','RQ06'),
   'Historical registered activity, nominal consideration, registration mix and geography.',
   'Only period and segment selectors available at the exact approved aggregate grain may modify a metric.',
   'Registered transaction activity is not inventory, household demand or a validated predictive model.',
   ('Registered sales','Composition and growth accounting','Geographic support')),
 'price_reality': PageGuide(
   'Pricing researchers and market observers',('RQ01','RQ02','RQ03','RQ14'),
   'Understand how transaction composition affects historical price summaries.',
   'Matched indices use fixed approved cohorts, weights and endpoint designs; filters cannot create new estimands.',
   'Matched-group price movement is not a repeat-sales index or inflation-adjusted appreciation.',
   ('Raw versus adjusted evidence','Size-composition support','Nominal budget context')),
 'community_intelligence': PageGuide(
   'Geographic analysts and research teams',('RQ07','RQ08','RQ09','RQ13'),
   'Explore comparable community histories without inventing unsupported rankings.',
   'Show community eligibility and coverage before any matched growth comparison.',
   'Insufficient evidence is not zero growth; recorded-price stability is not investment risk.',
   ('Community eligibility','Historical continuity','Comparable estimate support')),
 'market_structure': PageGuide(
   'Market structure and pricing analysts',('RQ10','RQ11','RQ12'),
   'Study registration, property size and recorded-attribute associations.',
   'Only supported matched designs and bedroom contrasts may be displayed. Parking remains withheld.',
   'Ready versus Off-Plan and bedroom associations must not be interpreted causally.',
   ('Registration common support','Size model diagnostics','Attribute identification')),
 'research_reliability': PageGuide(
   'Auditors, analysts and method reviewers',('RQ15',),
   'Make source integrity, population selection and claim restrictions transparent.',
   'Use the frozen source and final manifest; do not recalculate or reinterpret missing evidence.',
   'A successful software check does not prove causal identification or unrestricted population validity.',
   ('Data quality and cohorts','Sensitivity and uncertainty','Claim and release permissions')),
}

# Editorial placeholders only: descriptions of future modules, never market findings.
# Keep aligned to app.navigation.PAGES sections (three entries per page).
MODULE_DESCRIPTIONS: dict[str, tuple[str, str, str]] = {
 'intelligence_brief': (
  'Historical transaction activity and nominal registered consideration, with approved period context.',
  'A guided comparison of raw observations and fixed-design matched evidence.',
  'Publication-ready insights only, each paired with source coverage and qualifications.',
 ),
 'market_dynamics': (
  'Registration counts and values at explicitly authorized time grains.',
  'Ready and Off-Plan composition where category and period contracts permit.',
  'Geographic distribution and concentration with valid cohort definitions.',
 ),
 'price_reality': (
  'Raw price observations and approved matched-design estimates shown side by side.',
  'The effect of recorded unit-size and transaction mix on observed price summaries.',
  'Nominal budgets and upper-tail distributions for approved populations only.',
 ),
 'community_intelligence': (
  'Eligibility and endpoint coverage before any cross-community comparison.',
  'Comparable historical observations subject to complete coverage checks.',
  'Dispersion and stability as descriptive measures, not investment risk forecasts.',
 ),
 'market_structure': (
  'Within-stratum comparisons with their cohort overlap and design restrictions.',
  'Observed size relationships under the approved research specifications.',
  'Identified bedroom contrasts and explicit non-estimable parking outcomes.',
 ),
 'research_reliability': (
  'Frozen source provenance, integrity checks and analysis population selection.',
  'Precomputed robustness exercises and uncertainty evidence where approved.',
  'Research-question decisions, individual claim permissions and limitations.',
 ),
}
