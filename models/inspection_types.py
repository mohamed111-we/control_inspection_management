from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class InspectionType(models.Model):
    _name = 'inspection.type'
    _description = 'Inspection Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Inspection Type Name",
        required=True,
        tracking=True
    )

    is_active = fields.Boolean(
        string="Is Active",
        default=True,
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')],
        string='Status', default='draft', tracking=True
    )
    inspection_items = fields.One2many(
        'inspection.item',
        'inspection_type_id',
        string="Inspection Items"
    )

    # -----------------------------------------------------------------------------------------------------------------
    inspection_type_name = fields.Char(
        string='Inspection Type Name',
        required=True,
    )

    description = fields.Text(
        string='Description',
        required=True
    )

    inspection_check_list = fields.Char(
        string="Inspection check list",
        required=True
    )

    resources = fields.Char(
        string="Resources",
        required=True
    )

    output_template = fields.Char(
        string="Output template",
        required=True
    )

    required_minimum_score = fields.Integer(
        string="Required Minimum Score",
        help="Minimum score required for passing"
    )

    # -----------------------------------------------------------------------------------------------------------------

    history_ids = fields.One2many(
        'inspection.history',
        'inspection_type_id',
        string="History"
    )

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('inspection.type') or _('New')
        return super(InspectionType, self).create(vals)

    def action_to_approve(self):
        self.write({'state': 'to_approve'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    @api.constrains('inspection_type_name')
    def _check_lenght_inspection_type_name(self):
        for rec in self:
            if len(rec.inspection_type_name) > 250:
                raise ValidationError(
                    _("Inspection Type Name must not exceed 250 characters.")
                )

    @api.constrains('description')
    def _check_lenght_description(self):
        for rec in self:
            if len(rec.description) > 500:
                raise ValidationError(
                    _("Description must not exceed 500 characters.")
                )


class InspectionItem(models.Model):
    _name = 'inspection.item'
    _description = 'Inspection Item'
    _order = 'sequence'

    name = fields.Char(string="Item Name", required=True)
    item_type = fields.Selection(
        [('item', 'Item'),
         ('section', 'Section')],
        string="Item Type",
        required=True,
        compute="_compute_item_type",
        store=1
    )
    response = fields.Char(string="Response")
    is_mandatory = fields.Boolean(string="Is Mandatory")
    sequence = fields.Integer(string="Sequence", default=10)
    inspection_type_id = fields.Many2one('inspection.type', string="Inspection Type")
    correct_response = fields.Boolean(string="Correct")
    score = fields.Float(string="Score")
    display_type = fields.Selection(
        selection=[
            ('line_item', "Item"),
            ('line_section', "Section"),
        ],
        default=False
    )

    @api.depends("display_type")
    def _compute_item_type(self):
        for rec in self:
            if rec.display_type == "line_item":
                print(rec.display_type == "line_item")
                rec.item_type = "item"
            else:
                print(rec.display_type == "line_section")
                rec.item_type = "section"

    def create_inspection_history(self, change_description=None):
        self.env['inspection.history'].create({
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'inspection_type_id': self.inspection_type_id.id,
            'change_description': change_description
        })

    @api.constrains('score')
    def _check_lenght_score(self):
        for rec in self:
            if rec.score > 100:
                raise ValidationError(
                    _("Score must not exceed 100.")
                )

    @api.model
    def create(self, vals):
        if vals.get('display_type'):
            vals.update(response=False, is_mandatory=False)
        record = super().create(vals)
        record.create_inspection_history(
            _(f"The Item : {record.name} has been Created.")
        )
        return record

    def write(self, values):
        if 'display_type' in values and self.filtered(
                lambda line: line.display_type != values.get('display_type')
        ):
            raise UserError(
                _("You cannot change the type of an inspection item. Instead, you should delete the current item and create a new one of the proper type.")
            )

        for rec in self:
            changes = []
            for field_name, new_val in values.items():
                if field_name in rec._fields:
                    old_val = rec[field_name]
                    if rec._fields[field_name].type == "many2one":
                        old_val = old_val.display_name if old_val else "None"
                        new_record = rec.env[rec._fields[field_name].comodel_name].browse(new_val)
                        new_val = new_record.display_name if new_record.exists() else "None"
                    if old_val != new_val:
                        changes.append(
                            f"Field {field_name} changed from "
                            f"{old_val} to {new_val}"
                        )

            if changes:
                rec.create_inspection_history("<br/>".join(changes))

        return super().write(values)

    def unlink(self):
        for rec in self:
            rec.create_inspection_history(
                _(f"The Item : {rec.name} has been deleted.")
            )
        return super(InspectionItem, self).unlink()


class InspectionHistory(models.Model):
    _name = 'inspection.history'
    _description = 'Inspection History'

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    change_date = fields.Datetime(string="Change Date", default=fields.Datetime.now)
    change_description = fields.Text(string="Change Description")
    inspection_type_id = fields.Many2one('inspection.type', string="Inspection Type")
