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

    //--------------------------------------------------------------------------
    this.CreateZoomSelection = function() {
        var scales=[0.125,0.25,0.5,0.75,1, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
        var res='';
        res += '<label> Zoom factor for images </label>'+
               '<select id="zoomfactor">';
            for(var id=0;id<scales.length;id++) {
                if (scales[id]==this.ZoomFactor) {
                    res += "<option selected='selected'>";
                } else {
                    res += "<option>";
                }
                res += scales[id]+"</option>";
            }
        res += "</select><br/>";
        return res;
    }
    
    //--------------------------------------------------------------------------
    this.Create = function() {

        var results_html = "";
        var displayed_status = { "OK":"success", "KO":"failure" };
        
        // display result status
        if (res.status==="KO") {
            results_html += '  <p class="error"> '+res.error+' </p>';
        }
        
        results_html += this.CreateZoomSelection();

        for(var id=0;id<this.ddl_results.length;id++) {
            results_html+=this.CreateResult(this.ddl_results[id],id);
        }
        
        $("#ResultsDisplay").html(results_html);
//         $("#ResultsDisplay").change(
        $("#zoomfactor").change(
            function() {
                this.ZoomFactor = $("#zoomfactor option:selected").val();
                console.info(" ZoomFactor = ", this.ZoomFactor);
                this.Create();
            }.bind(this)
        );
    };
    
    //--------------------------------------------------------------------------
    this.CreateResult = function(res_desc,id) {
        var display = true;
        var visible_expr = undefined;
        if (res_desc.visible_new!==undefined) {
            visible_expr = res_desc.visible_new;
        } else {
            visible_expr = res_desc.visible;
        }
        if (visible_expr!==undefined) {
            // need sizeX, sizeY, ZoomFactor
            var ZoomFactor = this.ZoomFactor;
            var sizeX = this.params.x1-this.params.x0;
            var sizeY = this.params.y1-this.params.y0;
            // need imwidth and imheight
            var info     = this.res.algo_info;
            var meta     = this.res.algo_meta;
            var imwidth  = meta.max_width;
            var imheight = meta.max_height;
            var params   = this.params;
            
            
            display = eval(visible_expr);
            console.info("evaluating ", visible_expr);
            console.info('display result = ',display);
        }
        if (display) {
            switch(res_desc.type) {
                case "html_text":       return this.HtmlText      (res_desc);
                case "file_download":   return this.FileDownload  (res_desc);
                case "gallery":         return this.Gallery       (res_desc,id);
                case "repeat_gallery":  return this.RepeatGallery (res_desc);
                case "text_file":       return this.TextFile      (res_desc);
                case "warning":         return this.Warning       (res_desc);
                default: console.info(" result type "+ res_desc.type + " not available");
            }
        } else {
            return "";
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
        // need sizeX, sizeY, ZoomFactor
        var ZoomFactor = this.ZoomFactor;
        var sizeX = this.params.x1-this.params.x0;
        var sizeY = this.params.y1-this.params.y0;
        // need imwidth and imheight
        var info     = this.res.algo_info;
        var meta     = this.res.algo_meta;
        var imwidth  = meta.max_width;
        var imheight = meta.max_height;
        var params   = this.params;
        
        if(label.indexOf('?') === -1) return true;
        var c = label.split('?')[0];
        var value = eval(c)
        return value;
    }

    //--------------------------------------------------------------------------
    this.HtmlText = function(res_desc) {
        var contents = this.joinHtml(res_desc.contents);
        if (res_desc.contents_new!==undefined) {
            contents = this.joinHtml(res_desc.contents_new);
        } 
        if (contents[0]==="'") {
            // need sizeX, sizeY, ZoomFactor
            var ZoomFactor = this.ZoomFactor;
            var sizeX = this.params.x1-this.params.x0;
            var sizeY = this.params.y1-this.params.y0;
            // need imwidth and imheight
            var info     = this.res.algo_info;
            var meta     = this.res.algo_meta;
            var imwidth  = meta.max_width;
            var imheight = meta.max_height;
            var params   = this.params;
            var work_url = this.work_url;
            return "<div>"+eval(contents)+"</div><br/>";
        } else {
            console.info("contents=",contents);
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
    this.TextFile = function(res_desc) {

        // need sizeX, sizeY, ZoomFactor
        var ZoomFactor = this.ZoomFactor;
        var sizeX = this.params.x1-this.params.x0;
        var sizeY = this.params.y1-this.params.y0;
        // need imwidth and imheight
        var info     = this.res.algo_info;
        var meta     = this.res.algo_meta;
        var imwidth  = meta.max_width;
        var imheight = meta.max_height;
        var params   = this.params;

        var html = '';
        html += res_desc.label;
        html += '<iframe src="'+this.work_url+res_desc.contents+'" ';
        if (res_desc.style_new) {
            html += 'style="'+eval(res_desc.style_new)+'" >';
        } else {
            html += 'style="'+res_desc.style+'" >';
        }
        html += '</iframe>';
        return html;
    };
    
    //--------------------------------------------------------------------------
    this.FileDownload = function(res_desc) {
        var html = "";
        if (res_desc.repeat!=undefined) {
//         <span ng-repeat="idx in range($eval(result.repeat))">
//           <a href="{{work_url+result.contents|interpolate_loop:current_scope:idx}}">
//             <div bind-html-compile="result.label"></div> <br/>
//           </a>
//         </span>
        } else {
            if ($.type(res_desc.contents)==="object") {
              html += res_desc.label;
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
            html += '<br/><br/>';
        }
        return html;
    };
    
    //--------------------------------------------------------------------------
    this.Gallery = function(res_desc,id) {
        var res="";
        if (res_desc.label!=undefined) {
            res += '<span>'+ this.joinHtml(res_desc.label)+'</span><br/>';
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
        var index = 0;
        
        // compute style
        // TODO: improve security risks with eval()
        var style = eval(res_desc.style_new);
        
        // TODO: check what variable needs the style and remove its angular code
        res += '<div   class="gallery2" id=result_' + (id+1) + ' style="'+style+'">';
        
        if (res_desc.contents_new) {
            var contents = res_desc.contents_new;
        } else {
            var contents = res_desc.contents;
        }
            
        // compute longest text length
        // not so easy ... should be done once the text is in place ...
        this.maxlength = 0;
        // Measure the string 
        jQuery.each( contents, function( label, image ) {
            // Return width
            var l = this.GetLabel(label);
            this.maxlength = Math.max(this.maxlength,l.length);
        }.bind(this));
        console.info("maxlength=",this.maxlength);
        // reduce since em measures the height and the with is usually smaller
        this.maxlength *= 0.7;
        // set maximal length
        this.maxlength = Math.min(this.maxlength,14);
  
        res += '<ul class="index">';
        jQuery.each( contents, function( label, image ) {
            index++;
            // check label condition
            var label_condition=this.CheckLabelCondition(label);
            if (label_condition) {
                res += '<li>';
                res += '<a href="#" style="width:'+this.maxlength+'em">';
                // label
                var label = this.GetLabel(label);
                if (label[0]==="'") {
                    label = eval(label);
                }
                res += '<span>'+label+'</span>'
                // TODO: add loading text here
                // string case
                if ($.type(image)==="string") {
                    res += '<div class="galim" style="left:'+this.maxlength+'em">';
                    res += '<img  style="'+style+'"';
                    res += ' id=img_'+index+' ';
                    if (image==="'") {
                        image = eval(image);
                    }
                    res +=        'src="'+this.work_url+image+'"';
                    res += '/>';
                    res += '</div>';
                } else {
                    if ($.type(image)==="object") {
                        res += '<div class="galim" style="left:'+this.maxlength+'em">';
                        res += '<table border="1">';
                        res += '<tr>';
                        jQuery.each( image, function(l,im) {
                            res += '<td style="text-align:center">';
                            res += '<img  style="'+style+'"';
                            res += ' id=img_'+index+' ';
                            if (im[0]==="'") {
                                im = eval(im);
                            }
                            res +=        'src="'+this.work_url+im+'"';
                            res += '/>';
                            res += '</td>';
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
                        res += '</div>';
                    } else {
                        if ($.type(image)==="array") {
                            res += '<div class="galim" style="left:'+this.maxlength+'em">';
                            res += '<table border="1">';
                            res += '<tr>';
                            jQuery.each( image, function(index, im) {
                                res += '<td style="text-align:center">';
                                res += '<img  style="'+style+'"';
                                res += ' id=img_'+index+' ';
                                res +=        'src="'+this.work_url+im+'"';
                                res += '/>';
                                res += '</td>';
                            }.bind(this));
                            res += '</tr>';
                            res += '</table>';
                            res += '</div>';
                        }
                    }
                }
                res += '</a>';
                res += '</li>';
            }
        }.bind(this));
        res += '</ul>';
        res += '</div><br/><br/>';
        return res;
    }

                                
    //--------------------------------------------------------------------------
    this.RepeatGallery = function(res_desc) {
        var res="";
        if (res_desc.label!=undefined) {
            res += '<span>'+ this.joinHtml(res_desc.label)+'</span><br/>';
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
        
        // compute style
        // TODO: improve security risks with eval()
        var style = eval(res_desc.style_new);
        
        // TODO: check what variable needs the style and remove its angular code
        res += '<div   class="gallery2" style="'+style+'">';
        
        if (res_desc.contents_new) {
            var contents = res_desc.contents_new;
        } else {
            var contents = res_desc.contents;
        }
        
        res += '<ul class="index">';
        for(var idx=0;idx<eval(res_desc.repeat);idx++) {
            res += '<li>';
            res += '<a href="#" >';
            // label
            console.info(contents[0]);
            console.info(contents[1]);
            res += '<div>'+eval(contents[0])+'</div>'
            
            if ($.type(contents[1])!=="array") {
                res += '<span class="galim" >';
                res += '<img  style="'+style+'"';
                res +=        'src="'+this.work_url+eval(contents[1])+'"';
                res += '/>';
                res += '</span>';
            } else {
                res += '<span class="galim" >';
                res += '<table border="1">';
                res += '<tr>';
                jQuery.each( contents[1], function(index, im) {
                    res += '<td style="text-align:center">';
                    res += '<img  style="'+style+'"';
                    res +=        'src="'+this.work_url+eval(im)+'"';
                    res += '/>';
                    res += '</td>';
                }.bind(this));
                res += '</tr>';
                res += '</table>';
                res += '</span>';
            }
            res += '</a>';
            res += '</li>';
        }
        res += '</ul>';
        res += '</div><br/><br/>';
        return res;
    }
                                
}
