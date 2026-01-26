from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from t4alerts_backend.common.database import db

class NotificationSettings(db.Model):
    """
    Settings for dynamic notifications per app.
    Stores recipients and scheduling preferences.
    """
    __tablename__ = 'notification_settings'

    id = Column(Integer, primary_key=True)
    app_key = Column(String(50), unique=True, nullable=False)
    recipients = Column(JSON, nullable=True)  # List of emails/phone numbers
    schedule_enabled = Column(Boolean, default=False)
    schedule_interval_hours = Column(Integer, default=24) # How often to scan (mock for now)
    
    def to_dict(self):
        return {
            'app_key': self.app_key,
            'recipients': self.recipients or [],
            'schedule_enabled': self.schedule_enabled,
            'schedule_interval_hours': self.schedule_interval_hours
        }
