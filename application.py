import hmac
import os
from urllib.parse import quote_plus

from flask import Flask, jsonify, request
from marshmallow import ValidationError

from models import Blacklist, BlacklistSchema, db


def database_uri() -> str:
    # Si Beanstalk tiene una base RDS asociada, expone estas variables
    if 'RDS_HOSTNAME' in os.environ:
        return 'postgresql://{}:{}@{}:{}/{}'.format(
            os.environ['RDS_USERNAME'],
            quote_plus(os.environ['RDS_PASSWORD']),
            os.environ['RDS_HOSTNAME'],
            os.environ.get('RDS_PORT', '5432'),
            os.environ['RDS_DB_NAME'],
        )
    return os.environ.get('DATABASE_URL', 'sqlite:///blacklist.db')


application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] = database_uri()
application.json.ensure_ascii = False

AUTH_TOKEN = os.environ.get('AUTH_TOKEN', 'token-local-desarrollo')

db.init_app(application)
with application.app_context():
    db.create_all()

schema = BlacklistSchema()


def is_authorized() -> bool:
    header = request.headers.get('Authorization', '')
    return hmac.compare_digest(header, f'Bearer {AUTH_TOKEN}')


def client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


@application.route("/")
def health():
    # Beanstalk revisa la salud del entorno haciendo GET a "/"
    return jsonify({'status': 'ok'})


@application.route("/blacklists", methods=['POST'])
def add_to_blacklist():
    if not is_authorized():
        return jsonify({'msg': 'Token de autorización inválido o ausente'}), 401

    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({'msg': 'Datos inválidos', 'errors': error.messages}), 400

    email = data['email'].lower()
    if Blacklist.query.filter_by(email=email).first():
        return jsonify({'msg': f'El email {email} ya está en la lista negra'}), 409

    entry = Blacklist(
        email=email,
        app_uuid=str(data['app_uuid']),
        blocked_reason=data['blocked_reason'],
        ip_address=client_ip(),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'msg': f'El email {email} fue agregado a la lista negra'}), 201


@application.route("/blacklists/<string:email>", methods=['GET'])
def check_blacklist(email):
    if not is_authorized():
        return jsonify({'msg': 'Token de autorización inválido o ausente'}), 401

    entry = Blacklist.query.filter_by(email=email.lower()).first()
    return jsonify({
        'is_blacklisted': entry is not None,
        'blocked_reason': entry.blocked_reason if entry else None,
    })


if __name__ == "__main__":
    application.run(port=5000, debug=True)
