# Copyright 2026 Jarsa, (<https://www.jarsa.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.fields import Command

from odoo.addons.sale.tests.common import SaleCommon


class TestSaleProductCodeRemove(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coded_product, cls.no_description_product = cls.env[
            "product.product"
        ].create(
            [
                {
                    "name": "Coded Product",
                    "default_code": "TEST-CODE",
                    "description_sale": "Sale description",
                },
                {"name": "No Description Product", "default_code": "TEST-NODESC"},
            ]
        )
        cls.order = cls._create_so(
            user_id=cls._test_user.id,
            order_line=[Command.create({"product_id": cls.coded_product.id})],
        )
        cls.line = cls.order.order_line

    def test_label_without_default_code(self):
        self.assertEqual(self.line.label, "Coded Product\nSale description")
        self.assertNotIn("TEST-CODE", self.line.label)

    def test_label_without_description(self):
        line = self._create_so(
            user_id=self._test_user.id,
            order_line=[Command.create({"product_id": self.no_description_product.id})],
        ).order_line
        self.assertEqual(line.label, "No Description Product")

    def test_inverse_label(self):
        self.line.label = "Coded Product\nCustom description"
        self.assertEqual(self.line.name, "Custom description")
        self.assertEqual(self.line.label, "Coded Product\nCustom description")

    def test_label_from_previous_version(self):
        # Lines created before 18.0 already hold the product name, without
        # the code, at the beginning of their description.
        self.line.name = "Coded Product\nSale description"
        self.assertEqual(self.line.label, "Coded Product\nSale description")

    def test_report_without_default_code(self):
        html = self.env["ir.actions.report"]._render_qweb_html(
            "sale.action_report_saleorder", self.order.ids
        )[0]
        self.assertIn(b"Coded Product", html)
        self.assertNotIn(b"TEST-CODE", html)
