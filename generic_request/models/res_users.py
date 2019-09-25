from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def action_show_related_requests(self):
        return self.partner_id.action_show_related_requests()
