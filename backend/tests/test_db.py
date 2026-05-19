import time
from backend.db import (
    insert_lead, get_lead, list_leads_by_status,
    insert_customer, mark_cleaned, customers_due_on_or_before,
)


def test_insert_and_get_lead(tmp_db):
    lead_id = insert_lead(tmp_db, source="wizard", name="Sarah", email="s@x.com",
                          postcode="CH3 5AB", property_type="3bed_semi",
                          frequency="regular_6w", quote_pence=2500)
    lead = get_lead(tmp_db, lead_id)
    assert lead["name"] == "Sarah"
    assert lead["status"] == "new"
    assert lead["quote_pence"] == 2500


def test_list_leads_by_status_orders_newest_first(tmp_db, frozen_time):
    a = insert_lead(tmp_db, source="wizard", name="A", email="a@x.com")
    tmp_db.execute("UPDATE leads SET created_at = ? WHERE id = ?", (frozen_time - 60, a))
    b = insert_lead(tmp_db, source="wizard", name="B", email="b@x.com")
    rows = list_leads_by_status(tmp_db, "new")
    assert [r["name"] for r in rows] == ["B", "A"]


def test_mark_cleaned_advances_due_date_by_6_weeks(tmp_db):
    cid = insert_customer(tmp_db, name="C", address="1 St", postcode="CH3",
                          frequency="regular_6w", price_pence=2500,
                          next_due_date="2026-06-01")
    mark_cleaned(tmp_db, cid, cleaned_date="2026-06-01", price_pence=2500)
    cust = tmp_db.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
    assert cust["last_cleaned_date"] == "2026-06-01"
    assert cust["next_due_date"] == "2026-07-13"  # +42 days


def test_customers_due_on_or_before(tmp_db):
    cid_due = insert_customer(tmp_db, name="Due", address="1", postcode="CH3",
                              frequency="regular_6w", price_pence=2500,
                              next_due_date="2026-05-18")
    cid_future = insert_customer(tmp_db, name="Future", address="2", postcode="CH3",
                                 frequency="regular_6w", price_pence=2500,
                                 next_due_date="2026-06-01")
    rows = customers_due_on_or_before(tmp_db, "2026-05-20")
    ids = {r["id"] for r in rows}
    assert cid_due in ids and cid_future not in ids


def test_mark_cleaned_enqueues_review_after_2nd_clean(tmp_db):
    cid = insert_customer(tmp_db, name="A", address="1", postcode="CH3",
                          frequency="regular_6w", price_pence=2500,
                          next_due_date="2026-05-18")
    mark_cleaned(tmp_db, cid, cleaned_date="2026-05-18", price_pence=2500)
    pending = list(tmp_db.execute("SELECT * FROM review_requests"))
    assert pending == []
    mark_cleaned(tmp_db, cid, cleaned_date="2026-06-29", price_pence=2500)
    pending = list(tmp_db.execute("SELECT * FROM review_requests"))
    assert len(pending) == 1
    assert pending[0]["customer_id"] == cid
