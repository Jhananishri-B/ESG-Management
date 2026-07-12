# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import requests
import json

class AiPolicyGenerator(models.TransientModel):
    _name = 'ai.policy.generator'
    _description = 'AI Policy Generator Wizard'

    policy_id = fields.Many2one('esg.policy', string='Policy', required=True, default=lambda self: self._default_policy_id())
    policy_name = fields.Char(related='policy_id.name', readonly=True)
    
    prompt = fields.Text(string='Prompt Instructions', 
                         default="Generate a professional ESG policy for our company based on the policy title. "
                                 "Include sections for Purpose, Scope, Guidelines, and Enforcement.", 
                         required=True)
    
    generated_content = fields.Html(string='Generated Content', readonly=True)
    state = fields.Selection([('init', 'Init'), ('generated', 'Generated')], default='init')

    def _default_policy_id(self):
        return self.env.context.get('active_id')

    def action_generate(self):
        """ Calls OpenAI API to generate policy content. Uses a mock response if no API key is configured. """
        api_key = self.env['ir.config_parameter'].sudo().get_param('ecosphere_ai.openai_api_key')
        
        if not api_key:
            # Fallback/Mock behavior for demo purposes without requiring real API keys
            self.generated_content = f"""
                <h3>Purpose</h3>
                <p>The purpose of the <strong>{self.policy_name}</strong> is to establish clear guidelines for sustainable practices.</p>
                <h3>Scope</h3>
                <p>This policy applies to all employees and contractors.</p>
                <h3>Guidelines</h3>
                <ul>
                    <li>Reduce waste and carbon emissions.</li>
                    <li>Promote social responsibility.</li>
                    <li>Ensure strict adherence to ethical governance.</li>
                </ul>
                <p><em>(Note: This is a mock response. Configure your OpenAI API Key in Settings for real AI generation.)</em></p>
            """
            self.state = 'generated'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'ai.policy.generator',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        # Real API Call
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        
        system_msg = "You are an expert ESG compliance officer. Write professional corporate policies in HTML format."
        user_msg = f"{self.prompt}\n\nPolicy Title: {self.policy_name}"
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.7,
        }
        
        try:
            response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            self.generated_content = result['choices'][0]['message']['content']
            self.state = 'generated'
        except Exception as e:
            raise UserError(f"Failed to generate policy via AI: {str(e)}")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.policy.generator',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply(self):
        """ Applies the generated content to the policy document. """
        self.policy_id.write({'content': self.generated_content})
        return {'type': 'ir.actions.act_window_close'}
