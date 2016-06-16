//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_params.js
// date: march 2016
// author: Karl Krissian
//
// description:
// this file contains the code that renders and deals with the demo parameters
// associated with ipol_demo.html and ipol_demo.js
//

"use strict";

//------------------------------------------------------------------------------
// initialization of the parameters obtained from the DDL json file
// this function is not used for the moment
// compared to cherrypy version, we may not need to store the previous running
// parameters if we stay in the same loaded webpage: it will simplify the workflow
function initParams(  demo, params) {
    console.info("initParams");
    
//     // add pensize parameter for inpainting
//     if (params['pensize']==undefined) {
//         demo.params.pensize = 5;
//     } else {
//         demo.params.pensize = params['pensize'];
//     }
// 
//     // initialize input loading status
//     angular.forEach(demo.inputs, 
//         function(res) {
//         res.status = "trying";
//         }
//     );
// 
//     // initialize parameter values
//     angular.forEach(demo.params, 
//         function(param) {
//         console.info(param.type);
//         // range type
//         if (param.type=='range') {
//             if (params[param.id]==undefined) {
//             param.value = param.values.default;
//             } else {
//             param.value = params[param.id];
//             }
//         }
//         // range_scientic type
//         if (param.type=='range_scientific') {
//             if (params[param.id]==undefined) {
//             param.value = param.values.default;
//             } else {
//             param.value = params[param.id];
//             }
//             // initialize the slider position
//             param.value_slider = num2sci(param.value,param.values.digits);
//         }
//         // selection_collapsed type
//         if (param.type=='selection_collapsed') {
//             if (params[param.id]==undefined) {
//             param.value = param.default_value;
//             } else {
//             param.value = params[param.id].toString();
//             }
//         }
//         // selection_radio type
//         if (param.type=='selection_radio') {
//             if (params[param.id]==undefined) {
//             param.value = param.default_value;
//             } else {
//             param.value = params[param.id].toString();
//             }
//         }
//         // checkbox type
//         if (param.type=='checkbox') {
//             // if the variable xxx_checked (hidden input) is
//             // not defined: use default value, otherwise, use
//             // its value (we need this variable because checkboxes
//             // are only returned if they are checked in html)
//             if (params[param.id+"_checked"]==undefined) {
//             param.value = param.default_value;
//             } else {
//             param.value = params[param.id+"_checked"];
//             }
//         }
//         // checkboxes type
//         if (param.type=='checkboxes') {
//             // create one boolean value per checkbox ...
//             param.cb_values = {};
//             angular.forEach(param.values, 
//             function(checkboxes_info) {
//                 angular.forEach(checkboxes_info, 
//                 function(value,key)
//                 {
//                     // if the variable xxx_checked (hidden input) is
//                     // not defined: use default value, otherwise, use
//                     // its value (we need this variable because checkboxes
//                     // are only returned if they are checked in html)
//                     if (params[param.id+"_"+key+"_checked"]==undefined) {
//                     param.cb_values[key]=(param.default.indexOf(key)>-1);
//                     } else {
//                     param.cb_values[key]=params[param.id+"_"+key+"_checked"];
//                     }
//                 }
//                 );
//             }
//             );
//         }
//         if (param.type=='readonly') {
//             param.value='';
//         }
//         //console.info(param.cb_values);
//         }
//     );
};

    

//------------------------------------------------------------------------------
function AddLabel(param) {
    var html = "";
    html += '<td style="border:0px;max-width:25em">';
    html += '<label>'+joinHtml(param.label)+'</label>';
    html += '</td>';
    return html;
}
    
//------------------------------------------------------------------------------
function AddComments(param) {
    var html = "";
    if (param.comments!=undefined) {
        html += '<td   style="border:0px;max-width:25em">';
        html += '<label>'+joinHtml(param.comments)+'</label>';
        html += '</td>';
    }
    return html;
}

//------------------------------------------------------------------------------
function CreateSelectionCollapsed(param) {
    var html = "";
    html += AddLabel(param);
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
    html += AddComments(param);
    return html;
}
    
//------------------------------------------------------------------------------
function CreateSelectionCollapsedEvents(param, ddl_json) {
    $('#param_'+param.id).on('change', function(){
        UpdateParams(ddl_json.params);
    }.bind(this));
}

//------------------------------------------------------------------------------
function CreateSelectionRadio(param) {
    var html = "";
    html += AddLabel(param);
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
    html += AddComments(param);
    return html;
}

//------------------------------------------------------------------------------
function CreateSelectionRadioEvents(param, ddl_json) {
    $('input[name='+param.id+']').on('change', function(){
        UpdateParams(ddl_json.params);
    }.bind(this));
}

//------------------------------------------------------------------------------
function CreateSelectionRange(param) {
    var html = "";
    html += AddLabel(param);

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
    html += AddComments(param);

    return html;
}

//------------------------------------------------------------------------------
// function used by the range_scientific parameter type
// computes the slider position of a given value
function num2sci(value, numDigits)
{
    var exponent = Math.floor(Math.log(value) / Math.log(10));
    //console.info("exponent = ", exponent);
    var mantissa = value / Math.pow(10, exponent - numDigits);
    //console.info("mantissa = ", mantissa);
    return Math.round(mantissa + (9*exponent - 1)*Math.pow(10, numDigits));
}

//------------------------------------------------------------------------------
// function used by the range_scientific parameter type
// computes the number value from the slider position
function sci2str(sci, numDigits)
{
    var exponent = Math.floor(sci / (9*Math.pow(10, numDigits)));
    var mantissa = sci/Math.pow(10, numDigits) - (9*exponent - 1);
    var value = Math.pow(10, exponent) * mantissa;
    //console.info("sci2str ", exponent, mantissa, value, value.toExponential(numDigits))
    return value.toExponential(numDigits);
}

//------------------------------------------------------------------------------
function CreateSelectionRangeScientific(param) {
    var html = "";
    html += AddLabel(param);

    var limits= '';
    //console.info("num2sci ", param.values.min, param.values.digits, num2sci(param.values.min,param.values.digits))
    limits += ' min  ="' + num2sci(param.values.min,param.values.digits) + '"'; 
    limits += ' max  ="' + num2sci(param.values.max,param.values.digits) + '"';
    limits += ' step =1"';
    // TODO: need to improve this part to allow input parameters from
    // previous run?
    param.value = param.values.default;
    param.value_slider = num2sci(param.value,param.values.digits);
    limits += ' value="' + param.value_slider + '"';

    var number_id = 'number_'+param.id;
    var range_id  = 'range_' +param.id;
    
    html += '<td style="border:0px;width:5em">' 
         +  '<input  style="width:100%"  type="number"'
         + ' value="'+sci2str(param.value_slider,param.values.digits)+'"'
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
    html += AddComments(param);

    return html;
}

//------------------------------------------------------------------------------
function CreateSelectionRangeEvents(param, ddl_json) {

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
    if (hasdecimals(param.values.min,0)&&
        hasdecimals(param.values.max,0)&&
        hasdecimals(param.values.step,0)) {
        slider_options['format']= wNumb({ decimals: 0 });
    } else {
        if (hasdecimals(param.values.min,1)&&
            hasdecimals(param.values.max,1)&&
            hasdecimals(param.values.step,1)) {
            slider_options['format']= wNumb({ decimals: 1 });
        }
    }
    
    noUiSlider.create($('#'+range_id)[0], slider_options);
    
    
    $('#'+range_id).css("background","antiquewhite");
    
    $('#'+range_id)[0].noUiSlider.on('slide', 
        function(  ) {
            $('#'+number_id).val($('#'+range_id)[0].noUiSlider.get());
            UpdateParams(ddl_json.params);
        }
    );
    $('#'+range_id)[0].noUiSlider.on('update', 
        function(  ) {
            $('#'+number_id).val($('#'+range_id)[0].noUiSlider.get());
            UpdateParams(ddl_json.params);
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
//             UpdateParams(ddl_json.params);
//         },
//         change: function( event, ui ) {
//             $('#'+number_id).val($('#'+range_id).slider('value'));
//             UpdateParams(ddl_json.params);
//         }
//     });

    $('#'+number_id).on('input', function(){
        $('#'+range_id)[0].noUiSlider.set($('#'+number_id).val());
        UpdateParams(ddl_json.params);
    });
    
}

//------------------------------------------------------------------------------
function CreateSelectionRangeScientificEvents(param,ddl_json) {
    //console.info("CreateSelectionRangeScientificEvents");
    var number_id = 'number_'+param.id;
    var range_id  = 'range_' +param.id;
    
    $('#'+range_id).slider(
    {
        value:num2sci(param.values.default, param.values.digits),
        min:  num2sci(param.values.min,     param.values.digits),
        max:  num2sci(param.values.max,     param.values.digits),
        step: 1,
        slide: function( event, ui ) {
            var value_slider = $('#'+range_id).slider('value');
            $('#'+number_id).val(
                    sci2str(value_slider,param.values.digits)
                );
            UpdateParams(ddl_json.params);
        },
        change: function( event, ui ) {
            var value_slider = $('#'+range_id).slider('value');
            $('#'+number_id).val(
                    sci2str(value_slider,param.values.digits)
                );
            UpdateParams(ddl_json.params);
        }
    });

    
//     $('#'+range_id).on('input', function(){
//         var value_slider = $('#'+range_id).val();
//         $('#'+number_id).val(
//                 sci2str(value_slider,param.values.digits)
//             );
//         UpdateParams(ddl_json.params);
//     }.bind(this));

}

//------------------------------------------------------------------------------
function CreateReadOnly(param) {

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


//------------------------------------------------------------------------------
function CreateLabel(param) {

  return  "<th style='border:0' colspan=3>"+ 
              "<div>" + param.label + "</div>" +
          "</th>";
}

//------------------------------------------------------------------------------
function CreateCheckBox(param) {

    var html = "";
    html += AddLabel(param);
    html +=
        '<td style="border:0px;"  colspan="2" align="left"> ' +
        '<input  type="checkbox"' +
            'name="'+param.id+'"' + ' id="param_'+param.id+'"';            
//         '<input  type="text" '+
//             'name="'+param.id+'_checked" ' +
//             'value="{{demo.params[pos].value==true}}" hidden />' +
    if (param.default_value) {
        html += ' checked';
    }
    html += ' > </td>';
    html += AddComments(param);
    return html;
    
}    

//------------------------------------------------------------------------------
function CreateCheckBoxEvents(param,ddl_json) {
    $('#param_'+param.id).on('change', function(){
        UpdateParams(ddl_json.params);
    }.bind(this));
}

//------------------------------------------------------------------------------
function CreateCheckBoxes(param) {

    var html = "";
    html += AddLabel(param);
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
    html += AddComments(param);
    return html;
    
    
}    
    
//------------------------------------------------------------------------------
function CreateParams(ddl_json) {
    
    $("#ParamDescription").html(joinHtml(ddl_json.general.param_description));
    
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
                        params_html += CreateSelectionCollapsed(param);
                        break;
                    case "selection_radio":
                        params_html += CreateSelectionRadio(param);
                        break;
                    case "range":
                        params_html += CreateSelectionRange(param);
                        break;
                    case "range_scientific":
                        params_html += CreateSelectionRangeScientific(param);
                        break;
                    case "readonly":
                        params_html += CreateReadOnly(param);
                        break;
                    case "label":
                        params_html += CreateLabel(param);
                        break;
                    case "checkbox":
                        params_html += CreateCheckBox(param);
                        break;
                    case "checkboxes":
                        params_html += CreateCheckBoxes(param);
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
                        CreateSelectionCollapsedEvents(param,ddl_json);
                        break;
                    case "selection_radio":
                        CreateSelectionRadioEvents(param,ddl_json);
                        break;
                    case "range":
                        CreateSelectionRangeEvents(param,ddl_json);
                        break;
                    case "range_scientific":
                        CreateSelectionRangeScientificEvents(param,ddl_json);
                        break;
                    case "readonly":
                        break;
                    case "label":
                        break;
                    case "checkbox":
                        CreateCheckBoxEvents(param,ddl_json);
                        break;
                    case "checkboxes":
                        break;
                } // end switch
            } // end for param_group
        } // end for params_layout
    }

//     SetLegendFolding(".param_legend");
    
    UpdateParams(ddl_json.params);
    
}

//------------------------------------------------------------------------------
function UpdateParams(ddl_params) {

    var imwidth  = 512;
    var imheight = 512;
    
    //--------------------------------------------------------------------------
    function CheckImageDimensions() {
//         console.info("CheckImageDimensions() ");
        if ($("#inputimage").get(0)) {
            imwidth  = $("#inputimage").get(0).naturalWidth;
            imheight = $("#inputimage").get(0).naturalWidth;
            if ($("#id_cropinput")&&($("#id_cropinput").is(':checked'))) {
                var CropBox = $("#inputimage").cropper('getCropBoxData');
                imwidth  = CropBox.width;
                imheight = CropBox.height;
            }
        }
//         console.info(imwidth+"x"+imheight);
    }
    
    
    CheckImageDimensions();
    
    //--------------------------------------------------------------------------
    function UpdateReadOnly(param) {
        try {
            $("input[name='"+param.id+"']").val(eval(param.value_expr.join('')));
        } catch(err) {
            //console.info("UpdateReadOnly ", param.value_expr.join(''), ':', param, " error:",err.message);
        }
    }

    // get parameter values for eval()
    var params = GetParamValues(ddl_params);
    
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
                        UpdateReadOnly(param);
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
        }
    }
}

//------------------------------------------------------------------------------
function GetParamValue(params_ddl,index) {

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
    
//------------------------------------------------------------------------------
function GetParamValues(params_ddl) {
    // create parameters
    var params={};
    if (params_ddl) {
        for(var p=0;p<params_ddl.length;p++) {
            var name = params_ddl[p].id;
            var value = GetParamValue(params_ddl,p);
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

//------------------------------------------------------------------------------
// reset parameters to default values
//
function ResetParamValues() {
    
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
                    param.value_slider = num2sci(param.value,param.values.digits);
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
// Set parameters to given values
//
function SetParamValues(param_values) {
    
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
                        param.value_slider = num2sci(param.value,param.values.digits);
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

