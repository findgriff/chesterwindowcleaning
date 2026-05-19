from unittest.mock import patch
from backend.notify import send_lead_email, ping_owner_whatsapp, format_lead_message


def test_format_lead_message_for_wizard_lead():
    msg = format_lead_message({
        "id": 7, "name": "Sarah", "email": "s@x.com", "phone": "07111 222333",
        "postcode": "CH3 5AB", "property_type": "3bed_semi",
        "quote_pence": 2500, "source": "wizard",
        "notes_visitor": "back gate has a code",
    })
    assert "Sarah" in msg and "CH3 5AB" in msg
    assert "£25.00" in msg
    assert "back gate has a code" in msg


@patch("backend.notify.urllib.request.urlopen")
def test_send_lead_email_calls_resend(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{"id":"abc"}'
    mock_urlopen.return_value.__enter__.return_value.status = 200
    send_lead_email(
        api_key="re_xxx", from_addr="hello@x.co.uk", to_addr="craig@x.co.uk",
        subject="New lead", body_text="hi",
    )
    assert mock_urlopen.called
    call_args = mock_urlopen.call_args[0][0]
    assert call_args.full_url == "https://api.resend.com/emails"
    assert call_args.headers["Authorization"] == "Bearer re_xxx"


@patch("backend.notify.urllib.request.urlopen")
def test_ping_owner_whatsapp_uses_webhook_url(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.return_value = b"sent"
    mock_urlopen.return_value.__enter__.return_value.status = 200
    ping_owner_whatsapp(
        webhook_url="https://api.callmebot.com/whatsapp.php?phone=44...&apikey=K",
        message="New lead from Sarah",
    )
    assert mock_urlopen.called
    fetched_url = mock_urlopen.call_args[0][0].full_url
    assert "text=New+lead+from+Sarah" in fetched_url or "text=New%20lead%20from%20Sarah" in fetched_url
