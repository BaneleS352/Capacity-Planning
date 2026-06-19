from tests.conftest import ApiContext


async def test_health_endpoints_report_application_and_database(api_context: ApiContext) -> None:
    live = await api_context.client.get('/api/v1/health/live')
    assert live.status_code == 200
    assert live.json()['status'] == 'ok'
    assert live.json()['database'] is None

    ready = await api_context.client.get('/api/v1/health/ready')
    assert ready.status_code == 200
    assert ready.json()['status'] == 'ok'
    assert ready.json()['database'] == 'ok'


async def test_local_development_authenticates_without_a_token(api_context: ApiContext) -> None:
    response = await api_context.client.get('/api/v1/auth/me')

    assert response.status_code == 200
    assert response.json()['organization_id'] == str(api_context.organization_id)
    assert response.json()['roles'] == ['system_admin']
