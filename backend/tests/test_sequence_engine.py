"""Tests du moteur de sequences."""
from datetime import datetime, timezone

from app.services.sequence_engine import _kind_for, render_template


def test_kind_for():
    assert _kind_for("linkedin_invitation") == "invitation"
    assert _kind_for("linkedin_message") == "message"
    assert _kind_for("email") == "email"


def test_render_template():
    class FakeLead:
        full_name = "Claire Dubois"
        company = "SaaSFlow"
        role = "CEO"
    out = render_template("Bonjour {{prenom}} de {{entreprise}}", FakeLead())
    assert out == "Bonjour Claire de SaaSFlow"
