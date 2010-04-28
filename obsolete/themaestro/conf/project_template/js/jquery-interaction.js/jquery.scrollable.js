/**

Horizontal and Vertical scrolling of ordered lists

Basic structure, order not essential:

<div class="horizontal-scrollable">
<ol class="navi"></ol>
<button class="left"></button>
<button class="right"></button>
<div class="wrapping">
<ol class="items">
</ol>
</div>
</div>

 * @author Nater Kane <nater@naterkane.com>
 * @url $URL: http://svn.naterkane.net/jpmorgan/scrollable.html $
 * @modifiedby $LastChangedBy: henrikvendelbo $
 */
(function($) {
		
	// plugin initialization
	$.fn.extend({
		scrollable: function(arg1, arg2, arg3) { 
			
			return this.each(function() {
				if (typeof arg1 == "string") {
					var el = $.data(this, "scrollable");
					el[arg1].apply(el, [arg2, arg3]);
					
				} else { 
					new $.scrollable(this, arg1, arg2);
				}
			});
		}		
	});
		
	// constructor
	$.scrollable = function(el, opts) {   
			
		// store this instance
		$.data(el, "scrollable", this);
		
		this.init(el, opts); 
	};
	
	
	// methods
	$.extend($.scrollable.prototype, { 
			
		init: function(el, config)  {
			 
			// current instance
			var self = this;  
			
			var opts = {								
				size: 5,
				horizontal:false,				
				activeClass:'active',
				duration: 1500,
				onSeek: null,
				// jquery selectors
				wrapping: '.wrapping',
				items: '.items',
				prev:'.prev',
				next:'.next',
				navi:'.navi',
				naviItem:'li'
			}; 
	
			this.opts = $.extend(opts, config); 			
	
			// root / itemsRoot
			var root = this.root = $(el);			
			var itemsRoot = this.itemsRoot = $(opts.items, root);			
			if (!itemsRoot.length) itemsRoot = root;	
			
			this.items = $(opts.items+" li",root);
			this.index = 0;

			
			// set height based on size
			/*
			if (opts.horizontal) {
				itemsRoot.width(opts.size * (this.items.eq(1).offset().left - this.items.eq(0).offset().left) -2);	
			} else {
				itemsRoot.height(opts.size * (this.items.eq(1).offset().top - this.items.eq(0).offset().top) -2);	
			} 
			*/
	
			// mousewheel
			if ($.isFunction($.fn.mousewheel)) { 
				root.bind("mousewheel.scrollable", function(event, delta)  { 
					self.move(-delta, 50);		
					return false;
				});
			} 
	
			// keyboard
			$(window).bind("keypress.scrollable", function(evt) {

				if ($(evt.target).parents(self.opts.items,root).length) {
					
					if (opts.horizontal && (evt.keyCode == 37 || evt.keyCode == 39)) {
						self.move(evt.keyCode == 37 ? -1 : 1);
						return false;
					}	
					
					if (!opts.horizontal && (evt.keyCode == 38 || evt.keyCode == 40)) {
						self.move(evt.keyCode == 38 ? -1 : 1);
						return false;
					}
				}
				
				return true;
				
			});	
			
			
			// item.click()
			this.items.each(function(index, arg) {
				$(this).bind("click.scrollable", function() {
					self.click(index);		
				});
			});

			this.activeIndex = 0;
			
			// prev
			$(opts.prev, root).click(function() { self.prev() });
			

			// next
			$(opts.next, root).click(function() { self.next() });
			

			// navi 			
			$(opts.navi, root).each(function() { 				
				var navi = $(this);
				
				var status = self.getStatus();
				
				// generate new entries
				if (navi.is(":empty")) {
					for (var i = 0; i < status.pages; i++) {		
						
						var item = $("<" + opts.naviItem + "/>").attr("page", i).click(function() {							
							var el = $(this);
							el.parent().children().removeClass(opts.activeClass);
							el.addClass(opts.activeClass);
							self.setPage(el.attr("page"));
							
						});
						
						if (i == 0) item.addClass(opts.activeClass);
						navi.append(item);					
					}
					
				// assign onClick events to existing entries
				} else {
					
					navi.children().each(function(i)  {
						var item = $(this);
						item.attr("page", i);
						if (i == 0) item.addClass(opts.activeClass);
						
						item.click(function() {
							item.parent().children().removeClass(opts.activeClass);
							item.addClass(opts.activeClass);
							self.setPage(item.attr("page"));
						});
						
					});
				}
				
			});			
			
		},
		

		click: function(index) {

			var item = this.items.eq(index);
			var klass = this.opts.activeClass;
			
			if (!item.hasClass(klass) && (index >= 0 || index < this.items.size())) { 
				
				var prev = this.items.eq(this.activeIndex).removeClass(klass);
				item.addClass(klass);   
				
				this.seekTo(index - Math.floor(this.opts.size / 2));
				this.activeIndex = index;
			}  
		},
		
		getStatus: function() {
			var len =  this.items.size();
			var s = {
				length: len, 
				index: this.index, 
				size: this.opts.size,
				pages: Math.round(len / this.opts.size),
				page: Math.round(this.index / this.opts.size)
			};

			return s;
		}, 

		
		// all other seeking functions depend on this generic seeking function		
		seekTo: function(index, time) {
			
			if (index < 0) index = 0;			
			index = Math.min(index, this.items.length - this.opts.size);			
			
			var item = this.items.eq(index);			
			if (item.size() == 0) return false; 			
			this.index = index;

			
			if (this.opts.horizontal) {
				var left = this.itemsRoot.offset().left - item.offset().left;				
				this.itemsRoot.animate({left: left}, { "duration": this.opts.duration});
				
			} else {
				var top = this.itemsRoot.offset().top - item.offset().top;
				/// console.log(top);
				/// console.log({top:top});
				this.itemsRoot.animate({top: top}, { "duration": this.opts.duration});							
			}

			// custom onSeek callback
			if ($.isFunction(this.opts.onSeek)) {
				this.opts.onSeek.call(this.getStatus());
			}
			
			// navi status update
			var navi = $(this.opts.navi, this.root);
			
			if (navi.length) {
				var klass = this.opts.activeClass;
				var page = Math.round(index / this.opts.size);
				navi.children().removeClass(klass).eq(page).addClass(klass);
			}
			
			
			return true; 
		},
		
			
		move: function(offset, time) {
			this.seekTo(this.index + offset, time);
		},
		
		next: function(time) {
			this.move(1, time);	
		},
		
		prev: function(time) {
			this.move(-1, time);	
		},
		
		movePage: function(offset, time) {
			this.move(this.opts.size * offset, time);		
		},
		
		setPage: function(index, time) {
			this.seekTo(this.opts.size * index, time);
		},
		
		begin: function(time) {
			this.seekTo(0, time);	
		},
		
		end: function(time) {
			this.seekTo(this.items.size() - this.opts.size, time);	
		}

		
	});  
	
})(jQuery);