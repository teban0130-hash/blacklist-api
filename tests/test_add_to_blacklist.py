from unittest.mock import patch

BODY_VALIDO = {
    'email': 'Usuario@Ejemplo.com',
    'app_uuid': '6f1c2a8e-3b7d-4c55-9a0e-1f2b3c4d5e6f',
    'blocked_reason': 'Fraude',
}


# Con varios @patch, el más cercano a la función llega primero:
# mock_blacklist <- 'application.Blacklist', mock_db <- 'application.db'
@patch('application.db')
@patch('application.Blacklist')
def test_agregar_email_nuevo_retorna_201(mock_blacklist, mock_db, client, auth_headers):
    # Arrange: el email todavía no existe en la "base de datos"
    mock_blacklist.query.filter_by.return_value.first.return_value = None

    # Act: enviamos también X-Forwarded-For, como lo hace el balanceador de AWS
    response = client.post(
        '/blacklists',
        json=BODY_VALIDO,
        headers={**auth_headers, 'X-Forwarded-For': '203.0.113.7, 10.0.0.1'},
    )

    # Assert: respuesta correcta
    assert response.status_code == 201
    assert response.get_json() == {'msg': 'El email usuario@ejemplo.com fue agregado a la lista negra'}

    # Assert: el registro se construyó con los datos correctos (email en minúsculas, IP del cliente)
    mock_blacklist.assert_called_once_with(
        email='usuario@ejemplo.com',
        app_uuid='6f1c2a8e-3b7d-4c55-9a0e-1f2b3c4d5e6f',
        blocked_reason='Fraude',
        ip_address='203.0.113.7',
    )
    # Assert: se guardó ese mismo registro y se confirmó la transacción
    mock_db.session.add.assert_called_once_with(mock_blacklist.return_value)
    mock_db.session.commit.assert_called_once()


@patch('application.db')
@patch('application.Blacklist')
def test_agregar_email_existente_retorna_409(mock_blacklist, mock_db, client, auth_headers):
    # Arrange: la "base de datos" ya tiene ese email
    mock_blacklist.query.filter_by.return_value.first.return_value = object()

    # Act
    response = client.post('/blacklists', json=BODY_VALIDO, headers=auth_headers)

    # Assert: conflicto y no se guarda nada
    assert response.status_code == 409
    assert response.get_json() == {'msg': 'El email usuario@ejemplo.com ya está en la lista negra'}
    mock_db.session.add.assert_not_called()
    mock_db.session.commit.assert_not_called()


@patch('application.db')
@patch('application.Blacklist')
def test_agregar_con_datos_invalidos_retorna_400(mock_blacklist, mock_db, client, auth_headers):
    # Arrange: email mal formado y falta app_uuid
    body_invalido = {'email': 'esto-no-es-un-email', 'blocked_reason': 'Fraude'}

    # Act
    response = client.post('/blacklists', json=body_invalido, headers=auth_headers)

    # Assert: se informa qué campos fallaron y no se toca la base de datos
    assert response.status_code == 400
    body = response.get_json()
    assert body['msg'] == 'Datos inválidos'
    assert set(body['errors']) == {'email', 'app_uuid'}
    mock_blacklist.query.filter_by.assert_not_called()
    mock_db.session.add.assert_not_called()


@patch('application.db')
@patch('application.Blacklist')
def test_agregar_sin_token_retorna_401(mock_blacklist, mock_db, client):
    # Act: token incorrecto
    response = client.post(
        '/blacklists',
        json=BODY_VALIDO,
        headers={'Authorization': 'Bearer token-equivocado'},
    )

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'msg': 'Token de autorización inválido o ausente'}
    mock_blacklist.query.filter_by.assert_not_called()
    mock_db.session.add.assert_not_called()
