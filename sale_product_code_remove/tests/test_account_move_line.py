# Copyright 2026 Jarsa, (<https://www.jarsa.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.fields import Command

from odoo.addons.sale.tests.common import TestSaleCommon


class TestAccountMoveLineCodeRemove(TestSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coded_product = cls.env["product.product"].create(
            {
                "name": "Coded Product",
                "type": "service",
                "default_code": "TEST-CODE",
                "description_sale": "Sale description",
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [Command.create({"product_id": cls.coded_product.id})],
            }
        )
        cls.order.action_confirm()
        cls.invoice = cls.order._create_invoices()
        cls.invoice_line = cls.invoice.invoice_line_ids

    def test_invoice_label_without_default_code(self):
        self.assertEqual(self.invoice_line.label, "Coded Product\nSale description")

    def test_invoice_inverse_label(self):
        self.invoice_line.label = "Coded Product\nCustom description"
        self.assertEqual(self.invoice_line.name, "Custom description")
        self.assertEqual(self.invoice_line.label, "Coded Product\nCustom description")

    def test_invoice_label_from_previous_version(self):
        self.invoice_line.name = "Coded Product\nSale description"
        self.assertEqual(self.invoice_line.label, "Coded Product\nSale description")

    def test_manual_invoice_keeps_default_code(self):
        invoice = self._create_invoice(
            partner_id=self.partner_a,
            invoice_line_ids=[Command.create({"product_id": self.coded_product.id})],
        )
        self.assertEqual(
            invoice.invoice_line_ids.label,
            "[TEST-CODE] Coded Product\nSale description",
        )

    def test_invoice_report_without_default_code(self):
        self.invoice.action_post()
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", self.invoice.ids
        )[0]
        self.assertIn(b"Coded Product", html)
        self.assertNotIn(b"TEST-CODE", html)
