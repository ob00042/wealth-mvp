import unittest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.database import Base, get_db
from app.models import Advisor, Client, Bank, Account, Position
from app.utils.auth import hash_password, create_access_token


class ClientAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password('client-password')

    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        for i in (1, 2):
            self.db.add(Advisor(id=i, first_name='Advisor', last_name=str(i), email=f'advisor{i}@example.com', hashed_password=self.password_hash))
            self.db.add(Client(id=i, advisor_id=i, first_name='Client', last_name=str(i), email=f'client{i}@example.com', hashed_password=self.password_hash))
            self.db.add(Bank(id=i, client_id=i, name=f'Bank {i}'))
            self.db.add(Account(id=i, bank_id=i, name='Cash', account_type='cash', currency='EUR', balance=100))
            self.db.add(Position(id=i, account_id=i, security_name='Stock', quantity=1, market_value=50, currency='EUR'))
        self.db.add(Client(id=3, advisor_id=1, first_name='No', last_name='Login'))
        self.db.commit()
        def override_db():
            yield self.db
        app.dependency_overrides[get_db] = override_db
        self.api = TestClient(app)

    def tearDown(self):
        self.api.close()
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def headers(self, role='client', user_id=1):
        return {'Authorization': 'Bearer ' + create_access_token({'sub': str(user_id), 'role': role})}

    def test_login_and_own_dashboard(self):
        response = self.api.post('/clients/login', json={'email': 'CLIENT1@example.com', 'password': 'client-password'})
        self.assertEqual(response.status_code, 200)
        headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
        data = self.api.get('/clients/me/dashboard', headers=headers).json()
        self.assertEqual(data['id'], 1)
        self.assertEqual(float(data['total_assets']), 150)
        self.assertEqual(self.api.post('/clients/login', json={'email': 'client1@example.com', 'password': 'wrong'}).status_code, 401)

    def test_all_reads_are_scoped(self):
        for role in ('advisor', 'client'):
            headers = self.headers(role)
            for path in ('banks', 'accounts', 'positions'):
                response = self.api.get('/' + path, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual([item['id'] for item in response.json()], [1])
            self.assertEqual(self.api.get('/clients/2/dashboard', headers=headers).status_code, 404)
            self.assertEqual(self.api.get('/clients/1/dashboard', headers=headers).status_code, 200)
        self.assertEqual([c['id'] for c in self.api.get('/clients', headers=self.headers()).json()], [1])
        self.assertEqual(self.api.get('/advisors/dashboard', headers=self.headers()).status_code, 403)
        self.assertEqual(self.api.get('/advisors', headers=self.headers()).status_code, 403)
        self.assertEqual(self.api.get('/advisors/dashboard', headers=self.headers('advisor')).status_code, 200)

    def test_anonymous_and_invalid_tokens(self):
        for path in ('clients', 'banks', 'accounts', 'positions', 'advisors', 'clients/1/dashboard', 'clients/me/dashboard'):
            self.assertIn(self.api.get('/' + path).status_code, (401, 403))
        for claims in ({'sub': '1'}, {'sub': 'oops', 'role': 'client'}, {'sub': '999', 'role': 'client'}):
            headers = {'Authorization': 'Bearer ' + create_access_token(claims)}
            self.assertEqual(self.api.get('/clients', headers=headers).status_code, 401)
        expired = create_access_token({'sub': '1', 'role': 'client'}, timedelta(seconds=-1))
        self.assertEqual(self.api.get('/clients', headers={'Authorization': 'Bearer ' + expired}).status_code, 401)

    def test_writes_and_credential_provisioning(self):
        payloads = {
            'clients': {'first_name': 'New', 'last_name': 'Client', 'advisor_id': 2},
            'banks': {'name': 'New', 'client_id': 2},
            'accounts': {'name': 'New', 'account_type': 'cash', 'currency': 'EUR', 'balance': 0, 'bank_id': 2},
            'positions': {'security_name': 'New', 'quantity': 1, 'market_value': 1, 'currency': 'EUR', 'account_id': 2},
        }
        for path, payload in payloads.items():
            self.assertEqual(self.api.post('/' + path, json=payload, headers=self.headers()).status_code, 403)
            self.assertIn(self.api.post('/' + path, json=payload, headers=self.headers('advisor')).status_code, (403, 404))
        credentials = {'email': 'new@example.com', 'password': 'new-password'}
        self.assertEqual(self.api.put('/clients/1/credentials', json=credentials, headers=self.headers()).status_code, 403)
        self.assertEqual(self.api.put('/clients/2/credentials', json=credentials, headers=self.headers('advisor')).status_code, 404)
        response = self.api.put('/clients/3/credentials', json=credentials, headers=self.headers('advisor'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('hashed_password', response.json())
        self.assertEqual(self.api.post('/clients/login', json=credentials).status_code, 200)
        self.assertEqual(self.api.put('/clients/1/credentials', json=credentials, headers=self.headers('advisor')).status_code, 409)


if __name__ == '__main__':
    unittest.main()
