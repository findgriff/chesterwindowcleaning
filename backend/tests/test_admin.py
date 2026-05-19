from backend.admin import render_dashboard, render_leads_list, render_lead_detail
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


def test_render_leads_list_shows_recent_lead(tmp_db):
    insert_lead(tmp_db, source="wizard", name="Sarah", email="s@x.com",
                postcode="CH3 5AB", quote_pence=2500)
    out = render_leads_list(tmp_db)
    assert "Sarah" in out and "CH3 5AB" in out and "£25.00" in out


def test_render_lead_detail_returns_none_for_missing(tmp_db):
    assert render_lead_detail(tmp_db, 999) is None


def test_convert_lead_to_customer_creates_row_and_marks_converted(tmp_db):
    from backend.db import insert_lead
    from backend.admin import convert_lead_to_customer
    lid = insert_lead(tmp_db, source="wizard", name="Sarah", email="s@x.com",
                     address="1 St", postcode="CH3 5AB", property_type="3bed_semi",
                     frequency="regular_6w", quote_pence=2500)
    cust_id = convert_lead_to_customer(tmp_db, lid,
                                       first_clean_date="2026-06-01",
                                       price_pence=2500)
    assert cust_id > 0
    lead = tmp_db.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone()
    assert lead["status"] == "converted"
    assert lead["customer_id"] == cust_id
