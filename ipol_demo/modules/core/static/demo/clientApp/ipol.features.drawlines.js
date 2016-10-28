/**
 * @file 
 * this file contains the code related to line drawing features
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";

// ipol application namespace
var ipol = ipol || {};

/**
 * features namespace for additional interface 
 * required by some demos like drawing, display of specific inputs, etc ...
 * @namespace
 */
ipol.features = ipol.features || {};


//------------------------------------------------------------------------------
/**
 * Line drawing interface
 * @extends ipol.features.DrawBase
 * @constructor
 */
ipol.features.DrawLines = function() {

    // call super constructor.
    ipol.features.DrawBase.call(this); 

    //--------------------------------------------------------------------------
    /**
     * Updates the pen display: size, color, opacity ...
     * @function _updatePenDisplay
     * @memberOf ipol.features.DrawLines~
     * @private
     */
    var _updatePenDisplay = function() {
        // draw pen as a circle
        var sketch   = $("#colors_sketch").data().sketch;
        var color    = sketch.color;
        var diameter = sketch.size*sketch.scale_factor;
        var radius   = diameter/2;
        var center =6*sketch.scale_factor;
        $("#pensize_display")[0].width  = 12*sketch.scale_factor;
        $("#pensize_display")[0].height = 12*sketch.scale_factor;
        var ctx = $("#pensize_display")[0].getContext("2d");
        ctx.clearRect(0,0,12,12);
        ctx.lineWidth=1;
        ctx.beginPath();
        ctx.arc(center,center, radius,0,2*Math.PI,false);
        //ctx.strokeStyle=color;
        
        if (color[0]=="#") {
          var c = hexToRgb(color);
          color = 'rgba('+c.r+','+c.g+','+c.b+','+sketch.opacity+')';
          //console.info("color=",color);
        }
            
        ctx.strokeStyle="#000";
        ctx.fillStyle=color;
        if (sketch.tool=="eraser") {
            ctx.stroke();
        } else {
            ctx.fill();
        }
        ctx.closePath();
        
        var r1 = Math.ceil(radius); // get radius as integer, round so 0.5-->1
        var d1 = 2*r1+1; // new related diameter
        var imgData=ctx.getImageData(center-r1,center-r1,d1,d1);
        var newCanvas = $("<canvas>").attr("width", d1).attr("height", d1)[0];
        newCanvas.getContext("2d").putImageData(imgData, 0, 0);

        //var cursor_url = $("#pensize_display")[0].toDataURL();
        //$("#canvas_div").css('cursor','url('+cursor_url+') '+
        //        center + ' '+
        //        center + ',auto');
        
        // keep normal cursor for setting line points: it is better :)
        //var cursor_url = newCanvas.toDataURL();
        //$("#canvas_div").css('cursor','url('+cursor_url+') '+(r1+1)+' '+(r1+1)+',auto');
    }
    

    //--------------------------------------------------------------------------
    /**
     * Add created lines as a property in the parameters object
     * @function AddLinesParameters
     * @memberOf ipol.features.DrawLines~
     * @param params object containing the parameters
     * @public
     */
    this.AddToParameters = function(params) {
        var sketch   = $("#colors_sketch").data().sketch;
        sketch.stopPainting();
        params.drawlines = [];

        $.each(sketch.actions, function(index,action) {
            if (action.tool==='marker') {
                var line=[];
                $.each(action.events,function(index,event) {
                    line.push([event.x,event.y]);
                });
                params.drawlines.push(line);
            }
        });
    }

    //--------------------------------------------------------------------------
    /**
     * Creates and returns the HTML code for the line drawing interface
     * @function createHTML
     * @memberOf ipol.features.DrawLines~
     * @returns {string} the HTML code
     * @public
     */
    this.createHTML = function( ) {
        var html = '';
        // add draw line interface

        // zoom
        var limits= '';
        limits += ' min  ="' + 0.1  + '"'; 
        limits += ' max  ="' + 5 + '"';
        limits += ' step ="' + 0.1  + '"';
        limits += ' value="' + 1  + '"';
        var zoom_html =
                '<div>Zoom <input  style="width:3em"  type="number" id="zoom_number"'+
                    limits + ' >'+
                '<div  style="width:8em;display:inline-block;" id="zoom_range" ></div>'+
                    '</div>';
                
        // pensize limits
        var limits= '';
        limits += ' min  ="' + 1  + '"'; 
        limits += ' max  ="' + 5 + '"';
        limits += ' step ="' + 1  + '"';
        limits += ' value="' + 2  + '"';
        var pensize_html =
                '<div>Size <input  style="width:3em"  type="number" id="pensize_number"'+
                    limits + ' >'+
                '<div  style="width:8em;display:inline-block;" id="pensize_range" ></div>'+
                    '</div>'+
//                 '<input  style="width:8em" type="range" id="pensize_range"'+
//                     limits + ' >'+
                "<canvas id=pensize_display style='margin:2px;border:0px solid lightgrey;display:inline-block;'"+
                        " width=12px height=12px ></canvas> "+
                    '</div>';
                    
        // mask opacity
        var limits= '';
        limits += ' min  ="' + 0.01 + '"'; 
        limits += ' max  ="' + 1    + '"';
        limits += ' step ="' + 0.01 + '"';
        limits += ' value="' + 0.8  + '"';
        var opacity_html =
                '<div>Opacity <input  style="width:3em"  type="number" id="opacity_number"'+
                    limits + ' >'+
                '<div  style="width:8em;display:inline-block;" id="opacity_range" ></div>'+
//                 '<input  style="width:10em" type="range" id="opacity_range"'+
//                     limits + ' >'+
                    '</div>';
                    
        html += '<table id="drawlines_table" ">'+
                    '<tr>'+
                    //'</tr>'+
                    //'<tr>'+
                        '<td style="vertical-align:top">'+
                            "<label> <b>Zoom</b></label>"+
                            zoom_html+
                            "<hr><label> <b>Draw mask</b></label>"+
                            pensize_html+
                            opacity_html+
                            '<div class="drawlines_color" style="padding:2px"> </div>'+
                            '<div  style="padding:2px"> '+
                                '<button id="drawlines_newline" style="margin:2px;">New line</button>'+
                            '</div>'+
                            '<div class="drawlines_actions" style="padding:2px"> '+
                                '<button id="drawlines_undo"   style="margin:2px;">Undo</button>'+
                                '<button id="drawlines_clear"  style="margin:2px;">Clear</button>'+
                            '</div>'+
                        '</td>'+
                        '<td>'+
                            '<div id="canvas_div" style="float:left;padding:2px;">'+
                            '</div>'+
                        '</td>'+
                    '</tr>'+
                '</table>';
        //+
        //        '<div style="clear:both"> </div> <br/>';
        return html;
    }
    

    //--------------------------------------------------------------------------
    /**
     * Create the events for the draw line interface
     * @function createHTMLEvents
     * @memberOf ipol.features.DrawLines~
     * @public
     */
    this.createHTMLEvents = function( ) {
        
        var update_pen = _updatePenDisplay.bind(this);
        
        // add draw line events
        
        // Change display zoom
        $('#zoom_range').slider(
        {
            value:1,
            min:  0.1,
            max:  5,
            step: 0.1,
            slide: function( event, ui ) {
                var size = $('#zoom_range').slider('value');
                $('#zoom_number').val(size);
            },
            change: function( event, ui ) {
                var size = $('#zoom_range').slider('value');
                var sketch = $("#colors_sketch").data().sketch;
                $('#zoom_number').val(size);
                $("#colors_sketch").data().sketch.resize(size);
                $("#colors_sketch").data().sketch.redraw();
                update_pen();
            }
        });
        
        $('#zoom_number').on('input', function(){
            var size= $('#zoom_number').val();
            $('#zoom_range').slider('value',size);
        });
        
        $('#zoom_number').on('change', function(){
            var sketch = $("#colors_sketch").data().sketch;
            var size= $('#zoom_number').val();
            $('#zoom_range').slider('value',size);
            $("#colors_sketch").data().sketch.resize(size);
            $("#colors_sketch").data().sketch.redraw();
            update_pen();
        });

        
        // Change pen size
        $('#pensize_range').slider(
        {
            min:  1,
            max:  5,
            step: 1,
            value:2,
            slide: function( event, ui ) {
                var sketch = $("#colors_sketch").data().sketch;
                var size= $('#pensize_range').slider('value');
                $("#colors_sketch").data().sketch.size=size;
                $('#pensize_number').val(size);
                update_pen();
            },
            change: function( event, ui ) {
                var sketch = $("#colors_sketch").data().sketch;
                var size= $('#pensize_range').slider('value');
                $("#colors_sketch").data().sketch.size=size;
                $('#pensize_number').val(size);
                update_pen();
            }
        });
        
        $('#pensize_number').on('input', function(){
            var sketch = $("#colors_sketch").data().sketch;
            var size= $('#pensize_number').val();
            sketch.size=size;
            $('#pensize_range').slider('value',size);
            update_pen();
        });
        
        // Change opacity
        $('#opacity_range').slider(
        {
            value:0.8,
            min:  0.01,
            max:  1,
            step: 0.01,
            slide: function( event, ui ) {
                $("#colors_sketch").data().sketch.opacity=$('#opacity_range').slider('value');
                $('#opacity_number').val($('#opacity_range').slider('value'));
                update_pen();
                $("#colors_sketch").data().sketch.redraw();
            },
            change: function( event, ui ) {
                $("#colors_sketch").data().sketch.opacity=$('#opacity_range').slider('value');
                $('#opacity_number').val($('#opacity_range').slider('value'));
                update_pen();
                $("#colors_sketch").data().sketch.redraw();
            }
        });
        
        $('#opacity_number').on('input', function(){
            $("#colors_sketch").data().sketch.opacity=$('#opacity_number').val();
            $('#opacity_range').slider('value',$('#opacity_number').val());
            update_pen();
            $("#colors_sketch").data().sketch.redraw();
        });
        
        // new line
        $('#drawlines_newline').click( function() {
            $("#colors_sketch").data().sketch.stopPainting();
        });
         

        // undo button
        $('#drawlines_undo').click( function() {
            if ($("#colors_sketch").data().sketch.painting) {
                $("#colors_sketch").data().sketch.action.events.pop();
            } else {
                $("#colors_sketch").data().sketch.actions.pop();
            }
            $("#colors_sketch").data().sketch.redraw();
        });
        
        // clear button
        $('#drawlines_clear').click( function() {
            var sketch = $("#colors_sketch").data().sketch;
            // if still painting, stop painting
            sketch.stopPainting();
            var ctx0 = sketch.context;
            ctx0.clearRect(0, 0, $("#colors_sketch")[0].width, $("#colors_sketch")[0].height);
            sketch.actions=[];
            sketch.redraw();
            //_updateMask();
        }.bind(this));
        
    }

    
    //--------------------------------------------------------------------------
    /**
     * Updates the line drawing interface
     * @function updateDrawLines
     * @memberOf ipol.features.DrawLines~
     * @param {object} image  input image set as canvas painting background
     * @public
     */
    this.updateDrawing = function(image) {
        // 1. set background image and image size
        //       var image_src = $("#inputimage").attr('src');
        //       var image_src = $("#input_gallery #img_0_0").prop("src");
        var image_src = image.src;
        $('.drawlines_color').empty();
        $('.drawlines_color').append("Color");
        var color_index=0;
        $.each(['#f00', '#ff0', '#0f0', '#0ff', '#00f', '#f0f', '#000', '#fff'], function() {
            color_index++;
            $('.drawlines_color').append(
                "<div' class='set_color' id=set_color_"+color_index+" data-color='" + this + 
                "' style='margin:4px 0px 0px 4px;display:inline-block;"+
                "width:15px;height:15px; background: " + this + ";'></div> ");
        });
        
        var update_pen = _updatePenDisplay.bind(this);
        
        $(".set_color").click(function() {
            var color = $(this).attr("data-color");
            $(".set_color").css("border","");
            $(this).css("border","2px solid grey");
            //console.info("set_color click ", color);
            $("#colors_sketch").data().sketch.color = color;
            $("#colors_sketch").data().sketch.redraw();
            update_pen();
        }
        );
        
        $("#canvas_div").empty();
        $('<canvas>').attr({
            // don´t set borders since it displaces the coordinates ...
            // style       : 'border:1px solid black;margin:2px;',
            style       : 'border:0px;margin:2px;',
            id          : "colors_sketch",
            width       : image.naturalWidth + 'px',
            height      : image.naturalHeight + 'px',
            crossOrigin : "Anonymous"
        }).appendTo('#canvas_div');
        
        $("#colors_sketch").css("background-image", "url(" + image_src + ")");
        $("#colors_sketch").css("background-size", "cover");
        $('#colors_sketch').sketch();
        $("#colors_sketch").data().sketch.draw_polylines(true);
        //
        $("#drawlines_table").show();
        
        //$('#colors_sketch').data().sketch.redraw_callback = _updateMask;
        //$('#colors_sketch').data().sketch.stoppainting_callback = _updateMask;
//        $("#colors_sketch").data().sketch.redraw();
//         if (mask) {
//             var sketch = $("#colors_sketch").data().sketch;
//             sketch.initial_mask = mask;
//             sketch.redraw();
//             _updateMask();
//         }

        // update sketch settings
        $('#pensize_number').trigger('input');
        $('#opacity_number').trigger('input');
        $("#set_color_5")   .trigger('click');  // set blue pen
    }
    

    //--------------------------------------------------------------------------
    /**
     * Gets the current line interface state: different options like pen size
     * color and current actions (drawn lines)
     * @function getState
     * @memberOf ipol.features.DrawLines~
     * @public
     */
    this.getState = function() {
        var lines_state = {}
        var sketch   = $("#colors_sketch").data().sketch;
        
        lines_state.actions = sketch.actions;
        
        // zoom
        lines_state.zoom = $('#zoom_range').slider('value');
        // pensize
        // opacity
        
        
        return lines_state;
    }
    

    //--------------------------------------------------------------------------
    /**
     * Sets the current mask interface state: different options like pen size
     * color and current actions (drawn lines)
     * @function setState
     * @memberOf ipol.features.DrawLines~
     * @public
     */
    this.setState = function( lines_state) {
        var sketch   = $("#colors_sketch").data().sketch;
        
        sketch.actions = lines_state.actions;
        
        // zoom
        $('#zoom_range').slider('value',lines_state.zoom);
        // pensize
        // opacity
        
    }
    
    
}

// subclass extends superclass
ipol.features.DrawLines.prototype = Object.create(ipol.features.DrawBase.prototype);
ipol.features.DrawLines.prototype.constructor = ipol.features.DrawLines;
    
