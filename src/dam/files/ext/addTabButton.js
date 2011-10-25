Ext.ux.AddTabButton = (function() {
    function onTabPanelRender() {
        this.addTab = this.itemTpl.insertBefore(this.edge, {
            id: this.id + 'addTabButton',
            cls: 'add-tab',
            text: this.addTabText || '&#160',
            iconCls: ''
        }, true);
        this.addTab.child('em.x-tab-left').setStyle('padding-right', '6px');
        this.addTab.child('a.x-tab-right').setStyle('padding-left', '6px');
        new Ext.ToolTip({
            target: this.addTab,
            bodyCfg: {
                html: 'Add new tab'
            }
        });
        this.addTab.on({
            mousedown: stopEvent,
            click: onAddTabClick,
            scope: this
        });
    }

    function createScrollers() {
        this.scrollerWidth = (this.scrollRightWidth = this.scrollRight.getWidth()) + this.scrollLeft.getWidth();
    }

    function autoScrollTabs() {
        var scrollersVisible = (this.scrollLeft && this.scrollLeft.isVisible()),
            pos = this.tabPosition == 'top' ? 'header' : 'footer';
        if (scrollersVisible) {
            if (this.addTab.dom.parentNode === this.strip.dom) {
                if (this.addTabWrap) {
                    this.addTabWrap.show();
                } else {
                    this.addTabWrap = this[pos].createChild({
                        cls: 'x-tab-strip-wrap',
                        style: {
                            position: 'absolute',
                            right: (this.scrollRightWidth + 1) + 'px',
                            top: 0,
                            width: '30px',
                            margin: 0
                        }, cn: {
                            tag: 'ul',
                            cls: 'x-tab-strip x-tab-strip-' + this.tabPosition,
                            style: {
                                width: 'auto'
                            }
                        }
                    });
                    this.addTabWrap.setVisibilityMode(Ext.Element.DISPLAY);
                    this.addTabUl = this.addTabWrap.child('ul');
                }
                this.addTabUl.dom.appendChild(this.addTab.dom);
                this.addTab.setStyle('float', 'none');
            }
            this.stripWrap.setWidth(this[pos].getWidth(true) - (this.scrollerWidth + 31));
            this.stripWrap.setStyle('margin-right', (this.scrollRightWidth + 31) + 'px');
        } else {
//          
            if ((this.addTab.dom.parentNode !== this.strip.dom)) {
                var notEnoughSpace = (((this[pos].getWidth(true) - this.edge.getOffsetsTo(this.stripWrap)[0])) < 33)
                this.addTabWrap.hide();
                this.addTab.setStyle('float', '');
                this.strip.dom.insertBefore(this.addTab.dom, this.edge.dom);
                this.stripWrap.setWidth(this.stripWrap.getWidth() + 31);
                if (notEnoughSpace) {
                    this.autoScrollTabs();
                }
            }
        }
    }

    function autoSizeTabs() {
        this.addTab.child('.x-tab-strip-inner').setStyle('width', '14px');
    }

    function stopEvent(e) {
        e.stopEvent();
    }

    function onAddTabClick() {
        this.setActiveTab(this.add(this.createTab? this.createTab() : {
            title: 'New Tab'
        }));
    }

    return {
        init: function(tp) {
            if (tp instanceof Ext.TabPanel) {
                tp.onRender = tp.onRender.createSequence(onTabPanelRender);
                tp.createScrollers = tp.createScrollers.createSequence(createScrollers);
                tp.autoScrollTabs = tp.autoScrollTabs.createSequence(autoScrollTabs);
                tp.autoSizeTabs = tp.autoSizeTabs.createSequence(autoSizeTabs);
            }
        }
    };
})();