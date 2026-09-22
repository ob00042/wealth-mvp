"""Enable login for the two existing sample clients without reseeding their data."""
from fastapi.testclient import TestClient
from app.db.database import SessionLocal
from app.main import app
from app.models import Advisor, Client
from app.utils.auth import hash_password

PROFILES = [
    ('Jane', 'Doe', 'jane.doe@example.com', 'JaneDemo123!'),
    ('Mister', 'Agapitos', 'mister.agapitos@example.com', 'AgapitosDemo123!'),
]


def main():
    ids = []
    with SessionLocal() as db:
        advisor = db.query(Advisor).filter_by(email='john.smith@example.com').one()
        for first, last, email, password in PROFILES:
            client = db.query(Client).filter_by(advisor_id=advisor.id, first_name=first, last_name=last).one()
            client.email = email
            client.hashed_password = hash_password(password)
            ids.append(client.id)
        db.commit()

    with TestClient(app) as api:
        for index, (first, last, email, password) in enumerate(PROFILES):
            response = api.post('/clients/login', json={'email': email, 'password': password})
            assert response.status_code == 200, response.text
            headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
            response = api.get('/clients/me/dashboard', headers=headers)
            assert response.status_code == 200, response.text
            dashboard = response.json()
            assert dashboard['id'] == ids[index]
            assert api.get(f'/clients/{ids[1-index]}/dashboard', headers=headers).status_code == 404
            print(f'{first} {last}: login verified; {len(dashboard["banks"])} banks; total assets {dashboard["total_assets"]}; other client access blocked.')


if __name__ == '__main__':
    main()
