from backend.admin import render_dashboard
from backend.db import insert_lead, insert_customer


def test_dashboard_shows_lead_counts_and_active_customers(tmp_db):
    insert_lead(tmp_db, source="wizard", name="A", email="a@x.com")
    insert_lead(tmp_db, source="wizard", name="B", email="b@x.com")
    insert_customer(tmp_db, name="Reg", address="1", postcode="CH3",
                    frequency="regular_6w", price_pence=2500,
                    next_due_date="2030-01-01")
    html_out = render_dashboard(tmp_db)
    assert "<strong>1</strong> active" in html_out
    assert ">new<" in html_out  # status column value
