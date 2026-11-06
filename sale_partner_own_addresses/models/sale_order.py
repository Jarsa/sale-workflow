# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_invoice_domain = fields.Binary(compute="_compute_partner_address_domains")
    partner_shipping_domain = fields.Binary(compute="_compute_partner_address_domains")

    def _get_partner_addresses(self, address_type):
        """Addresses of the customer of the given type.

        Read with sudo: the salesperson of the order is not always allowed to
        read the customer (record rules), and the domains must still be
        computed to display the order.
        """
        self.ensure_one()
        partner = self.partner_id.sudo()
        return partner.child_ids.filtered(lambda p: p.type == address_type).sudo(False)

    def _get_partner_invoice_addresses(self):
        """The customer itself and its invoice addresses."""
        return self.partner_id | self._get_partner_addresses("invoice")

    def _get_partner_shipping_addresses(self):
        """The delivery addresses of the customer, or the customer itself
        when it has none."""
        return self._get_partner_addresses("delivery") or self.partner_id

    @api.depends("partner_id", "partner_id.child_ids.type")
    def _compute_partner_address_domains(self):
        for order in self:
            order.partner_invoice_domain = [
                ("id", "in", order._get_partner_invoice_addresses().ids)
            ]
            order.partner_shipping_domain = [
                ("id", "in", order._get_partner_shipping_addresses().ids)
            ]

    @api.depends("partner_id")
    def _compute_partner_invoice_id(self):
        for order in self:
            order.partner_invoice_id = order.partner_id

    @api.depends("partner_id")
    def _compute_partner_shipping_id(self):
        res = super()._compute_partner_shipping_id()
        for order in self.filtered("partner_id"):
            addresses = order._get_partner_shipping_addresses()
            if order.partner_shipping_id not in addresses:
                order.partner_shipping_id = addresses[:1]
        return res

    @api.constrains("partner_id", "partner_invoice_id", "partner_shipping_id")
    def _check_partner_addresses(self):
        for order in self:
            if order.partner_invoice_id not in order._get_partner_invoice_addresses():
                raise ValidationError(
                    self.env._(
                        "The invoice address of %s must be the customer "
                        "or one of its invoice addresses.",
                        order.display_name,
                    )
                )
            if order.partner_shipping_id not in order._get_partner_shipping_addresses():
                raise ValidationError(
                    self.env._(
                        "The delivery address of %s must be one of the delivery "
                        "addresses of the customer, or the customer itself when "
                        "it has none.",
                        order.display_name,
                    )
                )
