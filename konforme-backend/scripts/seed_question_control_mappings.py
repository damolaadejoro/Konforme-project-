"""Seed assessment_question_controls with mappings derived from NIS2 article alignment.

Questions and controls share NIS2 article tags. This script maps each question
to the controls that address the same article area.

Idempotent: deletes all rows and re-inserts on every run.
Called on application startup from main.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session  # noqa: E402

from models import AssessmentQuestionControl  # noqa: E402

# Mapping derived from article alignment between assessment_questions.py and seed_base_controls.py.
# Format: (question_id, control_id, weight)
# Questions tagged "Art 20" map to controls tagged "Art. 20", etc.
MAPPINGS = [
    # Art 20: Governance → ctrl-029..032 (Governance controls)
    ("nis2-020-01", "ctrl-029", 1.0),
    ("nis2-020-01", "ctrl-030", 0.5),
    ("nis2-020-02", "ctrl-030", 1.0),
    ("nis2-020-02", "ctrl-029", 0.5),
    ("nis2-020-03", "ctrl-031", 1.0),
    ("nis2-020-04", "ctrl-032", 1.0),
    ("nis2-020-04", "ctrl-004", 0.5),  # Also relates to security roles

    # Art 21(2)(a): Risk Analysis & IS Security Policies → ctrl-001..004
    ("nis2-21a-01", "ctrl-001", 1.0),
    ("nis2-21a-02", "ctrl-002", 1.0),
    ("nis2-21a-03", "ctrl-003", 1.0),
    ("nis2-21a-04", "ctrl-004", 1.0),
    ("nis2-21a-04", "ctrl-001", 0.5),  # Policy covers roles too

    # Art 21(2)(b): Incident Handling → ctrl-005..008
    ("nis2-21b-01", "ctrl-005", 1.0),
    ("nis2-21b-02", "ctrl-006", 1.0),
    ("nis2-21b-03", "ctrl-007", 1.0),
    ("nis2-21b-04", "ctrl-008", 1.0),
    ("nis2-21b-05", "ctrl-009", 1.0),  # Art 23 notification links to incident handling

    # Art 21(2)(c): Business Continuity → ctrl-010..013
    ("nis2-21c-01", "ctrl-010", 1.0),
    ("nis2-21c-02", "ctrl-011", 1.0),
    ("nis2-21c-03", "ctrl-012", 1.0),
    ("nis2-21c-04", "ctrl-013", 1.0),
    ("nis2-21c-05", "ctrl-010", 0.5),  # Crisis mgmt relates to continuity

    # Art 21(2)(d): Supply Chain Security → ctrl-014..016
    ("nis2-21d-01", "ctrl-014", 1.0),
    ("nis2-21d-02", "ctrl-015", 1.0),
    ("nis2-21d-03", "ctrl-016", 1.0),
    ("nis2-21d-04", "ctrl-014", 0.5),
    ("nis2-21d-04", "ctrl-016", 0.5),

    # Art 21(2)(e): Network & IS Security → ctrl-019..022
    ("nis2-21e-01", "ctrl-019", 1.0),
    ("nis2-21e-02", "ctrl-020", 1.0),
    ("nis2-21e-03", "ctrl-022", 1.0),  # Vulnerability handling
    ("nis2-21e-04", "ctrl-021", 1.0),  # Patch management
    ("nis2-21e-05", "ctrl-019", 0.5),

    # Art 21(2)(f): Effectiveness Assessment → ctrl-033..036
    ("nis2-21f-01", "ctrl-033", 1.0),
    ("nis2-21f-02", "ctrl-034", 1.0),
    ("nis2-21f-03", "ctrl-035", 1.0),
    ("nis2-21f-04", "ctrl-036", 1.0),

    # Art 21(2)(g): Cyber Hygiene & Training → ctrl-023..024, ctrl-037..038
    ("nis2-21g-01", "ctrl-023", 1.0),
    ("nis2-21g-01", "ctrl-037", 0.5),
    ("nis2-21g-02", "ctrl-024", 1.0),
    ("nis2-21g-02", "ctrl-038", 0.5),
    ("nis2-21g-03", "ctrl-037", 1.0),
    ("nis2-21g-04", "ctrl-038", 1.0),

    # Art 21(2)(h): Cryptography → ctrl-018, ctrl-039, ctrl-021
    ("nis2-21h-01", "ctrl-018", 1.0),
    ("nis2-21h-02", "ctrl-039", 1.0),
    ("nis2-21h-03", "ctrl-021", 1.0),  # Encryption in access control
    ("nis2-21h-04", "ctrl-018", 0.5),
    ("nis2-21h-04", "ctrl-039", 0.5),

    # Art 21(2)(i): HR Security & Access Control → ctrl-025..028
    ("nis2-21i-01", "ctrl-025", 1.0),
    ("nis2-21i-02", "ctrl-026", 1.0),
    ("nis2-21i-03", "ctrl-027", 1.0),
    ("nis2-21i-04", "ctrl-028", 1.0),
    ("nis2-21i-05", "ctrl-025", 0.5),
    ("nis2-21i-05", "ctrl-027", 0.5),
    ("nis2-21i-06", "ctrl-028", 0.5),

    # Art 21(2)(j): MFA & Secure Comms → ctrl-017, ctrl-040..043
    ("nis2-21j-01", "ctrl-017", 1.0),
    ("nis2-21j-01", "ctrl-040", 0.5),
    ("nis2-21j-02", "ctrl-041", 1.0),
    ("nis2-21j-03", "ctrl-042", 1.0),
    ("nis2-21j-04", "ctrl-043", 1.0),
]


def seed_question_control_mappings(db: Session) -> None:
    """Delete and re-insert all question-control mappings."""
    db.query(AssessmentQuestionControl).delete()

    for question_id, control_id, weight in MAPPINGS:
        db.add(AssessmentQuestionControl(
            question_id=question_id,
            control_id=control_id,
            weight=weight,
        ))

    db.commit()
