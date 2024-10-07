from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserQuestionnaire(db.Model):
    __tablename__ = 'user_questionnaire'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(255))
    organization = db.Column(db.String(255))
    location = db.Column(db.String(255))
    department = db.Column(db.String(255))
    job_function = db.Column(db.String(255))
    risk_tolerance = db.Column(db.String(50))
    alert_threshold = db.Column(db.String(50))
    alert_frequency = db.Column(db.String(50))
    threat_focus_areas = db.Column(db.Text)
    analysis_scope = db.Column(db.String(255))
    compliance_requirements = db.Column(db.Text)
    industry_specific_threats = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship to the User model
    user = db.relationship('User', backref=db.backref('questionnaire', uselist=False))
