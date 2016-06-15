
// from http://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
function hexToRgb(hex) {
    // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
    var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, function(m, r, g, b) {
        return r + r + g + g + b + b;
    });

    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

//
//
var __slice = Array.prototype.slice;
(function($) {
  var Sketch;

  //----------------------------------------------------------------------------
  $.fn.sketch = function() {
    var args, key, sketch;
    key = arguments[0], args = 2 <= arguments.length ? __slice.call(arguments, 1) : [];
    if (this.length > 1) {
      $.error('Sketch.js can only be called on one element at a time.');
    }
    sketch = this.data('sketch');
    if (typeof key === 'string' && sketch) {
      if (sketch[key]) {
        if (typeof sketch[key] === 'function') {
          return sketch[key].apply(sketch, args);
        } else if (args.length === 0) {
          return sketch[key];
        } else if (args.length === 1) {
          return sketch[key] = args[0];
        }
      } else {
        return $.error('Sketch.js did not recognize the given command.');
      }
    } else if (sketch) {
      return sketch;
    } else {
      this.data('sketch', new Sketch(this.get(0), key));
      return this;
    }
  };
  

  //----------------------------------------------------------------------------
  Sketch = (function() {
    function Sketch(el, opts) {
      this.el = el;
      this.canvas = $(el);
      this.context = el.getContext('2d');
      this.context.lineJoin = "round";
      this.context.lineCap = "round";
      this.options = $.extend({
        toolLinks: true,
        defaultTool: 'marker',
        defaultColor: '#000000',
        defaultSize: 5
      }, opts);
      this.painting = false;
      this.color = this.options.defaultColor;
      this.size = this.options.defaultSize;
      this.tool = this.options.defaultTool;
      this.opacity = 200;// opacity between 0 and 255
      this.actions = [];
      this.action = [];
      this.redraw_callback        = undefined;
      this.stoppainting_callback  = undefined;
      this.use_unique_color = true; // ignore each action color and 
      // set all actions to the current color
      this.scale_factor=1;
      this.initial_width=this.el.width;
      this.initial_height=this.el.height;
      this.initial_mask = undefined;
      
      this.canvas.bind('click mousedown touchstart', this.onEvent);
      
      if (this.options.toolLinks) {
        $('body').delegate("a[href=\"#" + (this.canvas.attr('id')) + "\"]", 'click', function(e) {
          var $canvas, $this, key, sketch, _i, _len, _ref;
          $this = $(this);
          $canvas = $($this.attr('href'));
          sketch = $canvas.data('sketch');
          _ref = ['color', 'size', 'tool'];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            key = _ref[_i];
            if ($this.attr("data-" + key)) {
              sketch.set(key, $(this).attr("data-" + key));
            }
          }
          if ($(this).attr('data-download')) {
            sketch.download($(this).attr('data-download'));
          }
          return false;
        });
      }
    }
    
    //--------------------------------------------------------------------------
    Sketch.prototype.resize = function(factor) {
      this.el.width   = this.initial_width*factor;
      this.el.height  = this.initial_height*factor;
      this.scale_factor=factor;
    }
    
    //--------------------------------------------------------------------------
    Sketch.prototype.download = function(format) {
      var mime;
      format || (format = "png");
      if (format === "jpg") {
        format = "jpeg";
      }
      mime = "image/" + format;
      return window.open(this.el.toDataURL(mime));
    };
    
    //--------------------------------------------------------------------------
    Sketch.prototype.set = function(key, value) {
      this[key] = value;
      return this.canvas.trigger("sketch.change" + key, value);
    };
    
    //--------------------------------------------------------------------------
    Sketch.prototype.startPainting = function() {
      this.canvas.bind('mouseup mousemove mouseleave mouseout touchmove touchend touchcancel', 
                       this.onEvent);
      this.painting = true;
      return this.action = {
        tool: this.tool,
        color: this.color,
        size: parseFloat(this.size),
        events: []
      };
    };
    
    //--------------------------------------------------------------------------
    Sketch.prototype.stopPainting = function() {
      this.canvas.unbind('mouseup mousemove mouseleave mouseout touchmove touchend touchcancel', this.onEvent);
      if (this.action) {
        this.actions.push(this.action);
      }
      this.painting = false;
      this.action = null;
      this.redraw();
      if (this.stoppainting_callback) {
          this.stoppainting_callback();
      }
    };
    
    //--------------------------------------------------------------------------
    Sketch.prototype.onEvent = function(e) {
      if (e.originalEvent && e.originalEvent.targetTouches) {
        e.pageX = e.originalEvent.targetTouches[0].pageX;
        e.pageY = e.originalEvent.targetTouches[0].pageY;
      }
      $.sketch.tools[$(this).data('sketch').tool].onEvent.call($(this).data('sketch'), e);
      e.preventDefault();
      return false;
    };
    
    //--------------------------------------------------------------------------
    Sketch.prototype.redraw = function() {
      var sketch;
      this.el.width = this.canvas.width();
      this.context = this.el.getContext('2d');
      if (this.initial_mask) {
        // process initial initial mask 
        var w = this.initial_mask.naturalWidth;
        var h = this.initial_mask.naturalHeight;
        var canvas = $("<canvas>").attr("width", w).attr("height", h)[0];
        var context = canvas.getContext('2d');
        context.drawImage(this.initial_mask, 0, 0 );
        var imgData = context.getImageData(0, 0, w, h);
        var c = hexToRgb(this.color);
        for (var i=0;i<imgData.data.length;i+=4)
        {
            // mask image is supposed to be black or white
            if (imgData.data[i]>0) {
                imgData.data[i]  =c.r;
                imgData.data[i+1]=c.g;
                imgData.data[i+2]=c.b;
                imgData.data[i+3]=Math.round(255*this.opacity);
            } else {
                imgData.data[i+3]=0;
            }
        }
        context.putImageData(imgData, 0, 0);

        this.context.setTransform(1, 0, 0, 1, 0, 0);
        this.context.scale(this.scale_factor,this.scale_factor);
        this.context.drawImage(canvas,0,0);
        this.context.setTransform(1, 0, 0, 1, 0, 0);
      }
      this.context.lineJoin = "round";
      this.context.lineCap = "round";
      sketch = this;
      $.each(this.actions, function(index,action) {
        if (action.tool) {
            return $.sketch.tools[action.tool].draw.call(sketch, action);
        }
      }.bind(this));
      if (this.painting && this.action) {
        //return 
        $.sketch.tools[this.action.tool].draw.call(sketch, this.action);
      }
      if (this.redraw_callback) {
          this.redraw_callback();
      }
    };
    
    return Sketch;
  })();
    
  //----------------------------------------------------------------------------
  $.sketch = {
    tools: {}
  };
  
  //----------------------------------------------------------------------------
  $.sketch.tools.marker = {
    onEvent: function(e) {
      switch (e.type) {
        case 'mousedown':
        case 'touchstart':
          this.startPainting();
          break;
        case 'mouseup':
        case 'mouseout':
        case 'mouseleave':
        case 'touchend':
        case 'touchcancel':
          this.stopPainting();
      }
      if (this.painting) {
        //console.info(" e=",e," offset=",this.canvas.offset());
        //console.info(" x=",e.pageX - this.canvas.offset().left,
        //             " y=",e.pageY - this.canvas.offset().top;
        this.action.events.push({
          x: (e.pageX - this.canvas.offset().left)/this.scale_factor,
          y: (e.pageY - this.canvas.offset().top )/this.scale_factor,
          event: e.type
        });
        return this.redraw();
      }
    },
 
    //--------------------------------------------------------------------------
    draw: function(action) {
        
        var ctx = this.context;
        // compute and set action color
        if (this.use_unique_color) {
            var action_color = this.color;
        } else {
            var action_color = action.color;
        }
        if (action.color[0]=="#") {
            var c = hexToRgb(action_color);
            var action_color = 'rgba('+c.r+','+c.g+','+c.b+','+this.opacity+')';
        }
        
        ctx.beginPath();
        // if only one point, draw a disk
        if (action.events.length===1) {
            var x     = action.events[0].x*this.scale_factor;
            var y     = action.events[0].y*this.scale_factor;
            var rayon = (action.size*this.scale_factor-1)/2.0;
            ctx.arc(x, y, rayon, 0, 2*Math.PI, false);
            ctx.fillStyle   = action_color;
            ctx.fill();
            ctx.lineWidth = 1;
        } else {
            ctx.moveTo(action.events[0].x*this.scale_factor, 
                                action.events[0].y*this.scale_factor);
            $.each(action.events,function(index,event) {
                ctx.lineTo(event.x*this.scale_factor, 
                                    event.y*this.scale_factor);
            }.bind(this));
            ctx.lineWidth = action.size*this.scale_factor;
        }
        ctx.strokeStyle = action_color;
        return ctx.stroke();
    }
  };
  
  //----------------------------------------------------------------------------
  return $.sketch.tools.eraser = {
    onEvent: function(e) {
      return $.sketch.tools.marker.onEvent.call(this, e);
    },
 
    //--------------------------------------------------------------------------
    draw: function(action) {
      var ctx = this.context;
      var oldcomposite;
      oldcomposite = ctx.globalCompositeOperation;
      ctx.globalCompositeOperation = "destination-out";
      action.color = "rgba(0,0,0,1)";
      //      $.sketch.tools.marker.draw.call(this, action);
      ctx.beginPath();
      if (action.events.length===1) {
        var x     = action.events[0].x*this.scale_factor;
        var y     = action.events[0].y*this.scale_factor;
        var rayon = (action.size*this.scale_factor-1)/2.0;
        ctx.arc(x, y, rayon, 0, 2*Math.PI, false);
        ctx.fillStyle   = action.color;
        ctx.lineWidth = 1;
        ctx.fill();
      } else {
        ctx.moveTo(action.events[0].x*this.scale_factor, 
                            action.events[0].y*this.scale_factor);
        $.each(action.events,function(index,event) {
            ctx.lineTo(event.x*this.scale_factor, 
                                event.y*this.scale_factor);
        }.bind(this));
        ctx.strokeStyle = action.color;
        ctx.lineWidth   = action.size*this.scale_factor;
      }
      ctx.stroke();
      
      return ctx.globalCompositeOperation = oldcomposite;
    }
  };
  
})(jQuery);
