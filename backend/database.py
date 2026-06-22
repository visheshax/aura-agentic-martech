import os
import uuid
import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class MockSupabaseClient:
    """Fallback in-memory mock database client for zero-config setups or testing."""
    def __init__(self):
        self.raw_touchpoints = []
        self.profiles = []
        self.campaign_logs = []
        self.seed_data()

    def seed_data(self):
        # Sample profiles
        self.profiles = [
            {
                "id": "e6a2b8e3-0d52-4752-9721-c4be672e811c",
                "email": "sid@example.com",
                "phone": "+44 7123 456789",
                "full_name": "Siddharth Sharma",
                "interests": ["Premium Running Shoes", "Marathon Training"],
                "preferred_channel": "email",
                "avg_order_value": 150.0,
                "price_sensitivity": "high",
                "updated_at": datetime.datetime.now().isoformat()
            },
            {
                "id": "8fa176df-c148-4cb2-87db-2eb318f0bb99",
                "email": "emma.jones@example.com",
                "phone": "+44 7987 654321",
                "full_name": "Emma Jones",
                "interests": ["Luxury Smartwatch", "Premium Leather Bands"],
                "preferred_channel": "email",
                "avg_order_value": 850.0,
                "price_sensitivity": "low",
                "updated_at": datetime.datetime.now().isoformat()
            }
        ]

        self.raw_touchpoints = [
            {
                "id": str(uuid.uuid4()),
                "email": "sid@example.com",
                "event_type": "page_view",
                "event_data": {"product_category": "Premium Running Shoes", "price": 150},
                "created_at": datetime.datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "sid@example.com",
                "event_type": "zero_party_survey",
                "event_data": {"preferred_sport": "marathon", "frequency": "daily"},
                "created_at": datetime.datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "emma.jones@example.com",
                "event_type": "page_view",
                "event_data": {"product_category": "Luxury Smartwatch", "price": 850},
                "created_at": datetime.datetime.now().isoformat()
            }
        ]

    def table(self, name: str):
        return MockTable(self, name)

class MockTable:
    def __init__(self, client: MockSupabaseClient, name: str):
        self.client = client
        self.name = name

    def select(self, *args, **kwargs):
        return MockQuery(self, "select", *args, **kwargs)

    def insert(self, data: Any):
        if self.name == "raw_customer_touchpoints":
            if isinstance(data, list):
                for item in data:
                    item["id"] = item.get("id", str(uuid.uuid4()))
                    item["created_at"] = datetime.datetime.now().isoformat()
                    self.client.raw_touchpoints.append(item)
                return MockResponse(data)
            else:
                data["id"] = data.get("id", str(uuid.uuid4()))
                data["created_at"] = datetime.datetime.now().isoformat()
                self.client.raw_touchpoints.append(data)
                return MockResponse([data])
        elif self.name == "customer_profiles":
            if isinstance(data, list):
                for item in data:
                    item["id"] = item.get("id", str(uuid.uuid4()))
                    item["updated_at"] = datetime.datetime.now().isoformat()
                    self.client.profiles.append(item)
                return MockResponse(data)
            else:
                data["id"] = data.get("id", str(uuid.uuid4()))
                data["updated_at"] = datetime.datetime.now().isoformat()
                self.client.profiles.append(data)
                return MockResponse([data])
        elif self.name == "campaign_logs":
            data["id"] = data.get("id", str(uuid.uuid4()))
            data["created_at"] = datetime.datetime.now().isoformat()
            self.client.campaign_logs.append(data)
            return MockResponse([data])
        return MockResponse([])

    def upsert(self, data: Any, on_conflict: Optional[str] = None):
        if self.name == "customer_profiles":
            email = data.get("email")
            existing = next((p for p in self.client.profiles if p["email"] == email), None)
            if existing:
                existing.update(data)
                existing["updated_at"] = datetime.datetime.now().isoformat()
                return MockResponse([existing])
            else:
                data["id"] = data.get("id", str(uuid.uuid4()))
                data["updated_at"] = datetime.datetime.now().isoformat()
                self.client.profiles.append(data)
                return MockResponse([data])
        return MockResponse([])

class MockQuery:
    def __init__(self, table: MockTable, action: str, *args, **kwargs):
        self.table = table
        self.action = action
        self.filters = []

    def eq(self, column: str, value: Any):
        self.filters.append(("eq", column, value))
        return self

    def execute(self):
        data_source = []
        if self.table.name == "raw_customer_touchpoints":
            data_source = self.table.client.raw_touchpoints
        elif self.table.name == "customer_profiles":
            data_source = self.table.client.profiles
        elif self.table.name == "campaign_logs":
            data_source = self.table.client.campaign_logs

        result = list(data_source)
        for op, col, val in self.filters:
            if op == "eq":
                result = [item for item in result if item.get(col) == val]

        return MockResponse(result)

class MockResponse:
    def __init__(self, data: Any):
        self.data = data
    def execute(self):
        return self

# Initialize the real or mock database client
db_client = None
is_mock = True

if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "your_supabase_url":
    try:
        from supabase import create_client
        db_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        is_mock = False
        print("Connected to Supabase Database successfully.")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}. Falling back to in-memory Mock Database.")
        db_client = MockSupabaseClient()
else:
    print("Supabase credentials not configured. Falling back to in-memory Mock Database.")
    db_client = MockSupabaseClient()

def get_db():
    return db_client
