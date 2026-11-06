# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Partner Own Addresses",
    "summary": "Top-level customers on sales orders, invoiced to themselves "
    "and delivered to their own addresses",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["sale"],
    "data": ["views/sale_order_views.xml"],
    "installable": True,
}
