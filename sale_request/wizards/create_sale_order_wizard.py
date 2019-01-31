# Copyright 2019, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lpgl.html).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class CreateSaleOrderWizard(models.TransientModel):
    _name = 'create.sale.order.wizard'
    _description = 'Create Sale Orders From Sale Request'

    line_ids = fields.One2many(
        comodel_name='create.sale.order.wizard.line',
        inverse_name='wizard_id',
        string='Proposition Sale Order Lines',
    )
    request_line_id = fields.Many2one(
        comodel_name='sale.request.line',
        string='Sale Request Line',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    product_qty = fields.Float(
        string="Required Quantity",
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'),
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        readonly=True,
    )
    remaining_product_qty = fields.Float(
        string="Remaining Quantity",
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True,
    )
    has_lines = fields.Boolean(
        compute='_compute_has_lines',
    )

    @api.multi
    @api.depends('request_line_id')
    def _compute_has_lines(self):
        for rec in self:
            rec.has_lines = bool(rec.line_ids)

    @api.onchange('line_ids')
    def _onchange_qty_to_sale(self):
        if self.line_ids:
            remaining_product_qty = self.request_line_id.remaining_product_qty
            qty_to_sale = 0.0
            for line in self.line_ids:
                qty_to_sale += line.product_uom_id._compute_quantity(
                    line.qty_to_sale, self.product_uom_id)
            new_remaining_qty = remaining_product_qty - qty_to_sale
            if new_remaining_qty < 0:
                self.remaining_product_qty = remaining_product_qty
                return {
                    'warning': {
                        'title': _('Error!'),
                        'message': _('You cannot request more than the'
                                     ' initial demand of this sale request.'),
                    },
                }
            self.remaining_product_qty = new_remaining_qty

    @api.model
    def _prepare_item(self, line):
        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'product_uom_qty': line.product_uom_qty,
            'product_uom_id': line.product_uom.id,
            'order_id': line.order_id.id,
            'sale_line_id': line.id,
            'remaining_product_qty': line.remaining_product_qty,
            'qty_to_sale': 0,
        }

    @api.model
    def default_get(self, res_fields):
        res = super().default_get(res_fields)
        rqst_line = self.env['sale.request.line'].browse(
            self._context.get('active_ids'))
        order_lines = self.env['sale.order.line'].search(
            [('state', '=', 'sale'),
             ('product_id', '=', rqst_line.product_id.id),
             ('order_id.master_sale_order', '=', True),
             ('remaining_product_qty', '>', 0.0),
             ('order_id.partner_id', '=', rqst_line.request_id.partner_id.id)])
        wiz_lines = []
        for line in order_lines:
            wiz_lines.append((0, 0, self._prepare_item(line)))
        res.update({
            'request_line_id': rqst_line.id,
            'product_id': rqst_line.product_id.id,
            'product_qty': rqst_line.product_qty,
            'product_uom_id': rqst_line.product_uom_id.id,
            'remaining_product_qty': rqst_line.remaining_product_qty,
            'line_ids': wiz_lines,
        })
        return res

    @api.model
    def prepare_sale_order(self, request_id, sale_line_id):
        client_order_ref = False
        if sale_line_id:
            client_order_ref = sale_line_id.order_id.client_order_ref
        return {
            'partner_id': request_id.partner_id.id,
            'user_id': self.env.user.id,
            'company_id': request_id.company_id.id,
            'date_order': fields.Date.context_today(self),
            'client_order_ref': client_order_ref,
            'origin': request_id.name,
            'warehouse_id': request_id.warehouse_id.id,
        }

    @api.multi
    def prepare_sale_order_line(self,  order, params):
        request_line = self.request_line_id
        return {
            'product_id': request_line.product_id.id,
            'product_uom_qty': params['qty_to_sale'],
            'product_uom': params['product_uom'],
            'request_line_id': request_line.id,
            'parent_id': params['sale_line_id'],
            'order_id': order.id,
            'price_unit': request_line.product_id.list_price,
        }

    @api.multi
    def create_sale_order_no_ref(self):
        self.ensure_one()
        so_obj = self.env['sale.order']
        sol_obj = self.env['sale.order.line']
        request_line = self.request_line_id
        order = so_obj.create(self.prepare_sale_order(
            request_line.request_id, False))
        params = {
            'qty_to_sale': request_line.product_qty,
            'product_uom': request_line.product_uom_id.id,
            'sale_line_id': False,
        }
        values = self.prepare_sale_order_line(order, params)
        sol_obj.create(values)
        order.action_confirm()
        request_line.write({
            'state': 'done',
            'remaining_product_qty': 0.0
        })
        return {
            'name': _('Sale Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': order.id,
            'type': 'ir.actions.act_window',
            'context': {
                'create': False,
                'delete': False,
            }
        }

    @api.multi
    def create_sale_order(self):
        self.ensure_one()
        qty_to_sale = 0.0
        for line in self.line_ids:
            qty_to_sale += line.product_uom_id._compute_quantity(
                line.qty_to_sale, self.product_uom_id)
        if qty_to_sale > self.request_line_id.remaining_product_qty:
            raise UserError(
                _('Error! The quantity to sale is greather than'
                    ' the requested quantity.'))
        so_obj = self.env['sale.order']
        sol_obj = self.env['sale.order.line']
        request_line = self.request_line_id
        items = self.line_ids.filtered('qty_to_sale')
        rqst_remaining_product_qty = request_line.remaining_product_qty
        for item in items:
            order = so_obj.create(self.prepare_sale_order(
                request_line.request_id, item.sale_line_id))
            so_obj |= order
            sale_line = item.sale_line_id
            line_remaining_qty = item.product_uom_id._compute_quantity(
                sale_line.remaining_product_qty, request_line.product_uom_id)
            if (line_remaining_qty >= rqst_remaining_product_qty):
                rqst_remaining_product_qty -= (
                    item.product_uom_id._compute_quantity(
                        item.qty_to_sale, request_line.product_uom_id))
            params = {
                'qty_to_sale': item.qty_to_sale,
                'product_uom': item.product_uom_id.id,
                'sale_line_id': item.sale_line_id.id,
            }
            values = self.prepare_sale_order_line(order, params)
            sol_obj.create(values)
        for sale_order in so_obj:
            sale_order.action_confirm()
        if request_line.remaining_product_qty == 0.0:
            request_line.state = 'done'
        if len(so_obj) == 1:
            return {
                'name': _('Sale Order'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': order.id,
                'type': 'ir.actions.act_window',
                'context': {
                    'create': False,
                    'delete': False,
                }
            }
        else:
            return {
                'name': _('Sale Order'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'res_id': so_obj.ids,
                'type': 'ir.actions.act_window',
                'context': {
                    'create': False,
                    'delete': False,
                }
            }


class CreateSaleOrderWizardLine(models.TransientModel):
    _name = 'create.sale.order.wizard.line'
    _description = 'Lines to Create Sale Orders From Sale Request'

    wizard_id = fields.Many2one(
        comodel_name='create.sale.order.wizard',
        string='Wizard',
    )
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        readonly=True,
    )
    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order Line',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    name = fields.Text(
        string="Description",
    )
    product_uom_qty = fields.Float(
        string='Ordered Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    remaining_product_qty = fields.Float(
        string='Remaining Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='sale_line_id.product_uom',
    )
    qty_to_sale = fields.Float(
        string='Quantity to Sale',
        digits=dp.get_precision('Product Unit of Measure'),
    )

    @api.onchange('qty_to_sale')
    def _onchange_qty_to_sale(self):
        if self.qty_to_sale:
            remaining_product_qty = self.sale_line_id.remaining_product_qty
            new_remaining_qty = remaining_product_qty - self.qty_to_sale
            if new_remaining_qty < 0:
                self.remaining_product_qty = remaining_product_qty
                return {
                    'warning': {
                        'title': _('Error!'),
                        'message': _(
                            'You cannot request more than the '
                            'remaining qty of this master sale order.'),
                    },
                }
            self.remaining_product_qty = new_remaining_qty