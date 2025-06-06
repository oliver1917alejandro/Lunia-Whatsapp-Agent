"""
calendar_service.py: Google Calendar integration service
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from src.core.config import Config
from src.core.logger import logger


class CalendarService:
    """Service to create and manage Google Calendar events."""

    def __init__(self):
        credentials_file = Config.GOOGLE_SERVICE_ACCOUNT_FILE
        if not credentials_file or not os.path.exists(credentials_file):
            logger.error(f"CalendarService: Service account file not found: {credentials_file}")
            raise ValueError("Invalid Google service account configuration.")

        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=scopes
        )
        self.service = build('calendar', 'v3', credentials=creds)

    def create_event(self, calendar_id: str, event_body: dict) -> dict:
        """
        Create an event in the specified Google Calendar.

        Args:
            calendar_id: Calendar identifier (e.g., 'primary')
            event_body: Event body as per Google Calendar API spec

        Returns:
            The created event resource as a dict
        """
        try:
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()
            logger.info(f"Event created: {event.get('id')}")
            return event
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            raise
