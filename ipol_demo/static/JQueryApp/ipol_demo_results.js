/**
 * @file 
 * this file contains the code that renders and deals with the demo results
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";

/**
 * Display the demo results
 * @constructor
 * @param {object} res          results obtained from running the algorithm
 * @param {object} ddl_results  results section of the demo description
 */
var DrawResults = function( res,ddl_results) {
    
    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function InfoMessage
     * @memberOf DrawResults~
     */
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- DrawResults ----");
            console.info.apply(console,args);
        }
    }
    
    /** 
     * Enable/Disable verbose output to the console
     * @var {boolean} verbose
     * @memberOf DrawInputs~
     */
    this.verbose=true;
    this.InfoMessage("DrawResults started");
    this.verbose = false;

    /** 
     * Results section of the DDL
     * @var {object} ddl_results
     * @memberOf DrawInputs~
     */
    this.ddl_results  = ddl_results;

    /** 
     * Results obtained from the algorithm execution
     * @var {object} res
     * @memberOf DrawInputs~
     */
    this.res          = res;

    /** 
     * params (algorithm parameters) part of the results
     * @var {object} params
     * @memberOf DrawInputs~
     */
    this.params       = res.params;
    
    /** 
     * default url to the algorithm results
     * @var {string} work_url
     * @memberOf DrawInputs~
     */
    this.work_url     = res.work_url;

    //--------------------------------------------------------------------------
    /**
     * Specify the archive experiment from which we are drawing the results
     * @function SetExperiment
     * @memberOf DrawResults~
     * @param {number} exp         experiment number
     * @param {object} ddl_archive archive section of the DDL
     */
    this.SetExperiment = function(exp,ddl_archive) {
        this.experiment = exp;
        this.ddl_archive = ddl_archive; // archive part of the DDL
    }

    //--------------------------------------------------------------------------
    /**
     * Creates all the HTML code for the displaying the results
     * @function Create
     * @memberOf DrawResults~
     */
    this.Create = function() {

        var results_html = "";
        var displayed_status = { "OK":"success", "KO":"failure" };
        
        // display result status
        if (this.res.status==="KO") {
            results_html += '  <p class="error"> '+res.error+' </p>';
        }
        
        if (this.res.algo_meta["process_inputs_msg"]!=undefined) {
            results_html +=
                "<p style='border:1px solid;margin:3px 0px;padding:5px;color:#9F6000;'>"+
                "<b>"+this.res.algo_meta["process_inputs_msg"]+"</b>"+
                "</p>";
        }
//         results_html += this.CreateZoomSelection();

        for(var id=0;id<this.ddl_results.length;id++) {
            results_html+=this.CreateResult(this.ddl_results[id],id);
        }
        
        $("#ResultsDisplay").html(results_html);

        for(var id=0;id<this.ddl_results.length;id++) {
            this.CreateResultEvents(this.ddl_results[id],id);
        }

    };
    
    //--------------------------------------------------------------------------
    /**
     * Creates one component of the results
     * @function CreateResult
     * @memberOf DrawResults~
     * @param {object} res_desc DDL description of this result component
     * @param {number} id       id of the result component
     * @returns {string} the HTML code to display this result component
     */
    this.CreateResult = function(res_desc,id) {
        this.InfoMessage("CreateResult ",id," type ",res_desc.type);
        var display = true;
        var visible_expr = res_desc.visible;
        if (visible_expr!==undefined) {
            display = this.EvalInContext(visible_expr);
            this.InfoMessage("evaluating ", visible_expr);
            this.InfoMessage('display result = ',display);
        }
        if (display) {
            switch(res_desc.type) {
                case "html_text":       return this.HtmlText      (res_desc);
                case "file_download":   return this.FileDownload  (res_desc);
                case "gallery":         return this.Gallery_new   (res_desc,id);;
                case "repeat_gallery":  return this.Gallery_new   (res_desc,id);
                case "text_file":       return this.TextFile      (res_desc,id);
                case "warning":         return this.Warning       (res_desc);
                default: this.InfoMessage(" result type "+ res_desc.type + " not available");
            }
        } else {
            return "";
        }
    };
    
    //--------------------------------------------------------------------------
    /**
     * Creates the events associated with a displayed result component
     * @function CreateResultEvents
     * @memberOf DrawResults~
     * @param {object} res_desc DDL description of this result component
     * @param {number} id       id of the result component
     */
    this.CreateResultEvents = function(res_desc,id) {
        var display = true;
        var visible_expr = res_desc.visible;
        if (visible_expr!==undefined) {
            display = this.EvalInContext(visible_expr);
            this.InfoMessage("evaluating ", visible_expr);
            this.InfoMessage('display result = ',display);
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
    /**
     * join array of strings to return a single string if needed
     * @function joinHtml
     * @memberOf DrawResults~
     * @param {string[]|string} html_code as string or string array
     * @returns {string}
     */
    this.joinHtml = function(html_code)
    {
        if ($.isArray(html_code)) {
          return html_code.join(' ');
        } else {
          return html_code;
        }
    };
    
    //--------------------------------------------------------------------------
    /**
     * Get the label part of a property for gallery object, since
     * a condition can be included with the '?' character.
     * @function GetLabel
     * @memberOf DrawResults~
     * @param {string} label with possible condition
     * @returns {string} label without the conditional part
     */
    this.GetLabel = function(label)
    {
        if(label.indexOf('?') === -1) 
            return label;
        else 
            return label.split('?')[1];
    };
    
    //--------------------------------------------------------------------------
    /**
     * If no condition, return true, otherwise return the condition
     * evaluation
     * @function CheckLabelCondition
     * @memberOf DrawResults~
     * @param {string} label with possible condition
     * @returns {boolean} result from evaluating the condition if any, 
     * true otherwise
     */
    this.CheckLabelCondition = function(label)
    {
        if(label.indexOf('?') === -1) return true;
        var c = label.split('?')[0];
        var value = this.EvalInContext(c)
        return value;
    }

    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type html_text
     * @function HtmlText
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     */
    this.HtmlText = function(res_desc) {
        var contents = this.joinHtml(res_desc.contents);
        if (contents[0]==="'") {
            //this.InfoMessage("HtmlText evaluating ", contents);
            return "<div>"+this.EvalInContext(contents)+"</div><br/>";
        } else {
            //this.InfoMessage("contents=",contents);
            return "<div>"+contents+"</div><br/>";
        }
    };
    
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type warning
     * @function Warning
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     */
    this.Warning = function(res_desc) {
        this.InfoMessage("display Warning ",res_desc);
        var html=  
        "<p style='border:1px solid;margin:10px 0px;padding:15px 10px 15px 50px;color:#9F6000;'>"+
          "<b><u>WARNING</u></b><br/><br/>"+
          "<span>"+res_desc.contents+"</span> <br/><br/>"+
        "</p>";
        this.InfoMessage(html);
        return html;
    }
        
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type text_file
     * @function TextFile
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     */
    this.TextFile = function(res_desc,id) {

        var default_style=  "width:auto;height:auto;background-color:#eee;overflow:auto;max-height:30em;"+
                            "white-space:pre;margin:1em 0;font-weight:normal;";
        var html = '';
        html += res_desc.label;
//        html += '<iframe src="'+this.work_url+res_desc.contents+'" ';
        html += '<pre id=result_' + id+ ' ';
        if (res_desc.style[0]==="'") {
            html += 'style="'+default_style + this.EvalInContext(res_desc.style) + '" >';
        } else {
            html += 'style="'+default_style + res_desc.style+'" >';
        }
        html += '</pre>';
//        html += '</iframe>';
        return html;
    };
    
    //--------------------------------------------------------------------------
    /**
     * search filename url, if the results are from an experiment, try
     * to use archive url, otherwise use work_url path
     * @function FindUrl
     * @memberOf DrawResults~
     * @param {string} filename filename to look for
     * @returns {string} the filename url to use
     */
    // search filename url, if the results are from an experiment, try
    // to use archive url, otherwise use work_url path
    this.FindUrl = function(filename) {
        var url=undefined;
        if (this.experiment) {
            url = ArchiveDisplay.find_archive_url(filename,
                                                  this.ddl_archive.files,
                                                  this.experiment.files);
        }
        if (!url) {
            url = this.work_url+filename;
        }
        return url;
    }
    
    //--------------------------------------------------------------------------
    /**
     * load text file
     * @function TextFile_events
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     */
    this.TextFile_events = function(res_desc,id) {
        $('#result_' + id).load(this.FindUrl(res_desc.contents));
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type file_download
     * @function FileDownload
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     */
    this.FileDownload = function(res_desc) {
        var html = "";
        
        if (res_desc.repeat!=undefined) {
            for(var idx=0;idx<this.EvalInContext(res_desc.repeat);idx++) {
                var file=this.EvalInContext(res_desc.contents,idx);
                var label=this.EvalInContext(res_desc.label,idx);
                html += '&nbsp;[&nbsp;<a href="'+this.FindUrl(file)+'" target="_blank">';
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
                html += '&nbsp;[&nbsp;<a href="'+this.FindUrl(file)+'" target="_blank">';
                html += label;
                html += "</a>&nbsp;]&nbsp;"
              }.bind(this));
            } else {
                html += '<a href="'+this.FindUrl(res_desc.contents)+'" target="_blank">';
                html += res_desc.label;
                html += '</a>';
            }
        }
        html += '<br/><br/>';
        return html;
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Evaluates an expression with the following variables in the local
     * context: idx, sizeX, sizeY, info, meta, params, imwidth, imheight, 
     * work_url
     * @function EvalInContext
     * @memberOf DrawResults~
     * @param {string} expr expression to evaluate
     * @param {number} idx  index associated to the evaluation, defaults to 0
     * @returns {string|number} result from evaluation
     */
    this.EvalInContext = function( expr, idx ) {
        if (idx===undefined) {
            idx=0;
        }
        // need sizeX, sizeY
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
    /**
     * Returns the HTML code for a result of type gallery or repeat_gallery
     * @function Gallery_new
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     * @returns {string} HTML code for this result component
     */
    this.Gallery_new = function(res_desc,id) {
        var res="";
        if (res_desc.label!=undefined) {
            var label = this.joinHtml(res_desc.label);
            if (label[0]=="'") {
                label = this.EvalInContext(label);
            }
            res += label;
        }
        
        // TODO: check what variable needs the style and remove its angular code
        res += '<div id=result_' + id + ' style="height:auto">';
        res += '</div><br/>';
        return res;

    } // end Gallery_new
    
    //--------------------------------------------------------------------------
    /**
     * Completes the HTML code and the associated events 
     * for a result of type gallery
     * @function Gallery_new_events
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     */
    this.Gallery_new_events = function(res_desc,id) {
        var contents = res_desc.contents;
        var new_contents = {};
        jQuery.each( contents, function( label, image ) {
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
                        new_contents[label]=this.FindUrl(image);
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
                            new_contents[label][l]=this.FindUrl(im);
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
                            new_contents[label][index]=this.FindUrl(im);
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
        
        if (this.onloadall_callback) {
            ig.SetOnLoadAll( this.onloadall_callback.bind(this) );
        }

    } // end Gallery_new_events
    

    //--------------------------------------------------------------------------
    /**
     * Completes the HTML code and the associated events 
     * for a result of type repeat_gallery
     * @function RepeatGallery_new_events
     * @memberOf DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     */
    this.RepeatGallery_new_events = function(res_desc, id ) {
        var contents = res_desc.contents;
        var new_contents = {};

        for(var idx=0;idx<this.EvalInContext(res_desc.repeat);idx++) {
            
            var label = this.EvalInContext(contents[0],idx);
            
            if ($.type(contents[1])!=="array") {
                new_contents[label]=this.FindUrl(this.EvalInContext(contents[1],idx));
            } else {
                // avoid modifying original contents
                var val={};
                val[label]=contents[1];
                $.extend(true,new_contents,val);
                jQuery.each( contents[1], function(index, im) {
                    new_contents[label][index]=this.FindUrl(this.EvalInContext(im,idx));
                }.bind(this));
            }
        }
        
        var ig = new ImageGallery(id);
        if ((res_desc.options)&&(res_desc.options.minheight)) {
            ig.SetMinHeight(res_desc.options.minheight);
        }
        if ((res_desc.options)&&(res_desc.options.minwidth)) {
            ig.SetMinWidth(res_desc.options.minwidth);
        }
        
        ig.Append(new_contents);
        var html = ig.CreateHtml();
        $("#result_"+id).html(html);
        ig.CreateEvents();
        $("#result_"+id).data("image_gallery",ig);
        
    }

}
