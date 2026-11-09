from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail
from orders_app.models import Order


class OrderApiBaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = self.create_user("customer", "customer")
        self.business = self.create_user("business", "business")
        self.other_customer = self.create_user("othercustomer", "customer")
        self.other_business = self.create_user("otherbusiness", "business")
        self.url = "/api/orders/"

    def create_user(self, username, user_type):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="safe-password",
            type=user_type,
        )

    def create_order(self, customer, business, **overrides):
        data = {
            "customer_user": customer,
            "business_user": business,
            "title": "Logo Design",
            "revisions": 3,
            "delivery_time_in_days": 5,
            "price": 150,
            "features": ["Logo Design", "Visitenkarten"],
            "offer_type": "basic",
        }
        data.update(overrides)
        return Order.objects.create(**data)


class OrderListApiTests(OrderApiBaseTestCase):
    def setUp(self):
        super().setUp()
        self.own_order = self.create_order(self.customer, self.business)
        self.foreign_order = self.create_order(self.other_customer, self.other_business)

    def order_ids(self, response):
        return [order["id"] for order in response.data]

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_customer_sees_own_orders(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order_ids(response), [self.own_order.id])

    def test_business_user_sees_orders_as_provider(self):
        self.client.force_authenticate(user=self.business)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order_ids(response), [self.own_order.id])

    def test_user_does_not_see_foreign_orders(self):
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.get(self.url)

        self.assertEqual(self.order_ids(response), [self.foreign_order.id])

    def test_list_is_empty_without_orders(self):
        self.client.force_authenticate(user=self.create_user("newcustomer", "customer"))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_response_is_plain_list_with_expected_fields(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.url)

        self.assertIsInstance(response.data, list)
        self.assertCountEqual(
            response.data[0].keys(),
            [
                "id",
                "customer_user",
                "business_user",
                "title",
                "revisions",
                "delivery_time_in_days",
                "price",
                "features",
                "offer_type",
                "status",
                "created_at",
                "updated_at",
            ],
        )

    def test_response_contains_order_values(self):
        self.client.force_authenticate(user=self.customer)

        order = self.client.get(self.url).data[0]

        self.assertEqual(order["customer_user"], self.customer.id)
        self.assertEqual(order["business_user"], self.business.id)
        self.assertEqual(order["price"], 150)
        self.assertEqual(order["features"], ["Logo Design", "Visitenkarten"])
        self.assertEqual(order["status"], "in_progress")


class OrderCreateApiTests(OrderApiBaseTestCase):
    def setUp(self):
        super().setUp()
        offer = Offer.objects.create(user=self.business, title="Grafikdesign")
        self.detail = OfferDetail.objects.create(
            offer=offer,
            title="Logo Design",
            revisions=3,
            delivery_time_in_days=5,
            price=150,
            features=["Logo Design", "Visitenkarten"],
            offer_type="basic",
        )

    def post_as(self, user, data):
        self.client.force_authenticate(user=user)
        return self.client.post(self.url, data, format="json")

    def test_create_requires_authentication(self):
        response = self.client.post(self.url, {"offer_detail_id": self.detail.id}, format="json")

        self.assertEqual(response.status_code, 401)

    def test_business_user_cannot_create_order(self):
        response = self.post_as(self.business, {"offer_detail_id": self.detail.id})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Order.objects.count(), 0)

    def test_customer_creates_order(self):
        response = self.post_as(self.customer, {"offer_detail_id": self.detail.id})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_copies_offer_detail_values(self):
        order = self.post_as(self.customer, {"offer_detail_id": self.detail.id}).data

        self.assertEqual(order["title"], "Logo Design")
        self.assertEqual(order["revisions"], 3)
        self.assertEqual(order["delivery_time_in_days"], 5)
        self.assertEqual(order["price"], 150)
        self.assertEqual(order["features"], ["Logo Design", "Visitenkarten"])
        self.assertEqual(order["offer_type"], "basic")

    def test_order_gets_customer_business_and_status(self):
        order = self.post_as(self.customer, {"offer_detail_id": self.detail.id}).data

        self.assertEqual(order["customer_user"], self.customer.id)
        self.assertEqual(order["business_user"], self.business.id)
        self.assertEqual(order["status"], "in_progress")

    def test_response_has_expected_fields(self):
        order = self.post_as(self.customer, {"offer_detail_id": self.detail.id}).data

        self.assertCountEqual(
            order.keys(),
            [
                "id", "customer_user", "business_user", "title", "revisions",
                "delivery_time_in_days", "price", "features", "offer_type",
                "status", "created_at", "updated_at",
            ],
        )

    def test_missing_offer_detail_id_returns_400(self):
        response = self.post_as(self.customer, {})

        self.assertEqual(response.status_code, 400)

    def test_invalid_offer_detail_id_returns_400(self):
        response = self.post_as(self.customer, {"offer_detail_id": "abc"})

        self.assertEqual(response.status_code, 400)

    def test_unknown_offer_detail_returns_404(self):
        response = self.post_as(self.customer, {"offer_detail_id": 9999})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Order.objects.count(), 0)
