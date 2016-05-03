
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
    this.style="height:200px;";
    this.hover_bgcolor='rgba(255,228,196,155)';
    this.ref_bgcolor  ='#BCD2EE';
    this.ZoomFactor   = 1;
    this.onload_callback    = undefined;
    this.ondisplay_callback = undefined;
    this.onloadall_callback = undefined;
    
    //--------------------------------------------------------------------------
    this.Append = function(content) {
        $.extend(this.contents,content);
    }
    
    //--------------------------------------------------------------------------
    this.SetStyle = function(s) {
        console.info("Gallery style is ", s);
        this.style=s;
    }

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
        var scales=[0.125,0.25,0.5,0.75,1, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
        var res='';
        this.zoom_id = 'gallery_'+this.galleryid+'_zoomfactor';
        res += "x&nbsp;<select id='"+this.zoom_id+"'>";
            for(var id=0;id<scales.length;id++) {
                if (scales[id]==this.ZoomFactor) {
                    res += "<option selected='selected'>";
                } else {
                    res += "<option>";
                }
                res += scales[id]+"</option>";
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
//             html += "<tr style='"+title_style+"'>";
//             html +=   "<td style='border:0;height:2em' >";
//             html +=   this.CreateZoomSelection();
//             html +=   "</td>";
//             html += "</tr>";
            $.each(titles, function(index,title) {
                html += "<tr style='"+title_style+"'>";
                html +=   "<td id='t"+index+"' style='white-space:nowrap;border:0;height:1.25em;' >";
                html +=   title;
                html +=   "</td>";
                html += "</tr>";
            }.bind(this)
            );
            html += "</table>";

        html +=   "</td>";
        html +=   "<td id='contents' "+style+">";
        html +=     "contents";
        html +=   "</td>";
        html += "</tr>";
            
        html += "</table>";
        return html;
    };
        
    
    //--------------------------------------------------------------------------
    this.CreateContents = function(title,index) {
        
        // need style ...
        
        var image = this.contents[title];
        console.info("CreateContents ", title, ": ", image);
        var res="";
        this.img_class = 'gallery_'+this.galleryid+'_img';

        var img_style = this.style;
        
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
    this.CreateImages = function(index) {
        
        // need style ...
        var titles = Object.keys(this.contents);
        var image = this.contents[titles[index]];
        console.info("CreateImages ", titles[index], ": ", image);
        
        var res=[];
        
        this.img_class = 'gallery_'+this.galleryid+'_img';

        var img_style = this.style;
        
        var loading_font = {'font-style':'italic','font-weight':'bold'};
        var normal_font  = {'font-style':'normal','font-weight':'normal'};
        
        // string case
        switch ($.type(image)){
            case "string": 
                var im = new Image();
                this.total_images++;
                res.push(im);
                $(this.Elt(index)).css(loading_font);
                im.onload = function() { 
                    $(this.Elt(index)).css(normal_font);
                    console.info("image for ",titles[index], " loaded");
                    if (this.onload_callback!=undefined) {
                        this.onload_callback(index,im);
                    }
                    this.total_loaded_images++;
                    if ((this.total_loaded_images===this.total_images)&&
                        (this.onloadall_callback!=undefined)) {
                        this.onloadall_callback();
                    }
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
                        //$(this.Elt(index)).css('font-style','normal');
                        console.info("[",l,"] for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==Object.keys(image).length) {
                            console.info("all images loaded for ",titles[index]);
                            $(this.Elt(index)).css(normal_font);
                        }
                        if (this.onload_callback!=undefined) {
                            this.onload_callback(index,_im);
                        }
                        this.total_loaded_images++;
                        if ((this.total_loaded_images===this.total_images)&&
                            (this.onloadall_callback!=undefined)) {
                            this.onloadall_callback();
                        }
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
                        //$(this.Elt(index)).css('font-style','normal');
                        console.info("image ",idx," for ",titles[index], " loaded");
                        this.nb_loaded_images[index]++;
                        // check if all images are loaded
                        if (this.nb_loaded_images[index]==image.length) {
                            console.info("all images loaded for ",titles[index]);
                            $(this.Elt(index)).css(normal_font);
                        }
                        this.total_loaded_images++;
                        if ((this.total_loaded_images===this.total_images)&&
                            (this.onloadall_callback!=undefined)) {
                            this.onloadall_callback();
                        }
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
        
//         $("#"+this.zoom_id).change( 
//             function() {
//                 this.ZoomFactor = $("#"+this.zoom_id+" option:selected").val();
//                 console.info(" new ZoomFactor = ", this.ZoomFactor);
//             }.bind(this)
//         );
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
