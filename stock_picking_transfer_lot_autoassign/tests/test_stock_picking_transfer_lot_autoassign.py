# -*- coding: utf-8 -*-
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl).

from odoo.tests import common
from odoo.exceptions import UserError


class TestStockPickingTransferLotAutoAssign(common.TransactionCase):

    def setUp(self):
        super(TestStockPickingTransferLotAutoAssign, self).setUp()
        self.partner = self.browse_ref('base.res_partner_2')
        self.warehouse = self.env['stock.warehouse'].search([], limit=1)
        self.picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
        })
        self.Move = self.env['stock.move']
        self.product = self.browse_ref('product.product_product_5')
        self.product.tracking = 'lot'
        self.product_no_lot = self.browse_ref('product.product_product_1')
        self.product_no_lot.tracking = 'none'
        self.lot1 = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
            'name': 'Lot 1',
        })
        self.quant1 = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.picking.location_id.id,
            'quantity': 6,
            'lot_id': self.lot1.id,
        })
        self.lot2 = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
            'name': 'Lot 2',
        })
        self.quant2 = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.picking.location_id.id,
            'quantity': 10,
            'lot_id': self.lot2.id,
        })
        self.Move.create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom': self.product.uom_id.id,
            'picking_id': self.picking.id,
            'location_id': self.picking.location_id.id,
            'location_dest_id': self.picking.location_dest_id.id})

    def test_transfer(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        self.assertEqual(len(self.picking.move_lines), 1)
        self.assertEqual(len(self.picking.move_line_ids), 2)
        self.assertEqual(self.picking.move_line_ids[0].ordered_qty, 6)
        self.assertEqual(self.picking.move_line_ids[1].ordered_qty, 4)
        self.assertEqual(self.picking.move_lines.quantity_done, 0)
        res = self.picking.button_validate()
        self.assertEqual(res['res_model'], 'stock.immediate.transfer')
        self.env['stock.immediate.transfer'].browse(res['res_id']).process()
        self.assertEqual(self.picking.move_lines.quantity_done, 10)

    def test_failing_transfer(self):
        self.picking.picking_type_id.avoid_internal_assignment = True
        self.picking.action_confirm()
        self.picking.action_assign()
        self.assertEqual(len(self.picking.move_lines), 1)
        self.assertEqual(len(self.picking.move_line_ids), 2)
        self.assertEqual(self.picking.move_line_ids[0].ordered_qty, 6)
        self.assertEqual(self.picking.move_line_ids[1].ordered_qty, 4)
        self.assertEqual(self.picking.move_lines.quantity_done, 0)
        with self.assertRaises(UserError):
            self.picking.button_validate()
