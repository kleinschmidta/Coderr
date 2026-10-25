from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail


class OfferCreationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.business_user = user_model.objects.create_user(
            username="businessuser",
            email="business@example.com",
            password="safe-password",
            type="business",
        )
        self.customer_user = user_model.objects.create_user(
            username="customeruser",
            email="customer@example.com",
            password="safe-password",
            type="customer",
        )
        self.client.force_authenticate(user=self.business_user)
        self.url = "/api/offers/"
        self.payload = {
            "title": "Grafikdesign-Paket",
            "image": None,
            "description": "Ein umfassendes Grafikdesign-Paket.",
            "details": [
                {
                    "title": "Basic Design",
                    "revisions": 2,
                    "delivery_time_in_days": 5,
                    "price": 100,
                    "features": ["Logo Design"],
                    "offer_type": "basic",
                },
                {
                    "title": "Standard Design",
                    "revisions": 5,
                    "delivery_time_in_days": 7,
                    "price": 200,
                    "features": ["Logo Design", "Visitenkarte"],
                    "offer_type": "standard",
                },
                {
                    "title": "Premium Design",
                    "revisions": 10,
                    "delivery_time_in_days": 10,
                    "price": 500,
                    "features": ["Logo Design", "Visitenkarte", "Flyer"],
                    "offer_type": "premium",
                },
            ],
        }

    def test_business_user_creates_offer_with_three_details(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Grafikdesign-Paket")
        self.assertEqual(len(response.data["details"]), 3)
        self.assertCountEqual(
            [detail["offer_type"] for detail in response.data["details"]],
            ["basic", "standard", "premium"],
        )

    def test_offer_creation_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 401)

    def test_only_business_users_can_create_offers(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 403)

    def test_business_user_can_list_offers(self):
        self.client.post(self.url, self.payload, format="json")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Grafikdesign-Paket")
        self.assertEqual(len(response.data["results"][0]["details"]), 3)

    def test_offer_list_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_offer_list_supports_filters_and_pagination(self):
        other_business_user = self.business_user.__class__.objects.create_user(
            username="otherbusiness",
            email="other@example.com",
            password="safe-password",
            type="business",
        )

        offer_a = Offer.objects.create(
            user=self.business_user,
            title="Logo Package",
            image=None,
            description="Brand identity design package.",
        )
        offer_b = Offer.objects.create(
            user=other_business_user,
            title="Website Package",
            image=None,
            description="Full website package.",
        )

        for offer, title, price, delivery_days in [
            (offer_a, "Starter", 250, 5),
            (offer_b, "Pro", 300, 10),
        ]:
            for offer_type in ("basic", "standard", "premium"):
                OfferDetail.objects.create(
                    offer=offer,
                    title=title,
                    revisions=2,
                    delivery_time_in_days=delivery_days,
                    price=price,
                    features=["Feature"],
                    offer_type=offer_type,
                )

        response = self.client.get(
            self.url,
            {"creator_id": self.business_user.id, "min_price": 200, "search": "Logo", "page_size": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Logo Package")
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)

    def test_offer_list_rejects_invalid_query_parameters(self):
        response = self.client.get(
            self.url,
            {"creator_id": "not-an-int", "min_price": "abc", "max_delivery_time": "-1"},
        )

        self.assertEqual(response.status_code, 400)

    def test_offer_requires_exactly_three_details(self):
        self.payload["details"] = self.payload["details"][:2]

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 400)
