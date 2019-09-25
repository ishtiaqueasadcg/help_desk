# -*- coding: utf-8 -*-

from odoo import models, fields, api

AVAILABLE_PRIORITIES = [
    ('1', 'Normal'),
    ('2', 'Low'),
    ('3', 'High'),
    ('4', 'Very High'),
]

class InheritedRequest(models.Model):
     _inherit = 'request.request'
     set_priority = fields.Selection(AVAILABLE_PRIORITIES, select=True)

