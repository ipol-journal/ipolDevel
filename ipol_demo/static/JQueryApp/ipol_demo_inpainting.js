//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_inpainting.js
// date: june 2016
// author: Karl Krissian
//
// description:
// this file contains the code related to inpainting features
//

"use strict";


//------------------------------------------------------------------------------
// Inpainting class
//------------------------------------------------------------------------------
var Inpainting = function() {


    //--------------------------------------------------------------------------
    this.random_letters = function(){
        /* Several text samples about TV inpainting */
        var Text = [];
        Text[0] =
            "A coalescent process is a many particle system which evolves in time by merging particles into clusters. " +
            "They have found a variety of applications in genetics where the coalescent models ancestral relationships as time runs backwards. " +
            "The work on coalescents with pairs of particles merging dates back to the seminal paper of Kingman [Kin82]. " +
            "In [Pit99] and [Sag99], this is extended to the case where multiple merges are allowed to happen. We defer the precise defiition to Section 3. " +
            "In this paper we shall examine the Kingman's coalescent and Beta(2-a, a)-coalescents with 1 < a < 2. " +
            "These have the property that they come down from infinity, that is, when starting with infinitely many particles, " +
            "the process has finitely many particles for any time t > 0. Our goal is to gain precise information. ";
        Text[1] = 
            "about the behaviour near time zero by constructing a scaling limit in some suitable sense. " +
            "Our limiting object will be a coalescent process with infinite mass. " +
            "This requires us to change the usual definition of a coalescent process. Formally, we will be working " +
            "In this article we discuss the implementation of the combined 1st and 2nd order total variation inpainting " +
            "that was introduced in [13]. We describe the algorithm (split Bregman) in detail and we give some examples " +
            "that indicate the difference between pure first and pure second order total variation inpainting. " +
            "Finally we provide a source code for the algorithm written in C and an online demonstration for the IPOL website. ";
        Text[2] =
            "Image inpainting methods can be roughly separated in four categories, depending on being variational or non-variational " +
            "and local or non-local. The variational methods in contrast with the non-variational are characterised by the fact that " +
            "the reconstructed image ur is obtained as a mimimiser of a certain energy functional. A method is local if the information " +
            "that is needed to fill in the inpainting domain is only taken by the neighboring points of the boundary of D. " +
            "Non-local or global inpainting methods take into account all the information from the known part of the image, " +
            "usually weighted by its distance to the point that is to be filled in. The latter class of methods is very powerful, "+
            "allowing to fill in structures and textures almost equally well. However, they still have some disadvantages. ";
            
        Text[3] =
            "Mathematicians, those adorable and nerdy creatures... Not many people know what they actually do... " +
            "or even if what they do is useful, but almost everybody has a mental picture of what they look like. " +
            "Some people imagine bearded men walking aimlessly in circles while muttering words to themselves; " +
            "others picture men with thick glasses making sums and multiplications all day long with a powerful " +
            "mental skill; the most generous ones think of 'beautiful minds'. No, I do not do a PhD because I " +
            "want to become a high school teacher, but because I want to do research. No, not everything has " +
            "been discovered in Mathematics. Actually there is still a lot to be discoreved. And yes,... I wear thick glasses. ";
            
        var height = $("#colors_sketch").height();
        var width  = $("#colors_sketch").width();

        var ctx=$("#colors_sketch").data().sketch.context;
        ctx.font="18px sans-serif";

        var LineBuffer = "";
        
        for(var y = -4; y < height; y += 19)
        {
            var i = Math.round(Math.random()*100000)%4;
            var TextLength = Text[i].length;
            var k = Math.round(Math.random()*100000)%TextLength;
            LineBuffer = "";

            do
            {
                LineBuffer += Text[i][k % TextLength];
                k++;
            }while(LineBuffer.length < 1023 && ctx.measureText(LineBuffer).width < width + 5);

            /* Draw the text with an 18-point sans serif font */
            ctx.fillText(LineBuffer, -2, y);
        }

    }


    //--------------------------------------------------------------------------
    this.CreateHTML = function( ) {
        var html = '';
        // add inpainting interface

        // zoom
        var limits= '';
        limits += ' min  ="' + 0.1  + '"'; 
        limits += ' max  ="' + 5 + '"';
        limits += ' step ="' + 0.1  + '"';
        limits += ' value="' + 1  + '"';
        var zoom_html =
                '<div>Zoom <input  style="width:3em"  type="number" id="zoom_number"'+
                    limits + ' >'+
                '<input  style="width:8em" type="range" id="zoom_range"'+
                    limits + ' >'+
                    '</div>';
                
        // pensize limits
        var limits= '';
        limits += ' min  ="' + 1  + '"'; 
        limits += ' max  ="' + 50 + '"';
        limits += ' step ="' + 1  + '"';
        limits += ' value="' + 10  + '"';
        var pensize_html =
                '<div>Size <input  style="width:3em"  type="number" id="pensize_number"'+
                    limits + ' >'+
                '<input  style="width:8em" type="range" id="pensize_range"'+
                    limits + ' >'+
                "<canvas id=pensize_display style='margin:2px;border:1px solid lightgrey;display:inline-block;'"+
                        " width=50px height=50px ></canvas> "+
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
                '<input  style="width:10em" type="range" id="opacity_range"'+
                    limits + ' ></div>';
                    
        html += '<table id="inpaint_table" ">'+
                    '<tr>'+
                    //'</tr>'+
                    //'<tr>'+
                        '<td style="vertical-align:top">'+
                            "<label> <b>Zoom</b></label>"+
                            zoom_html+
                            "<hr><label> <b>Draw mask</b></label>"+
                            pensize_html+
                            opacity_html+
                            '<div class="inpaint_color" style="padding:2px"> </div>'+
                            '<div  style="padding:2px"> '+
                                '<button id="inpaint_marker" class="inpaint_tools" style="margin:2px;">Marker</button>'+
                                '<button id="inpaint_eraser" class="inpaint_tools" style="margin:2px;">Eraser</button>'+
                            '</div>'+
                            '<div class="inpaint_actions" style="padding:2px"> '+
                                '<button id="inpaint_undo"   style="margin:2px;">Undo</button>'+
                                '<button id="inpaint_clear"  style="margin:2px;">Clear</button>'+
                                // '<button id="inpaint_update_mask"  style="margin:2px;">Update</button>'+
                            '</div>'+
                            "<hr><label> <b>Generate mask</b></label>"+
                            '<div class="inpaint_random" style="padding:2px"> '+
                                '<button id="inpaint_random_text" style="margin:2px;">Random text</button>'+
                            '</div>'+
                        '</td>'+
                        '<td>'+
                            '<div id="canvas_div" style="float:left;padding:2px;">'+
                            '</div>'+
                            '<img  id="maskimage_id" crossOrigin="Anonymous"></img>'+
                        '</td>'+
                    '</tr>'+
                '</table>';
        //+
        //        '<div style="clear:both"> </div> <br/>';
        return html;
    }
        
    //--------------------------------------------------------------------------
    this.UpdatePenDisplay = function(image) {
        // draw pen as a circle
        var sketch   = $("#colors_sketch").data().sketch;
        var color    = sketch.color;
        var diameter = sketch.size*sketch.scale_factor;
        var radius   = diameter/2;
        var center =25*sketch.scale_factor;
        $("#pensize_display")[0].width  = 50*sketch.scale_factor;
        $("#pensize_display")[0].height = 50*sketch.scale_factor;
        var ctx = $("#pensize_display")[0].getContext("2d");
        ctx.clearRect(0,0,50,50);
        ctx.lineWidth=1;
        ctx.beginPath();
        ctx.arc(center,center,
                radius,0,2*Math.PI,false);
        //ctx.strokeStyle=color;
        
        if (color[0]=="#") {
          var c = hexToRgb(color);
          color = 'rgba('+c.r+','+c.g+','+c.b+','+sketch.opacity+')';
          console.info("color=",color);
        }
            
        ctx.strokeStyle="#000";
        ctx.fillStyle=color;
        if (sketch.tool=="eraser") {
            ctx.stroke();
        } else {
            ctx.fill();
        }
        ctx.closePath();
        
        var r1 = Math.round(radius); // get radius as integer, round so 0.5-->1
        var d1 = 2*r1; // new related diameter
        var imgData=ctx.getImageData(center-r1,center-r1,d1,d1);
        var newCanvas = $("<canvas>").attr("width", d1).attr("height", d1)[0];
        newCanvas.getContext("2d").putImageData(imgData, 0, 0);

        //var cursor_url = $("#pensize_display")[0].toDataURL();
        //$("#canvas_div").css('cursor','url('+cursor_url+') '+
        //        center + ' '+
        //        center + ',auto');
        
        var cursor_url = newCanvas.toDataURL();
        $("#canvas_div").css('cursor','url('+cursor_url+') '+r1+' '+r1+',auto');
    }
    
    //--------------------------------------------------------------------------
    this.UpdateInpaint = function(image,mask) {
        // 1. set background image and image size
        //             var image_src = $("#inputimage").attr('src');
//         var image_src = $("#input_gallery #img_0_0").prop("src");
        var image_src = image.src;
        $('.inpaint_color').empty();
        $('.inpaint_color').append("Color");
        var color_index=0;
        $.each(['#f00', '#ff0', '#0f0', '#0ff', '#00f', '#f0f', '#000', '#fff'], function() {
            color_index++;
            $('.inpaint_color').append(
                "<div' class='set_color' id=set_color_"+color_index+" data-color='" + this + 
                "' style='margin:4px 0px 0px 4px;display:inline-block;"+
                "width:15px;height:15px; background: " + this + ";'></div> ");
        });
        
        var update_pen = this.UpdatePenDisplay.bind(this);
        
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
            style       : 'border:1px solid black;margin:2px;',
            id          : "colors_sketch",
            width       : image.naturalWidth + 'px',
            height      : image.naturalHeight + 'px',
            crossOrigin : "Anonymous"
        }).appendTo('#canvas_div');
        
        $('<canvas>').attr({
            style       : 'border:1px solid black;margin:2px;background:url(background_transparency.png)',
            id          : "mask_canvas",
            width       : image.naturalWidth + 'px',
            height      : image.naturalHeight + 'px',
            crossOrigin : "Anonymous"
        }).appendTo('#canvas_div');
        
        // for the moment, hide the mask canvas
        $("#mask_canvas").hide();
        
        $("#colors_sketch").css("background-image", "url(" + image_src + ")");
        $("#colors_sketch").css("background-size", "cover");
        $('#colors_sketch').sketch();
        //
        $("#inpaint_table").show();
        
        //$('#colors_sketch').data().sketch.redraw_callback = this.UpdateMask;
        $('#colors_sketch').data().sketch.stoppainting_callback = this.UpdateMask;
//        $("#colors_sketch").data().sketch.redraw();
        if (mask) {
            var sketch = $("#colors_sketch").data().sketch;
            sketch.initial_mask = mask;
            this.UpdateMask();
        }

        // update sketch settings
        $('#pensize_range') .trigger('input');
        $("#set_color_5")   .trigger('click');  // set blue pen
        $("#inpaint_marker").trigger('click');  // set marker
        
    }
    
    //--------------------------------------------------------------------------
    this.CreateHTMLEvents = function( ) {
        
        var update_pen = this.UpdatePenDisplay.bind(this);
        
        // add inpainting events
        $('#zoom_range').on('input', function(){
            var size= $('#zoom_range').val();
            $('#zoom_number').val(size);
        });
        
        $('#zoom_range').on('change', function(){
            var sketch = $("#colors_sketch").data().sketch;
            var size= $('#zoom_range').val();
            $('#zoom_number').val(size);
            $("#colors_sketch").data().sketch.resize(size);
            $("#colors_sketch").data().sketch.redraw();
            update_pen();
        });

        $('#zoom_number').on('input', function(){
            var size= $('#zoom_number').val();
            $('#zoom_range').val(size);
        });
        
        $('#zoom_number').on('change', function(){
            var sketch = $("#colors_sketch").data().sketch;
            var size= $('#zoom_number').val();
            $('#zoom_range').val(size);
            $("#colors_sketch").data().sketch.resize(size);
            $("#colors_sketch").data().sketch.redraw();
            update_pen();
        });

        $('#pensize_range').on('input', function(){
            var sketch = $("#colors_sketch").data().sketch;
            var size= $('#pensize_range').val();
            $("#colors_sketch").data().sketch.size=size;
            $('#pensize_number').val(size);
            update_pen();
        });

        $('#pensize_number').on('input', function(){
            var sketch = $("#colors_sketch").data().sketch;
            var size= $('#pensize_number').val();
            sketch.size=size;
            $('#pensize_range').val(size);
            update_pen();
        });
        
        // add inpainting events
        $('#opacity_range').on('input', function(){
            $("#colors_sketch").data().sketch.opacity=$('#opacity_range').val();
            $('#opacity_number').val($('#opacity_range').val());
            update_pen();
            $("#colors_sketch").data().sketch.redraw();
        });

        $('#opacity_number').on('input', function(){
            $("#colors_sketch").data().sketch.opacity=$('#opacity_number').val();
            $('#opacity_range').val($('#opacity_number').val());
            update_pen();
            $("#colors_sketch").data().sketch.redraw();
        });
        
        $('#inpaint_undo').click( function() {
            $("#colors_sketch").data().sketch.actions.pop();
            $("#colors_sketch").data().sketch.redraw();
        });
        
        $('#inpaint_clear').click( function() {
            var sketch = $("#colors_sketch").data().sketch;
            var ctx0 = sketch.context;
            ctx0.clearRect(0, 0, $("#colors_sketch")[0].width, $("#colors_sketch")[0].height);
            sketch.actions=[];
            sketch.redraw();
            this.UpdateMask();
        }.bind(this));
        
        $('#inpaint_marker').click( function() {
            $(".inpaint_tools").css("border","");
            $(this).css("border","2px solid black");
            $("#colors_sketch").data().sketch.tool="marker";
            update_pen();
        });
        
        $('#inpaint_eraser').click( function() {
            $(".inpaint_tools").css("border","");
            $(this).css("border","2px solid black");
            $("#colors_sketch").data().sketch.tool="eraser";
            update_pen();
        });
        
        $('#inpaint_random_text').click( function() {
            $("#colors_sketch").data().sketch.actions=[];
            $("#colors_sketch").data().sketch.redraw();
            var sketch = $("#colors_sketch").data().sketch;
            sketch.context.fillStyle=sketch.color;
            this.random_letters();
            this.UpdateMask();
        }.bind(this));
    }

    //--------------------------------------------------------------------------
    this.UpdateMask = function( ddl_json, upload_callback ) {
        
        var sketch = $("#colors_sketch").data().sketch;
        var ctx0 = sketch.context;
        var ctx1 = $("#mask_canvas")[0].getContext("2d");
        var width  = $("#colors_sketch").width();
        var height = $("#colors_sketch").height();
        
        var imgData=ctx0.getImageData(0,0,width,height);
        
        // copy
        var i=0;
        for(var y=0;y<height;y++) {
            for(var x=0;x<width;x++) {
                var alpha = imgData.data[i+3];
                if (alpha>0) {
                    imgData.data[i]   = 255;
                    imgData.data[i+1] = 255;
                    imgData.data[i+2] = 255;
                    imgData.data[i+3] = 255;
                } else {
                    imgData.data[i]   = 0;
                    imgData.data[i+1] = 0;
                    imgData.data[i+2] = 0;
                    imgData.data[i+3] = 0;
                }
                i+=4;
            }
        }
        
        var newCanvas = $("<canvas>").attr("width", width).attr("height", height)[0];
        newCanvas.getContext("2d").putImageData(imgData, 0, 0);

        ctx1.setTransform(1, 0, 0, 1, 0, 0);
        ctx1.clearRect(0, 0, $("#mask_canvas")[0].width, $("#mask_canvas")[0].height);
        ctx1.scale(1/sketch.scale_factor,1/sketch.scale_factor);
        ctx1.drawImage(newCanvas,0,0);
        //ctx1.putImageData(imgData, 0, 0);
        
        // update the mask in the input image gallery ...
        var ig = $("#input_gallery").data("image_gallery");
        
        // set object input to have information text below the image
        var obj = {};
        var keys = Object.keys(ig.contents);
        var image_id =  keys.length;
        // TODO: try to find position of mask in contents
        for(var i=0;i<keys.length;i++) {
            if (keys[i]==="Mask") {
                image_id = i;
                break;
            }
        }
        obj['<span id="inputinfo_'+image_id+'">mask info</span>'] = $("#mask_canvas")[0].toDataURL();
        ig.Append({ "Mask":  obj} );
        // disable onload callback, since it was creating the inpainting interface
        ig.SetOnLoad(undefined);
        ig.SetOnLoadAll(undefined);
        ig.keep_dimensions_onload=true;
        var bg_im = ig.GetImage(0)[0].src;
        ig.user_image_style="background:url("+bg_im+");background-size:cover;";
        ig.BuildContents();
    }
    
    //--------------------------------------------------------------------------
    this.SubmitInpaint = function( ddl_json, upload_callback ) {
        // with inpainting upload input and mask ...
        // upload files and run the demo
        this.progress_info = "input upload";

        // fill form data to upload
        var formData = new FormData();
        formData.append('demo_id',    ddl_json.demo_id);
        formData.append('ddl_inputs', JSON.stringify(ddl_json.inputs));
        var inputs  = ddl_json.inputs;
        // we should have two inputs: the image and the mask
        // if several input image, TODO: deal with crop of first image
        var blobs_in_form=0;
        // TODO: change this line to avoid depending on the html code
        var ig = $("#input_gallery").data("image_gallery");
        var image_src = ig.GetImage(0)[0].src;
        // upload input image
        blobUtil.imgSrcToBlob(image_src,"image/png","Anonymous").then(
            function(blob) { 
                formData.append('file_0', blob);
                blobs_in_form++;
                if(blobs_in_form==ddl_json.inputs.length) {
                    upload_callback(formData);
                }
            }, 'image/png' );
        // upload input mask
        var mask_src = $("#mask_canvas")[0].toDataURL("image/png");

        blobUtil.dataURLToBlob(mask_src).then(
            function(blob) {
                    formData.append('file_1', blob);
                    blobs_in_form++;
                    if(blobs_in_form==ddl_json.inputs.length) {
                        upload_callback(formData);
                    }
            });
    }
    
}
