//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_results.js
// date: march 2016
// author: Karl Krissian
//
// description:
// this file contains the code that renders and deals with the demo results
// associated with ipol_demo.html and ipol_demo.js
//

"use strict";

var DrawResults = function( //demo_id,key,
                            res,ddl_results) {
    
    this.ddl_results  = ddl_results;
    this.res          = res;
    this.params       = res.params;
    this.work_url     = res.work_url;
    this.ZoomFactor   = 1;
    console.info("DrawResults");

//     //--------------------------------------------------------------------------
//     this.CreateZoomSelection = function() {
//         var scales=[0.125,0.25,0.5,0.75,1, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
//         var res='';
//         res += '<label> Zoom factor for images </label>'+
//                '<select id="zoomfactor">';
//             for(var id=0;id<scales.length;id++) {
//                 if (scales[id]==this.ZoomFactor) {
//                     res += "<option selected='selected'>";
//                 } else {
//                     res += "<option>";
//                 }
//                 res += scales[id]+"</option>";
//             }
//         res += "</select><br/>";
//         return res;
//     }
//     
    //--------------------------------------------------------------------------
    this.Create = function() {

        var results_html = "";
        var displayed_status = { "OK":"success", "KO":"failure" };
        
        // display result status
        if (res.status==="KO") {
            results_html += '  <p class="error"> '+res.error+' </p>';
        }
        
//         results_html += this.CreateZoomSelection();

        for(var id=0;id<this.ddl_results.length;id++) {
            results_html+=this.CreateResult(this.ddl_results[id],id);
        }
        
        $("#ResultsDisplay").html(results_html);
//         $("#ResultsDisplay").change(

        for(var id=0;id<this.ddl_results.length;id++) {
            this.CreateResultEvents(this.ddl_results[id],id);
        }


//         $("#zoomfactor").change(
//             function() {
//                 this.ZoomFactor = $("#zoomfactor option:selected").val();
//                 console.info(" ZoomFactor = ", this.ZoomFactor);
//                 this.Create();
//             }.bind(this)
//         );
    };
    
    //--------------------------------------------------------------------------
    this.CreateResult = function(res_desc,id) {
        console.info("CreateResult ",id," type ",res_desc.type);
        var display = true;
        var visible_expr = undefined;
        if (res_desc.visible_new!==undefined) {
            visible_expr = res_desc.visible_new;
        } else {
            visible_expr = res_desc.visible;
        }
        if (visible_expr!==undefined) {
            display = this.EvalInContext(visible_expr);
            console.info("evaluating ", visible_expr);
            console.info('display result = ',display);
        }
        if (display) {
            switch(res_desc.type) {
                case "html_text":       return this.HtmlText      (res_desc);
                case "file_download":   return this.FileDownload  (res_desc);
                case "gallery":         return this.Gallery_new   (res_desc,id);;
                case "repeat_gallery":  return this.Gallery_new   (res_desc,id);
                case "text_file":       return this.TextFile      (res_desc,id);
                case "warning":         return this.Warning       (res_desc);
                default: console.info(" result type "+ res_desc.type + " not available");
            }
        } else {
            return "";
        }
    };
    
    //--------------------------------------------------------------------------
    this.CreateResultEvents = function(res_desc,id) {
        var display = true;
        var visible_expr = undefined;
        if (res_desc.visible_new!==undefined) {
            visible_expr = res_desc.visible_new;
        } else {
            visible_expr = res_desc.visible;
        }
        if (visible_expr!==undefined) {
            display = this.EvalInContext(visible_expr);
            console.info("evaluating ", visible_expr);
            console.info('display result = ',display);
        }
        if (display) {
            switch(res_desc.type) {
                case "gallery":
                    this.Gallery_new_events(res_desc,id);
                    break;
                case "repeat_gallery":
                    this.RepeatGallery_new_events(res_desc,id);
                    break;
                case "text_file":
                    this.TextFile_events(res_desc,id);
                    break;
            }
        }
    };
    
    //--------------------------------------------------------------------------
    this.joinHtml = function(html_code)
    {
        if ($.isArray(html_code)) {
          return html_code.join(' ');
        } else {
          return html_code;
        }
    };
    
    //--------------------------------------------------------------------------
    this.GetLabel = function(label)
    {
        if(label.indexOf('?') === -1) 
            return label;
        else 
            return label.split('?')[1];
    };
    
    //--------------------------------------------------------------------------
    this.CheckLabelCondition = function(label)
    {
        if(label.indexOf('?') === -1) return true;
        var c = label.split('?')[0];
        var value = this.EvalInContext(c)
        return value;
    }

    //--------------------------------------------------------------------------
    this.HtmlText = function(res_desc) {
        var contents = this.joinHtml(res_desc.contents);
        if (res_desc.contents_new!==undefined) {
            contents = this.joinHtml(res_desc.contents_new);
        } 
        if (contents[0]==="'") {
            //console.info("HtmlText evaluating ", contents);
            return "<div>"+this.EvalInContext(contents)+"</div><br/>";
        } else {
            //console.info("contents=",contents);
            return "<div>"+contents+"</div><br/>";
        }
    };
    
    //--------------------------------------------------------------------------
    this.Warning = function(res_desc) {
        console.info("display Warning ",res_desc);
        var html=  
        "<p style='border:1px solid;margin:10px 0px;padding:15px 10px 15px 50px;color:#9F6000;'>"+
          "<b><u>WARNING</u></b><br/><br/>"+
          "<span>"+res_desc.contents+"</span> <br/><br/>"+
        "</p>";
        console.info(html);
        return html;
    }
        
    //--------------------------------------------------------------------------
    this.TextFile = function(res_desc,id) {

        var default_style=  "width:auto;height:auto;background-color:#eee;overflow:auto;max-height:30em;"+
                            "white-space:pre;margin:1em 0;font-weight:normal;";
        var html = '';
        html += res_desc.label;
//        html += '<iframe src="'+this.work_url+res_desc.contents+'" ';
        html += '<pre id=result_' + id+ ' ';
        if (res_desc.style_new) {
            html += 'style="'+default_style + this.EvalInContext(res_desc.style_new) + '" >';
        } else {
            html += 'style="'+default_style + res_desc.style+'" >';
        }
        html += '</pre>';
//        html += '</iframe>';
        return html;
    };
    
    //--------------------------------------------------------------------------
    this.TextFile_events = function(res_desc,id) {

        $('#result_' + id).load(this.work_url+res_desc.contents);
    };
    
    //--------------------------------------------------------------------------
    this.FileDownload = function(res_desc) {
        var html = "";
        
        if (res_desc.repeat!=undefined) {
            for(var idx=0;idx<this.EvalInContext(res_desc.repeat);idx++) {
                var file=this.EvalInContext(res_desc.contents,idx);
                var label=this.EvalInContext(res_desc.label,idx);
                html += '&nbsp;[&nbsp;<a href="'+this.work_url+file+'" target="_blank">';
                html += label;
                html += "</a>&nbsp;]<br/>"
            }
        } else {
            var label = this.joinHtml(res_desc.label);
            if (label[0]=="'") {
                label = this.EvalInContext(label);
            }
            html += label;
            if ($.type(res_desc.contents)==="object") {
              jQuery.each(res_desc.contents, function(label,file) {
                html += '&nbsp;[&nbsp;<a href="'+this.work_url+file+'" target="_blank">';
                html += label;
                html += "</a>&nbsp;]&nbsp;"
              }.bind(this));
            } else {
                html += '<a href="'+this.work_url+res_desc.contents+'" target="_blank">';
                html += res_desc.label;
                html += '</a>';
            }
        }
        html += '<br/><br/>';
        return html;
    };
    
    
    //--------------------------------------------------------------------------
    this.EvalInContext = function( expr, idx ) {
        if (idx===undefined) {
            idx=0;
        }
        // need sizeX, sizeY, ZoomFactor
        var ZoomFactor = this.ZoomFactor;
        var sizeX = this.params.x1-this.params.x0;
        var sizeY = this.params.y1-this.params.y0;
        // need imwidth and imheight
        var info     = this.res.algo_info;
        var meta     = this.res.algo_meta;
        var params   = this.params;
        var imwidth  = meta.max_width;
        var imheight = meta.max_height;
        var work_url = this.work_url;
        return eval(expr);

    }
    
    //--------------------------------------------------------------------------
    this.Gallery_new = function(res_desc,id) {
        var res="";
        if (res_desc.label!=undefined) {
            var label = this.joinHtml(res_desc.label);
            if (label[0]=="'") {
                label = this.EvalInContext(label);
            }
            res += label;
        }
        
        var index = 0;
        
        // compute style
        // TODO: improve security risks with eval()
        var style = this.EvalInContext(res_desc.style_new);
        
        // TODO: check what variable needs the style and remove its angular code
        res += '<div id=result_' + id + ' style="height:auto">';
        res += '</div><br/>';
        return res;

    } // end Gallery_new
    
    //--------------------------------------------------------------------------
    this.Gallery_new_events = function(res_desc,id) {
        var index = 0;
        if (res_desc.contents_new) {
            var contents = res_desc.contents_new;
        } else {
            var contents = res_desc.contents;
        }
        var new_contents = {};
        jQuery.each( contents, function( label, image ) {
            index++;
            // check label condition
            var label_condition=this.CheckLabelCondition(label);
            if (label_condition) {
                // label
                var label = this.GetLabel(label);
                if (label[0]==="'") {
                    label = this.EvalInContext(label);
                }
                // string case
                switch ($.type(image)) {
                    case "string":
                        if (image==="'") {
                            image = this.EvalInContext(image);
                        }
                        new_contents[label]=this.work_url+image;
                        break;
                    case "object":
                        // avoid modifying original contents, using
                        // jquery extend with deep copy
                        var val={};
                        val[label]=image;
                        $.extend(true,new_contents,val);
                        jQuery.each( image, function(l,im) {
                            if (im==="'") {
                                im = this.EvalInContext(im);
                            }
                            new_contents[label][l]=this.work_url+im;
                        }.bind(this));
                        break;
                    case "array":
                        // avoid modifying original contents
                        var val={};
                        val[label]=image;
                        $.extend(true,new_contents,val);
                        jQuery.each( image, function(index, im) {
                            if (im==="'") {
                                im = this.EvalInContext(im);
                            }
                            new_contents[label][index]=this.work_url+im;
                        }.bind(this));
                        break;
                } // end switch
            } // if label condition
        }.bind(this));
        
        var ig = new ImageGallery(id);
        ig.Append(new_contents);
        var html = ig.CreateHtml();
        $("#result_"+id).html(html);
        ig.CreateEvents();
        $("#result_"+id).data("image_gallery",ig);

    } // end Gallery_new_events
    

//     //--------------------------------------------------------------------------
//     this.RepeatGallery = function(res_desc) {
//         var res="";
//         if (res_desc.label!=undefined) {
//             res += '<span>'+ this.joinHtml(res_desc.label)+'</span><br/>';
//         }
// 
//         
//         // compute style
//         // TODO: improve security risks with eval()
//         var style = this.EvalInContext(res_desc.style_new);
//         
//         // TODO: check what variable needs the style and remove its angular code
//         res += '<div   class="gallery2" style="'+style+'">';
//         
//         if (res_desc.contents_new) {
//             var contents = res_desc.contents_new;
//         } else {
//             var contents = res_desc.contents;
//         }
//         
//         res += '<ul class="index">';
//         for(var idx=0;idx<this.EvalInContext(res_desc.repeat);idx++) {
//             res += '<li>';
//             res += '<a href="#" >';
//             // label
//             console.info(contents[0]);
//             console.info(contents[1]);
//             res += '<div>'+this.EvalInContext(contents[0],idx)+'</div>'
//             
//             if ($.type(contents[1])!=="array") {
//                 res += '<span class="galim" >';
//                 res += '<img  style="'+style+'"';
//                 res +=        'src="'+this.work_url+this.EvalInContext(contents[1],idx)+'"';
//                 res += '/>';
//                 res += '</span>';
//             } else {
//                 res += '<span class="galim" >';
//                 res += '<table border="1">';
//                 res += '<tr>';
//                 jQuery.each( contents[1], function(index, im) {
//                     res += '<td style="text-align:center">';
//                     res += '<img  style="'+style+'"';
//                     res +=        'src="'+this.work_url+this.EvalInContext(im,idx)+'"';
//                     res += '/>';
//                     res += '</td>';
//                 }.bind(this));
//                 res += '</tr>';
//                 res += '</table>';
//                 res += '</span>';
//             }
//             res += '</a>';
//             res += '</li>';
//         }
//         res += '</ul>';
//         res += '</div><br/><br/>';
//         return res;
//     }
//                                 

    //--------------------------------------------------------------------------
    this.RepeatGallery_new_events = function(res_desc, id ) {
        var index = 0;
        if (res_desc.contents_new) {
            var contents = res_desc.contents_new;
        } else {
            var contents = res_desc.contents;
        }
        var new_contents = {};

        for(var idx=0;idx<this.EvalInContext(res_desc.repeat);idx++) {
            
            var label = this.EvalInContext(contents[0],idx);
            
            if ($.type(contents[1])!=="array") {
                new_contents[label]=this.work_url+this.EvalInContext(contents[1],idx);
            } else {
                // avoid modifying original contents
                var val={};
                val[label]=contents[1];
                $.extend(true,new_contents,val);
                jQuery.each( contents[1], function(index, im) {
                    new_contents[label][index]=this.work_url+this.EvalInContext(im,idx);
                }.bind(this));
            }
        }
        
        var ig = new ImageGallery(id);
        ig.Append(new_contents);
        var html = ig.CreateHtml();
        $("#result_"+id).html(html);
        ig.CreateEvents();
        $("#result_"+id).data("image_gallery",ig);
        
    }

}
