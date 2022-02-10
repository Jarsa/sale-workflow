# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2022, Jarsa Sistemas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    invoice_policy = fields.Selection(
        [
            ("order", "Invoice what is ordered"),
            ("delivery", "Invoice what is delivered"),
        ],
        string="Invoicing Policy",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        help="Ordered Quantity: Invoice quantities ordered by the customer.\n"
        "Delivered Quantity: Invoice quantities delivered to the customer.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrder, self).default_get(fields_list)
        default_sale_invoice_policy = self.env["ir.default"].get(
            "product.template", "invoice_policy"
        )
        if "invoice_policy" not in res:
            res.update({"invoice_policy": default_sale_invoice_policy})
        return res
