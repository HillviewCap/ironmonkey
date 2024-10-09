from app.extensions import db
from datetime import datetime

class Rollup(db.Model):
    __tablename__ = 'rollups'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.JSON, nullable=False)
    audio_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Rollup {self.type} {self.created_at}>'
