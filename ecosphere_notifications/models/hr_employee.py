# -*- coding: utf-8 -*-
from odoo import api, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def grant_xp(self, amount, reason, source_model=False, source_id=False, is_spendable=True):
        """Override to trigger email notification on level up."""
        self.ensure_one()
        old_level = self.esg_level
        
        # Call super which handles the actual ledger creation and XP recompute
        res = super().grant_xp(amount, reason, source_model, source_id, is_spendable)
        
        # Check if leveled up after the grant
        if self.esg_level > old_level:
            # Send Email via template
            template = self.env.ref('ecosphere_notifications.email_template_gamification_level_up', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=False)
                
        return res
