from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate

db = SQLAlchemy()


class Blacklist(db.Model):
    __tablename__ = 'blacklists'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    app_uuid = db.Column(db.String(36), nullable=False)
    blocked_reason = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class BlacklistSchema(Schema):
    """Valida el cuerpo del POST /blacklists."""
    email = fields.Email(required=True)
    app_uuid = fields.UUID(required=True)
    blocked_reason = fields.String(load_default=None, validate=validate.Length(max=255))
