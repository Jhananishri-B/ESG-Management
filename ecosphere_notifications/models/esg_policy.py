# -*- coding: utf-8 -*-
from odoo import api, models

class PolicyAcknowledgement(models.Model):
    _inherit = 'policy.acknowledgement'

    @api.model_create_multi
    def create(self, vals_list):
        """Override to send an email when an acknowledgement request is created."""
        records = super().create(vals_list)
        
        template = self.env.ref('ecosphere_notifications.email_template_policy_ack_request', raise_if_not_found=False)
        if template:
            for record in records:
                if record.state == 'pending':
                    template.send_mail(record.id, force_send=False)
                    
        return records
