import os

import pytest

# Estas variables se definen ANTES de importar la aplicación, porque
# application.py lee la configuración apenas se importa.
# - Base de datos en memoria: no se crea ningún archivo ni se usa PostgreSQL.
# - Token conocido para poder construir el header Authorization en las pruebas.
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['AUTH_TOKEN'] = 'token-de-prueba'

from application import application  # noqa: E402


@pytest.fixture
def client():
    """Cliente HTTP falso de Flask: hace peticiones a la API sin levantar un servidor."""
    application.config['TESTING'] = True
    with application.test_client() as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    """Header de autorización válido para los endpoints protegidos."""
    return {'Authorization': 'Bearer token-de-prueba'}
