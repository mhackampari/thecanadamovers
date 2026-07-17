import json
import unittest
from unittest.mock import patch, MagicMock

import handler


def make_event(body_dict):
    return {"body": json.dumps(body_dict), "requestContext": {"http": {"sourceIp": "127.0.0.1"}}}


VALID_BODY = {
    "name": "Test User",
    "email": "test@example.com",
    "phone": "6478850450",
    "move_date": "2026-08-01",
    "services": ["Piano"],
    "origin_city": "Toronto",
    "origin_postal": "M5V1A1",
    "dest_city": "Ottawa",
    "dest_postal": "K1A0A6",
    "instructions": "test",
}


class TestHandler(unittest.TestCase):
    def test_honeypot_drops_silently_no_ses_call(self):
        with patch.object(handler, "get_ses") as mock_get_ses:
            resp = handler.handler(make_event({**VALID_BODY, "middle_name": "bot"}), None)
        self.assertEqual(resp["statusCode"], 200)
        mock_get_ses.assert_not_called()

    def test_invalid_email_rejected(self):
        resp = handler.handler(make_event({**VALID_BODY, "email": "not-an-email"}), None)
        self.assertEqual(resp["statusCode"], 400)

    def test_invalid_phone_rejected(self):
        resp = handler.handler(make_event({**VALID_BODY, "phone": "abc"}), None)
        self.assertEqual(resp["statusCode"], 400)

    def test_valid_submission_sends_lead_and_confirm_email(self):
        mock_ses = MagicMock()
        with patch.object(handler, "get_ses", return_value=mock_ses):
            resp = handler.handler(make_event(VALID_BODY), None)
        self.assertEqual(resp["statusCode"], 200)
        self.assertEqual(mock_ses.send_email.call_count, 2)

    def test_confirm_email_failure_does_not_fail_request(self):
        mock_ses = MagicMock()
        mock_ses.send_email.side_effect = [None, Exception("SES down")]
        with patch.object(handler, "get_ses", return_value=mock_ses):
            resp = handler.handler(make_event(VALID_BODY), None)
        self.assertEqual(resp["statusCode"], 200)
        self.assertEqual(mock_ses.send_email.call_count, 2)


if __name__ == "__main__":
    unittest.main()
