odoo.define('crnd_web_list_popover_widget.DynamicPopoverMixin', function (require) {
    "use strict";

    var Core = require('web.core');
    var QWeb = Core.qweb;

    var DynamicPopoverMixin = {

        events: {
            'mousedown': 'popover_hide',
        },

        init: function () {
            this.maxWidth = this.nodeOptions.max_width;
            this.popoverMaxWidth = this.nodeOptions.popover_max_width;
            this.lineClamp = this.nodeOptions.line_clamp;
            this.placement = this.nodeOptions.placement || "auto";
            this.animation = this.nodeOptions.animation || false;
            this.allow_html = false;
            // IE do not supports webkit, and we detected IE <=10, 11, 12
            this.isIE = navigator.userAgent.search(/(MSIE|Trident|Edge)/) > -1;
        },

        start: function () {
            if (this.mode === 'readonly') {
                this.popover_init();
            }
        },

        destroy: function () {
            this.popover_destroy();
        },

        get_popover_template: function (template, style) {
            return QWeb.render(
                template || "PopoverTemplate",
                {popover_style:
                    style || "max-width: " + this.popoverMaxWidth + ";"}
            );
        },

        get_popover_content: function () {
            return this.value;
        },

        get_popover_options: function () {
            return {
                template: this.get_popover_template(),
                content: this.get_popover_content(),
                trigger: 'hover',
                placement: this.placement,
                container: 'body',
                html: this.allow_html,
                animation: this.animation,
            };
        },

        popover_init: function () {
            var style = {
                "max-width": this.maxWidth,
                "-webkit-line-clamp": this.lineClamp,
            };
            this.$el = this.$el.css(style).addClass(
                this.isIE ? 'o_popover_widget_ie' : 'o_popover_widget');
            this.$el.popover(this.get_popover_options());
        },

        popover_destroy: function () {
            $('div.popover').popover('destroy');
        },

        popover_hide: function () {
            $('div.popover').popover('hide');
        },
    };
    return DynamicPopoverMixin;
});
