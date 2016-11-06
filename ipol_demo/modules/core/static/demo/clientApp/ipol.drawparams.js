/**
 * @file 
 * this file contains the code that renders and deals with the demo parameters
 * associated with demo.html and ipol_demo.js
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";

// ipol application namespace
var ipol = ipol || {};

/**
 * Display and manage demo parameters
 * @namespace
 */
ipol.params = ipol.params || {};

//------------------------------------------------------------------------------
/**
 * IPOL interface for the demo parameters
 * @constructor
 */

ipol.DrawParams = function() {
    
    /** 
     * By convention, we create a private variable '_this' to
     * make the object available to the private methods.
     * @var {object} _this
     * @memberOf ipol.DrawParams~
     * @private
     */
    var _this = this;

    //--------------------------------------------------------------------------
    // PRIVATE METHODS
    //--------------------------------------------------------------------------
    
    //--------------------------------------------------------------------------
    /** 
    * Creates html code from param.label
    * @param {object} param the current parameter object, containing a label 
    * property
    * @returns {string} HTML code
    * @function _addLabel
    * @memberOf ipol.DrawParams~
    */
    var _addLabel = function (param) {
        var html = "";
        html += '<td style="border:0px;max-width:25em">';
        html += '<label>'+ipol.utils.joinHtml(param.label)+'</label>';
        html += '</td>';
        return html;
    }
    
    //--------------------------------------------------------------------------
    /** 
    * Creates html code from param.comments
    * @param {object} param the current parameter object, containing a comments 
    * property
    * @returns {string} HTML code
    * @function _addComments
    * @memberOf ipol.DrawParams~
    */
    var _addComments = function (param) {
        var html = "";
        if (param.comments!=undefined) {
            html += '<td   style="border:0px;max-width:25em">';
            html += '<label>'+ipol.utils.joinHtml(param.comments)+'</label>';
            html += '</td>';
        }
        return html;
    }

    //--------------------------------------------------------------------------
    /** 
    * Creates selection collapsed interface
    * @param {object} param the current parameter object, containing the 
    * properties label, comments, id, values, default_value
    * @returns {string} HTML code
    * @function _createSelectionCollapsed
    * @memberOf ipol.DrawParams~
    */
    var _createSelectionCollapsed = function (param) {
        var html = "";
        html += _addLabel(param);
        html += '<td style="border:0px;" colspan="2">';
        html += '<select name="'+param.id+'" id="param_'+param.id+'" >';
        jQuery.each( param.values, function( key, value ) {
            html += '<option value="'+value+'"';
            if (value===param.default_value) {
                html += ' selected="selected"';
            }
            html += '>';
            html += key;
            html += '</option>';
        });
        html += '</select>';
        html += '</td>';
        html += _addComments(param);
        return html;
    }
        
    //--------------------------------------------------------------------------
    /** 
    * Creates events related to a selection collapsed widget (onchange event)
    * @param {object} param the current parameter object, containing the 
    * properties label, comments, id, values, default_value
    * @param {object} ddl_json the DDL description of the demo
    * @function _createSelectionCollapsedEvents
    * @memberOf ipol.DrawParams~
    */
    var _createSelectionCollapsedEvents = function (param, ddl_json) {
        $('#param_'+param.id).on('change', function(){
            ipol.DrawParams.staticUpdateParams(ddl_json.params);
        });
    }

    //--------------------------------------------------------------------------
    /** 
    * Creates selection radio interface
    * @param {object} param the current parameter object, can contain the 
    * properties label, comments, id, values, vertical, default_value
    * @returns {string} HTML code
    * @function _createSelectionRadio
    * @memberOf ipol.DrawParams~
    */
    var _createSelectionRadio = function (param) {
        var html = "";
        html += _addLabel(param);
        html += '<td style="border:0px;" colspan="2">';
        jQuery.each( param.values, function( key, value ) {

            html += '<label>';
            html += '<input type="radio"';
            html += ' name="'+param.id+'"';
            html += ' value="'+value+'"';
    //        html += ' id="param_'+param.id+'"';
            if (value===param.default_value) {
                html += ' checked';
            }
            html += '>';
            html += '<span>'+key+'</span>';
            html += '</label> &nbsp';
            if (param.vertical!==undefined &&  param.vertical) {
                html += '<br>';
            }
        });
        html += '</td>';
        html += _addComments(param);
        return html;
    }

    //--------------------------------------------------------------------------
    /**
     * Creates selection radio events interface
     * @param {object} param the current parameter object, can contain the 
     * properties label, comments, id, values, vertical, default_value
     * @param {object} ddl_json demo description (DDL) object 
     * @function _createSelectionRadioEvents
     * @memberOf ipol.DrawParams~
     */
    var _createSelectionRadioEvents = function (param, ddl_json) {
        $('input[name='+param.id+']').on('change', function(){
            ipol.DrawParams.staticUpdateParams(ddl_json.params);
        });
    }

    //------------------------------------------------------------------------------
    /** 
     * Creates selection range interface (slider)
     * @param {object} param the current parameter object, can contain the properties
     * label, values.{min,max,step,default}, id
     * @returns {string} HTML code
     * @function _createSelectionRange
     * @memberOf ipol.DrawParams~
     */
    var _createSelectionRange = function (param) {
        var html = "";
        html += _addLabel(param);

        var limits= '';
        limits += ' min  ="' + param.values.min     + '"'; 
        limits += ' max  ="' + param.values.max     + '"';
        limits += ' step ="' + param.values.step    + '"';
        limits += ' value="' + param.values.default + '"';

        var number_id = 'number_'+param.id;
        var range_id  = 'range_' +param.id;
        
        html += '<td style="border:0px;width:5em">';
        html += '<input  style="width:100%"  type="number"';
        html += ' id="'+number_id+'"';
        html += ' name="'+param.id+'" '+limits + ' >';
        html += '</td>';
        html += '<td style="border:0px;width:20em">';
        
        html += '<div  style="width:100%"';
        html += ' id="'+range_id+'"';
        html += ' div>';
        
        html += '</td>';
        html += _addComments(param);

        return html;
    }

    //--------------------------------------------------------------------------
    /** 
     * function used by the range_scientific parameter type
     * computes the the number value from the slider position
     * @param {number} sci
     * @param {number} numDigits
     * @returns {number}
     * @function _sci2Str
     * @memberOf ipol.DrawParams~
     */
    var _sci2Str = function (sci, numDigits)
    {
        var exponent = Math.floor(sci / (9*Math.pow(10, numDigits)));
        var mantissa = sci/Math.pow(10, numDigits) - (9*exponent - 1);
        var value = Math.pow(10, exponent) * mantissa;
        //console.info("_sci2Str ", exponent, mantissa, value, 
        // value.toExponential(numDigits))
        return value.toExponential(numDigits);
    }

    //--------------------------------------------------------------------------
    /** 
    * Creates selection range interface (slider) with scientific notations
    * @param {object} param the current parameter object, can contain the 
    * properties label, values.{min,max,digits,default}, id
    * @returns {string} HTML code
     * @function _createSelectionRangeScientific
     * @memberOf ipol.DrawParams~
    */
    var _createSelectionRangeScientific = function (param) {
        var html = "";
        html += _addLabel(param);

        var limits= '';
        //console.info("num2sci ", param.values.min, param.values.digits, 
        // num2sci(param.values.min,param.values.digits))
        limits += ' min  ="' + ipol.DrawParams.staticNum2Sci(
            param.values.min,param.values.digits) + '"'; 
        limits += ' max  ="' + ipol.DrawParams.staticNum2Sci(
            param.values.max,param.values.digits) + '"';
        limits += ' step =1"';
        // TODO: need to improve this part to allow input parameters from
        // previous run?
        param.value = param.values.default;
        param.value_slider = ipol.DrawParams.staticNum2Sci(
            param.value,param.values.digits);
        limits += ' value="' + param.value_slider + '"';

        var number_id = 'number_'+param.id;
        var range_id  = 'range_' +param.id;
        
        html += '<td style="border:0px;width:5em">' 
            +  '<input  style="width:100%"  type="number"'
            + ' value="'+_sci2Str(param.value_slider,param.values.digits)+'"'
            + ' id="'+number_id+'"'
            + ' name="'+param.id+'" '+limits + ' readonly >'
            + '</td>';
        
        html += '<td style="border:0px;width:20em">'
            +  '<div  style="width:100%"'
            +  ' id="'+range_id+'"'
            +  ' div>'
    //          + '<input  style="width:100%"  type="range"'
    //          + ' id="'+range_id+'"'
    //          + ' name="'+param.id+'" '+limits + ' >'
            + '</td>';
        html += _addComments(param);

        return html;
    }

    //--------------------------------------------------------------------------
    /** 
     * Creates selection range events
     * @param {object} param 
     * @param {object} ddl_json 
     * @function _createSelectionRangeEvents
     * @memberOf ipol.DrawParams~
     */
    var _createSelectionRangeEvents = function (param, ddl_json) {

        var number_id = 'number_'+param.id;
        var range_id  = 'range_' +param.id;
        
        var slider_options = {
            start: param.values.default,
            connect: "lower",
    //         orientation: "vertical",
            range: {
            'min': param.values.min,
            'max': param.values.max
            },
            step:param.values.step
        };
        
        function hasdecimals(val,n) {
            var v = val*Math.pow(10,n);
            return v===parseInt(v);
        }
        
        // try to set the right decimal values
        var num_decimals = 0;
        var ok = false;
        while ((!ok)&&(num_decimals<15)) {
            ok = (hasdecimals(param.values.min, num_decimals)&&
                  hasdecimals(param.values.max, num_decimals)&&
                  hasdecimals(param.values.step,num_decimals));
            
            if (!ok) {
                num_decimals++;
            }
        }

        try {
            slider_options['format']= wNumb({ decimals: num_decimals });
        } catch(err) {
        }


        
        
        noUiSlider.create($('#'+range_id)[0], slider_options);
        
        
        $('#'+range_id).css("background","antiquewhite");
        
        $('#'+range_id)[0].noUiSlider.on('slide', 
            function(  ) {
                $('#'+number_id).val($('#'+range_id)[0].noUiSlider.get());
                ipol.DrawParams.staticUpdateParams(ddl_json.params);
            }
        );
        $('#'+range_id)[0].noUiSlider.on('update', 
            function(  ) {
                $('#'+number_id).val($('#'+range_id)[0].noUiSlider.get());
                ipol.DrawParams.staticUpdateParams(ddl_json.params);
            }
        );

        //     $('#'+range_id).slider(
        //     {
        //         value:param.values.default,
        //         min: param.values.min,
        //         max: param.values.max,
        //         step: param.values.step,
        //         slide: function( event, ui ) {
        //             $('#'+number_id).val($('#'+range_id).slider('value'));
        //             ipol.DrawParams.staticUpdateParams(ddl_json.params);
        //         },
        //         change: function( event, ui ) {
        //             $('#'+number_id).val($('#'+range_id).slider('value'));
        //             ipol.DrawParams.staticUpdateParams(ddl_json.params);
        //         }
        //     });

        $('#'+number_id).on('input', function(){
            $('#'+range_id)[0].noUiSlider.set($('#'+number_id).val());
            ipol.DrawParams.staticUpdateParams(ddl_json.params);
        });
        
    }

    
    //--------------------------------------------------------------------------
    /** 
     * Creates selection scientific notation range events
     * @param {object} param 
     * @param {object} ddl_json 
     * @function _createSelectionRangeEvents
     * @memberOf ipol.DrawParams~
     */
    var _createSelectionRangeScientificEvents = function (param,ddl_json) {
        //console.info("CreateSelectionRangeScientificEvents");
        var number_id = 'number_'+param.id;
        var range_id  = 'range_' +param.id;
        
        $('#'+range_id).slider(
        {
            value:ipol.DrawParams.staticNum2Sci(param.values.default, 
                                                param.values.digits),
            min:  ipol.DrawParams.staticNum2Sci(param.values.min,     
                                                param.values.digits),
            max:  ipol.DrawParams.staticNum2Sci(param.values.max,     
                                                param.values.digits),
            step: 1,
            slide: function( event, ui ) {
                var value_slider = $('#'+range_id).slider('value');
                $('#'+number_id).val(
                        _sci2Str(value_slider,param.values.digits)
                    );
                ipol.DrawParams.staticUpdateParams(ddl_json.params);
            },
            change: function( event, ui ) {
                var value_slider = $('#'+range_id).slider('value');
                $('#'+number_id).val(
                        _sci2Str(value_slider,param.values.digits)
                    );
                ipol.DrawParams.staticUpdateParams(ddl_json.params);
            }
        });

        //     $('#'+range_id).on('input', function(){
        //         var value_slider = $('#'+range_id).val();
        //         $('#'+number_id).val(
        //                 _sci2Str(value_slider,param.values.digits)
        //             );
        //         ipol.DrawParams.staticUpdateParams(ddl_json.params);
        //     }.bind(this));
    }

    //--------------------------------------------------------------------------
    /** 
     * Creates readonly text element
     * @param {object} param the current parameter object
     * @returns {string} HTML code
     * @function _createReadOnly
     * @memberOf ipol.DrawParams~
     */
    var _createReadOnly = function (param) {

        var html = "";
        html = 
            "<td style='border:0;max-width:25em'>" +
            '<label> ' + param.label + ' </label>'+
            '</td>'+
            '<td style="border:0px;"  colspan="2"  >'+
            '<input  style="20em"'+
                    ' type="text" ' + 
                    ' name="' + param.id + '" ' + 
                        +
                        '" ' +
                    'readonly/>' +
            '</td>'
        return html;
    }    

    //--------------------------------------------------------------------------
    /** 
     * Creates a label element
     * @param {object} param the current parameter object
     * @returns {string} HTML code
     * @function _createLabel
     * @memberOf ipol.DrawParams~
     */
    var _createLabel = function (param) {

    return  "<th style='border:0' colspan=3>"+ 
                "<div>" + param.label + "</div>" +
            "</th>";
    }

    //--------------------------------------------------------------------------
    /** 
     * Creates a checkbox element
     * @param {object} param the current parameter object 
     * (id,default_value,label,comments)
     * @returns {string} HTML code
     * @function _createCheckBox
     * @memberOf ipol.DrawParams~
     */
    var _createCheckBox = function (param) {

        var html = "";
        html += _addLabel(param);
        html +=
            '<td style="border:0px;"  colspan="2" align="left"> ' +
            '<input  type="checkbox"' +
                'name="'+param.id+'"' + ' id="param_'+param.id+'"';            
            //       '<input  type="text" '+
            //           'name="'+param.id+'_checked" ' +
            //           'value="{{demo.params[pos].value==true}}" hidden />' +
        if (param.default_value) {
            html += ' checked';
        }
        html += ' > </td>';
        html += _addComments(param);
        return html;
        
    }    

    //--------------------------------------------------------------------------
    /** 
     * Creates a checkbox element
     * @param {object} param the current parameter object 
     * (id,default_value,label,comments)
     * @param {object} ddl_json the DDL description of the demo
     * @function _createCheckBoxEvents
     * @memberOf ipol.DrawParams~
     */
    var _createCheckBoxEvents = function (param,ddl_json) {
        $('#param_'+param.id).on('change', function(){
            ipol.DrawParams.staticUpdateParams(ddl_json.params);
        });
    }

    //--------------------------------------------------------------------------
    /** 
     * Creates several checkbox elements
     * @param {object} param the current parameter object 
     * param.{id,values,default,comments}
     * @returns {string} HTML code
     * @function _createCheckBoxes
     * @memberOf ipol.DrawParams~
     */
    var _createCheckBoxes = function (param) {

        var html = "";
        html += _addLabel(param);
        html += '<td style="border:0"  colspan="2" align="left"> ';
        
        for (var n=0;n< param.values.length; n++) {
            var group = param.values[n];
            html += "<div>";
            for (var id in group) {
                html += '<input  type="checkbox" ' +
                        'name="'+param.id+'_'+id+'" id="'+id+'"';
                if ($.inArray(id,param.default)>-1) {
                    html += ' checked ';
                }
                html += ' />';
                html += '<label for="'+id+'">'+ group[id] +'</label> &nbsp;&nbsp;';
            }
            html += "<br/></div>";
        }
            
        html += '</td>';
        html += _addComments(param);
        return html;
        
    }    
    
    //--------------------------------------------------------------------------
    // PUBLIC METHODS
    //--------------------------------------------------------------------------
    
    //------------------------------------------------------------------------------
    /** 
     * Creates all the parameters HTML code and events
     * @param {object} ddl_json demo DDL object
     * @returns {string} HTML code
     * @function createParams
     * @memberOf ipol.DrawParams~
     * @public
     */
    this.createParams = function (ddl_json) {
        
        $("#ParamDescription").html(
            ipol.utils.joinHtml(ddl_json.general.param_description));
        
        var params_html = "";
        if ((ddl_json.params)&&(ddl_json.params.length>0)) {
            var one_group = ddl_json.params_layout.length===1;
            // for each param group
            for(var pg=0;pg<ddl_json.params_layout.length;pg++) {
                var param_group = ddl_json.params_layout[pg];
                if (!one_group) {
                    params_html += '<fieldset style="display:inline-block;'+
                                        'margin:3px;' +
                                        'border:1px solid darkgrey;'+
                                        '-moz-border-radius:4px;'+
                                        '-webkit-border-radius:4px;'+
                                        'border-radius:4px;">';
                    params_html += '<legend class="param_legend">'+param_group[0]+
        //                 ' <span>[-]</span> </legend>';
                        ' </legend>';
                }
                
                params_html += '<table  style="float:left;border:1px;">';
                for(var n=0;n<param_group[1].length;n++) {
                    var pos=param_group[1][n]; 
                    var param = ddl_json.params[pos];
                    params_html += '<tr style="border:0px;" id="tr_param_'+pos+'" >';
                    switch(param.type) {
                        case "selection_collapsed":
                            params_html += _createSelectionCollapsed(param);
                            break;
                        case "selection_radio":
                            params_html += _createSelectionRadio(param);
                            break;
                        case "range":
                            params_html += _createSelectionRange(param);
                            break;
                        case "range_scientific":
                            params_html += _createSelectionRangeScientific(param);
                            break;
                        case "readonly":
                            params_html += _createReadOnly(param);
                            break;
                        case "label":
                            params_html += _createLabel(param);
                            break;
                        case "checkbox":
                            params_html += _createCheckBox(param);
                            break;
                        case "checkboxes":
                            params_html += _createCheckBoxes(param);
                            break;
                    }
                    params_html += '</tr>';
                }
                params_html += '</table>';
                if (!one_group) {
                    params_html += '</fieldset>';
                }
            }
        }
        
        $("#DisplayParams").html(params_html);
        $("#DisplayParams").data("ddl_params",ddl_json.params);

        if ((ddl_json.params)&&(ddl_json.params.length>0)) {
            // add events
            for(var pg=0;pg<ddl_json.params_layout.length;pg++) {
                var param_group = ddl_json.params_layout[pg];
                for(var n=0;n<param_group[1].length;n++) {
                    var pos=param_group[1][n]; 
                    var param = ddl_json.params[pos];
                    switch(param.type) {
                        case "selection_collapsed":
                            _createSelectionCollapsedEvents(param,ddl_json);
                            break;
                        case "selection_radio":
                            _createSelectionRadioEvents(param,ddl_json);
                            break;
                        case "range":
                            _createSelectionRangeEvents(param,ddl_json);
                            break;
                        case "range_scientific":
                            _createSelectionRangeScientificEvents(param,ddl_json);
                            break;
                        case "readonly":
                            break;
                        case "label":
                            break;
                        case "checkbox":
                            _createCheckBoxEvents(param,ddl_json);
                            break;
                        case "checkboxes":
                            break;
                    } // end switch
                } // end for param_group
            } // end for params_layout
        }

        ipol.DrawParams.staticUpdateParams(ddl_json.params);
        
    }



}


//------------------------------------------------------------------------------
// STATIC METHODS
//------------------------------------------------------------------------------
    
//------------------------------------------------------------------------------
/** 
 * Updates parameters, if they depend on other param values (in the case
 * of readonly for example).
 * @param {object} ddl_params the parameter section of the DDL object
 * @function staticUpdateParams
 * @memberOf ipol.DrawParams
 * @static
 */
ipol.DrawParams.staticUpdateParams = function (ddl_params) {

    // image dimensions, can be used in parameter expressions
    var imwidth  = 512;
    var imheight = 512;
    
    //----------------------------------------------------------------------
    function checkImageDimensions() {
//         console.info("checkImageDimensions() ");
        if ($("#inputimage").get(0)) {
            imwidth  = $("#inputimage").get(0).naturalWidth;
            imheight = $("#inputimage").get(0).naturalHeight;
            if ($("#id_cropinput")&&($("#id_cropinput").is(':checked'))) {
                var CropBox = $("#inputimage").cropper('getCropBoxData');
                imwidth  = CropBox.width;
                imheight = CropBox.height;
            }
        }
//         console.info(imwidth+"x"+imheight);
    }
    
    
    checkImageDimensions();
    
    //----------------------------------------------------------------------
    function updateReadOnly(param) {
        try {
            $("input[name='"+param.id+"']").val(
                eval(param.value_expr.join('')));
        } catch(err) {
            //console.info("updateReadOnly ", 
            //param.value_expr.join(''), ':', param, " error:",err.message);
        }
    }

    // get parameter values for eval()
    var params = ipol.DrawParams.staticGetParamValues(ddl_params);
    
    // add events
    if ((ddl_params)&&(ddl_params.length>0)) {
        for(var n=0;n<ddl_params.length;n++) {
            var param = ddl_params[n];
            
            if (param.visible===undefined||eval(param.visible)) {
                $("#tr_param_"+n).show();
                switch(param.type) {
                    case "selection_collapsed":
                        break;
                    case "selection_radio":
                        break;
                    case "range":
                        break;
                    case "range_scientific":
                        break;
                    case "readonly":
                        updateReadOnly(param);
                        break;
                    case "label":
                        break;
                    case "checkbox":
                        break;
                    case "checkboxes":
                        break;
                } // end switch
            } else { //param.visible
                $("#tr_param_"+n).hide();
            }
        } // end for
    } // end if
} // end ipol.DrawParams.staticUpdateParams()

//--------------------------------------------------------------------------
/** 
 * Get the value of a parameter
 * @param {object} ddl_params the parameter section of the DDL object
 * @param {index}  index of the parameter to get
 * @returns {number|string|array} parameter value
 * @function staticGetParamValue
 * @memberOf ipol.DrawParams
 * @static
 */
ipol.DrawParams.staticGetParamValue = function (params_ddl,index) {

    var param = params_ddl[index];
    var name  = param.id;
    
    switch(param.type) {
        case "selection_collapsed":
            var value = $("select[name="+name+"]").val();
            return value;
        case "selection_radio":
            var value = $("input[name="+name+"]:checked").val();
            return value;
            break;
        case "range":
            var value = $("input[name="+name+"]").val();
            return parseFloat(value);
        case "range_scientific":
            var value = $("input[name="+name+"]").val();
            return parseFloat(value);
        case "readonly":
            var value = $("input[name="+name+"]").val();
            return value;
        case "label":
            break;
        case "checkbox":
            var value = $("input[name="+name+"]").is(':checked');
            return value;
        case "checkboxes":
            var values = [];
            for (var n=0;n< param.values.length; n++) {
                var group = param.values[n];
                for (var id in group) {
                    if ($("input[name="+param.id+'_'+id+"]").is(':checked')) {
                        values.push(id);
                    }
                }
            }
            //console.info("values",values);
            return values;
    }
    return undefined;
}

//--------------------------------------------------------------------------
/** 
 * Get all the parameter values
 * @param {object} ddl_params the parameter section of the DDL object
 * @returns {object} pairs param.id:value
 * @function staticGetParamValues
 * @memberOf ipol.DrawParams
 * @static
 */
ipol.DrawParams.staticGetParamValues = function (params_ddl) {
    // create parameters
    var params={};
    if (params_ddl) {
        for(var p=0;p<params_ddl.length;p++) {
            var name = params_ddl[p].id;
            var value = ipol.DrawParams.staticGetParamValue(params_ddl,p);
            if (params_ddl[p].type==="checkbox") {
                // set both ...
                params[name+"_checked"] = value;
                params[name] = value;
            } else {
                if (params_ddl[p].type==="checkboxes") {
                    $.each( value, 
                                function(index,param) {
                                    params[name+'_'+param]=true;
                                }
                            );
                } else {
                    params[name] = value;
                }
            }
            //console.info("param ",p," ",name, ":", value);
        }
    }
    return params;
}

    
    
//--------------------------------------------------------------------------
/** 
 * function used by the range_scientific parameter type
 * computes the slider position of a given value
 * @param {number} value
 * @param {number} numDigits
 * @returns {number}
 * @function staticNum2Sci
 * @memberOf ipol.DrawParams~
 * @static
 */
ipol.DrawParams.staticNum2Sci = function (value, numDigits)
{
    var exponent = Math.floor(Math.log(value) / Math.log(10));
    //console.info("exponent = ", exponent);
    var mantissa = value / Math.pow(10, exponent - numDigits);
    //console.info("mantissa = ", mantissa);
    return Math.round(mantissa + (9*exponent - 1)*Math.pow(10, numDigits));
}

    
//--------------------------------------------------------------------------
/** 
 * Reset parameters to default values
 * @function staticResetParamValues
 * @memberOf ipol.DrawParams
 * @static
 */
ipol.DrawParams.staticResetParamValues = function () {
    
    var ddl_params = $("#DisplayParams").data("ddl_params");
    if (ddl_params===undefined) {
        return;
    }

    // create parameters
    if (ddl_params) {
        for(var p=0;p<ddl_params.length;p++) {
            var param = ddl_params[p];
            var name = param.id;
            
            switch(param.type) {
                case "selection_collapsed":
                    $("select[name="+name+"]").val(param.default_value);
                    $("select[name="+name+"]").trigger("input");
                    break;
                case "selection_radio":
                    $("input[name="+name+"]").filter('[value="'+param.default_value+'"]').click();
                    break;
                case "range":
                    $("input[name="+name+"]").val(param.values.default);
                    $("input[name="+name+"]").trigger("input");
                    break;
                case "range_scientific":
                    param.value = param.values.default;
                    param.value_slider = 
                        ipol.DrawParams.staticNum2Sci(param.value,
                                                        param.values.digits);
                    var range_id  = 'range_' +param.id;
                    $('#'+range_id).slider('value',param.value_slider);
                    $('#'+range_id).trigger("input");
                    break;
                case "checkbox":
                    $("input[name="+name+"]").prop('checked',param.default_value);
                    break;
                case "checkboxes":
                    for (var n=0;n< param.values.length; n++) {
                        var group = param.values[n];
                        for (var id in group) {
                            $("input[name="+param.id+'_'+id+"]").prop(
                                'checked',
                                ($.inArray(id,param.default)>-1));
                        }
                    }
                    break;
            } // end switch
        }
    }
}
    
//------------------------------------------------------------------------------
/** 
 * Set parameters to given values
 * @param {object} param_values object containing the parameters ids and their
 * associated values to set
 * @function staticSetParamValues
 * @memberOf ipol.DrawParams
 * @static
 */
ipol.DrawParams.staticSetParamValues = function (param_values) {
    
    var ddl_params = $("#DisplayParams").data("ddl_params");
    if (ddl_params===undefined) {
        return;
    }

    if (ddl_params) {
        for(var p=0;p<ddl_params.length;p++) {
            var param = ddl_params[p];
            var name = param.id;
            
            var pval=param_values[name];
            if ((pval!==undefined)||(param.type=="checkboxes")) {
            
                switch(param.type) {
                    case "selection_collapsed":
                        $("select[name="+name+"]").val(pval);
                        $("select[name="+name+"]").trigger("input");
                        break;
                    case "selection_radio":
                        $("input[name="+name+"]").filter('[value="'+pval+'"]').click();
                        break;
                    case "range":
                        $("input[name="+name+"]").val(pval);
                        $("input[name="+name+"]").trigger("input");
                        break;
                    case "range_scientific":
                        param.value = pval;
                        param.value_slider = ipol.DrawParams.staticNum2Sci(
                            param.value,param.values.digits);
                        var range_id  = 'range_' +param.id;
                        $('#'+range_id).slider('value',param.value_slider);
                        $('#'+range_id).trigger("input");
                        break;
                    case "checkbox":
                        $("input[name="+name+"]").prop('checked',pval);
                        break;
                    case "checkboxes":
                        for (var n=0;n< param.values.length; n++) {
                            var group = param.values[n];
                            for (var id in group) {
                                //console.info("checking ",param.id+'_'+id+" :",
                                //    $.inArray(param.id+'_'+id,Object.keys(param_values))
                                //);
                                $("input[name="+param.id+'_'+id+"]").prop(
                                    'checked',
                                    ($.inArray(param.id+'_'+id,Object.keys(param_values))>-1)&&
                                    (param_values[param.id+'_'+id])
                                );
                            }
                        }
                        break;
                } // end switch
            }
        }
    }
}


