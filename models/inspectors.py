from odoo import fields, models

class Inspectors(models.Model):
    _name = 'inspection.inspector'
    _description = 'Inspectors'

    name = fields.Many2one(
        'hr.employee',
        string="Inspector Name",
        required=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Inspector Department",
        related='name.department_id',
        readonly=True
    )
    is_active = fields.Boolean(string="Is Active", default=True)