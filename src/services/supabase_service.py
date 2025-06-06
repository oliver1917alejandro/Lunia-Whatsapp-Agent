"""
supabase_service.py: Supabase database integration service
"""
from supabase import create_client, Client
from src.core.config import Config
from src.core.logger import logger


class SupabaseService:
    """Service to interact with a Supabase database."""

    def __init__(self):
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_KEY

        if not url or not key:
            logger.error("SupabaseService: Missing URL or key in Config.")
            raise ValueError("Invalid Supabase configuration.")

        self.client: Client = create_client(url, key)

    def insert(self, table: str, data: dict):
        """
        Insert a record into the specified Supabase table.

        Args:
            table: Name of the Supabase table
            data: Dictionary of column-value pairs

        Returns:
            Response from Supabase insert operation
        """
        try:
            response = self.client.table(table).insert(data).execute()
            logger.info(f"Inserted into {table}: {response.data}")
            return response
        except Exception as e:
            logger.error(f"Supabase insert error: {e}")
            raise
