def test_health_responde_ok_y_version(client):
    # Act: hacer la petición al endpoint
    response = client.get('/')

    # Assert: verificar el código HTTP y el cuerpo de la respuesta
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok', 'version': 'v5'}
