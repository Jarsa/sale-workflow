# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestSaleOrder(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env["res.partner"]
        cls.company = Partner.create({"name": "Customer Co", "is_company": True})
        cls.delivery_1, cls.delivery_2, cls.invoice, cls.person = Partner.create(
            [
                {"name": "Warehouse", "parent_id": cls.company.id, "type": "delivery"},
                {"name": "Shop", "parent_id": cls.company.id, "type": "delivery"},
                {"name": "Billing", "parent_id": cls.company.id, "type": "invoice"},
                {"name": "John", "parent_id": cls.company.id, "type": "contact"},
            ]
        )
        cls.person_alone = Partner.create({"name": "Jane"})
        cls.other = Partner.create({"name": "Other"})
        cls.env.user.group_ids += cls.env.ref("account.group_delivery_invoice_address")

    def _order(self, partner):
        with Form(self.env["sale.order"]) as order_form:
            order_form.partner_id = partner
        return order_form.save()

    def test_defaults_with_addresses(self):
        order = self._order(self.company)
        self.assertEqual(order.partner_invoice_id, self.company)
        self.assertIn(order.partner_shipping_id, self.delivery_1 | self.delivery_2)
        self.assertEqual(
            set(order.partner_invoice_domain[0][2]),
            set((self.company | self.invoice).ids),
        )
        self.assertEqual(
            set(order.partner_shipping_domain[0][2]),
            set((self.delivery_1 | self.delivery_2).ids),
        )

    def test_defaults_without_addresses(self):
        order = self._order(self.person_alone)
        self.assertEqual(order.partner_invoice_id, self.person_alone)
        self.assertEqual(order.partner_shipping_id, self.person_alone)
        self.assertEqual(
            order.partner_shipping_domain, [("id", "in", self.person_alone.ids)]
        )

    def test_changing_customer_resets_addresses(self):
        order = self._order(self.company)
        with Form(order) as order_form:
            order_form.partner_id = self.person_alone
        self.assertEqual(order.partner_invoice_id, self.person_alone)
        self.assertEqual(order.partner_shipping_id, self.person_alone)

    def test_other_addresses_are_refused(self):
        order = self._order(self.company)
        order.partner_shipping_id = self.delivery_2
        order.partner_invoice_id = self.invoice
        with self.assertRaises(ValidationError):
            order.partner_shipping_id = self.other
        with self.assertRaises(ValidationError):
            order.partner_shipping_id = self.person
        with self.assertRaises(ValidationError):
            order.partner_invoice_id = self.delivery_1
