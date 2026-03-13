#!/usr/bin/env python3
"""Seed the countries table from Phase 1 research JSON files.

Usage:
    python scripts/seed_countries.py

This script is idempotent — it can be run multiple times without duplicating data.
It reads all *.json files from data/countries/ (excluding _index.json) and upserts
country records, entity tiers, and deadlines.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal  # noqa: E402
from models import Country, CountryDeadline, EntityTier  # noqa: E402


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "countries"


def _parse_date(date_str: str | None) -> date | None:
    """Parse a date string (YYYY-MM-DD) or return None."""
    if not date_str:
        return None
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def _extract_law_name(data: dict) -> str | None:
    """Extract the law name from various JSON structures."""
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return law.get("name") or law.get("short_name")
    return None


def _extract_law_reference(data: dict) -> str | None:
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return law.get("formal_citation") or law.get("law_number")
    return None


def _extract_law_url(data: dict) -> str | None:
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return law.get("gazette_url")
    return None


def _extract_date_published(data: dict) -> date | None:
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return _parse_date(law.get("publication_date"))
    return None


def _extract_date_effective(data: dict) -> date | None:
    law = data.get("national_law", {})
    if isinstance(law, dict):
        return _parse_date(law.get("entry_into_force"))
    return None


def _extract_authority_name(data: dict) -> str | None:
    auth = data.get("competent_authority", {})
    if isinstance(auth, dict):
        name = auth.get("name", "")
        acronym = auth.get("acronym", "")
        if acronym and name:
            return f"{name} ({acronym})"
        return name or acronym or None
    return None


def _extract_authority_url(data: dict) -> str | None:
    auth = data.get("competent_authority", {})
    if isinstance(auth, dict):
        return auth.get("website") or auth.get("nis2_page")
    return None


def _extract_csirt_name(data: dict) -> str | None:
    csirt = data.get("csirt", {})
    if isinstance(csirt, dict):
        return csirt.get("name")
    return None


def _extract_csirt_url(data: dict) -> str | None:
    csirt = data.get("csirt", {})
    if isinstance(csirt, dict):
        return csirt.get("website")
    return None


EU_DEFAULT_PENALTIES = {
    "essential": {"maximum": "EUR 10,000,000 or 2% of annual global turnover, whichever is higher"},
    "important": {"maximum": "EUR 7,000,000 or 1.4% of annual global turnover, whichever is higher"},
}


def _extract_entity_tiers(data: dict) -> list[dict]:
    """Extract entity tier data from the JSON structure."""
    tiers = []
    ec = data.get("entity_classification", {})
    penalties = data.get("penalties", {})
    incident = data.get("incident_reporting", {})

    if not isinstance(ec, dict):
        return tiers

    for key, value in ec.items():
        if not isinstance(value, dict):
            continue

        tier_key = key.replace("_entities", "").replace("_", "_")
        # Normalize tier keys
        if "essential" in key:
            tier_key = "essential"
        elif "important" in key:
            tier_key = "important"
        elif "public" in key:
            tier_key = "public_admin"
        else:
            tier_key = key

        local_name = value.get("local_name") or value.get("italian_term") or value.get("german_term")
        description = value.get("description", "")

        # Ensure public_admin tier has a proper display name
        if tier_key == "public_admin" and not local_name:
            local_name = "Public Administration"
        if tier_key == "public_admin" and not description:
            description = "Public administration entities subject to NIS2 obligations under national transposition"

        tier_data = {
            "tier_key": tier_key,
            "local_name": local_name,
            "description": description,
            "size_thresholds": {},
        }

        if "size_threshold" in value:
            tier_data["size_thresholds"] = {"description": value["size_threshold"]}

        # Extract penalties for this tier
        tier_penalties = {}
        if isinstance(penalties, dict):
            for pk, pv in penalties.items():
                if tier_key in pk.lower():
                    if isinstance(pv, dict):
                        tier_penalties = pv
                    elif isinstance(pv, str):
                        tier_penalties = {"maximum": pv}

        # Fall back to NIS2 EU defaults when country data has no penalties
        if not tier_penalties and tier_key in EU_DEFAULT_PENALTIES:
            tier_penalties = EU_DEFAULT_PENALTIES[tier_key]
        tier_data["penalties"] = tier_penalties

        # Extract incident reporting as obligations
        tier_data["obligations"] = {}
        if isinstance(incident, dict):
            tier_data["obligations"]["incident_reporting"] = incident

        tiers.append(tier_data)

    # If no classification found, create default essential/important tiers
    if not tiers:
        for tk in ["essential", "important"]:
            tier_penalties = {}
            if isinstance(penalties, dict):
                for pk, pv in penalties.items():
                    if tk in pk.lower():
                        if isinstance(pv, dict):
                            tier_penalties = pv
                        elif isinstance(pv, str):
                            tier_penalties = {"maximum": pv}

            # Fall back to NIS2 EU defaults when country data has no penalties
            if not tier_penalties and tk in EU_DEFAULT_PENALTIES:
                tier_penalties = EU_DEFAULT_PENALTIES[tk]

            tiers.append({
                "tier_key": tk,
                "local_name": None,
                "description": None,
                "size_thresholds": {},
                "penalties": tier_penalties,
                "obligations": {"incident_reporting": incident} if isinstance(incident, dict) else {},
            })

    return tiers


def _extract_deadlines(data: dict) -> list[dict]:
    """Extract deadline records from the JSON data."""
    deadlines = []
    cd = data.get("compliance_deadlines", {})
    if not isinstance(cd, dict):
        return deadlines

    for key, value in cd.items():
        if not value:
            continue

        # Try to parse date from value
        parsed_date = None
        description = None

        if isinstance(value, str):
            parsed_date = _parse_date(value)
            if parsed_date:
                description = key.replace("_", " ").title()
            else:
                # Value is a description, not a date
                description = value
                continue  # Skip if no parseable date
        elif isinstance(value, dict):
            continue

        if parsed_date:
            deadlines.append({
                "deadline_date": parsed_date,
                "description": description,
                "applies_to_tiers": json.dumps(["essential", "important"]),
                "legal_reference": data.get("national_law", {}).get("formal_citation")
                if isinstance(data.get("national_law"), dict) else None,
            })

    return deadlines


def _extract_sectors(data: dict) -> list[str]:
    """Extract all sectors from the JSON data."""
    sectors = []
    sc = data.get("sectors_covered", {})

    if isinstance(sc, dict):
        for key, value in sc.items():
            if isinstance(value, list):
                sectors.extend(value)
    elif isinstance(sc, list):
        sectors = sc

    return sectors


# NIS2 Directive EU-level default sectors
EU_ANNEX_I_SECTORS = [
    "Energy", "Transport", "Banking", "Financial market infrastructures",
    "Health", "Drinking water", "Waste water", "Digital infrastructure",
    "ICT service management", "Space", "Public administration",
]
EU_ANNEX_II_SECTORS = [
    "Postal and courier services", "Waste management", "Chemicals",
    "Food", "Manufacturing", "Digital providers", "Research",
]


def _extract_sectors_for_tier(data: dict, tier_key: str) -> list[str]:
    """Extract sectors specific to a tier based on NIS2 classification.

    - Essential: Annex I (high criticality) sectors — large enterprises in these sectors
    - Important: Annex I + Annex II sectors — medium-sized enterprises
    - Public Admin: National additions (e.g. public administration)

    Falls back to EU-level Annex I/II defaults when country data is empty.
    """
    sc = data.get("sectors_covered", {})
    if not isinstance(sc, dict):
        flat = _extract_sectors(data)
        if flat:
            # Flat list = country's known sectors (treated as Annex I / high-criticality)
            if tier_key == "essential":
                return flat
            elif tier_key == "important":
                # Important covers both Annex I + II; add EU Annex II defaults
                annex_ii_extra = [s for s in EU_ANNEX_II_SECTORS if s not in flat]
                return flat + annex_ii_extra
            elif tier_key == "public_admin":
                return ["Public administration"]
            return flat
        # Fall back to EU defaults
        if tier_key == "essential":
            return list(EU_ANNEX_I_SECTORS)
        elif tier_key == "important":
            return list(EU_ANNEX_I_SECTORS) + list(EU_ANNEX_II_SECTORS)
        elif tier_key == "public_admin":
            return ["Public administration"]
        return list(EU_ANNEX_I_SECTORS)

    annex_i = []
    annex_ii = []
    national = []

    for key, value in sc.items():
        if not isinstance(value, list):
            continue
        k = key.lower()
        # Check annex_ii BEFORE annex_i since "annex_ii" contains "annex_i" as substring
        if "annex_ii" in k or "other_critical" in k or "annex_2" in k:
            annex_ii.extend(value)
        elif "annex_i" in k or "high_criticality" in k or "annex_1" in k:
            annex_i.extend(value)
        elif "national" in k or "addition" in k:
            national.extend(value)
        else:
            # Unknown category — include in both
            annex_i.extend(value)
            annex_ii.extend(value)

    if tier_key == "essential":
        # Essential entities: Annex I high-criticality sectors
        return annex_i if annex_i else _extract_sectors(data) or list(EU_ANNEX_I_SECTORS)
    elif tier_key == "important":
        # Important entities: Annex I + Annex II sectors
        return (annex_i + annex_ii) if (annex_i or annex_ii) else _extract_sectors(data) or (list(EU_ANNEX_I_SECTORS) + list(EU_ANNEX_II_SECTORS))
    elif tier_key == "public_admin":
        # Public admin: national additions, or if none specified, all sectors
        return national if national else ["Public administration"]
    else:
        return _extract_sectors(data)


def seed_country(db, filepath: Path) -> str:
    """Seed a single country from a JSON file. Returns country code."""
    with open(filepath) as f:
        data = json.load(f)

    code = data.get("country_code", "")
    if not code:
        print(f"  SKIP {filepath.name}: no country_code")
        return ""

    # Upsert country
    country = db.query(Country).filter(Country.code == code).first()
    if not country:
        country = Country(code=code)
        db.add(country)

    country.name = data.get("country_name", "")
    country.name_local = data.get("local_name")
    country.transposition_status = data.get("transposition_status", "unknown")
    country.transposition_law_name = _extract_law_name(data)
    country.transposition_law_reference = _extract_law_reference(data)
    country.transposition_law_url = _extract_law_url(data)
    country.date_published = _extract_date_published(data)
    country.date_effective = _extract_date_effective(data)
    country.competent_authority_name = _extract_authority_name(data)
    country.competent_authority_url = _extract_authority_url(data)
    country.csirt_name = _extract_csirt_name(data)
    country.csirt_url = _extract_csirt_url(data)
    country.research_confidence = data.get("transposition_confidence", "medium")
    country.research_notes = "\n".join(data.get("notes", []))

    db.flush()  # Get country.id

    # Upsert entity tiers
    tier_data_list = _extract_entity_tiers(data)
    for td in tier_data_list:
        tier = (
            db.query(EntityTier)
            .filter(EntityTier.country_id == country.id, EntityTier.tier_key == td["tier_key"])
            .first()
        )
        if not tier:
            tier = EntityTier(country_id=country.id, tier_key=td["tier_key"])
            db.add(tier)

        tier.local_name = td.get("local_name")
        tier.description = td.get("description")
        tier.sectors = json.dumps(_extract_sectors_for_tier(data, td["tier_key"]))
        tier.size_thresholds = json.dumps(td.get("size_thresholds", {}))
        tier.obligations = json.dumps(td.get("obligations", {}))
        tier.penalties = json.dumps(td.get("penalties", {}))

    # Replace deadlines (clear existing, re-insert)
    db.query(CountryDeadline).filter(CountryDeadline.country_id == country.id).delete()
    for dd in _extract_deadlines(data):
        deadline = CountryDeadline(
            country_id=country.id,
            deadline_date=dd["deadline_date"],
            description=dd.get("description"),
            applies_to_tiers=dd.get("applies_to_tiers", "[]"),
            legal_reference=dd.get("legal_reference"),
        )
        db.add(deadline)

    return code


def main():
    if not DATA_DIR.exists():
        print(f"ERROR: Data directory not found: {DATA_DIR}")
        sys.exit(1)

    json_files = sorted(DATA_DIR.glob("*.json"))
    json_files = [f for f in json_files if f.name != "_index.json"]

    if not json_files:
        print(f"ERROR: No JSON files found in {DATA_DIR}")
        sys.exit(1)

    print(f"Seeding {len(json_files)} countries from {DATA_DIR}")

    db = SessionLocal()
    try:
        seeded = []
        for filepath in json_files:
            code = seed_country(db, filepath)
            if code:
                seeded.append(code)
                print(f"  OK  {code} ({filepath.name})")

        db.commit()
        print(f"\nSeeded {len(seeded)} countries: {', '.join(sorted(seeded))}")

        # Verify
        count = db.query(Country).count()
        tier_count = db.query(EntityTier).count()
        deadline_count = db.query(CountryDeadline).count()
        print(f"Database totals: {count} countries, {tier_count} entity tiers, {deadline_count} deadlines")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
