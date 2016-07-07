/**
 * @file 
 * this file contains the code that renders and deals with the demo results
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";

// ipol application namespace
var ipol = ipol || {};


/**
 * Display the demo results
 * @constructor
 * @param {object} res          results obtained from running the algorithm
 * @param {object} ddl_results  results section of the demo description
 */
ipol.DrawResults = function( res,ddl_results) {
    
    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function _infoMessage
     * @memberOf ipol.DrawResults~
     * @private
     */
    var _infoMessage = function( ) {
        if (_verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- DrawResults ----");
            console.info.apply(console,args);
        }
    }
    
    /** 
     * Enable/Disable verbose output to the console
     * @var {boolean} _verbose
     * @memberOf ipol.DrawResults~
     * @private
     */
    var _verbose=true;
    
    _infoMessage("DrawResults started");
    _verbose = false;

    /** 
     * Results section of the DDL
     * @var {object} _ddl_results
     * @memberOf ipol.DrawResults~
     * @private
     */
    var _ddl_results  = ddl_results;

    /** 
     * Results obtained from the algorithm execution
     * @var {object} _res
     * @memberOf ipol.DrawResults~
     * @private
     */
    var _res          = res;

    /** 
     * params (algorithm parameters) part of the results
     * @var {object} _params
     * @memberOf ipol.DrawResults~
     * @private
     */
    var _params       = res.params;
    
    /** 
     * default url to the algorithm results
     * @var {string} _work_url
     * @memberOf ipol.DrawResults~
     * @private
     */
    var _work_url     = res.work_url;

    //--------------------------------------------------------------------------
    /**
     * Creates one component of the results
     * @function _createResult
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc DDL description of this result component
     * @param {number} id       id of the result component
     * @returns {string} the HTML code to display this result component
     * @private
     */
    var _createResult = function(res_desc,id) {
        _infoMessage("CreateResult ",id," type ",res_desc.type);
        var display = true;
        var visible_expr = res_desc.visible;
        if (visible_expr!==undefined) {
            display = _evalInContext(visible_expr);
            _infoMessage("evaluating ", visible_expr);
            _infoMessage('display result = ',display);
        }
        if (display) {
            switch(res_desc.type) {
                case "html_text":       return _htmlText      (res_desc);
                case "file_download":   return _fileDownload  (res_desc);
                case "gallery":         return _gallery_new   (res_desc,id);;
                case "repeat_gallery":  return _gallery_new   (res_desc,id);
                case "text_file":       return _textFile      (res_desc,id);
                case "warning":         return _warning       (res_desc);
                default: _infoMessage(" result type "+ res_desc.type + " not available");
            }
        } else {
            return "";
        }
    };
    
    //--------------------------------------------------------------------------
    /**
     * Creates the events associated with a displayed result component
     * @function _createResultEvents
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc DDL description of this result component
     * @param {number} id       id of the result component
     * @private
     */
    var _createResultEvents = function(res_desc,id) {
        var display = true;
        var visible_expr = res_desc.visible;
        if (visible_expr!==undefined) {
            display = _evalInContext(visible_expr);
            _infoMessage("evaluating ", visible_expr);
            _infoMessage('display result = ',display);
        }
        if (display) {
            switch(res_desc.type) {
                case "gallery":
                    _gallery_new_events(res_desc,id);
                    break;
                case "repeat_gallery":
                    _repeatGallery_new_events(res_desc,id);
                    break;
                case "text_file":
                    _textFile_events(res_desc,id);
                    break;
            }
        }
    };
    
    //--------------------------------------------------------------------------
    /**
     * join array of strings to return a single string if needed
     * @function _joinHtml
     * @memberOf ipol.DrawResults~
     * @param {string[]|string} html_code as string or string array
     * @returns {string}
     * @private
     */
    var _joinHtml = function(html_code)
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
     * @function _getLabel
     * @memberOf ipol.DrawResults~
     * @param {string} label with possible condition
     * @returns {string} label without the conditional part
     * @private
     */
    var _getLabel = function(label)
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
     * @function _checkLabelCondition
     * @memberOf ipol.DrawResults~
     * @param {string} label with possible condition
     * @returns {boolean} result from evaluating the condition if any, 
     * true otherwise
     * @private
     */
    var _checkLabelCondition = function(label)
    {
        if(label.indexOf('?') === -1) return true;
        var c = label.split('?')[0];
        var value = _evalInContext(c)
        return value;
    }

    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type html_text
     * @function _htmlText
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     * @private
     */
    var _htmlText = function(res_desc) {
        var contents = _joinHtml(res_desc.contents);
        if (contents[0]==="'") {
            //_infoMessage("HtmlText evaluating ", contents);
            return "<div>"+_evalInContext(contents)+"</div><br/>";
        } else {
            //_infoMessage("contents=",contents);
            return "<div>"+contents+"</div><br/>";
        }
    };
    
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type warning
     * @function _warning
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     * @private
     */
    var _warning = function(res_desc) {
        _infoMessage("display Warning ",res_desc);
        var html=  
        "<p style='border:1px solid;margin:10px 0px;padding:15px 10px 15px 50px;color:#9F6000;'>"+
          "<b><u>WARNING</u></b><br/><br/>"+
          "<span>"+res_desc.contents+"</span> <br/><br/>"+
        "</p>";
        _infoMessage(html);
        return html;
    }
        
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type text_file
     * @function _textFile
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     * @private
     */
    var _textFile = function(res_desc,id) {

        var default_style=  "width:auto;height:auto;background-color:#eee;overflow:auto;max-height:30em;"+
                            "white-space:pre;margin:1em 0;font-weight:normal;";
        var html = '';
        html += res_desc.label;
//        html += '<iframe src="'+_work_url+res_desc.contents+'" ';
        html += '<pre id=result_' + id+ ' ';
        if (res_desc.style[0]==="'") {
            html += 'style="'+default_style + _evalInContext(res_desc.style) + '" >';
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
     * @function _findUrl
     * @memberOf ipol.DrawResults~
     * @param {string} filename filename to look for
     * @returns {string} the filename url to use
     * @private
     */
    // search filename url, if the results are from an experiment, try
    // to use archive url, otherwise use work_url path
    var _findUrl = function(filename) {
        var url=undefined;
        if (this.experiment) {
            url = ipol.ArchiveDisplay.staticFindArchiveUrl(filename,
                                                  this.ddl_archive.files,
                                                  this.experiment.files);
        }
        if (!url) {
            url = _work_url+filename;
        }
        return url;
    }
    
    //--------------------------------------------------------------------------
    /**
     * load text file
     * @function _textFile_events
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     * @private
     */
    var _textFile_events = function(res_desc,id) {
        $('#result_' + id).load(_findUrl(res_desc.contents));
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type file_download
     * @function _fileDownload
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @returns {string} HTML code for this result component
     * @private
     */
    var _fileDownload = function(res_desc) {
        var html = "";
        
        if (res_desc.repeat!=undefined) {
            for(var idx=0;idx<_evalInContext(res_desc.repeat);idx++) {
                var file=_evalInContext(res_desc.contents,idx);
                var label=_evalInContext(res_desc.label,idx);
                html += '&nbsp;[&nbsp;<a href="'+_findUrl(file)+'" target="_blank">';
                html += label;
                html += "</a>&nbsp;]<br/>"
            }
        } else {
            var label = _joinHtml(res_desc.label);
            if (label[0]=="'") {
                label = _evalInContext(label);
            }
            html += label;
            if ($.type(res_desc.contents)==="object") {
              jQuery.each(res_desc.contents, function(label,file) {
                html += '&nbsp;[&nbsp;<a href="'+_findUrl(file)+'" target="_blank">';
                html += label;
                html += "</a>&nbsp;]&nbsp;"
              }.bind(this));
            } else {
                html += '<a href="'+_findUrl(res_desc.contents)+'" target="_blank">';
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
     * @function _evalInContext
     * @memberOf ipol.DrawResults~
     * @param {string} expr expression to evaluate
     * @param {number} idx  index associated to the evaluation, defaults to 0
     * @returns {string|number} result from evaluation
     * @private
     */
    var _evalInContext = function( expr, idx ) {
        if (idx===undefined) {
            idx=0;
        }
        // need sizeX, sizeY
        var sizeX = _params.x1-_params.x0;
        var sizeY = _params.y1-_params.y0;
        // need imwidth and imheight
        var info     = _res.algo_info;
        var meta     = _res.algo_meta;
        var params   = _params;
        var imwidth  = meta.max_width;
        var imheight = meta.max_height;
        var work_url = _work_url;
        return eval(expr);

    }
    
    //--------------------------------------------------------------------------
    /**
     * Returns the HTML code for a result of type gallery or repeat_gallery
     * @function _gallery_new
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     * @returns {string} HTML code for this result component
     * @private
     */
    var _gallery_new = function(res_desc,id) {
        var res="";
        if (res_desc.label!=undefined) {
            var label = _joinHtml(res_desc.label);
            if (label[0]=="'") {
                label = _evalInContext(label);
            }
            res += label;
        }
        
        // TODO: check what variable needs the style and remove its angular code
        res += '<div id=result_' + id + ' style="height:auto">';
        res += '</div><br/>';
        return res;

    } // end _gallery_new
    
    //--------------------------------------------------------------------------
    /**
     * Completes the HTML code and the associated events 
     * for a result of type gallery
     * @function _gallery_new_events
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     * @private
     */
    var _gallery_new_events = function(res_desc,id) {
        var contents = res_desc.contents;
        var new_contents = {};
        jQuery.each( contents, function( label, image ) {
            // check label condition
            var label_condition=_checkLabelCondition(label);
            if (label_condition) {
                // label
                var label = _getLabel(label);
                if (label[0]==="'") {
                    label = _evalInContext(label);
                }
                // string case
                switch ($.type(image)) {
                    case "string":
                        if (image==="'") {
                            image = _evalInContext(image);
                        }
                        new_contents[label]=_findUrl(image);
                        break;
                    case "object":
                        // avoid modifying original contents, using
                        // jquery extend with deep copy
                        var val={};
                        val[label]=image;
                        $.extend(true,new_contents,val);
                        jQuery.each( image, function(l,im) {
                            if (im==="'") {
                                im = _evalInContext(im);
                            }
                            new_contents[label][l]=_findUrl(im);
                        }.bind(this));
                        break;
                    case "array":
                        // avoid modifying original contents
                        var val={};
                        val[label]=image;
                        $.extend(true,new_contents,val);
                        jQuery.each( image, function(index, im) {
                            if (im==="'") {
                                im = _evalInContext(im);
                            }
                            new_contents[label][index]=_findUrl(im);
                        }.bind(this));
                        break;
                } // end switch
            } // if label condition
        }.bind(this));
        
        var ig = new ipol.ImageGallery(id);
        ig.Append(new_contents);
        var html = ig.CreateHtml();
        $("#result_"+id).html(html);
        ig.CreateEvents();
        $("#result_"+id).data("image_gallery",ig);
        
        if (this.onloadall_callback) {
            ig.SetOnLoadAll( this.onloadall_callback.bind(this) );
        }

    } // end _gallery_new_events
    

    //--------------------------------------------------------------------------
    /**
     * Completes the HTML code and the associated events 
     * for a result of type repeat_gallery
     * @function _repeatGallery_new_events
     * @memberOf ipol.DrawResults~
     * @param {object} res_desc description if this result component
     * @param {number} id result component index
     * @private
     */
    var _repeatGallery_new_events = function(res_desc, id ) {
        var contents = res_desc.contents;
        var new_contents = {};

        for(var idx=0;idx<_evalInContext(res_desc.repeat);idx++) {
            
            var label = _evalInContext(contents[0],idx);
            
            if ($.type(contents[1])!=="array") {
                new_contents[label]=_findUrl(_evalInContext(contents[1],idx));
            } else {
                // avoid modifying original contents
                var val={};
                val[label]=contents[1];
                $.extend(true,new_contents,val);
                jQuery.each( contents[1], function(index, im) {
                    new_contents[label][index]=_findUrl(_evalInContext(im,idx));
                }.bind(this));
            }
        }
        
        var ig = new ipol.ImageGallery(id);
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

    
    //--------------------------------------------------------------------------
    //  PUBLIC METHODS
    //--------------------------------------------------------------------------

    //--------------------------------------------------------------------------
    /**
     * Specify the archive experiment from which we are drawing the results
     * @function setExperiment
     * @memberOf ipol.DrawResults~
     * @param {number} exp         experiment number
     * @param {object} ddl_archive archive section of the DDL
     * @public
     */
    this.setExperiment = function(exp,ddl_archive) {
        this.experiment = exp;
        this.ddl_archive = ddl_archive; // archive part of the DDL
    }

    //--------------------------------------------------------------------------
    /**
     * Creates all the HTML code for the displaying the results
     * @function create
     * @memberOf ipol.DrawResults~
     * @public
     */
    this.create = function() {

        var results_html = "";
        var displayed_status = { "OK":"success", "KO":"failure" };
        
        // display result status
        if (_res.status==="KO") {
            results_html += '  <p class="error"> '+res.error+' </p>';
        }
        
        if (_res.algo_meta["process_inputs_msg"]!=undefined) {
            results_html +=
                "<p style='border:1px solid;margin:3px 0px;padding:5px;color:#9F6000;'>"+
                "<b>"+_res.algo_meta["process_inputs_msg"]+"</b>"+
                "</p>";
        }
//         results_html += this.CreateZoomSelection();

        for(var id=0;id<_ddl_results.length;id++) {
            results_html+=_createResult(_ddl_results[id],id);
        }
        
        $("#ResultsDisplay").html(results_html);

        for(var id=0;id<_ddl_results.length;id++) {
            _createResultEvents(_ddl_results[id],id);
        }

    };
    
};
