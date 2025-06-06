import pytest
from src.services.supabase_service import SupabaseService
import src.services.supabase_service as supabase_module

class DummyResponse:
    def __init__(self, data):
        self.data = data

class DummyTable:
    def __init__(self):
        self.inserted = []
    def insert(self, data):
        self.inserted.append(data)
        return self
    def execute(self):
        return DummyResponse(self.inserted)

class DummyClient:
    def __init__(self):
        self.tables = {}
    def table(self, name):
        tbl = DummyTable()
        self.tables[name] = tbl
        return tbl

@pytest.fixture(autouse=True)
def patch_create_client(monkeypatch):
    def dummy_create_client(url, key):
        return DummyClient()
    monkeypatch.setattr(supabase_module, 'create_client', dummy_create_client)
    yield

@pytest.mark.asyncio
async def test_insert_success():
    svc = SupabaseService()
    resp = svc.insert('test_table', {'col': 'value'})
    assert resp.data == [{'col': 'value'}]

@pytest.mark.asyncio
async def test_insert_failure(monkeypatch):
    # Simulate execute raising
    class BadTable(DummyTable):
        def execute(self):
            raise Exception('DB error')
    def bad_create_client(url, key):
        client = DummyClient()
        # monkeypatch table method to return BadTable
        client.table = lambda name: BadTable()
        return client
    monkeypatch.setattr(supabase_module, 'create_client', bad_create_client)
    svc = SupabaseService()
    with pytest.raises(Exception) as excinfo:
        svc.insert('bad_table', {'x': 1})
    assert 'DB error' in str(excinfo.value)
