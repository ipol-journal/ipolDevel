
// ImageGallery class
// displays image contents associated with different titles
// that changes based on mouse hover events
// designed to replace the CSS based image gallery for IPOL
var ImageGallery = function(galleryid)  {
    
    //--------------------------------------------------------------------------
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- ImageGallery ----");
            console.info.apply(console,args);
        }
    }
    

    // contents is an object of type 'title':'image contents'
    // where image contents can be:
    //   - a single location of an image
    //   - an array of image location
    //   - an object containing image and titles
    this.contents = {};
    this.ref_index      = 0;
    this.compare_index  = 1;
    this.galleryid = galleryid;
    this.img_class = 'gallery_'+this.galleryid+'_img';
    this.style="height:200px;";
    this.hover_bgcolor='rgba(255,228,196,155)';
    this.ref_bgcolor  ='#BCD2EE';
    this.ZoomFactor   = 1;
    this.onload_callback    = undefined;
    this.ondisplay_callback = undefined;
    this.onloadall_callback = undefined;
    // set maximum display dimensions
    this.display_maxwidth  = $(window).width()*0.80;
    this.display_maxheight = $(window).height()*0.80;
    this.verbose=true;
    this.InfoMessage("max dimensions = "+this.display_maxwidth+ "x"+this.display_maxheight);
    this.display_minwidth  = 400;
    this.display_minheight = 300;
    this.scales=[0.125,0.25, 0.333, 0.5, 0.667, 0.75, 1, 1.25, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
    this.current_contents = "#contents1";
    this.keep_dimensions_onload = false;
    
    //--------------------------------------------------------------------------
    this.Append = function(content) {
        $.extend(this.contents,content);
    }
    
//     //--------------------------------------------------------------------------
//     this.SetStyle = function(s) {
//         console.info("Gallery style is ", s);
//         this.style=s;
//     }
// 
    //--------------------------------------------------------------------------
    this.SetOnLoad = function( callback ) {
        this.onload_callback = callback;
    }

    //--------------------------------------------------------------------------
    this.SetOnDisplay = function( callback ) {
        this.ondisplay_callback = callback;
    }

    //--------------------------------------------------------------------------
    this.SetOnLoadAll = function( callback ) {
        this.onloadall_callback = callback;
    }

    //--------------------------------------------------------------------------
    this.CreateZoomSelection = function() {
        var res='';
        this.zoom_id = 'gallery_'+this.galleryid+'_zoomfactor';
        res += "x&nbsp;<select id='"+this.zoom_id+"'>";
            for(var id=0;id<this.scales.length;id++) {
                if (this.scales[id]==this.ZoomFactor) {
                    res += "<option selected='selected'>";
                } else {
                    res += "<option>";
                }
                res += this.scales[id]+"</option>";
            }
        res += "</select>";
        return res;
    }
    
    //--------------------------------------------------------------------------
    this.CreateHtml = function() {
        var html = "";

//        var style="style='border:1px solid black;border-collapse: collapse;'";
        var style="style='border:0px;border-collapse: collapse;'";
        
        html += "<table "+style+" id='gallery_"+this.galleryid+"' >";
        
        var titles = Object.keys(this.contents);
        
        var title_style = "border:0;padding:0;margin:0;background-color:#FFFFFF;"
        
        html += "<tr "+style+">";
        html +=   "<td style='vertical-align:top;"+title_style+"'>";

            html += "<table style='"+title_style+"'>";
            $.each(titles, function(index,title) {
                html += "<tr style='"+title_style+"'>";
                html +=   "<td id='t"+index+"' style='white-space:nowrap;border:0;height:1.25em;' >";
                html +=   title;
                html +=   "</td>";
//                 html +=   "<td class='compare_class' id='compare_"+index+"' style='white-space:nowrap;border:1px;height:1.25em;' >";
//                 html +=   "&nbsp;&nbsp;";
//                 html +=   "</td>";
                html += "</tr>";
            }.bind(this)
            );
            html += "<tr style='"+title_style+"'>";
            html +=   "<td style='border:0;height:2em;white-space:nowrap' >";
            html +=   this.CreateZoomSelection();
            html +=   "</td>";
            html += "</tr>";
            html += "<tr style='"+title_style+"'>";
            html +=   "<td style='border:0;height:2em;white-space:nowrap' >";
            html +=        "<input  type='checkbox' id='id_compare'>";
            html +=        "<label>compare</label>";
            html +=   "</td>";
            html += "</tr>";
            html += "<tr style='"+title_style+"'>";
            html +=   "<td style='border:0;height:2em' >";
            html +=   "<button id='popup_all'>all</button>"
            html +=   "</td>";
            html += "</tr>";
            
            html += "</table>";

        html +=   "</td>";
//         html +=   "<td id='contents1' "+style+">";
        html +=   "<td class='image_class' "+style+">";
        html +=   "<div id='contents1' "+"style='border:1px;max-width:1000px;max-height:1000px;overflow-x:auto;overflow-y:auto'>";
        html +=     "contents1";
        html +=   "</div>";
        html +=   "</td>";
        html +=   "<td class='compare_class' "+style+">";
        html +=   "<div id='contents2' "+"style='border:1px;max-width:1000px;max-height:1000px;overflow-x:auto;overflow-y:auto'>";
        html +=     "contents2";
        html +=   "</div>";
        html +=   "</td>";
        
        html +=   "<td class='compare_class' style='vertical-align:top;"+title_style+"'>";

            html += "<table style='"+title_style+"'>";
            $.each(titles, function(index,title) {
                html += "<tr style='"+title_style+"'>";
                html +=   "<td  id='compare_"+index+"' style='white-space:nowrap;border:1px;height:1.25em;' >";
                if(title.length>15) {
                    html +=   title.substring(0,12)+"...";
                } else {
                    html +=   title;
                }
                html +=   "</td>";
                html += "</tr>";
            }.bind(this)
            );
            html += "</table>";

        html +=   "</td>";
        html += "</tr>";
            
        html += "</table>";
        
        html += "<div id='gallery_"+this.galleryid+"_all' title='Gallery Images' ></div>";
        
//     // parameters description dialog
//     var param_desc_dialog;
//     param_desc_dialog = $("#ParamDescription").dialog({
//       autoOpen: false,
// //       height: 500,
//       width: 800,
//       modal: true,
//     });
//     
//     $("#description_params").button().on("click", 
//         function() 
//         { 
//             param_desc_dialog.dialog("open");
//         });
        return html;
        
        
    };
        
    
    //--------------------------------------------------------------------------
    this.CreateContents = function(title,index) {
        
        // need style ...
        
        var image = this.contents[title];
        this.InfoMessage("CreateContents "+ title+ ": "+ image);
        var res="";

        // try to have nearest neighbor interpolation 
        // (see https://developer.mozilla.org/fr/docs/Web/CSS/Image-rendering)
        var img_style = "image-rendering:pixelated;"+
                        "-ms-interpolation-mode:nearest-neighbor;"+
                        "image-rendering:optimizeSpeed;"+
                        "image-rendering:-moz-crisp-edges;"+
                        "image-rendering:-o-crisp-edges;"+
//                         "image-rendering:-webkit-optimize-contrast;"+
                        "image-rendering:optimize-contrast;"+
                        "image-rendering:crisp-edges;";
        //this.style;
//         .pixelated {
//             image-rendering:optimizeSpeed;             /* Legal fallback */
//             image-rendering:-moz-crisp-edges;          /* Firefox        */
//             image-rendering:-o-crisp-edges;            /* Opera          */
//             image-rendering:-webkit-optimize-contrast; /* Safari         */
//             image-rendering:optimize-contrast;         /* CSS3 Proposed  */
//             image-rendering:crisp-edges;               /* CSS4 Proposed  */
//             image-rendering:pixelated;                 /* CSS4 Proposed  */
//             -ms-interpolation-mode:nearest-neighbor;   /* IE8+           */
//         }
        
        // string case
        switch ($.type(image)){
            case "string": 
                res += '<img  crossorigin="anonymous"  style="'+img_style+'"';
                res += ' id=img_'+index+' ';
                res += ' class='+this.img_class+' ';
                res +=        'src="'+image+'"';
                res += '/>';
                this.InfoMessage("returning ",res);
                return res;
            case "object":
                res += '<table style="border:0px">';
                res += '<tr>';
                var idx=0;
                jQuery.each( image, function(l,im) {
                    res += '<td style="text-align:center">';
                    res += '<img  crossorigin="anonymous"  style="'+img_style+'"';
                    res += ' class='+this.img_class+' ';
                    res += ' id=img_'+index+'_'+idx+' ';
                    res +=        'src="'+im+'"';
                    res += '/>';
                    res += '</td>';
                    idx++;
                }.bind(this));
                res += '</tr>';
                res += '<tr>';
                jQuery.each( image, function(l,im) {
                    res += '<td style="text-align:center">';
                    res += '<span>'+l+'</span>';
                    res += '</td>';
                }.bind(this));
                res += '</tr>';
                res += '</table>';
                return res;
            case "array":
                var res="";
                res += '<table style="border:0px">';
                res += '<tr>';
                jQuery.each( image, function(idx, im) {
                    res += '<td style="text-align:center">';
                    res += '<img  crossorigin="anonymous"  style="'+img_style+'"';
                    res += '      class='+this.img_class+' ';
                    res += '      id=img_'+index+'_'+idx+' src="'+im+'"/>';
                    res += '</td>';
                }.bind(this));
                res += '</tr>';
                res += '</table>';
                return res;
        }
    }
    
    
    //--------------------------------------------------------------------------
    // automatically computes image scales based on the window available width
    //
    this.CheckDimensions = function() {
        // update window size
        var compare_sel = '#gallery_'+this.galleryid+' #id_compare';
        var compare_checked = $(compare_sel).is(':checked');
        var used_width = $("#t0").parent().outerWidth();
        if (compare_checked) {
            used_width += $("#compare_0").parent().outerWidth();
        }
        this.display_maxwidth  = $(window).width()-used_width-120;
        this.display_maxheight = $(window).height()*0.80;
        
        // set max width/height:
        if (compare_checked) {
            $("#contents1").css({ "max-width":  this.display_maxwidth/2+"px",
                                "max-height": this.display_maxheight+"px"});
            $("#contents2").css({ "max-width":  this.display_maxwidth/2+"px",
                                "max-height": this.display_maxheight+"px"});
        } else {
            $("#contents1").css({ "max-width":  this.display_maxwidth+"px",
                                "max-height": this.display_maxheight+"px"});
        }
        
        // adapt zoom factor based on maximum display allowed
//         var ratio = 1;
//         ratio = Math.min(ratio,this.display_maxheight/this.max_height);
        ratio = this.display_maxheight/this.max_height;
        if (compare_checked) {
            ratio = Math.min(ratio,this.display_maxwidth/(2*this.max_width));
        } else {
            ratio = Math.min(ratio,this.display_maxwidth/this.max_width);
        }
        this.InfoMessage("ratio = ",ratio);
        if (ratio<1) {
            // find scale to select
            var idx=0;
            while (this.scales[idx]<=ratio) {
                idx++
            }
            // be sure to fit in the window
            if (idx>0) {
                idx--;
            }
            this.InfoMessage("scale ",idx," = ",this.scales[idx]);
            $("#"+this.zoom_id).val(this.scales[idx]);
            $("#"+this.zoom_id).trigger("change");
        } else {
            // check min display constraint
            // also risk of incompatibilities between min and max constraints
            // don´t zoom by default
            var ratio = 1;
            ratio = Math.max(ratio,this.display_minheight/this.max_height);
            ratio = Math.max(ratio,this.display_minwidth/this.max_width);
            this.InfoMessage("ratio = ",ratio);
            if (ratio>=1) {
                var idx=this.scales.length-1;
                while (this.scales[idx]>ratio) {
                    idx--
                }
                // TODO: check max constraint is still OK
                this.InfoMessage("scale ",idx," = ",this.scales[idx]);
                $("#"+this.zoom_id).val(this.scales[idx]);
                $("#"+this.zoom_id).trigger("change");
            }
        }
    }
    
    //--------------------------------------------------------------------------
    this.CheckLoadAllImages = function() {
        
        if (this.total_loaded_images===this.total_images) {
            if (!this.keep_dimensions_onload) { this.CheckDimensions(); }
            this.UpdateSelection();
            this.UpdateCompareSelection();
            this.InfoMessage("All images are loaded ... running callback ");
            if (this.onloadall_callback!=undefined) {
                this.onloadall_callback();
            }
        }
    }
    
    //--------------------------------------------------------------------------
    this.CreateImages = function(index) {
        
        // need style ...
        var titles = Object.keys(this.contents);
        var image = this.contents[titles[index]];
        this.InfoMessage("*** CreateImages ", titles[index], ": ", image);
        
        var res=[];
        

        // compute max width and height of all input images
        this.max_height=10;
        this.max_width=10;
    
        var loading_font = {'font-style':'italic','font-weight':'bold'};
        var normal_font  = {'font-style':'normal','font-weight':'normal'};
        
        // string case
        switch ($.type(image)){
            case "string": 
                this.InfoMessage("string image");
                var im = new Image();
                this.total_images++;
                res.push(im);
                $(this.Elt(index)).css(loading_font);
                im.crossOrigin = "Anonymous";
                im.onload = function() { 
                    this.max_height = Math.max(this.max_height,im.height);
                    this.max_width  = Math.max(this.max_width, im.width);
                    this.InfoMessage(" max :", this.max_width, "x" , this.max_height);
                    $(this.Elt(index)).css(normal_font);
                    this.InfoMessage("image for ",titles[index], " loaded");
                    if (this.onload_callback!=undefined) {
                        this.onload_callback(index,im);
                    }
                    this.total_loaded_images++;
                    this.CheckLoadAllImages();
                }.bind(this);
                im.src = image;
                return res;
            case "object":
                $(this.Elt(index)).css(loading_font);
                jQuery.each( image, function(l,im) {
                    var _im = new Image();
                    this.total_images++;
                    res.push(_im);
                    _im.crossOrigin = "Anonymous";
                    _im.onload = function() { 
                        this.max_height = Math.max(this.max_height,_im.height);
                        this.total_width[index] += _im.width;
                        this.InfoMessage(" max :", this.max_width, "x" , this.max_height);
                        //$(this.Elt(index)).css('font-style','normal');
                        this.InfoMessage("[",l,"] for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==Object.keys(image).length) {
                            this.InfoMessage("all images loaded for ",titles[index]);
                            this.max_width  = Math.max(this.max_width, this.total_width[index]);
                            $(this.Elt(index)).css(normal_font);
                        }
                        if (this.onload_callback!=undefined) {
                            this.onload_callback(index,_im);
                        }
                        this.total_loaded_images++;
                        this.CheckLoadAllImages();
                    }.bind(this);
                    _im.src = im;
                }.bind(this) );
                return res;
            case "array":
                $(this.Elt(index)).css(loading_font);
                jQuery.each( image, function(idx, im) {
                    var _im = new Image();
                    this.total_images++;
                    res.push(_im);
                    _im.crossOrigin = "Anonymous";
                    _im.onload = function() { 
                        this.max_height = Math.max(this.max_height,_im.height);
                        this.total_width[index] += _im.width;
                        this.InfoMessage(" max :", this.max_width, "x" , this.max_height);
                        //$(this.Elt(index)).css('font-style','normal');
                        this.InfoMessage("image ",idx," for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==image.length) {
                            this.InfoMessage("all images loaded for ",titles[index]);
                            this.max_width  = Math.max(this.max_width, this.total_width[index]);
                            $(this.Elt(index)).css(normal_font);
                        }
                        this.total_loaded_images++;
                        this.CheckLoadAllImages();
                    }.bind(this);
                    _im.src = im;
                }.bind(this) );
                return res;
        
        }
    }
    
    //--------------------------------------------------------------------------
    this.Elt = function(index) {
        return "#gallery_"+this.galleryid+" #t"+index;
    }
    
    //--------------------------------------------------------------------------
    this.CompareElt = function(index) {
        return "#gallery_"+this.galleryid+" #compare_"+index;
    }
    
    //--------------------------------------------------------------------------
    this.RefElt = function() {
        return "#gallery_"+this.galleryid+" #t"+this.ref_index;
    }
    
    //--------------------------------------------------------------------------
    this.CompareRefElt = function() {
        return "#gallery_"+this.galleryid+" #compare_"+this.compare_index;
    }
    
    //--------------------------------------------------------------------------
    this.SelContents = function(pos) {
        return "#gallery_"+this.galleryid+" "+"#contents"+pos;
//         this.current_contents;
    }
    
    //--------------------------------------------------------------------------
    this.SetContents = function(pos,index) {
        $(this.SelContents(pos)).html(this.html_contents[index]);
        $("."+this.img_class).css("height",(this.ZoomFactor*this.max_height)+"px");
        if (this.ondisplay_callback!=undefined) {
            this.ondisplay_callback(index);
        }
    }
        
    //--------------------------------------------------------------------------
    this.UpdateSelection = function() {
        $(this.RefElt()).css('background-color',this.ref_bgcolor);
        this.SetContents(1,this.ref_index);
    }
    
    //--------------------------------------------------------------------------
    this.UpdateCompareSelection = function() {
        $(this.CompareRefElt()).css('background-color',this.ref_bgcolor);
        this.SetContents(2,this.compare_index);
    }
    
    //--------------------------------------------------------------------------
    this.SetSelection = function(index) {
        $(this.RefElt()).css('background-color','');
        this.ref_index = index;
        this.UpdateSelection();
    }

    //--------------------------------------------------------------------------
    this.SetCompareSelection = function(index) {
        $(this.CompareRefElt()).css('background-color','');
        this.compare_index = index;
        this.UpdateCompareSelection();
    }

    //--------------------------------------------------------------------------
    this.GetImage = function(index) {
        return this.images_contents[index];
    }
    
    //--------------------------------------------------------------------------
    this.BuildContents = function() {
        // create and store all contents
        var titles = Object.keys(this.contents);
        
        this.html_contents = [];
        // create html content for each tab
        $.each(titles, function(index,title) {
            var c = this.CreateContents(title,index);
            this.html_contents.push(c);
        }.bind(this));
        
        this.images_contents = [];
        // count loaded images to know when all images of a tab are loaded
        this.nb_loaded_images = Array(titles.length);
        for (var i = 0; i < titles.length; i++) this.nb_loaded_images[i] = 0; 

        // compute total width for array or object elements
        this.total_width = Array(titles.length);
        for (var i = 0; i < titles.length; i++) this.total_width[i] = 0; 

        // count total number of loaded images
        this.total_loaded_images = 0;
        this.total_images = 0;

        // create list of images to load for each tab
        $.each(titles, function(index,title) {
            var c = this.CreateImages(index);
            this.images_contents.push(c);
        }.bind(this));
    }

    //--------------------------------------------------------------------------
    this.CreateEvents = function() {

        // deal with this.maxlength for text part
        
        this.InfoMessage("ImageGallery::CreateEvents() contents= ", this.contents);
        var titles = Object.keys(this.contents);

        this.BuildContents();
        
        //         $("#gallery_"+this.galleryid+" #contents1").unbind().click(
        //             function() {
        //                 this.current_contents="#contents1";
        //                 $("#gallery_"+this.galleryid+" #contents1").css({ "background-color":"wheat"});
        //                 $("#gallery_"+this.galleryid+" #contents2").css({ "background-color":"white"});
        //             }.bind(this)
        //         );
        //         
        //         $("#gallery_"+this.galleryid+" #contents2").unbind().click(
        //             function() {
        //                 this.current_contents="#contents2";
        //                 $("#gallery_"+this.galleryid+" #contents2").css({ "background-color":"wheat"});
        //                 $("#gallery_"+this.galleryid+" #contents1").css({ "background-color":"white"});
        //             }.bind(this)
        //         );
        
        // Set ref index to 0
        this.SetSelection(0);
        // Set compare index to 1
        this.SetCompareSelection(1);
        
        this.InfoMessage("CreateEvents");
        // create events
        $.each(titles, function(index,title) {
            this.InfoMessage("index =",index);
            $(this.Elt(index)).hover( 
                function() {
                    this.SetContents(1,index);
                    $(this.Elt(index)).css('background-color',this.hover_bgcolor);
                }.bind(this),
                function() {
                    if (index!=this.ref_index) {
                        this.SetContents(1,this.ref_index);
                        $(this.Elt(index)).css('background-color','');
                    } else {
                        $(this.Elt(index)).css('background-color',this.ref_bgcolor);
                    }
                }.bind(this)
            );
            $(this.Elt(index)).click( 
                function() { 
                    this.SetSelection(index);
                }.bind(this) ); 
            $(this.CompareElt(index)).hover( 
                function() {
                    this.SetContents(2,index);
                    $(this.CompareElt(index)).css('background-color',this.hover_bgcolor);
                }.bind(this),
                function() {
                    if (index!=this.compare_index) {
                        this.SetContents(2,this.compare_index);
                        $(this.CompareElt(index)).css('background-color','');
                    } else {
                        $(this.CompareElt(index)).css('background-color',this.ref_bgcolor);
                    }
                }.bind(this)
            );
            $(this.CompareElt(index)).click( 
                function() { 
                    this.SetCompareSelection(index);
                }.bind(this) ); 
        }.bind(this));
        
        // zoom factor selection events
        $("#"+this.zoom_id).unbind().change( 
            function() {
                this.ZoomFactor = $("#"+this.zoom_id+" option:selected").val();
                this.InfoMessage(this.zoom_id+ " changed ", this.ZoomFactor);
                this.UpdateSelection();
            }.bind(this)
        );
        
//         // for the moment the wheel event to change scale is commented
//         $("#gallery_"+this.galleryid).unbind("wheel").bind("wheel",
//             function(e) {
//                 e.preventDefault();
//                 var deltaY = 0;
//                 var oe = e.originalEvent;
//                 if (oe.deltaY) { // FireFox 17+ (IE9+, Chrome 31+?)
//                         deltaY = oe.deltaY;
//                 } else {
//                     if (oe.wheelDelta) {
//                         deltaY = -oe.wheelDelta;
//                     }
//                 }
//                 var ZoomFactor = $("#"+this.zoom_id+" option:selected").val();
//                 //console.info(" deltaY=",deltaY);
//                 // find next or previous zoom factor
//                 for(var i=0;i<this.scales.length;i++) {
//                     if (ZoomFactor==this.scales[i]) {
//                         if ((deltaY>0)&&(i<this.scales.length-1)) {
//                             ZoomFactor = this.scales[i+1];
//                             $("#"+this.zoom_id).val(ZoomFactor);
//                             $("#"+this.zoom_id).trigger("change");
//                         }
//                         if ((deltaY<0)&&(i>0)) {
//                             ZoomFactor = this.scales[i-1];
//                             $("#"+this.zoom_id).val(ZoomFactor);
//                             $("#"+this.zoom_id).trigger("change");
//                         }
//                         break;
//                     }
//                 }
//             }.bind(this)
//         );
        
        var contents1_sel = "#gallery_"+this.galleryid+" #contents1";
        var contents2_sel = "#gallery_"+this.galleryid+" #contents2";
        
        // move image with the mouse
        function gal_mousemove(e) {
            var info=$(contents1_sel).data(info);
            if (info.moving) {
                $(contents1_sel).scrollLeft(info.sl-(e.pageX-info.x));
                $(contents1_sel).scrollTop( info.sr-(e.pageY-info.y));
            }
        };

        function gal_mouseup() {
            var info={ moving:false };
            //console.info("end move ", info.sl);
            $(contents1_sel).data(info);
            $(document).unbind("mousemove",gal_mousemove);
            $(document).unbind("mouseup",gal_mouseup);
        };

        $("#gallery_"+this.galleryid+ " .compare_class, #gallery_"+this.galleryid+ " .image_class").
        unbind("mousedown").mousedown(
            function(e) {
                //console.info("start move ");
                e.preventDefault();
                var info={  
                    sl:$(contents1_sel).scrollLeft(), 
                    sr:$(contents1_sel).scrollTop(), 
                    x:e.pageX, 
                    y:e.pageY, 
                    moving:true };
                $(contents1_sel).data(info);
                $(document).mousemove(gal_mousemove);
                $(document).mouseup(gal_mouseup);
            }
        );
        
        // bind scroll events between compare views
        $(contents1_sel).unbind().scroll(
            function() {
                // set scroll position to contents2
                $(contents2_sel).scrollTop ($(contents1_sel).scrollTop());
                $(contents2_sel).scrollLeft($(contents1_sel).scrollLeft());
            }
        );
        $(contents2_sel).unbind().scroll(
            function() {
                // set scroll position to contents2
                $(contents1_sel).scrollTop ($(contents2_sel).scrollTop());
                $(contents1_sel).scrollLeft($(contents2_sel).scrollLeft());
            }
        );
        
        var compare_sel = '#gallery_'+this.galleryid+' #id_compare';
        var compare_class_sel = '#gallery_'+this.galleryid+' .compare_class';
        $(compare_sel).unbind().change( function()   { 
            var compare_checked = $(compare_sel).is(':checked');
            if (compare_checked) {
                $(compare_class_sel).show();
                this.CheckDimensions();
            } else {
                $(compare_class_sel).hide();
                this.CheckDimensions();
            }
        }.bind(this));
        
        $(compare_class_sel).hide();
        
//         $("#gallery_"+this.galleryid).unbind().on("resize",function() { console.info("gallery resized"); } ); 
                                                                         
        $("#gallery_"+this.galleryid+" #popup_all").button().unbind().on("click", 
            function() 
            { 
                // parameters description dialog
//                     width: 'auto',
//                     height: 'auto',
//                     maxWidth: $(window).width()*0.95,
//                     maxHeight: $(window).height()*0.95,
//                     position: [30,30],
                    //{ my: "center", at: "center", of: window },
                this.gallery_dialog = $("#gallery_"+this.galleryid+"_all").dialog({
                    autoOpen: false,
                    width: $(window).width()*0.95,
                    height: $(window).height()*0.95,
                    modal: true,
                    buttons: {
                        Close: function() {
                            $(this).dialog( "close" );
                        }
                    },
                    close: function(event, ui) {
                        $(this).empty().dialog('destroy');
                    },
                    // close on outside click ...
                    open: function(){
                        $('.ui-widget-overlay').bind('click',function(){
                            $("#gallery_"+this.galleryid+"_all").dialog('close');
                        }.bind(this))
                    }.bind(this)
                });
        
                this.InfoMessage("popup_all click length=",this.html_contents.length);
                var html = "<div >";
                for(var i=0;i<this.html_contents.length;i++) {
                    html += '<div style="display:inline-block;vertical-align:top;margin:2px">';
                    html += "<table>";
                    html +=   "<tr><td>";
                    html +=   this.html_contents[i];
                    html +=   "</td></tr>";
                    html +=   "<tr><td style='text-align:center;'>";
                    html +=   titles[i];
                    html +=   "</td></tr>";
                    html += "</table>";
                    html += "</div>";
                }
                html += "</div>";
                this.InfoMessage("setting ","#gallery_"+this.galleryid+"_all", " to ", html);
                this.gallery_dialog.dialog("open");
                $("#gallery_"+this.galleryid+"_all").html(html);
                $("."+this.img_class).css("height",(this.ZoomFactor*this.max_height)+"px");
                if (this.ondisplay_callback!=undefined) {
                    for(var i=0;i<this.html_contents.length;i++) {
                        this.ondisplay_callback(i);
                    }
                }
            }.bind(this));
        
    }
    
}

// //------------------------------------------------------------------------------
// // Starts processing when document is ready
// function DocumentReady() {
//   var html="";
//   var contents= { "title 1":"test/input_0.sel.png", "title 2":"test/output.png"};
//   var ig = new ImageGallery();
//   ig.Append(contents);
//   $("#GalleryTest").html(ig.CreateHtml());
//   ig.CreateEvents();
// }
// $(document).ready(DocumentReady);
