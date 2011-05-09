Ext.namespace('Ext.ux');

/**
 * @class Ext.ux.StarRating
 * @extends Ext.form.Field
 * 
 * Ext.ux.StarRating
 * @author S. Alexandre Lemaire (Saeven)
 * 
 * Stand-alone or form component object that provides a visual rating system.
 * (c) 2007, saeven.net consulting inc.
 * http://saeven.net/ext
 *
 * Distributed under the Ext dual-licensing model
 * http://extjs.com/license
 *
 * @constructor
 * Creates a new StarRating object
 * @param {Ext.Element} el The target element, null if inserted into a field (optional)
 * @param {Object} config Configuration options, accepts Ext.form.Field parameters in addition to ( totalStars, average )
 */
Ext.ux.StarRating = function( el, config ){	
	this.totalStars	= 5;	
	this.focusClass	= '';	
	
	if( typeof el == 'object' && !config ){
		config 	= el;
		el 		= null;
	}
	else{
		if( el ){
	    	this.primaryContainer 	= Ext.get( el );
			this.primaryContainer.addClass( 'rating' );	
		}
	}
	
	Ext.ux.StarRating.superclass.constructor.call( this, config );	
		
	if( config ){
	   this.cancelRating = config.cancelRating;
	   		
		if( config.totalStars ){
			this.totalStars = config.totalStars;
			delete( config.totalStars );		
		}
		
		if( config.average ){
			this.average = config.average;
			delete( config.average );
		}
	}
	
    this.addEvents({ rate : true });		
	if( el ){
		this.isFormField = false;
		this.createInterface();		
	}	
};

Ext.extend( Ext.ux.StarRating, Ext.form.Field, {
	/**
     * @cfg {Integer} totalStars The total amount of stars to be displayed (defaults to 5)
     */
	totalStars: null,
	
	/**
     * @cfg {Float} average The current average for the value being voted on (defaults to 0)
     */
	average: 0,
	
	// private
	stars: null,
	
	// private
	cancel: null,
	
	// private
	selectedValue: 0,
	
	// private
	valueClicked: false,
	
	// private
	autoSize: Ext.emptyFn,
	
	// private
	monitorValid: false,
	
	// private
	inputType: 'string',
	
	// private
	primaryContainer: null,
	
	/**
     * Clears selected stars
     */
	clear: function(){
	  
		this.stars.each( function( e, t, i ){
			t.item( i ).removeClass( 'on' );
			t.item( i ).removeClass( 'hover' );
			t.item( i ).dom.firstChild.style.width = "100%";
		});
	},
	
	/**
     * Fills stars (hover) up to a particular star
     */
	fill: function( e ){
		var el  = Ext.get( e.getTarget() );
		var idx = el.dom.innerHTML;
		for( var i = 0 ; i < idx; i++ ){
			this.stars.item( i ).addClass( 'hover' );
		}		
	},	
	
	// private
	clearAndFill: function( e ){
	  
		if( this.valueClicked )
			return;
			
		this.clear();		
		this.fill( e );
	},
	
	/**
     * Reset selections, and display the current average
     */
	resetStars: function(){
	  
		if( this.valueClicked )
			return;
			
		this.clear();
		if( this.average ){
			var lta = Math.floor( this.average );
			for( var i = 0 ; i < lta + 1 ; i++ )
				this.stars.item( i ).addClass( 'on' );
			
			var diff = (this.average - Math.floor( this.average )) * 100;
			if( diff ){
				this.stars.item( lta ).dom.firstChild.style.width = diff + "%";
			}
		}
		
	},	
	
	/**
     * Adjust rating to a target star, triggers the 'rate' event
	 * @param {Element} el The star that is recording the vote
     * @return {String} name The field name
     */
	adjustRating: function( e ){
	   if(this.cancelRating)
	       this.reinitialize();
	   
		if( !this.valueClicked ){
		    
			var el  			= Ext.get( e.getTarget() );
			var idx 			= el.dom.innerHTML;
			this.setValue( idx );
			this.fill( e );
			this.fireEvent( "rate", this, idx );
		}
		
		this.valueClicked = !this.valueClicked;
		//this.valueClicked = true
	},
	
	// private
	reinitialize: function(){
	   
		this.valueClicked	= false;
		this.setValue( 0 );
		this.clear();
		this.resetStars();		
	},
	
	// private
	initBehavior : function(){
		this.stars.on( 'mouseover', this.clearAndFill, this );
		this.stars.on( 'mouseout', this.resetStars, this );
		this.stars.on( 'focus', this.clearAndFill, this );
		this.stars.on( 'blur', this.resetStars, this );	
		this.stars.on( 'click', this.adjustRating, this );
		if(this.cancelRating)
		  this.cancel.on( 'click', function(){this.fireEvent( "cancel"); this.reinitialize(); }, this );
	},
	
	// private
	createInterface: function(){
		// add the cancel button
		
		
		if(this.cancelRating)
    		this.cancel	= Ext.DomHelper.append( this.primaryContainer, { 
    			tag: 'div', 
    			'class': 'cancel',
    			 
    			style: "padding-right:5px;",
    			html: '<a href="javascript:;" title="Cancel Rating">Cancel Rating</a>'
    		}, true );
		
		
		this.stars = new Ext.CompositeElement();
		for( var i = 0 ; i < this.totalStars ; i++ ){
			this.stars.add( Ext.DomHelper.append( this.primaryContainer, { 
				tag: 'div', 
				'class': 'star',
				html: '<a href="javascript:;" title="Rate it at ' + ( i + 1 ) + '/' + this.totalStars + '">' + ( i + 1 ) + '</a>' 
			}, true ) );
		}
			
		this.initBehavior();
		this.resetStars();
	},
	
	// private
	onRender : function( ct, position ){
		// 
		// If I add this it works, but it creates an unwanted text field...
		//
		Ext.ux.StarRating.superclass.onRender.call(this, ct, position);
		
		this.grow = false;
		
		this.el.radioClass( 'x-hidden' );
		this.setValue( 0 );
		
		ct.addClass( 'rating' );
		this.primaryContainer = ct;
		this.createInterface();		

	},	
	
	/**
     * Returns the name attribute of the field if available
     * @return {String} name The field name
     */
	getName: function(){
		return this.name;	
	},
	
	/**
     * Returns the integer vote value. Synonymous to {@link #getValue}.
     * @return {Integer} value The field value
     */
	getRawValue: function(){
		return this.getValue();	
	},
	
	/**
     * Returns the integer vote value. Synonymous to {@link #getValue}.
     * @return {Integer} value The field value
     */
	getValue: function(){
		return this.selectedValue;		
	},
	
	/**
     * Set the voted value to a certain integer
     * @return {Integer} value The field value
     */
	setValue: function( x ){
		if( x > this.totalStars )
			x = this.totalStars;
		
		this.selectedValue = x;
		if( this.el ) // form field?
			this.el.dom.value  = x;
	},
	
	// private
	validate: function(){
		return true;	
	},
	
	// private
	clearInvalid : function(){
        return;
    },
	
	// private
	reset : function(){
        this.setValue( 0 );
    }
});