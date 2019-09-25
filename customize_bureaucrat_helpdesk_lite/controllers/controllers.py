# -*- coding: utf-8 -*-
from odoo import http

# class CustomizeBureaucratHelpdeskLite(http.Controller):
#     @http.route('/customize_bureaucrat_helpdesk_lite/customize_bureaucrat_helpdesk_lite/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customize_bureaucrat_helpdesk_lite/customize_bureaucrat_helpdesk_lite/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customize_bureaucrat_helpdesk_lite.listing', {
#             'root': '/customize_bureaucrat_helpdesk_lite/customize_bureaucrat_helpdesk_lite',
#             'objects': http.request.env['customize_bureaucrat_helpdesk_lite.customize_bureaucrat_helpdesk_lite'].search([]),
#         })

#     @http.route('/customize_bureaucrat_helpdesk_lite/customize_bureaucrat_helpdesk_lite/objects/<model("customize_bureaucrat_helpdesk_lite.customize_bureaucrat_helpdesk_lite"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customize_bureaucrat_helpdesk_lite.object', {
#             'object': obj
#         })