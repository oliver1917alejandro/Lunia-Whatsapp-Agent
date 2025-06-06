import pytest
import asyncio
from email.message import EmailMessage

import aiosmtplib
from src.services.email_service import EmailService

class DummySMTP:
    sent_messages = []

    @staticmethod
    async def send(message, hostname, port, start_tls, username, password):
        DummySMTP.sent_messages.append((message, hostname, port, start_tls, username, password))
        return None

@pytest.fixture(autouse=True)
def patch_aiosmtplib(monkeypatch):
    monkeypatch.setattr(aiosmtplib, 'send', DummySMTP.send)
    yield
    DummySMTP.sent_messages.clear()

@pytest.mark.asyncio
async def test_send_email_success(monkeypatch):
    # Setup config environment variables
    service = EmailService()
    # Use test values
    result = await service.send_email(
        to="test@example.com",
        subject="Hello",
        body="This is a test"
    )
    assert result is True
    # Verify a message was sent
    assert len(DummySMTP.sent_messages) == 1
    message, hostname, port, start_tls, username, password = DummySMTP.sent_messages[0]
    assert message['To'] == 'test@example.com'
    assert message['Subject'] == 'Hello'

@pytest.mark.asyncio
async def test_send_email_failure(monkeypatch):
    # Simulate failure by raising exception
    async def fail_send(*args, **kwargs):
        raise aiosmtplib.SMTPException("SMTP error")
    monkeypatch.setattr(aiosmtplib, 'send', fail_send)

    service = EmailService()
    result = await service.send_email(
        to="fail@example.com",
        subject="Fail",
        body="Should fail"
    )
    assert result is False
