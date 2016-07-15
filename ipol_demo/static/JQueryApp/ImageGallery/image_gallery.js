/**
 * @file 
 * Interface for displaying image gallery.
 * Display several images or tables containing images with/without captions.
 * Allows resizing, and fast switch between the different inputs.
 * Allows image comparison.
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";


// ipol application namespace
var ipol = ipol || {};



/**
 * ImageGallery class: 
 * displays image contents associated with different titles
 * that changes based on mouse hover events,
 * designed to replace the CSS based image gallery for IPOL.
 * @constructor
 */
ipol.ImageGallery = function(galleryid)  {
    

    /** 
     * Enable/Disable display of (tracing/debugging) 
     * information in browser console.
     * @var {boolean} _verbose
     * @memberOf ipol.ArchiveDisplay~
     * @private
     */
    var _verbose=false;

    //--------------------------------------------------------------------------
     /**
     * Displays message in console if _verbose is true
     * @function _infoMessage
     * @memberOf ipol.ImageGallery~
     * @private
     */
   var _infoMessage = function( ) {
        if (_verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- ImageGallery ----");
            console.info.apply(console,args);
        }
    }
    

    /** 
     * contents is an object of type 'title':'image contents'
     * where image contents can be:
     *   - a single location of an image
     *   - an array of image location
     *   - an object containing image and titles
     * @var {object} contents
     * @memberOf ipol.ImageGallery~
     */
    this.contents = {};
    
    /** 
     * index of the reference displayed contents. 
     * @default 0
     * @var {number} _ref_index
     * @memberOf ipol.ImageGallery~
     * @private
     */
    var _ref_index      = 0;
    
    /** 
     * index of the reference compared contents. 
     * @default 1
     * @var {number} _compare_index
     * @memberOf ipol.ImageGallery~
     * @private
     */
    var _compare_index  = 1;
    
    /** 
     * gallery id for HTML
     * @var {string} _galleryid
     * @memberOf ipol.ImageGallery~
     * @private
     */
    var _galleryid = galleryid;
    
    /** 
     * name of the image HTML class for this gallery
     * @var {string} img_class
     * @memberOf ipol.ImageGallery~
     */
    this.img_class = 'gallery_'+_galleryid+'_img';
    
    /** 
     * CSS style info
     * @var {string} style
     * @memberOf ipol.ImageGallery~
     */
    this.style="height:200px;";
    
    /** 
     * background color on hover over input labels
     * @var {string} hover_bgcolor 
     * @default 'rgba(255,228,196,155)'
     * @memberOf ipol.ImageGallery~
     */
    this.hover_bgcolor='rgba(255,228,196,155)';
    
    /** 
     * background color of the reference input
     * @var {string} ref_bgcolor 
     * @default '#BCD2E'
     * @memberOf ipol.ImageGallery~
     */
    this.ref_bgcolor  ='#BCD2EE';
    
    /** 
     * Images zoom factor
     * @var {string} zoom_factor 
     * @default 1
     * @memberOf ipol.ImageGallery~
     */
    this.zoom_factor   = 1;
    
    /** 
     * callback called after loading each input image
     * @var {callback} onload_callback
     * @default undefined
     * @memberOf ipol.ImageGallery~
     */
    this.onload_callback    = undefined;

    /** 
     * callback called after displaying an input
     * @var {callback} ondisplay_callback 
     * @default undefined
     * @memberOf ipol.ImageGallery~
     */
    this.ondisplay_callback = undefined;
    
    /** 
     * callback called after loading all input images
     * @var {callback} onloadall_callback 
     * @default undefined
     * @memberOf ipol.ImageGallery~
     */
    this.onloadall_callback = undefined;

    // set maximum display dimensions
    this.display_maxwidth  = $(window).width()*0.80;

    this.display_maxheight = $(window).height()*0.80;

    _infoMessage("max dimensions = "+this.display_maxwidth+ "x"+this.display_maxheight);

    this.display_minwidth  = 300;

    this.display_minheight = 300;

    this.scales=[0.125,0.25, 0.333, 0.5, 0.667, 0.75, 1, 1.25, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];

    this.current_contents = "#contents1";

    this.keep_dimensions_onload = false;

    this.user_image_style = "";
    
    //--------------------------------------------------------------------------
    /** 
     * Sets minimal display height
     * @param {number} mh minimal height of display
     * @function SetMinHeight
     * @memberOf ipol.ImageGallery~
     */
    this.SetMinHeight = function(mh) {
        this.display_minheight = mh;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Sets minimal display width
     * @param {number} mh minimal width of display
     * @function SetMinWidth
     * @memberOf ipol.ImageGallery~
     */
    this.SetMinWidth = function(mw) {
        this.display_minwidth = mw;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Add input contents
     * @param {object} content to add to the gallery
     * @function Append
     * @memberOf ipol.ImageGallery~
     */
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
    /** 
     * Sets on image load event callback
     * @param {callback} callback
     * @function SetOnLoad
     * @memberOf ipol.ImageGallery~
     */
    this.SetOnLoad = function( callback ) {
        this.onload_callback = callback;
    }

    //--------------------------------------------------------------------------
    /** 
     * Sets on display contents  callback
     * @param {callback} callback
     * @function SetOnDisplay
     * @memberOf ipol.ImageGallery~
     */
    this.SetOnDisplay = function( callback ) {
        this.ondisplay_callback = callback;
    }

    //--------------------------------------------------------------------------
    /** 
     * Sets on load all input images callback
     * @param {callback} callback
     * @function SetOnLoadAll
     * @memberOf ipol.ImageGallery~
     */
    this.SetOnLoadAll = function( callback ) {
        this.onloadall_callback = callback;
    }

    //--------------------------------------------------------------------------
    /** 
     * Creates the HTML code for selecting the Zoom factor
     * @function CreateZoomSelection
     * @memberOf ipol.ImageGallery~
     * @returns {string} HTML code
     */
    this.CreateZoomSelection = function() {
        var res='';
        this.zoom_id = 'gallery_'+_galleryid+'_zoomfactor';
        res += "x&nbsp;<select id='"+this.zoom_id+"'>";
            for(var id=0;id<this.scales.length;id++) {
                if (this.scales[id]==this.zoom_factor) {
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
    /** 
     * Creates the main HTML code for the Gallery
     * @function CreateHtml
     * @memberOf ipol.ImageGallery~
     * @returns {string} HTML code
     */
    this.CreateHtml = function() {
        var html = "";

        // set border 0px to avoid coordinates problems in the canvas
        var style="style='border:0px;border-collapse: collapse;'";
        
        html += "<table "+style+" id='gallery_"+_galleryid+"' >";
        
        var titles = Object.keys(this.contents);
        
        var title_style = "border:0;padding:0;margin:0;background-color:#FFFFFF;"
        
        html += "<tr "+style+">";
        html +=   "<td style='vertical-align:top;"+title_style+"'>";

            html += "<table style='"+title_style+"'>";
            // loop over titles
            $.each(titles, function(index,title) {
                html += "<tr style='"+title_style+"'>";
                html +=   "<td id='t"+index+"' style='border:0;height:1.25em;max-width:10em;' >"; // white-space:nowrap;
                html +=   title;
                html +=   "</td>";
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
        html +=   "<td class='image_class' "+style+">";
        html +=   "<div id='contents1' "+"style='border:0px;margin:0px;padding:0px;max-width:1000px;max-height:1000px;overflow-x:auto;overflow-y:auto'>";
        html +=     "contents1";
        html +=   "</div>";
        html +=   "</td>";
        html +=   "<td class='compare_class' "+style+">";
        html +=   "<div id='contents2' "+"style='border:0px;margin:0px;padding:0px;max-width:1000px;max-height:1000px;overflow-x:auto;overflow-y:auto'>";
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
        
        html += "<div id='gallery_"+_galleryid+"_all' title='Gallery Images' ></div>";
        
        return html;
        
    };
        
    
    //--------------------------------------------------------------------------
    /** 
     * Creates the array of contents for a given title and index
     * @function CreateContents
     * @memberOf ipol.ImageGallery~
     * @param {string} title
     * @param {number} index
     * @returns {string} HTML code
     */
    this.CreateContents = function(title,index) {
        
        // need style ...
        
        var image = this.contents[title];
        _infoMessage("CreateContents "+ title+ ": "+ image);
        var res="";

        // try to have nearest neighbor interpolation 
        // (see https://developer.mozilla.org/fr/docs/Web/CSS/Image-rendering)
        var img_style = this.user_image_style+
                        "image-rendering:pixelated;"+
                        "-ms-interpolation-mode:nearest-neighbor;"+
                        "image-rendering:optimizeSpeed;"+
                        "image-rendering:-moz-crisp-edges;"+
                        "image-rendering:-o-crisp-edges;"+
                        // "image-rendering:-webkit-optimize-contrast;"+
                        "image-rendering:optimize-contrast;"+
                        "image-rendering:crisp-edges;";
        
        // string case
        switch ($.type(image)){
            case "string": 
                res += '<img  crossorigin="anonymous"  style="'+img_style+'"';
                res += ' id=img_'+index+' ';
                res += ' class='+this.img_class+' ';
                res +=        'src="'+image+'"';
                res += '/>';
                _infoMessage("returning ",res);
                return res;
            case "object":
                res += '<table style="margin:1px;">';
                res += '<tr style="margin:1px">';
                var idx=0;
                jQuery.each( image, function(l,im) {
                    res += '<td style="text-align:center;border:1px;padding:1px;margin:1px">';
                    res += '<img  crossorigin="anonymous"  style="'+img_style+'"';
                    res += ' class='+this.img_class+' ';
                    res += ' id=img_'+index+'_'+idx+' ';
                    res +=        'src="'+im+'"';
                    res += '/>';
                    res += '</td>';
                    idx++;
                }.bind(this));
                res += '</tr>';
                res += '<tr style="margin:1px">';
                jQuery.each( image, function(l,im) {
                    res += '<td style="text-align:center;border:1px;padding:1px;margin:1px">';
                    res += '<span>'+l+'</span>';
                    res += '</td>';
                }.bind(this));
                res += '</tr>';
                res += '</table>';
                return res;
            case "array":
                var res="";
                res += '<table style="margin:1px;">';
                res += '<tr style="margin:1px">';
                jQuery.each( image, function(idx, im) {
                    res += '<td style="text-align:center;border:1px;padding:1px;margin:1px">';
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
    /** 
     * automatically computes image scales (zoom factor) 
     * based on the window available width
     * @function CheckDimensions
     * @memberOf ipol.ImageGallery~
     */
    //
    this.CheckDimensions = function() {
        // update window size
        var compare_sel = '#gallery_'+_galleryid+' #id_compare';
        var compare_checked = $(compare_sel).is(':checked');
        var used_width = $("#t0").parent().outerWidth();
        if (compare_checked) {
            used_width += $("#compare_0").parent().outerWidth();
        }
        this.display_maxwidth  = $(window).width()-used_width-120;
        this.display_maxheight = $(window).height()*0.80;
        
        var contents1_sel = "#gallery_"+_galleryid+" #contents1";
        var contents2_sel = "#gallery_"+_galleryid+" #contents2";
        
        // set max width/height:
        if (compare_checked) {
            $(contents1_sel).css({ "max-width":  (this.display_maxwidth/2-5)+"px",
                                "max-height": this.display_maxheight+"px"});
            $(contents2_sel).css({ "max-width":  (this.display_maxwidth/2-5)+"px",
                                "max-height": this.display_maxheight+"px"});
        } else {
            $(contents1_sel).css({ "max-width":  this.display_maxwidth+"px",
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
        _infoMessage("ratio = ",ratio);
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
            _infoMessage("scale ",idx," = ",this.scales[idx]);
            $("#"+this.zoom_id).val(this.scales[idx]);
            $("#"+this.zoom_id).trigger("change");
        } else {
            // check min display constraint
            // also risk of incompatibilities between min and max constraints
            // don´t zoom by default
            var ratio = 1;
            ratio = Math.max(ratio,this.display_minheight/this.max_height);
            ratio = Math.max(ratio,this.display_minwidth/this.max_width);
            _infoMessage("ratio = ",ratio);
            if (ratio>=1) {
                var idx=this.scales.length-1;
                while (this.scales[idx]>ratio) {
                    idx--
                }
                // TODO: check max constraint is still OK
                _infoMessage("scale ",idx," = ",this.scales[idx]);
                $("#"+this.zoom_id).val(this.scales[idx]);
                $("#"+this.zoom_id).trigger("change");
            }
        }
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Check if all images are loaded, if so update the current contents
     * for the selection (left) and comparing selection (right) if available,
     * and triggers the callback if any
     * @function CheckLoadAllImages
     * @memberOf ipol.ImageGallery~
     */
    this.CheckLoadAllImages = function() {
        
        if (this.total_loaded_images===this.total_images) {
            if (!this.keep_dimensions_onload) { this.CheckDimensions(); }
            this.UpdateSelection();
            this.UpdateCompareSelection();
            _infoMessage("All images are loaded ... running callback ");
            if (this.onloadall_callback!=undefined) {
                this.onloadall_callback();
            }
        }
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Create images to load for a given content index
     * on each image load, update max_width and max_height variables and 
     * triggers on image load callback if any
     * update the total count of images this.total_images and of loaded images
     * this.total_loaded_images
     * @param {number} index
     * @function CreateImages
     * @memberOf ipol.ImageGallery~
     * @returns {object[]} array of images for the given index
     */
    this.CreateImages = function(index) {
        
        // need style ...
        var titles = Object.keys(this.contents);
        var image = this.contents[titles[index]];
        _infoMessage("*** CreateImages ", titles[index], ": ", image);
        
        var res=[];
        

        // compute max width and height of all input images
        this.max_height=10;
        this.max_width=10;
    
        var loading_font = {'font-style':'italic','font-weight':'bold'};
        var normal_font  = {'font-style':'normal','font-weight':'normal'};
        
        // string case
        switch ($.type(image)){
            case "string": 
                _infoMessage("string image");
                var im = new Image();
                this.total_images++;
                res.push(im);
                $(this.Elt(index)).css(loading_font);
                im.crossOrigin = "Anonymous";
                im.onload = function() { 
                    this.max_height = Math.max(this.max_height,im.height);
                    this.max_width  = Math.max(this.max_width, im.width);
                    _infoMessage(" max :", this.max_width, "x" , this.max_height);
                    $(this.Elt(index)).css(normal_font);
                    _infoMessage("image for ",titles[index], " loaded");
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
                        _infoMessage(" max :", this.max_width, "x" , this.max_height);
                        //$(this.Elt(index)).css('font-style','normal');
                        _infoMessage("[",l,"] for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==Object.keys(image).length) {
                            _infoMessage("all images loaded for ",titles[index]);
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
                        _infoMessage(" max :", this.max_width, "x" , this.max_height);
                        //$(this.Elt(index)).css('font-style','normal');
                        _infoMessage("image ",idx," for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==image.length) {
                            _infoMessage("all images loaded for ",titles[index]);
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
    /** 
     * returns the string for selecting (using JQuery) the contents of the given
     * index
     * @function Elt
     * @memberOf ipol.ImageGallery~
     * @param {integer} index
     * @returns {string} string for selecting the gallery content
     */
    this.Elt = function(index) {
        return "#gallery_"+_galleryid+" #t"+index;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * returns the string for selecting (using JQuery) the contents 
     * of the given index in the comparison side
     * @function CompareElt
     * @memberOf ipol.ImageGallery~
     * @param {integer} index
     * @returns {string} string for selecting the compared gallery content
     */
    this.CompareElt = function(index) {
        return "#gallery_"+_galleryid+" #compare_"+index;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * returns the string for selecting (using JQuery) the reference contents 
     * @function RefElt
     * @memberOf ipol.ImageGallery~
     * @returns {string} string for selecting the compared gallery content
     */
    this.RefElt = function() {
        return "#gallery_"+_galleryid+" #t"+_ref_index;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * returns the string for selecting (using JQuery) the compared 
     * reference contents 
     * @function CompareRefElt
     * @memberOf ipol.ImageGallery~
     * @returns {string} string for selecting the compared gallery content
     */
    this.CompareRefElt = function() {
        return "#gallery_"+_galleryid+" #compare_"+_compare_index;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * returns the string for setting reference contents 
     * @function SelContents
     * @memberOf ipol.ImageGallery~
     * @param {number} pos contents to select: 1 left side (main), 2 right side (comparison)
     * @returns {string} string for setting the reference content
     */
    this.SelContents = function(pos) {
        return "#gallery_"+_galleryid+" "+"#contents"+pos;
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Sets the contents
     * @function SetContents
     * @memberOf ipol.ImageGallery~
     * @param {number} pos contents to set: 1 left side (main), 2 right side (comparison)
     * @param {number} index
     */
    this.SetContents = function(pos,index) {
        $(this.SelContents(pos)).html(this.html_contents[index]);
        $("."+this.img_class).css("height",(this.zoom_factor*this.max_height)+"px");
        if (this.ondisplay_callback!=undefined) {
            this.ondisplay_callback(index);
        }
    }
        
    //--------------------------------------------------------------------------
    /** 
     * Sets the main contents (left side) to their reference
     * @function UpdateSelection
     * @memberOf ipol.ImageGallery~
     */
    this.UpdateSelection = function() {
        $(this.RefElt()).css('background-color',this.ref_bgcolor);
        this.SetContents(1,_ref_index);
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Sets the comparison contents (right side) to their reference
     * @function UpdateCompareSelection
     * @memberOf ipol.ImageGallery~
     */
    this.UpdateCompareSelection = function() {
        $(this.CompareRefElt()).css('background-color',this.ref_bgcolor);
        this.SetContents(2,_compare_index);
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Sets the main contents reference index
     * @param {integer} index
     * @function SetSelection
     * @memberOf ipol.ImageGallery~
     */
    this.SetSelection = function(index) {
        $(this.RefElt()).css('background-color','');
        _ref_index = index;
        this.UpdateSelection();
    }

    //--------------------------------------------------------------------------
    /** 
     * Sets the comparison contents reference index
     * @param {integer} index
     * @function SetCompareSelection
     * @memberOf ipol.ImageGallery~
     */
    this.SetCompareSelection = function(index) {
        $(this.CompareRefElt()).css('background-color','');
        _compare_index = index;
        this.UpdateCompareSelection();
    }

    //--------------------------------------------------------------------------
    /** 
     * Gets the image contents for the given title index
     * @param {integer} index
     * @function GetImage
     * @memberOf ipol.ImageGallery~
     * @return {object[]} array of images of the requested index
     */
    this.GetImage = function(index) {
        return this.images_contents[index];
    }
    
    //--------------------------------------------------------------------------
    /** 
     * Creates all the HTML contents in the array html_contents and also 
     * all the images to load with their associated events
     * @function BuildContents
     * @memberOf ipol.ImageGallery~
     */
    this.BuildContents = function() {
        // create and store all contents
        var titles = Object.keys(this.contents);
        
        /** 
         * stores all the HTML contents
         * @var {string[]} html_contents html contents for each title
         * @memberOf ipol.ImageGallery~
         */
        this.html_contents = [];
        // create html content for each tab
        $.each(titles, function(index,title) {
            var c = this.CreateContents(title,index);
            this.html_contents.push(c);
        }.bind(this));
        
        /** 
         * stores all the images for each title
         * @var {object[][]} images_contents array of images to display for 
         * each title
         * @memberOf ipol.ImageGallery~
         */
        this.images_contents = [];
        
        /** 
         * counts loaded images to know when all images of a tab are loaded
         * @var {number[]} nb_loaded_images for each title
         * each title
         * @memberOf ipol.ImageGallery~
         */
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
    /** 
     * Calls BuildContents(), then creates all the events: hover, click, 
     * select zoom, etc...
     * @function BuildContents
     * @memberOf ipol.ImageGallery~
     */
    this.CreateEvents = function() {

        // deal with this.maxlength for text part
        
        _infoMessage("ImageGallery::CreateEvents() contents= ", this.contents);
        var titles = Object.keys(this.contents);

        this.BuildContents();
        
        // Set ref index to 0
        this.SetSelection(0);
        // Set compare index to 1
        this.SetCompareSelection(1);
        
        _infoMessage("CreateEvents");
        // create events
        $.each(titles, function(index,title) {
            _infoMessage("index =",index);
            $(this.Elt(index)).hover( 
                function() {
                    this.SetContents(1,index);
                    $(this.Elt(index)).css('background-color',this.hover_bgcolor);
                }.bind(this),
                function() {
                    if (index!=_ref_index) {
                        this.SetContents(1,_ref_index);
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
                    if (index!=_compare_index) {
                        this.SetContents(2,_compare_index);
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
                this.zoom_factor = $("#"+this.zoom_id+" option:selected").val();
                _infoMessage(this.zoom_id+ " changed ", this.zoom_factor);
                this.UpdateSelection();
            }.bind(this)
        );
        
//         // for the moment the wheel event to change scale is commented
//         $("#gallery_"+_galleryid).unbind("wheel").bind("wheel",
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
        
        var contents1_sel = "#gallery_"+_galleryid+" #contents1";
        var contents2_sel = "#gallery_"+_galleryid+" #contents2";
        
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

        $("#gallery_"+_galleryid+ " .compare_class, #gallery_"+_galleryid+ " .image_class").
        unbind("mousedown").mousedown(
            function(e) {
                if (e.target.nodeName.toLowerCase()==="img") {
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
        
        var compare_sel = '#gallery_'+_galleryid+' #id_compare';
        var compare_class_sel = '#gallery_'+_galleryid+' .compare_class';
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
        
//         $("#gallery_"+_galleryid).unbind().on("resize",function() { console.info("gallery resized"); } ); 
                                                                         
        $("#gallery_"+_galleryid+" #popup_all").button().unbind().on("click", 
            function() 
            { 
                // parameters description dialog
//                     width: 'auto',
//                     height: 'auto',
//                     maxWidth: $(window).width()*0.95,
//                     maxHeight: $(window).height()*0.95,
//                     position: [30,30],
                    //{ my: "center", at: "center", of: window },
                this.gallery_dialog = $("#gallery_"+_galleryid+"_all").dialog({
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
                            $("#gallery_"+_galleryid+"_all").dialog('close');
                        }.bind(this))
                    }.bind(this)
                });
        
                _infoMessage("popup_all click length=",this.html_contents.length);
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
                _infoMessage("setting ","#gallery_"+_galleryid+"_all", " to ", html);
                this.gallery_dialog.dialog("open");
                $("#gallery_"+_galleryid+"_all").html(html);
                $("."+this.img_class).css("height",(this.zoom_factor*this.max_height)+"px");
                if (this.ondisplay_callback!=undefined) {
                    for(var i=0;i<this.html_contents.length;i++) {
                        this.ondisplay_callback(i);
                    }
                }
            }.bind(this));
        
    }
    
}

