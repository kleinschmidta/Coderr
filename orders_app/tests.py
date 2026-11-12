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
        self.foreign_order = self.create_order(
            self.other_customer, self.other_business)

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
        self.client.force_authenticate(
            user=self.create_user("newcustomer", "customer"))

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
        response = self.client.post(
            self.url, {"offer_detail_id": self.detail.id}, format="json")

        self.assertEqual(response.status_code, 401)

    def test_business_user_cannot_create_order(self):
        response = self.post_as(
            self.business, {"offer_detail_id": self.detail.id})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Order.objects.count(), 0)

    def test_customer_creates_order(self):
        response = self.post_as(
            self.customer, {"offer_detail_id": self.detail.id})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_copies_offer_detail_values(self):
        order = self.post_as(
            self.customer, {"offer_detail_id": self.detail.id}).data

        self.assertEqual(order["title"], "Logo Design")
        self.assertEqual(order["revisions"], 3)
        self.assertEqual(order["delivery_time_in_days"], 5)
        self.assertEqual(order["price"], 150)
        self.assertEqual(order["features"], ["Logo Design", "Visitenkarten"])
        self.assertEqual(order["offer_type"], "basic")

    def test_order_gets_customer_business_and_status(self):
        order = self.post_as(
            self.customer, {"offer_detail_id": self.detail.id}).data

        self.assertEqual(order["customer_user"], self.customer.id)
        self.assertEqual(order["business_user"], self.business.id)
        self.assertEqual(order["status"], "in_progress")

    def test_response_has_expected_fields(self):
        order = self.post_as(
            self.customer, {"offer_detail_id": self.detail.id}).data

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


class OrderUpdateApiTests(OrderApiBaseTestCase):
    def setUp(self):
        super().setUp()
        self.order = self.create_order(self.customer, self.business)

    def patch_as(self, user, data):
        self.client.force_authenticate(user=user)
        return self.client.patch(f"{self.url}{self.order.id}/", data, format="json")

    def test_no_authentication_returns_401(self):
        response = self.client.patch(
            f"{self.url}{self.order.id}/", {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_customer_cannot_update_order(self):
        response = self.patch_as(self.customer, {"status": "completed"})
        self.assertEqual(response.status_code, 403)

    def test_foreign_business_cannot_update_order(self):
        response = self.patch_as(self.other_business, {"status": "completed"})
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "in_progress")

    def test_business_can_update_order_status(self):
        response = self.patch_as(self.business, {"status": "completed"})
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "completed")

    def test_invalid_status_value_returns_400(self):
        response = self.patch_as(self.business, {"status": "invalid_status"})
        self.assertEqual(response.status_code, 400)

    def test_missing_status_field_returns_400(self):
        response = self.patch_as(self.business, {})
        self.assertEqual(response.status_code, 400)

    def test_more_than_one_field_returns_400(self):
        response = self.patch_as(
            self.business, {"status": "completed", "title": "New Title"})
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.title, "Logo Design")

    def test_unknown_id_returns_404(self):
        self.client.force_authenticate(user=self.business)
        response = self.client.patch(
            f"{self.url}9999/", {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_response_contains_all_order_fields_after_update(self):
        response = self.patch_as(self.business, {"status": "completed"})
        self.assertCountEqual(
            response.data.keys(),
            [
                "id", "customer_user", "business_user", "title", "revisions",
                "delivery_time_in_days", "price", "features", "offer_type",
                "status", "created_at", "updated_at",
            ],
        )


class OrderDeleteApiTests(OrderApiBaseTestCase):
    def setUp(self):
        super().setUp()
        self.order = self.create_order(self.customer, self.business)
        self.staff = get_user_model().objects.create_user(
            username="staff", email="staff@example.com",
            password="safe-password", type="customer", is_staff=True)

    def delete_as(self, user):
        self.client.force_authenticate(user=user)
        return self.client.delete(f"{self.url}{self.order.id}/")

    def test_no_authentication_returns_401(self):
        response = self.client.delete(f"{self.url}{self.order.id}/")
        self.assertEqual(response.status_code, 401)

    def test_customer_cannot_delete_order(self):
        response = self.delete_as(self.customer)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_business_cannot_delete_order(self):
        response = self.delete_as(self.business)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_staff_can_delete_order(self):
        response = self.delete_as(self.staff)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())

    def test_unknown_id_returns_404(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.delete(f"{self.url}9999/")
        self.assertEqual(response.status_code, 404)


class OrderCountApiTests(OrderApiBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/order-count/"

    def get_as(self, user, business_id):
        self.client.force_authenticate(user=user)
        return self.client.get(f"{self.url}{business_id}/")

    def test_no_authentication_returns_401(self):
        response = self.client.get(f"{self.url}{self.business.id}/")
        self.assertEqual(response.status_code, 401)

    def test_unknown_business_returns_404(self):
        response = self.get_as(self.customer, 9999)
        self.assertEqual(response.status_code, 404)

    def test_customer_id_returns_404(self):
        response = self.get_as(self.customer, self.other_customer.id)
        self.assertEqual(response.status_code, 404)

    def test_business_without_orders_returns_zero(self):
        response = self.get_as(self.customer, self.business.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"order_count": 0})

    def test_counts_only_in_progress_orders(self):
        self.create_order(self.customer, self.business)
        self.create_order(self.customer, self.business)
        self.create_order(self.customer, self.business, status="completed")
        response = self.get_as(self.customer, self.business.id)
        self.assertEqual(response.data, {"order_count": 2})

    def test_ignores_orders_of_other_business(self):
        self.create_order(self.customer, self.business)
        self.create_order(self.customer, self.other_business)
        response = self.get_as(self.customer, self.business.id)
        self.assertEqual(response.data, {"order_count": 1})

    def test_business_user_can_query_count(self):
        response = self.get_as(self.other_business, self.business.id)
        self.assertEqual(response.status_code, 200)
