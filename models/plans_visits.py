from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
import re


class InspectionPlan(models.Model):
    _name = 'inspection.plan'
    _description = 'Inspection Plan'

    name = fields.Char(string='Plan Name', required=True,translate=True,
        size=250)
    description = fields.Text(string='Description', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date',required=True)
    status = fields.Selection(
        [('draft', 'Draft'), ('completed', 'Completed')],
        string='Status',
        required=True,
        default='draft',
        help="Status"
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help="Attachments"
    )
    planned_visits_ids = fields.One2many('inspection.visit', 'plan_id', string='Planned Visits')
    visits_count = fields.Integer(compute='_compute_visits_count', string='Visits Count')

    @api.constrains('start_date')
    def _check_start_date_today(self):
        for record in self:
            if record.start_date and record.start_date < fields.Date.today():
                raise ValidationError(_("Start Date must be greater than or equal to today's date."))

    @api.constrains('start_date', 'end_date')
    def _check_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("End Date must be greater than or equal to Start Date."))

    @api.constrains('attachment_ids')
    def _check_attachment_type(self):
        for record in self:
            for attachment in record.attachment_ids:
                if attachment.mimetype not in ['application/pdf', 'application/msword', 'image/jpeg', 'image/png']:
                    raise ValidationError(_("Invalid file type. Please upload a PDF, Word, or Image file."))

    @api.constrains('planned_visits_ids')
    def _check_unique_visit_name(self):
        for record in self:
            visit_names = [visit.name for visit in record.planned_visits_ids]
            if len(visit_names) != len(set(visit_names)):
                raise ValidationError(
                    'An inspection visit with the same name already exists. Please use a unique name.')


    @api.constrains('planned_visits_ids')
    def _check_unique_visit_name(self):
        for record in self:
            visit_names = [visit.name for visit in record.planned_visits_ids]
            if len(visit_names) != len(set(visit_names)):
                raise ValidationError(
                    'An inspection visit with the same name already exists. Please use a unique name.')

    def _compute_visits_count(self):
        for plan in self:
            plan.visits_count = len(plan.planned_visits_ids)

    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Plan Visits',
            'res_model': 'inspection.visit',
            'view_mode': 'tree,form,calendar',
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id},
        }


class InspectionVisit(models.Model):
    _name = 'inspection.visit'
    _description = 'Inspection Visit'

    name = fields.Char(string='Title', required=True,size=250)
    target_entity = fields.Char(string='Target Entity', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('submitted', 'Submitted'),
    ], string='Status', default='new')
    plan_id = fields.Many2one('inspection.plan', string='Inspection Plan', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    inspector = fields.Many2one(
        'inspection.inspector',
        string="Inspector",
        required=True
    )

    def write(self, vals):
        """
        Override the write method to restrict editing if the status is not 'Scheduled'.
        """
        for visit in self:
            if visit.status != 'new':
                raise UserError("You cannot edit a visit that is not in 'Scheduled' status.")
        return super(InspectionVisit, self).write(vals)

    def unlink(self):
        """
        Override the unlink method to restrict deletion if the status is not 'Scheduled'.
        """
        for visit in self:
            if visit.status != 'new':
                raise UserError("You cannot delete a visit that is not in 'Scheduled' status.")
        return super(InspectionVisit, self).unlink()

    def action_open_inspection_plan(self):
        """
        Action to open the related Inspection Plan form view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'inspection.plan',
            'res_id': self.plan_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.constrains('name')
    def _check_name_length(self):
        for record in self:
            if len(record.name) > 250:
                raise ValidationError(f"The {record.name} field cannot exceed 250 characters.")

    @api.constrains('start_date', 'end_date')
    def _check_date_order(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError("End Date must be greater than or equal to Start Date.")

    @api.constrains('attachment_ids')
    def _check_attachment_type(self):
        for record in self:
            for attachment in record.attachment_ids:
                if attachment.mimetype not in ['application/pdf', 'application/msword', 'image/jpeg', 'image/png']:
                    raise ValidationError("Invalid file type. Please upload a PDF, Word, or Image file.")

    @api.constrains('attachment_ids')
    def _check_attachment_size(self):
        for record in self:
            for attachment in record.attachment_ids:
                if attachment.file_size > 25 * 1024 * 1024:
                    raise ValidationError("File size exceeds the maximum limit of 25MB.")

    @api.constrains('name', 'target_entity', 'start_date', 'end_date', 'attachment_ids')
    def _validate_all_fields(self):
        """Comprehensive validation of all field formats"""
        error_messages = []

        # Validate name
        if not self.name or not isinstance(self.name, str):
            error_messages.append(_("Title: Invalid data format"))
        elif not self.name.strip():
            error_messages.append(_("Title: Cannot be empty"))
        elif len(self.name) > 250:
            error_messages.append(_("Title: Cannot exceed 250 characters"))

        # Validate target entity
        if not self.target_entity or not isinstance(self.target_entity, str):
            error_messages.append(_("Target Entity: Invalid data format"))
        elif not self.target_entity.strip():
            error_messages.append(_("Target Entity: Cannot be empty"))
        elif not re.match(r'^[\w\s\-]+$', self.target_entity):
            error_messages.append(_("Target Entity: Contains invalid characters"))

        # Validate dates
        try:
            if self.start_date:
                datetime.strptime(str(self.start_date), '%Y-%m-%d')
            if self.end_date:
                datetime.strptime(str(self.end_date), '%Y-%m-%d')
        except ValueError:
            error_messages.append(_("Date fields: Invalid format (use YYYY-MM-DD)"))

        # Validate date logic
        if self.start_date and self.end_date and self.start_date > self.end_date:
            error_messages.append(_("End Date must be after Start Date"))

        # Validate attachments (if any)
        for attachment in self.attachment_ids:
            if attachment.file_size > 25 * 1024 * 1024:
                error_messages.append(_("Attachment size exceeds 25MB limit"))
            if attachment.mimetype not in ['application/pdf',
                                           'application/msword',
                                           'image/jpeg',
                                           'image/png']:
                error_messages.append(_("Invalid file type for attachments"))

        if error_messages:
            full_message = _(
                "One or more fields contain invalid data. Please review and correct:\n\n") + \
                           "\n".join(f"- {msg}" for msg in error_messages)
            raise ValidationError(full_message)
