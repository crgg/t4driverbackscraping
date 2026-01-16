from datetime import datetime
from t4alerts_backend.common.database import db

class SSLCertificate(db.Model):
    __tablename__ = 'ssl_certificates'

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(255), unique=True, nullable=False)
    port = db.Column(db.Integer, default=443, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'hostname': self.hostname,
            'port': self.port,
            'created_at': self.created_at.isoformat()
        }
