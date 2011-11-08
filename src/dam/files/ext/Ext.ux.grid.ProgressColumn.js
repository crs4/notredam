/**
 * Ext.ux.grid.ProgressColumn - Ext.ux.grid.ProgressColumn is a grid plugin that
 * shows a progress bar for a number between 0 and 100 to indicate some sort of
 * progress. The plugin supports all the normal cell/column operations including
 * sorting, editing, dragging, and hiding. It also supports special progression
 * coloring or standard Ext.ProgressBar coloring for the bar.
 *
 * @author Benjamin Runnels <kraven@kraven.org>
 * @copyright (c) 2008, by Benjamin Runnels
 * @date 06 June 2008
 * @version 1.1
 *
 * @license Ext.ux.grid.ProgressColumn is licensed under the terms of the Open
 *          Source LGPL 3.0 license. Commercial use is permitted to the extent
 *          that the code/component(s) do NOT become part of another Open Source
 *          or Commercially licensed development library or toolkit without
 *          explicit permission.
 *
 * License details: http://www.gnu.org/licenses/lgpl.html
 */

Ext.namespace('Ext.ux.grid');

Ext.ux.grid.ProgressColumn = function(config) {
  Ext.apply(this, config);
  this.renderer = this.renderer.createDelegate(this);
  this.addEvents('action');
  Ext.ux.grid.ProgressColumn.superclass.constructor.call(this);
};

Ext.extend(Ext.ux.grid.ProgressColumn, Ext.util.Observable, {
  /**
   * @cfg {String} colored determines whether use special progression coloring
   *      or the standard Ext.ProgressBar coloring for the bar (defaults to
   *      false)
   */
  textPst : '%',
  /**
   * @cfg {String} colored determines whether use special progression coloring
   *      or the standard Ext.ProgressBar coloring for the bar (defaults to
   *      false)
   */
  colored : false,
  /**
   * @cfg {String} actionEvent Event to trigger actions, e.g. click, dblclick,
   *      mouseover (defaults to 'dblclick')
   */
  actionEvent : 'dblclick',

  init : function(grid) {
    this.grid = grid;
    this.view = grid.getView();

    if (this.editor && grid.isEditor) {
      var cfg = {
        scope : this
      };
      cfg[this.actionEvent] = this.onClick;
      grid.afterRender = grid.afterRender.createSequence(function() {
        this.view.mainBody.on(cfg);
      }, this);
    }
  },

  onClick : function(e, target) {
    var rowIndex = e.getTarget('.x-grid3-row').rowIndex;
    var colIndex = this.view.findCellIndex(target.parentNode.parentNode);

    var t = e.getTarget('.x-progress-text');
    if (t) {
      this.grid.startEditing(rowIndex, colIndex);
    }
  },

  renderer : function(v, p, record) {
    var style = '';
    var textClass = (v < 55) ? 'x-progress-text-back' : 'x-progress-text-front' + (Ext.isIE6 ? '-ie6' : '');

    //ugly hack to deal with IE6 issue
    var text = String.format('</div><div class="x-progress-text {0}" style="width:100%;" id="{1}">{2}</div></div>',
      textClass, Ext.id(), v + this.textPst
    );
    text = (v<96) ? text.substring(0, text.length - 6) : text.substr(6);

    if (this.colored == true) {
      if (v <= 100 && v > 66)
        style = '-green';
      if (v < 67 && v > 33)
        style = '-orange';
      if (v < 34)
        style = '-red';
    }

    p.css += ' x-grid3-progresscol';
    return String.format(
      '<div class="x-progress-wrap"><div class="x-progress-inner"><div class="x-progress-bar{0}" style="width:{1}%;">{2}</div>' +
      '</div>', style, v, text
    );
  }
});