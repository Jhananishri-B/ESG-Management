# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CarbonTransaction(models.Model):
    """
    Carbon Transaction: Records a single carbon emission event.

    Each transaction captures:
      - The source (purchase order, manufacturing, fleet expense, manual)
      - The emission factor used
      - The quantity of activity and resulting kg CO₂e
      - The responsible department

    After creation/update, the department's total_carbon_kg is recalculated
    and the ESG score is propagated upward.
    """
    _name = 'carbon.transaction'
    _description = 'Carbon Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference', required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('carbon.transaction') or 'New')
    date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    description = fields.Char(string='Description')

    # Source
    source_type = fields.Selection([
        ('purchase',      'Purchase Order'),
        ('manufacturing', 'Manufacturing'),
        ('fleet',         'Fleet / Vehicle'),
        ('electricity',   'Electricity Bill'),
        ('air_travel',    'Air Travel'),
        ('waste',         'Waste Disposal'),
        ('water',         'Water Consumption'),
        ('material',      'Raw Material'),
        ('manual',        'Manual Entry'),
        ('other',         'Other'),
    ], string='Source Type', required=True, default='manual', tracking=True)

    # Source document references (optional)
    source_purchase_id = fields.Many2one(
        'purchase.order', string='Purchase Order',
        ondelete='set null', index=True)
    source_document = fields.Char(string='Source Document Reference')

    # Emission calculation
    emission_factor_id = fields.Many2one(
        'emission.factor', string='Emission Factor',
        required=True, tracking=True,
        ondelete='restrict')
    activity_quantity = fields.Float(
        string='Activity Quantity', required=True, digits=(10, 4),
        help='Amount of activity (e.g., litres of fuel, kWh, km)')
    activity_unit = fields.Char(
        string='Unit', related='emission_factor_id.unit', readonly=True, store=True)
    factor_value = fields.Float(
        string='Factor (kg CO₂e/unit)',
        related='emission_factor_id.factor_value', readonly=True, store=True)
    carbon_kg = fields.Float(
        string='Carbon (kg CO₂e)', compute='_compute_carbon_kg',
        store=True, digits=(10, 3), tracking=True)
    scope = fields.Selection(
        related='emission_factor_id.scope', string='GHG Scope', store=True, readonly=True)

    # Organization
    department_id = fields.Many2one(
        'esg.department', string='Department',
        required=True, tracking=True, ondelete='restrict', index=True)

    # Status
    state = fields.Selection([
        ('draft',     'Draft'),
        ('confirmed', 'Confirmed'),
        ('verified',  'Verified'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Verification
    verified_by = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_on = fields.Datetime(string='Verified On', readonly=True)
    notes = fields.Text(string='Notes')

    # Computed flags
    exceeds_threshold = fields.Boolean(
        string='Exceeds Threshold', compute='_compute_exceeds_threshold', store=True)

    @api.depends('activity_quantity', 'factor_value')
    def _compute_carbon_kg(self):
        for tx in self:
            tx.carbon_kg = tx.activity_quantity * tx.factor_value

    @api.depends('department_id', 'carbon_kg')
    def _compute_exceeds_threshold(self):
        threshold_pct = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'ecosphere.carbon_threshold_pct', '90'))
        for tx in self:
            dept = tx.department_id
            if dept and dept.carbon_target_kg:
                pct = (dept.total_carbon_kg / dept.carbon_target_kg) * 100
                tx.exceeds_threshold = pct >= threshold_pct
            else:
                tx.exceeds_threshold = False

    # ── State Transitions ──────────────────────────────────────────────
    def action_confirm(self):
        for tx in self:
            if tx.state != 'draft':
                raise UserError('Only draft transactions can be confirmed.')
            tx.state = 'confirmed'
            tx._update_department_score()

    def action_verify(self):
        self.write({
            'state': 'verified',
            'verified_by': self.env.uid,
            'verified_on': fields.Datetime.now(),
        })

    def action_cancel(self):
        for tx in self:
            if tx.state == 'verified':
                raise UserError('Verified transactions cannot be cancelled.')
            old_state = tx.state
            tx.state = 'cancelled'
            if old_state == 'confirmed':
                tx._update_department_score(reverse=True)

    def action_reset_draft(self):
        self.filtered(lambda t: t.state == 'cancelled').write({'state': 'draft'})

    # ── Department Score Update ────────────────────────────────────────
    def _update_department_score(self, reverse=False):
        """
        Recalculate department total carbon and update ESG scores.
        Called after confirm/cancel.
        """
        depts = self.mapped('department_id')
        for dept in depts:
            confirmed_txs = self.search([
                ('department_id', '=', dept.id),
                ('state', 'in', ['confirmed', 'verified']),
            ])
            total = sum(confirmed_txs.mapped('carbon_kg'))
            dept.write({'total_carbon_kg': total})
            # Update env_score based on carbon vs target
            if dept.carbon_target_kg > 0:
                ratio = 1 - min(total / dept.carbon_target_kg, 1.5)
                env_score = max(round(ratio * 100, 2), 0)
                dept.write({'env_score': env_score})
            _logger.info(
                'Department %s carbon updated: %.2f kg CO₂e (env_score: %.1f)',
                dept.name, total, dept.env_score)

    # ── ORM Hooks ─────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'carbon.transaction') or 'CTX-0001'
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if 'activity_quantity' in vals or 'emission_factor_id' in vals:
            confirmed = self.filtered(lambda t: t.state in ('confirmed', 'verified'))
            if confirmed:
                confirmed._update_department_score()
        return result

    # ── Factory Methods ───────────────────────────────────────────────
    @api.model
    def create_from_purchase(self, purchase_order):
        """
        Create carbon transactions from a confirmed purchase order.
        Matches products with their ESG profiles and emission factors.
        """
        created = self.env['carbon.transaction']
        for line in purchase_order.order_line:
            profile = line.product_id.product_tmpl_id.esg_profile_id
            if not profile or not profile.emission_factor_id:
                continue
            tx = self.create({
                'source_type': 'purchase',
                'source_purchase_id': purchase_order.id,
                'source_document': purchase_order.name,
                'emission_factor_id': profile.emission_factor_id.id,
                'activity_quantity': line.product_qty * profile.emission_per_unit,
                'department_id': (
                    purchase_order.partner_id.esg_department_id.id
                    if hasattr(purchase_order.partner_id, 'esg_department_id')
                    else self.env['esg.department'].search([], limit=1).id
                ),
                'description': f'Auto: {purchase_order.name} — {line.product_id.name}',
                'state': 'draft',
            })
            created |= tx
        return created

    @api.model
    def _cron_auto_confirm_draft(self):
        """Scheduled: auto-confirm old draft transactions."""
        cutoff = fields.Date.subtract(fields.Date.today(), days=7)
        old_drafts = self.search([
            ('state', '=', 'draft'),
            ('date', '<=', cutoff),
        ])
        old_drafts.action_confirm()
        _logger.info('Auto-confirmed %d carbon transactions.', len(old_drafts))


class PurchaseOrderCarbon(models.Model):
    """
    Extends purchase.order to add ESG carbon tracking integration.
    """
    _inherit = 'purchase.order'

    carbon_tx_ids = fields.One2many(
        'carbon.transaction', 'source_purchase_id',
        string='Carbon Transactions')
    carbon_tx_count = fields.Integer(
        string='Carbon Transactions', compute='_compute_carbon_tx_count')
    total_carbon_kg = fields.Float(
        string='Estimated Carbon (kg CO₂e)',
        compute='_compute_total_carbon_kg', digits=(10, 2))

    def _compute_carbon_tx_count(self):
        for po in self:
            po.carbon_tx_count = len(po.carbon_tx_ids)

    @api.depends('carbon_tx_ids.carbon_kg')
    def _compute_total_carbon_kg(self):
        for po in self:
            po.total_carbon_kg = sum(po.carbon_tx_ids.mapped('carbon_kg'))

    def button_confirm(self):
        """Override: create carbon transactions on PO confirmation."""
        result = super().button_confirm()
        for po in self:
            try:
                self.env['carbon.transaction'].create_from_purchase(po)
            except Exception as e:
                _logger.warning('Carbon transaction creation failed for %s: %s', po.name, e)
        return result

    def action_view_carbon_transactions(self):
        return {
            'name': f'Carbon Transactions — {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'carbon.transaction',
            'view_mode': 'list,form',
            'domain': [('source_purchase_id', '=', self.id)],
            'context': {'default_source_purchase_id': self.id},
        }
