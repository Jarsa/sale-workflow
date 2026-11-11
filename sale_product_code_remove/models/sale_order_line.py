# Copyright 2023 Jarsa, (<https://www.jarsa.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_label(self):
        return super(
            SaleOrderLine, self.with_context(display_default_code=False)
        )._compute_label()

    def _inverse_label(self):
        return super(
            SaleOrderLine, self.with_context(display_default_code=False)
        )._inverse_label()
