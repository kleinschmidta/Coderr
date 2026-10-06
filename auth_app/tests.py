from django.test import TestCase

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


class CustomUserTests(TestCase):
    def test_user_can_be_created_as_customer_or_business(self):
        user_model = get_user_model()

        customer = user_model.objects.create_user(
            username="customer1",
            email="customer@example.com",
            password="safe-password",
            type="customer",
        )
        business = user_model.objects.create_user(
            username="business1",
            email="business@example.com",
            password="safe-password",
            type="business",
        )

        self.assertEqual(customer.type, "customer")
        self.assertEqual(business.type, "business")
        self.assertTrue(customer.check_password("safe-password"))


class RegistrationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/registration/"
        self.payload = {
            "username": "newcustomer",
            "email": "customer@example.com",
            "password": "safe-password-123",
            "repeated_password": "safe-password-123",
            "type": "customer",
        }

    def test_registers_user_and_returns_auth_token(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            set(response.data),
            {"token", "username", "email", "user_id"},
        )
        self.assertTrue(response.data["token"])

        user = get_user_model().objects.get(username="newcustomer")
        self.assertEqual(user.email, "customer@example.com")
        self.assertEqual(user.type, "customer")
        self.assertTrue(user.check_password("safe-password-123"))

    def test_rejects_mismatched_passwords(self):
        self.payload["repeated_password"] = "different-password"

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.exists())

    def test_rejects_unknown_user_type(self):
        self.payload["type"] = "admin"

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.exists())

    def test_requires_user_type(self):
        self.payload.pop("type")

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.exists())


class LoginApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/login/"
        self.user = get_user_model().objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="correct-password",
            type="customer",
        )

    def test_logs_in_user_and_returns_auth_token(self):
        response = self.client.post(
            self.url,
            {"username": "loginuser", "password": "correct-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data),
            {"token", "username", "email", "user_id"},
        )
        self.assertEqual(response.data["username"], "loginuser")
        self.assertEqual(response.data["email"], "login@example.com")
        self.assertTrue(response.data["token"])

    def test_rejects_invalid_credentials(self):
        response = self.client.post(
            self.url,
            {"username": "loginuser", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Invalid credentials")


class ProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="businessuser",
            email="business@example.com",
            password="safe-password",
            type="business",
        )
        self.other_user = self.user_model.objects.create_user(
            username="customeruser",
            email="customer@example.com",
            password="safe-password",
            type="customer",
        )
        self.client.force_authenticate(user=self.user)

    def test_gets_profile_with_empty_strings_for_optional_fields(self):
        response = self.client.get(f"/api/profile/{self.user.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["username"], "businessuser")
        for field in ("first_name", "last_name", "location", "tel", "description", "working_hours"):
            self.assertEqual(response.data[field], "")

    def test_returns_not_found_for_unknown_profile(self):
        response = self.client.get("/api/profile/99999/")

        self.assertEqual(response.status_code, 404)

    def test_updates_own_profile(self):
        response = self.client.patch(
            f"/api/profile/{self.user.id}/",
            {"first_name": "Max", "location": "Berlin", "email": "max@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Max")
        self.assertEqual(self.user.location, "Berlin")
        self.assertEqual(self.user.email, "max@example.com")

    def test_cannot_update_another_users_profile(self):
        response = self.client.patch(
            f"/api/profile/{self.other_user.id}/",
            {"first_name": "Not allowed"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.other_user.refresh_from_db()
        self.assertEqual(self.other_user.first_name, "")

    def test_lists_only_business_profiles_on_business_route(self):
        response = self.client.get("/api/profiles/business/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([profile["user"] for profile in response.data], [self.user.id])
        self.assertEqual(response.data[0]["type"], "business")

    def test_lists_only_customer_profiles_on_customer_route(self):
        response = self.client.get("/api/profiles/customer/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([profile["user"] for profile in response.data], [self.other_user.id])
        self.assertEqual(response.data[0]["type"], "customer")

    def test_profile_routes_require_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(f"/api/profile/{self.user.id}/")

        self.assertEqual(response.status_code, 401)

    def test_profile_list_routes_require_authentication(self):
        self.client.force_authenticate(user=None)

        for url in ("/api/profiles/business/", "/api/profiles/customer/"):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 401)
