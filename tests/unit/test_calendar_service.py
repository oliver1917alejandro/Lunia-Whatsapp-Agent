import pytest
from src.services.calendar_service import CalendarService
import src.services.calendar_service as cal_mod

class DummyEvents:
    def __init__(self):
        self.created = []
    def insert(self, calendarId, body):
        self.created.append((calendarId, body))
        return self
    def execute(self):
        return {'id': 'evt123', 'htmlLink': 'http://link'}

class DummyService:
    def __init__(self):
        self.events = DummyEvents()

@pytest.fixture(autouse=True)
def patch_build(monkeypatch):
    class DummyCreds:
        pass
    monkeypatch.setattr(cal_mod, 'service_account', type('SA', (), {'Credentials': type('C', (), {'from_service_account_file': lambda *args, **kwargs: DummyCreds()})}))
    monkeypatch.setattr(cal_mod, 'build', lambda svc, ver, credentials: DummyService())
    yield

@pytest.mark.asyncio
async def test_create_event_success():
    svc = CalendarService()
    evt = svc.create_event('primary', {'summary': 'Test'})
    assert evt['id'] == 'evt123'

@pytest.mark.asyncio
async def test_create_event_failure(monkeypatch):
    def bad_insert(calendarId, body):
        raise Exception('API error')
    class BadService(DummyService):
        def __init__(self):
            self.events = DummyEvents()
        def events(self):
            return type('E', (), {'insert': lambda *args, **kwargs: (_ for _ in ()).throw(Exception('API error'))})()
    monkeypatch.setattr(cal_mod, 'build', lambda svc, ver, credentials: BadService())
    svc = CalendarService()
    with pytest.raises(Exception):
        svc.create_event('primary', {'anything': 'value'})
