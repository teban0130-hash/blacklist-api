from unittest.mock import MagicMock, patch


@patch('application.Blacklist')
def test_email_en_lista_negra_retorna_true_y_motivo(mock_blacklist, client, auth_headers):
    # Arrange: la "base de datos" encuentra un registro con motivo "Fraude"
    registro_falso = MagicMock(blocked_reason='Fraude')
    mock_blacklist.query.filter_by.return_value.first.return_value = registro_falso

    # Act
    response = client.get('/blacklists/Usuario@Ejemplo.com', headers=auth_headers)

    # Assert: respuesta correcta
    assert response.status_code == 200
    assert response.get_json() == {'is_blacklisted': True, 'blocked_reason': 'Fraude'}
    # Assert: la consulta se hizo con el email en minúsculas
    mock_blacklist.query.filter_by.assert_called_once_with(email='usuario@ejemplo.com')


@patch('application.Blacklist')
def test_email_no_esta_en_lista_negra_retorna_false(mock_blacklist, client, auth_headers):
    # Arrange: la "base de datos" no encuentra nada
    mock_blacklist.query.filter_by.return_value.first.return_value = None

    # Act
    response = client.get('/blacklists/limpio@ejemplo.com', headers=auth_headers)

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'is_blacklisted': False, 'blocked_reason': None}


@patch('application.Blacklist')
def test_consulta_sin_token_retorna_401(mock_blacklist, client):
    # Act: petición sin header Authorization
    response = client.get('/blacklists/usuario@ejemplo.com')

    # Assert: se rechaza y nunca se consulta la base de datos
    assert response.status_code == 401
    assert response.get_json() == {'msg': 'Token de autorización inválido o ausente'}
    mock_blacklist.query.filter_by.assert_not_called()
