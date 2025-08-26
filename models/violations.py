from odoo import fields, models

class Violations(models.Model):
    _name = 'inspection.violations'
    _description = 'Violations'

    name = fields.Char(
        string="Violation Name",
        required=True
    )