from locust import HttpUser, task, between


class LibraryUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        response = self.client.post("/api/auth/login", json={
            "username": "locust_user",
            "password": "locustpass"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task
    def get_books(self):
        self.client.get(
            "/api/books",
            headers={"Authorization": f"Bearer {self.token}"}
        )