from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail


class OfferApiBaseTestCase(TestCase):
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


class OfferCreationApiTests(OfferApiBaseTestCase):
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

    def test_offer_requires_exactly_three_details(self):
        self.payload["details"] = self.payload["details"][:2]

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 400)


class OfferListApiTests(OfferApiBaseTestCase):
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


class OfferSingleApiBaseTestCase(OfferApiBaseTestCase):
    def setUp(self):
        super().setUp()
        created = self.client.post(self.url, self.payload, format="json").data
        self.offer_id = created["id"]
        self.detail_ids = {detail["offer_type"]: detail["id"] for detail in created["details"]}
        self.single_url = f"{self.url}{self.offer_id}/"
        self.missing_url = f"{self.url}{self.offer_id + 1}/"


class OfferRetrieveApiTests(OfferSingleApiBaseTestCase):
    def test_authenticated_user_retrieves_offer(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.get(self.single_url)

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.data.keys(),
            [
                "id",
                "user",
                "title",
                "image",
                "description",
                "created_at",
                "updated_at",
                "details",
                "min_price",
                "min_delivery_time",
            ],
        )
        self.assertEqual(response.data["id"], self.offer_id)
        self.assertEqual(response.data["user"], self.business_user.id)
        self.assertEqual(response.data["min_price"], 100)
        self.assertEqual(response.data["min_delivery_time"], 5)

    def test_offer_details_contain_absolute_urls(self):
        response = self.client.get(self.single_url)

        self.assertCountEqual(
            response.data["details"],
            [
                {"id": detail_id, "url": f"http://testserver/api/offerdetails/{detail_id}/"}
                for detail_id in self.detail_ids.values()
            ],
        )

    def test_retrieve_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.single_url)

        self.assertEqual(response.status_code, 401)

    def test_retrieve_unknown_offer_returns_404(self):
        response = self.client.get(self.missing_url)

        self.assertEqual(response.status_code, 404)


class OfferUpdateApiTests(OfferSingleApiBaseTestCase):
    def test_owner_updates_only_given_fields(self):
        response = self.client.patch(self.single_url, {"title": "Updated"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated")
        self.assertEqual(response.data["description"], self.payload["description"])
        self.assertEqual(len(response.data["details"]), 3)

    def test_update_response_contains_documented_fields(self):
        response = self.client.patch(self.single_url, {"title": "Updated"}, format="json")

        self.assertCountEqual(
            response.data.keys(),
            ["id", "title", "image", "description", "details"],
        )
        self.assertEqual(response.data["details"][0]["id"], self.detail_ids["basic"])
        self.assertIn("features", response.data["details"][0])

    def test_owner_updates_single_detail_by_offer_type(self):
        changes = {"title": "Basic Updated", "price": 120, "offer_type": "basic"}

        response = self.client.patch(self.single_url, {"details": [changes]}, format="json")

        self.assertEqual(response.status_code, 200)
        details = {detail["offer_type"]: detail for detail in response.data["details"]}
        self.assertEqual(details["basic"]["id"], self.detail_ids["basic"])
        self.assertEqual(details["basic"]["title"], "Basic Updated")
        self.assertEqual(float(details["basic"]["price"]), 120)
        self.assertEqual(details["basic"]["revisions"], 2)
        self.assertEqual(details["standard"]["title"], "Standard Design")

    def test_detail_price_is_rendered_as_number(self):
        changes = {"price": 120, "offer_type": "basic"}

        response = self.client.patch(self.single_url, {"details": [changes]}, format="json")

        self.assertEqual(response.json()["details"][0]["price"], 120)

    def test_update_never_creates_or_removes_details(self):
        self.client.patch(
            self.single_url,
            {"details": [{"price": 120, "offer_type": "premium"}]},
            format="json",
        )

        self.assertCountEqual(
            OfferDetail.objects.filter(offer_id=self.offer_id).values_list("id", flat=True),
            self.detail_ids.values(),
        )

    def test_detail_without_offer_type_is_rejected(self):
        body = {"title": "Updated", "details": [{"price": 120}]}

        response = self.client.patch(self.single_url, body, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Offer.objects.get(id=self.offer_id).title, self.payload["title"])

    def test_duplicate_offer_type_is_rejected(self):
        details = [{"price": 120, "offer_type": "basic"}, {"price": 130, "offer_type": "basic"}]

        response = self.client.patch(self.single_url, {"details": details}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_offer_type_missing_on_offer_is_rejected(self):
        OfferDetail.objects.filter(id=self.detail_ids["premium"]).delete()
        body = {"details": [{"price": 120, "offer_type": "premium"}]}

        response = self.client.patch(self.single_url, body, format="json")

        self.assertEqual(response.status_code, 400)

    def test_invalid_field_value_is_rejected(self):
        body = {"details": [{"price": "abc", "offer_type": "basic"}]}

        response = self.client.patch(self.single_url, body, format="json")

        self.assertEqual(response.status_code, 400)

    def test_update_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.patch(self.single_url, {"title": "Updated"}, format="json")

        self.assertEqual(response.status_code, 401)

    def test_only_owner_can_update_offer(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.patch(self.single_url, {"title": "Updated"}, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Offer.objects.get(id=self.offer_id).title, self.payload["title"])

    def test_update_unknown_offer_returns_404(self):
        response = self.client.patch(self.missing_url, {"title": "Updated"}, format="json")

        self.assertEqual(response.status_code, 404)

    def test_put_is_not_allowed(self):
        response = self.client.put(self.single_url, self.payload, format="json")

        self.assertEqual(response.status_code, 405)


class OfferDeleteApiTests(OfferSingleApiBaseTestCase):
    def test_owner_deletes_offer_with_details(self):
        response = self.client.delete(self.single_url)

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
        self.assertFalse(Offer.objects.filter(id=self.offer_id).exists())
        self.assertFalse(OfferDetail.objects.filter(offer_id=self.offer_id).exists())

    def test_delete_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.single_url)

        self.assertEqual(response.status_code, 401)

    def test_only_owner_can_delete_offer(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.delete(self.single_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Offer.objects.filter(id=self.offer_id).exists())

    def test_delete_unknown_offer_returns_404(self):
        response = self.client.delete(self.missing_url)

        self.assertEqual(response.status_code, 404)
