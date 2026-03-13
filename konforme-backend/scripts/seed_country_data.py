#!/usr/bin/env python3
"""Seed country_controls and country_assessment_questions from research JSON files.

Usage:
    python scripts/seed_country_data.py

This script is idempotent — it can be run multiple times without duplicating data.
It reads all *.json files from data/countries/ (excluding _index.json) and generates:
  - 49 country_controls per country (~1,323 total)
  - 0-4 additional country_assessment_questions per country (~30-50 total)
"""
import json
import os
import re
import sys
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assessment_questions import QUESTIONS  # noqa: E402
from database import SessionLocal  # noqa: E402
from models import Country, CountryAssessmentQuestion, CountryControl  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "countries"

# ── Article-area mapping for controls ────────────────────────────────────────
# Maps article strings from QUESTIONS to the JSON fields that might contain
# country-specific info going beyond EU baseline.
ARTICLE_AREA_MAP = {
    "Art 20": "governance",
    "Art 21(2)(a)": "risk_analysis",
    "Art 21(2)(b)": "incident_handling",
    "Art 21(2)(c)": "business_continuity",
    "Art 21(2)(d)": "supply_chain",
    "Art 21(2)(e)": "vulnerability_handling",
    "Art 21(2)(f)": "effectiveness_assessment",
    "Art 21(2)(g)": "cyber_hygiene",
    "Art 21(2)(h)": "cryptography",
    "Art 21(2)(i)": "access_control",
    "Art 21(2)(j)": "mfa_communications",
}


def _get_national_legal_ref(data: dict) -> str | None:
    """Extract the primary national legal reference from country JSON.

    Prefers shorter references (short_name, law_number) over verbose formal_citation
    since these are used as compact badges in the UI.
    """
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return law.get("short_name") or law.get("law_number") or law.get("formal_citation") or law.get("name")
    return None


def _get_law_name(data: dict) -> str | None:
    """Extract the law name for pending-transposition countries."""
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return law.get("name") or law.get("short_name")
    return None


def _get_csirt_name(data: dict) -> str | None:
    csirt = data.get("csirt", {})
    if isinstance(csirt, dict):
        return csirt.get("name")
    return None


def _get_authority_name(data: dict) -> str | None:
    auth = data.get("competent_authority", {})
    if isinstance(auth, dict):
        return auth.get("acronym") or auth.get("name")
    return None


def _is_transposed(data: dict) -> bool:
    return data.get("transposition_status") == "transposed"


# ── Goes-beyond-EU detection ────────────────────────────────────────────────

def _governance_goes_beyond(data: dict) -> tuple[bool, str | None, list[str]]:
    """Check if country goes beyond EU for Art 20 (Governance)."""
    ml = data.get("management_liability", {})
    if not isinstance(ml, dict) or not ml.get("applicable"):
        return False, None, []

    desc = ml.get("description", "").lower()
    extras = []
    goes_beyond = False

    if "personal liability" in desc or re.search(r"\bliability\b.*\b(negligence|infringement|security)\b", desc):
        extras.append("Personal liability for management in cybersecurity decisions")
        goes_beyond = True
    if "executive liability" in desc or "enhanced enforcement" in desc:
        extras.append("Enhanced executive liability beyond EU baseline")
        goes_beyond = True
    if re.search(r"every\s+\d+\s+year", desc) or "training" in desc:
        extras.append(f"Management training requirement: {ml.get('description', '')}")
        goes_beyond = True
    if "cannot be" in desc and "delegat" in desc:
        extras.append("Security responsibility cannot be fully delegated")
        goes_beyond = True

    spec = ml.get("description") if goes_beyond else None
    return goes_beyond, spec, extras


def _incident_goes_beyond(data: dict) -> tuple[bool, str | None, list[str]]:
    """Check if country goes beyond EU for Art 21(2)(b) (Incident Handling)."""
    ir = data.get("incident_reporting", {})
    # Also check national_specifics for stricter timelines
    ns = data.get("national_specifics", {})
    if not isinstance(ir, dict):
        ir = {}
    if not isinstance(ns, dict):
        ns = {}

    extras = []
    goes_beyond = False

    # Check for stricter early warning timeline (EU baseline is 24h)
    ew = ir.get("early_warning_stricter") or ns.get("early_warning_deadline", "")
    if isinstance(ew, str) and ew:
        # Detect timelines shorter than 24 hours
        match = re.search(r"(\d+)\s*hour", ew.lower())
        if match and int(match.group(1)) < 24:
            extras.append(f"Stricter early warning: {ew}")
            goes_beyond = True

    # Check for end-of-impact notification (unique to some countries like PT)
    if ir.get("end_of_impact_notification"):
        extras.append(f"End-of-impact notification: {ir['end_of_impact_notification']}")
        goes_beyond = True

    # Check for authority response requirement
    if ir.get("authority_response"):
        extras.append(f"Authority response: {ir['authority_response']}")
        goes_beyond = True

    # Check for interim reports
    if ir.get("interim_reports"):
        extras.append(f"Interim reports: {ir['interim_reports']}")
        goes_beyond = True

    # Check for pre-notification (different from early_warning)
    if ir.get("pre_notification"):
        extras.append(f"Pre-notification: {ir['pre_notification']}")
        goes_beyond = True

    spec = "; ".join(extras) if goes_beyond else None
    return goes_beyond, spec, extras


def _supply_chain_goes_beyond(data: dict) -> tuple[bool, str | None, list[str]]:
    """Check if country goes beyond EU for Art 21(2)(d) (Supply Chain)."""
    sc = data.get("supply_chain_requirements", {})
    if not isinstance(sc, dict) or not sc.get("applicable"):
        return False, None, []

    desc = sc.get("description", "").lower()
    extras = []
    goes_beyond = False

    # Detailed requirements beyond generic "supply chain" mention
    specifics = ["ict equipment restrictions", "coordinated risk", "supplier practices",
                 "comprehensive documentation", "supplier vulnerabilities"]
    for kw in specifics:
        if kw in desc:
            goes_beyond = True
            break

    if goes_beyond:
        extras.append(sc.get("description", ""))
        return True, sc.get("description"), extras
    return False, None, []


def _risk_goes_beyond(data: dict) -> tuple[bool, str | None, list[str]]:
    """Check if country goes beyond EU for Art 21(2)(a) (Risk Analysis)."""
    # Check top-level framework block first
    framework = data.get("framework", {})
    if isinstance(framework, dict) and framework.get("name"):
        name = framework["name"]
        desc = framework.get("description", "")
        return True, f"Requires {name}: {desc}", [f"Mandatory framework: {name}"]
    # Fallback: check national_law.framework (some countries store it here)
    law = data.get("national_law", {})
    if isinstance(law, dict):
        law_fw = law.get("framework")
        if isinstance(law_fw, str) and law_fw:
            return True, f"Requires {law_fw}", [f"Mandatory framework: {law_fw}"]
    return False, None, []


def _get_goes_beyond_for_article(article: str, data: dict) -> tuple[bool, str | None, list[str]]:
    """Dispatch to the appropriate goes-beyond checker for an article."""
    if article == "Art 20":
        return _governance_goes_beyond(data)
    elif article == "Art 21(2)(b)":
        return _incident_goes_beyond(data)
    elif article == "Art 21(2)(d)":
        return _supply_chain_goes_beyond(data)
    elif article == "Art 21(2)(a)":
        return _risk_goes_beyond(data)
    return False, None, []


def _get_national_specification(article: str, data: dict) -> str | None:
    """Get a national specification string for a given article area."""
    if not _is_transposed(data):
        return "Pending transposition"

    area = ARTICLE_AREA_MAP.get(article, "")

    # Try to pull relevant info from the JSON
    if area == "governance":
        ml = data.get("management_liability", {})
        if isinstance(ml, dict) and ml.get("description"):
            return ml["description"]
    elif area == "incident_handling":
        ir = data.get("incident_reporting", {})
        if isinstance(ir, dict):
            parts = []
            for k, v in ir.items():
                if isinstance(v, str) and k != "note":
                    parts.append(f"{k.replace('_', ' ').title()}: {v}")
            if parts:
                return "; ".join(parts)
    elif area == "supply_chain":
        sc = data.get("supply_chain_requirements", {})
        if isinstance(sc, dict) and sc.get("description"):
            return sc["description"]
    elif area == "risk_analysis":
        fw = data.get("framework", {})
        if isinstance(fw, dict) and fw.get("name"):
            return f"Compliance via {fw['name']} framework"
        core = data.get("core_compliance", {})
        if isinstance(core, dict) and core.get("description"):
            return core["description"]

    return None


# ── Country controls generation ──────────────────────────────────────────────

def generate_controls(data: dict, country_id: str) -> list[dict]:
    """Generate 49 CountryControl rows from a country JSON."""
    is_transposed = _is_transposed(data)
    national_ref = _get_national_legal_ref(data) if is_transposed else _get_law_name(data)

    controls = []
    for q in QUESTIONS:
        article = q["article"]
        goes_beyond, spec_override, additional = _get_goes_beyond_for_article(article, data)

        if not is_transposed:
            goes_beyond = False
            additional = []

        national_spec = spec_override or _get_national_specification(article, data)

        controls.append({
            "country_id": country_id,
            "control_id": q["id"],
            "eu_article": article,
            "national_legal_reference": national_ref,
            "national_specification": national_spec,
            "goes_beyond_eu": goes_beyond,
            "applies_to_tiers": json.dumps(["essential", "important"]),
            "additional_requirements": json.dumps(additional),
            "is_mandatory": True,
        })

    return controls


# ── Additional assessment questions ──────────────────────────────────────────

def generate_additional_questions(data: dict, country_id: str) -> list[dict]:
    """Generate additional country-specific assessment questions."""
    if not _is_transposed(data):
        return []

    questions = []
    code = data.get("country_code", "")
    national_ref = _get_national_legal_ref(data) or ""
    authority = _get_authority_name(data) or "competent authority"
    csirt = _get_csirt_name(data) or "national CSIRT"

    # ─ Trigger 1: Management training requirement ─
    ml = data.get("management_liability", {})
    if isinstance(ml, dict) and ml.get("applicable"):
        desc = ml.get("description", "").lower()
        if "training" in desc or "every" in desc:
            # Extract training period if mentioned
            period_match = re.search(r"every\s+(\d+)\s+year", desc)
            period = f" every {period_match.group(1)} years" if period_match else ""
            questions.append({
                "country_id": country_id,
                "base_question_id": None,
                "question_text": f"Has management completed mandatory cybersecurity training per {national_ref}?",
                "help_text": f"National law requires management body members to undergo cybersecurity training{period}. {ml.get('description', '')}",
                "eu_article": "Art 20",
                "national_legal_reference": national_ref,
                "applies_to_tiers": json.dumps(["essential", "important"]),
                "domain": "Governance",
                "weight": 1.0,
                "is_additional": True,
            })

    # ─ Trigger 2: CSO/officer appointment deadline ─
    deadlines = data.get("compliance_deadlines", {})
    if isinstance(deadlines, dict):
        for key, value in deadlines.items():
            if not isinstance(value, str):
                continue
            key_lower = key.lower()
            if "officer" in key_lower or "cso" in key_lower or "contact_point" in key_lower:
                questions.append({
                    "country_id": country_id,
                    "base_question_id": None,
                    "question_text": f"Has a cybersecurity officer been appointed within the legally required timeframe ({value})?",
                    "help_text": f"National transposition requires appointment by: {value}",
                    "eu_article": "Art 20",
                    "national_legal_reference": national_ref,
                    "applies_to_tiers": json.dumps(["essential", "important"]),
                    "domain": "Governance",
                    "weight": 1.0,
                    "is_additional": True,
                })
                break  # Only one CSO question per country

    # ─ Trigger 3: End-of-impact notification ─
    ir = data.get("incident_reporting", {})
    if isinstance(ir, dict) and ir.get("end_of_impact_notification"):
        questions.append({
            "country_id": country_id,
            "base_question_id": None,
            "question_text": f"Is there a process to notify {csirt} within 24h of incident impact ending?",
            "help_text": f"National law requires end-of-impact notification: {ir['end_of_impact_notification']}",
            "eu_article": "Art 21(2)(b)",
            "national_legal_reference": national_ref,
            "applies_to_tiers": json.dumps(["essential", "important"]),
            "domain": "Incident Handling",
            "weight": 1.0,
            "is_additional": True,
        })

    # ─ Trigger 4: Registration deadline ─
    if isinstance(deadlines, dict):
        for key, value in deadlines.items():
            if not isinstance(value, str):
                continue
            key_lower = key.lower()
            if "registration" in key_lower and "portal" not in key_lower and "cycle" not in key_lower:
                questions.append({
                    "country_id": country_id,
                    "base_question_id": None,
                    "question_text": f"Is the organisation registered on the {authority} platform by {value}?",
                    "help_text": f"Registration deadline: {value}",
                    "eu_article": "Art 20",
                    "national_legal_reference": national_ref,
                    "applies_to_tiers": json.dumps(["essential", "important"]),
                    "domain": "Governance",
                    "weight": 1.0,
                    "is_additional": True,
                })
                break  # Only one registration question per country

    # ─ Trigger 5: Country-specific framework (e.g. Belgium CyFun) ─
    framework = data.get("framework", {})
    if isinstance(framework, dict) and framework.get("name"):
        fw_name = framework["name"]
        questions.append({
            "country_id": country_id,
            "base_question_id": None,
            "question_text": f"Has the organisation completed a {fw_name} self-assessment?",
            "help_text": f"{fw_name}: {framework.get('description', '')}",
            "eu_article": "Art 21(2)(a)",
            "national_legal_reference": national_ref,
            "applies_to_tiers": json.dumps(["essential", "important"]),
            "domain": "Risk Analysis",
            "weight": 1.0,
            "is_additional": True,
        })

    return questions


# ── Seed logic ───────────────────────────────────────────────────────────────

def seed_country_data(db, filepath: Path) -> tuple[str, int, int]:
    """Seed controls and additional questions for one country. Returns (code, controls_count, questions_count)."""
    with open(filepath) as f:
        data = json.load(f)

    code = data.get("country_code", "")
    if not code:
        print(f"  SKIP {filepath.name}: no country_code")
        return "", 0, 0

    # Look up country — must already exist (run seed_countries.py first)
    country = db.query(Country).filter(Country.code == code).first()
    if not country:
        print(f"  SKIP {code}: country not in DB (run seed_countries.py first)")
        return code, 0, 0

    # ── Controls: delete and re-insert (idempotent) ──
    db.query(CountryControl).filter(CountryControl.country_id == country.id).delete()
    controls = generate_controls(data, country.id)
    for c in controls:
        db.add(CountryControl(**c))

    # ── Additional questions: delete and re-insert ──
    db.query(CountryAssessmentQuestion).filter(
        CountryAssessmentQuestion.country_id == country.id
    ).delete()
    questions = generate_additional_questions(data, country.id)
    for q in questions:
        db.add(CountryAssessmentQuestion(**q))

    return code, len(controls), len(questions)


def main():
    if not DATA_DIR.exists():
        print(f"ERROR: Data directory not found: {DATA_DIR}")
        sys.exit(1)

    json_files = sorted(DATA_DIR.glob("*.json"))
    json_files = [f for f in json_files if f.name != "_index.json"]

    if not json_files:
        print(f"ERROR: No JSON files found in {DATA_DIR}")
        sys.exit(1)

    print(f"Seeding country controls & questions from {len(json_files)} countries")

    db = SessionLocal()
    try:
        total_controls = 0
        total_questions = 0
        seeded = []

        for filepath in json_files:
            code, ctrl_count, q_count = seed_country_data(db, filepath)
            if code:
                seeded.append(code)
                total_controls += ctrl_count
                total_questions += q_count
                extra = f" + {q_count} additional questions" if q_count else ""
                print(f"  OK  {code}: {ctrl_count} controls{extra}")

        db.commit()
        print(f"\nSeeded {len(seeded)} countries:")
        print(f"  {total_controls} country_controls rows")
        print(f"  {total_questions} country_assessment_questions rows")

        # Verify
        ctrl_db = db.query(CountryControl).count()
        q_db = db.query(CountryAssessmentQuestion).count()
        q_additional = db.query(CountryAssessmentQuestion).filter(
            CountryAssessmentQuestion.is_additional == True  # noqa: E712
        ).count()
        print(f"\nDatabase totals:")
        print(f"  country_controls: {ctrl_db}")
        print(f"  country_assessment_questions: {q_db} ({q_additional} additional)")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
