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


var DrawResults = function( //demo_id,key,
                            res,ddl_results) {
    
    this.ddl_results  = ddl_results;
    this.res          = res;
    this.params       = res.params;
    this.work_url     = res.work_url;
    this.ZoomFactor   = 1;


    this.CreateZoomSelection = function() {
        var scales=[0.125,0.25,0.5,0.75,1, 1.5, 2, 3, 4, 5, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
        var res='';
        res += '<label> Zoom factor for images </label>'+
               '<select>';
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
    
    this.Create = function() {

        var results_html = "";
        var displayed_status = { "OK":"success", "KO":"failure" };
        
        // display result status
        results_html += '<p>';
        results_html += '  Execution: '+res.run_time.toPrecision(2)+' sec.';
        results_html += '  ('+displayed_status[res.status]+')';
        results_html += '</p>';
        if (res.status==="KO") {
            results_html += '  <p class="error"> '+res.error+' </p>';
        }
        
        results_html += this.CreateZoomSelection();

        for(var id=0;id<this.ddl_results.length;id++) {
            results_html+=this.CreateResult(this.ddl_results[id]);
        }
        
        $("#ResultsDisplay").html(results_html);
        $("#ResultsDisplay").change(
            function() {
                this.ZoomFactor = $("#ResultsDisplay option:selected").val();
                console.info(" ZoomFactor = ", this.ZoomFactor);
                this.Create();
            }.bind(this)
        );
    };
    
    this.CreateResult = function(res_desc) {
        switch(res_desc.type) {
            case "html_text":     return this.HtmlText(res_desc);
            case "file_download": return this.FileDownload(res_desc);
            case "gallery":       return this.Gallery(res_desc);
            default: console.info(" result type "+ res_desc.type + " not available");
        }
    };
    
    this.joinHtml = function(html_code)
    {
        if ($.isArray(html_code)) {
          return html_code.join(' ');
        } else {
          return html_code;
        }
    };
    
    this.GetLabel = function(label)
    {
        if(label.indexOf('?') === -1) 
            return label;
        else 
            return label.split('?')[1];
    };
    
    this.CheckLabelCondition = function(label)
    {
        if(label.indexOf('?') === -1) return true;
        var c = label.split('?')[0];
        var value = eval(c)
        return value;
    }

    this.HtmlText = function(res_desc) {
        return "<div>"+this.joinHtml(res_desc.contents)+"</div><br/>";
    };
    
    this.FileDownload = function(res_desc) {
        return "";
    };
    
    this.Gallery = function(res_desc) {
        var res="";
        res += '<span>'+ this.joinHtml(res_desc.label)+'</span><br/>';
        
        // need sizeX, sizeY, ZoomFactor
        var ZoomFactor = this.ZoomFactor;
        var sizeX = this.params.x1-this.params.x0;
        var sizeY = this.params.y1-this.params.y0;
        style = eval(res_desc.style_new);
        
        // TODO: check what variable needs the style and remove its angular code
        res += '<div   class="gallery2" style="'+style+'">';
        
        if (res_desc.contents_new) {
            contents = res_desc.contents_new;
        } else {
            contents = res_desc.contents;
        }
            
        res += '<ul class="index">';
        jQuery.each( contents, function( label, image ) {
            // check label condition
            var label_condition=this.CheckLabelCondition(label);
            if (label_condition) {
                res += '<li>';
                res += '<a href="#" style="width:16em">';
                // label
                res += '<span>'+this.GetLabel(label)+'</span>'
                // TODO: add loading text here
                // string case
                if ($.type(image)==="string") {
                    res += '<div class="galim" style="left:16em">';
                    res += '<img  style="'+style+'"';
                    res +=        'src="'+this.work_url+image+'"';
                    res += '/>';
                    res += '</div>';
                } else {
                    if ($.type(image)==="object") {
                        res += '<div class="galim" style="left:16em">';
                        res += '<table border="1">';
                        res += '<tr>';
                        jQuery.each( image, function(l,im) {
                            res += '<td style="text-align:center">';
                            res += '<img  style="'+style+'"';
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
}
