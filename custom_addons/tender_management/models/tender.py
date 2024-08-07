from odoo import api, fields, models
from datetime import date


class TenderManagement(models.Model):
    _name = "tender.management"
    _description = "Tender Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('res.users', string="Purchase Representative")
    ref = fields.Char(string="Reference", readonly=True, copy=False, default='New')
    partner_id = fields.Many2many('res.partner', string="Vendor")
    date_created = fields.Date(string='Start Date', default=fields.Datetime.now)
    date_bid_to_end = fields.Date(string='End Date', default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('submit', 'SUBMITTED'),
        ('approve', 'APPROVE'),
        ('approved', 'IN PROGRESS'),
        ('done', 'DONE'),
        ('cancel', 'CANCEL')], string='State', default='draft', required=True
    )
    days_to_deadline = fields.Integer(string='Days To Deadline', compute='_compute_days')
    bid_ids = fields.One2many('tender.bid', 'tender_id', string="Bids")
    bid_count = fields.Integer(string='Bid Count', compute='_compute_bid_count')
    tender_management_line_ids = fields.One2many('tender.management.line', 'tender_management_id', string='Tender Management Line')
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    category=fields.Char(string='Category')
    top_rank=fields.Char(string='Top Rank')
    is_active = fields.Boolean(string='Active', default=True)
    website_published = fields.Boolean('Publish on Website', copy=False)
    # bid_count = fields.Integer(string='Bids', compute='_compute_bid_count')
    rank = fields.Integer(string='Rank')

    @api.depends('date_created')
    def _compute_formatted_date(self):
        for record in self:
            if record.date_created:
                date_obj = fields.Date.from_string(record.date_created)
                record.formatted_date = f''' {date_obj.strftime("%d")} \n {date_obj.strftime("%b %Y")} '''
            else:
                record.formatted_date = ''

    @api.depends('date_bid_to_end')
    def _compute_days(self):
        for rec in self:
            today = date.today()
            if rec.date_bid_to_end:
                days_difference = (rec.date_bid_to_end - today).days
                rec.days_to_deadline = days_difference
            else:
                rec.days_to_deadline = 0

    @api.depends('bid_ids')
    def _compute_bid_count(self):
        for tender in self:
            tender.bid_count = len(tender.bid_ids)

    def action_approve(self):
        for rec in self:
            rec.state = 'approve'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'

    def action_submit(self):
        for rec in self:
            rec.state = 'submit'

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code('tender.management') or 'New'
        return super(TenderManagement, self).create(vals)

    def toggle_website_publish(self):
        for record in self:
            record.website_published = not record.website_published
        return True


class TenderManagementLine(models.Model):
    _name = 'tender.management.line'
    _description = "Tender Management Line"

    product_id = fields.Many2one('product.product', string='Products')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Uom',
        compute='_compute_product_uom_id', store=True, readonly=False, precompute=True,
        ondelete="restrict",
    )
    product_quantity = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Quantity',
        compute='_compute_product_uom_id', store=True, readonly=False, precompute=True,
        ondelete="restrict",
    )
    price_unit = fields.Float(string='Price', related='product_id.list_price')
    qty = fields.Integer(string='Quantity')
    default_code = fields.Char(related='product_id.default_code', string='Code')
    name = fields.Char(string='Description')
    tender_management_id = fields.Many2one('tender.management', string='Tender Management')


class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    def toggle_active(self):
        record_to_deactivate = self.filtered(lambda rec: rec._active_name and rec[rec._active_name])
        record_to_activate = self - record_to_deactivate
        record_to_deactivate.write({record_to_deactivate._active_name: False})
        record_to_activate.write({record_to_activate._active_name: True})