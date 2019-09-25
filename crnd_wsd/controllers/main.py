import logging

from odoo import _
from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.osv import expression
from odoo.exceptions import UserError, AccessError, ValidationError

from odoo.addons.website.controllers.main import QueryURL

from .controller_mixin import WSDControllerMixin

_logger = logging.getLogger(__name__)


GROUP_USER_ADVANCED = (
    'crnd_wsd.group_service_desk_website_user_advanced'
)

ITEMS_PER_PAGE = 20

# NOTE: here is name collision with request, so be careful, when use name
# `request`. To avoid this name collision use names `req` and reqs` for
# `request.request` records


class WebsiteRequest(WSDControllerMixin, http.Controller):

    def _requests_get_request_domain_base(self, search, **post):
        domain = []
        if search:
            domain += [
                '|', '|', '|', ('name', 'ilike', search),
                ('category_id.name', 'ilike', search),
                ('type_id.name', 'ilike', search),
                ('request_text', 'ilike', search)]
        return domain

    def _requests_get_request_domains(self, search, **post):
        domain = self._requests_get_request_domain_base(search, **post)

        return {
            'all': domain,
            'open': domain + [('closed', '=', False)],
            'closed': domain + [('closed', '=', True)],
            'my': domain + [
                ('closed', '=', False),
                '|',
                ('user_id', '=', request.env.user.id),
                ('created_by_id', '=', request.env.user.id),
            ],
        }

    def _requests_list_get_extra_context(self, req_status, search, **post):
        return {}

    def _request_page_get_extra_context(self, req_id, **post):
        return {}

    @http.route(['/requests',
                 "/requests/<string:req_status>",
                 '/requests/<string:req_status>/page/<int:page>'],
                type='http', auth="user", website=True)
    def requests(self, req_status='my', page=0, search="", **post):
        if req_status not in ('my', 'open', 'closed', 'all'):
            return request.not_found()

        Request = request.env['request.request']

        url = '/requests/' + req_status
        keep = QueryURL(
            url, [], search=search, **post)
        domains = self._requests_get_request_domains(search, **post)

        req_count = {
            'all': Request.search_count(domains['all']),
            'open': Request.search_count(domains['open']),
            'closed': Request.search_count(domains['closed']),
            'my': Request.search_count(domains['my']),
        }

        # make pager
        pager = request.website.pager(
            url=url,
            total=req_count[req_status],
            page=page,
            step=ITEMS_PER_PAGE,
            url_args=dict(
                post, search=search),
        )

        # search the count to display, according to the pager data
        reqs = request.env['request.request'].search(
            domains[req_status], limit=ITEMS_PER_PAGE, offset=pager['offset'])
        values = {
            'search': search,
            'reqs': reqs.sudo(),
            'pager': pager,
            'default_url': url,
            'req_status': req_status,
            'req_count': req_count,
            'keep': keep,
        }

        values.update(self._requests_list_get_extra_context(
            req_status=req_status, search=search, **post
        ))

        return request.render(
            'crnd_wsd.wsd_requests', values)

    def _request_get_available_routes(self, req, **post):
        Route = http.request.env['request.stage.route']
        result = Route.browse()

        user = http.request.env.user
        group_ids = user.sudo().groups_id.ids
        action_routes = Route.search(expression.AND([
            [('request_type_id', '=', req.sudo().type_id.id)],
            [('stage_from_id', '=', req.sudo().stage_id.id)],
            [('website_published', '=', True)],
            expression.OR([
                [('allowed_user_ids', '=', False)],
                [('allowed_user_ids', '=', user.id)],
            ]),
            expression.OR([
                [('allowed_group_ids', '=', False)],
                [('allowed_group_ids', 'in', group_ids)],
            ]),
        ]))

        for route in action_routes:
            try:
                route._ensure_can_move(req)
            except AccessError:  # pylint: disable=except-pass
                pass
            except ValidationError:  # pylint: disable=except-pass
                pass
            else:
                result += route
        return result

    @http.route(["/requests/request/<int:req_id>"],
                type='http', auth="user", website=True)
    def request(self, req_id, **kw):
        values = {}
        reqs = request.env['request.request'].search(
            [('id', '=', req_id)])

        if not reqs:
            raise request.not_found()

        reqs.check_access_rights('read')
        reqs.check_access_rule('read')

        action_routes = self._request_get_available_routes(reqs, **kw)

        disable_new_comments = (
            reqs.closed and reqs.sudo().type_id.website_comments_closed
        )

        values.update({
            'req': reqs.sudo(),
            'action_routes': action_routes.sudo(),
            'can_change_request_text': reqs.can_change_request_text,
            'disable_composer': disable_new_comments,
        })

        values.update(self._request_page_get_extra_context(req_id, **kw))

        return request.render(
            "crnd_wsd.wsd_request", values)

    @http.route(["/requests/new"], type='http', auth="user",
                methods=['GET'], website=True)
    def request_new(self, **kwargs):
        # May be overridden to change start step
        return request.redirect(QueryURL(
            '/requests/new/step/category', [])(**kwargs))

    def _request_new_get_public_categs_domain(self, category_id=None, **post):
        if request.env.user.has_group(GROUP_USER_ADVANCED):
            return []
        return [('website_published', '=', True)]

    def _request_new_get_public_categs(self, category_id=None, **post):
        categs = request.env['request.category'].search(
            self._request_new_get_public_categs_domain(
                category_id=category_id, **post))
        return categs.filtered(
            lambda r: self._request_new_get_public_types(
                category_id=r.id, **post))

    @http.route(["/requests/new/step/category"], type='http', auth="user",
                methods=['GET', 'POST'], website=True)
    def request_new_select_category(self, category_id=None, **kwargs):
        keep = QueryURL('', [], category_id=category_id, **kwargs)
        req_category = self._id_to_record('request.category', category_id)
        if request.httprequest.method == 'POST' and req_category:
            return request.redirect(keep(
                '/requests/new/step/type',
                category_id=req_category.id, **kwargs))

        public_categories = self._request_new_get_public_categs(
            category_id=category_id, **kwargs).filtered(
                lambda r: self._request_new_get_public_types(
                    category_id=r.id, **kwargs))

        if len(public_categories) <= 1 and not http.request.debug:
            return request.redirect(keep(
                '/requests/new/step/type',
                category_id=public_categories.id, **kwargs))

        values = {
            'req_categories': public_categories,
            'req_category_sel': req_category,
            'keep': keep,
        }

        return request.render(
            "crnd_wsd.wsd_requests_new_select_category", values)

    def _request_new_get_public_types(self, type_id=None, category_id=None,
                                      **kwargs):
        domain = []
        if not request.env.user.has_group(GROUP_USER_ADVANCED):
            domain += [('website_published', '=', True)]

        if category_id:
            domain += [('category_ids.id', '=', category_id)]
        else:
            domain += [('category_ids', '=', False)]

        return request.env['request.type'].search(domain)

    @http.route(["/requests/new/step/type"], type='http', auth="user",
                methods=['GET', 'POST'], website=True)
    def request_new_select_type(self, type_id=None, category_id=None,
                                **kwargs):
        keep = QueryURL('', [], type_id=type_id, category_id=category_id,
                        **kwargs)
        req_type = self._id_to_record('request.type', type_id)
        req_category = self._id_to_record('request.category', category_id)
        if request.httprequest.method == 'POST' and req_type:
            return request.redirect(keep(
                '/requests/new/step/data', type_id=req_type.id,
                category_id=req_category.id, **kwargs))

        public_types = self._request_new_get_public_types(
            type_id=type_id, category_id=req_category.id, **kwargs)

        if len(public_types) == 1 and not http.request.debug:
            return request.redirect(keep(
                '/requests/new/step/data', type_id=public_types.id,
                category_id=req_category.id, **kwargs))

        values = {
            'req_types': public_types,
            'req_type_sel': req_type,
            'req_category': req_category,
            'keep': keep,
        }

        return request.render(
            "crnd_wsd.wsd_requests_new_select_type", values)

    def _request_new_process_data(self, req_type, req_category=False,
                                  req_text=None, **post):
        return {
            'req_type': req_type,
            'req_category': req_category,
            'req_text': req_text,
        }

    def _request_new_validate_data(self, req_type, req_category,
                                   req_text, data, **post):
        errors = []
        if not req_text or req_text == '<p><br></p>':
            errors.append(_(
                "Request text is empty!"))
        return errors

    def _request_new_prepare_data(self, req_type, req_category,
                                  req_text, **post):
        return {
            'category_id': req_category and req_category.id,
            'type_id': req_type.id,
            'request_text': req_text,
        }

    @http.route(["/requests/new/step/data"],
                type='http', auth="user",
                methods=['GET', 'POST'], website=True)
    def request_new_fill_data(self, type_id=None, category_id=None,
                              req_text=None, **kwargs):
        req_type = self._id_to_record('request.type', type_id)

        if not req_type:
            return request.redirect(QueryURL(
                '/requests/new/step/type', [])(
                    type_id=type_id, category_id=category_id, **kwargs))

        req_category = self._id_to_record('request.category', category_id)

        values = self._request_new_process_data(
            req_type, req_category, req_text=req_text, **kwargs)

        if request.httprequest.method == 'POST':
            req_data = self._request_new_prepare_data(
                req_type, req_category, req_text, **kwargs)

            validation_errors = self._request_new_validate_data(
                req_type, req_category, req_text, req_data, **kwargs)

            if not validation_errors:
                try:
                    req = request.env['request.request'].create(req_data)
                except (UserError, AccessError, ValidationError) as exc:
                    validation_errors.append(ustr(exc))
                except Exception:
                    _logger.error(
                        "Error caught during request creation", exc_info=True)
                    validation_errors.append(
                        _("Unknown server error. See server logs."))
                else:
                    return request.render(
                        "crnd_wsd.wsd_requests_new_congratulation",
                        {'req': req.sudo()})

            values['validation_errors'] = validation_errors
            # TODO: update values with posted values to save data entered by
            # user

        return request.render(
            "crnd_wsd.wsd_requests_new_request_data", values)
