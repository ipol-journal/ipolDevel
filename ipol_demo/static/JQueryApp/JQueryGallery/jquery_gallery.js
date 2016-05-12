
// ImageGallery class
// displays image contents associated with different titles
// that changes based on mouse hover events
// designed to replace the CSS based image gallery for IPOL
var ImageGallery = function(galleryid)  {
    
    // contents is an object of type 'title':'image contents'
    // where image contents can be:
    //   - a single location of an image
    //   - an array of image location
    //   - an object containing image and titles
    this.contents = {};
    this.ref_index = 0;
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
    console.info("max dimensions = ",this.display_maxwidth, "x",this.display_maxheight);
    this.display_minwidth  = 400;
    this.display_minheight = 300;
    this.scales=[0.125,0.25, 0.333, 0.5, 0.667, 0.75,1, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
    
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
                html += "</tr>";
            }.bind(this)
            );
            html += "<tr style='"+title_style+"'>";
            html +=   "<td style='border:0;height:2em' >";
            html +=   this.CreateZoomSelection();
            html +=   "</td>";
            html += "</tr>";
            html += "<tr style='"+title_style+"'>";
            html +=   "<td style='border:0;height:2em' >";
            html +=   "<button id='popup_all'>all</button>"
            html +=   "</td>";
            html += "</tr>";
            html += "</table>";

        html +=   "</td>";
        html +=   "<td id='contents' "+style+">";
        html +=     "contents";
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
        console.info("CreateContents ", title, ": ", image);
        var res="";

        var img_style = "";
        //this.style;
        
        // string case
        switch ($.type(image)){
            case "string": 
                res += '<img  style="'+img_style+'"';
                res += ' id=img_'+index+' ';
                res += ' class='+this.img_class+' ';
                res +=        'src="'+image+'"';
                res += '/>';
                console.info("returning ",res);
                return res;
            case "object":
                res += '<table style="border:0px">';
                res += '<tr>';
                var idx=0;
                jQuery.each( image, function(l,im) {
                    res += '<td style="text-align:center">';
                    res += '<img  style="'+img_style+'"';
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
                    res += '<img  style="'+img_style+'"';
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
    this.CheckLoadAllImages = function(index) {
        if (this.total_loaded_images===this.total_images) {
            console.info("All images are loaded ... running callback ");
            if (this.onloadall_callback!=undefined) {
                this.onloadall_callback();
            }
            // adapt zoom factor based on maximum display allowed
            var ratio = 1;
            ratio = Math.min(ratio,this.display_maxheight/this.max_height);
            ratio = Math.min(ratio,this.display_maxwidth/this.max_width);
            console.info("ratio = ",ratio);
            if (ratio<1) {
                // find scale to select
                var idx=0;
                while (this.scales[idx]<ratio) {
                    idx++
                }
                if (idx>0) {
                    idx--;
                }
                console.info("scale ",idx," = ",this.scales[idx]);
                $("#"+this.zoom_id).val(this.scales[idx]);
                $("#"+this.zoom_id).trigger("change");
            } else {
                // check min display constraint
                // also risk of incompatibilities between min and max constraints
                var ratio = 1;
                ratio = Math.max(ratio,this.display_minheight/this.max_height);
                ratio = Math.max(ratio,this.display_minwidth/this.max_width);
                console.info("ratio = ",ratio);
                if (ratio>1) {
                    var idx=this.scales.length-1;
                    while (this.scales[idx]>ratio) {
                        idx--
                    }
                    if (idx<this.scales.length-1) {
                        idx++;
                    }
                    // TODO: check max constraint is still OK
                    console.info("scale ",idx," = ",this.scales[idx]);
                    $("#"+this.zoom_id).val(this.scales[idx]);
                    $("#"+this.zoom_id).trigger("change");
                }
            }
            this.UpdateSelection();
        }
    }
    
    //--------------------------------------------------------------------------
    this.CreateImages = function(index) {
        
        // need style ...
        var titles = Object.keys(this.contents);
        var image = this.contents[titles[index]];
        console.info("*** CreateImages ", titles[index], ": ", image);
        
        var res=[];
        

        // compute max width and height of all input images
        this.max_height=10;
        this.max_width=10;
    
        var loading_font = {'font-style':'italic','font-weight':'bold'};
        var normal_font  = {'font-style':'normal','font-weight':'normal'};
        
        // string case
        switch ($.type(image)){
            case "string": 
                console.info("string image");
                var im = new Image();
                this.total_images++;
                res.push(im);
                $(this.Elt(index)).css(loading_font);
                im.onload = function() { 
                    this.max_height = Math.max(this.max_height,im.height);
                    this.max_width  = Math.max(this.max_width, im.width);
                    console.info(" max :", this.max_width, "x" , this.max_height);
                    $(this.Elt(index)).css(normal_font);
                    console.info("image for ",titles[index], " loaded");
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
                    _im.onload = function() { 
                        this.max_height = Math.max(this.max_height,_im.height);
                        this.total_width[index] += _im.width;
                        console.info(" max :", this.max_width, "x" , this.max_height);
                        //$(this.Elt(index)).css('font-style','normal');
                        console.info("[",l,"] for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==Object.keys(image).length) {
                            console.info("all images loaded for ",titles[index]);
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
                    _im.onload = function() { 
                        this.max_height = Math.max(this.max_height,_im.height);
                        this.total_width[index] += _im.width;
                        console.info(" max :", this.max_width, "x" , this.max_height);
                        //$(this.Elt(index)).css('font-style','normal');
                        console.info("image ",idx," for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==image.length) {
                            console.info("all images loaded for ",titles[index]);
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
    this.RefElt = function(index) {
        return "#gallery_"+this.galleryid+" #t"+this.ref_index;
    }
    
    //--------------------------------------------------------------------------
    this.SelContents = function() {
        return "#gallery_"+this.galleryid+" #contents";
    }
    
    //--------------------------------------------------------------------------
    this.SetContents = function(index) {
        $(this.SelContents()).html(this.html_contents[index]);
        $("."+this.img_class).css("height",(this.ZoomFactor*this.max_height)+"px");
        if (this.ondisplay_callback!=undefined) {
            this.ondisplay_callback(index);
        }
    }
    
    //--------------------------------------------------------------------------
    this.UpdateSelection = function() {
        var titles = Object.keys(this.contents);
        $(this.RefElt()).css('background-color',this.ref_bgcolor);
        this.SetContents(this.ref_index);
    }
    
    //--------------------------------------------------------------------------
    this.SetSelection = function(index) {
        $(this.RefElt()).css('background-color','');
        this.ref_index = index;
        this.UpdateSelection();
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
        
        console.info("ImageGallery::CreateEvents() contents= ", this.contents);
        var titles = Object.keys(this.contents);

        this.BuildContents();
        
        // Set ref index to 0
        this.SetSelection(0);
        
        console.info("CreateEvents");
        // create events
        $.each(titles, function(index,title) {
            console.info("index =",index);
            $(this.Elt(index)).hover( 
                function() {
                    this.SetContents(index);
                    $(this.Elt(index)).css('background-color',this.hover_bgcolor);
                }.bind(this),
                function() {
                    if (index!=this.ref_index) {
                        this.SetContents(this.ref_index);
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
        }.bind(this));
        
        $("#"+this.zoom_id).change( 
            function() {
                this.ZoomFactor = $("#"+this.zoom_id+" option:selected").val();
                console.info(this.zoom_id+ " changed ", this.ZoomFactor);
                this.UpdateSelection();
            }.bind(this)
        );
        
        
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
                    }
                });
        
                console.info("popup_all click length=",this.html_contents.length);
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
                console.info("setting ","#gallery_"+this.galleryid+"_all", " to ", html);
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
