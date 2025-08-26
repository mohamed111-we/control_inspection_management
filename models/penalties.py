from odoo import fields, models


class Penalties(models.Model):
    _name = 'inspection.penalties'
    _description = 'Penalties'

    name = fields.Char(
        string="Penalty Name",
        required=True
    )

    description = fields.Char(
        string="Description"
    )

    type = fields.Selection(
        string="Type",
        selection=[('warning', 'Warning'), ('fine', 'Fine')],
        default='warning',
        help="Penalty type"
    )
    status = fields.Selection(
        string="Status",
        selection=[('issued', 'Issued'), ('paid', 'Paid'),('waived', 'Waived')],
        default='issued',
        help="Penalty status"
    )
    amount = fields.Float(
        string="Amount",
        help = "Penalty amount"
    )