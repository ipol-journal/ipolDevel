//------------------------------------------------------------------------------
// This function creates syntax highlight for pretty display of json files
//
function syntaxHighlight(json) {
    if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 2);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function(match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

//------------------------------------------------------------------------------
function DeserializeJSON(json_str)
{
    // need to deserialize twice: TODO: fix this problem
    var json_obj = jQuery.parseJSON(json_str);
    json_obj = jQuery.parseJSON(json_obj);
    return json_obj
}


//------------------------------------------------------------------------------
// calls a module service with its parameters and executes the function func
//
function ModuleService(module,service,params,func)
{
    var proxy_server = 
//     "http://127.0.0.1:9003/";
                        "http://ns3018037.ip-151-80-24.eu:9003/";
    var link =  proxy_server + 
                '/?module='+ module +
                '&service='+ service +
                '&'+params;
    console.info("getting service:"+link);


    $.getJSON(link).done(func);
}



//------------------------------------------------------------------------------
function range(min, max, step) {
    // parameters validation for method overloading
    if (max == undefined) {
        max = min;
        min = 0;
    }
    step = Math.abs(step) || 1;
    if (min > max) {
        step = -step;
    }
    // building the array
    var output = [];
    for (var value=min; value<max; value+=step) {
        output.push(value);
    }
    // returning the generated array
    return output;
};


//------------------------------------------------------------------------------
// preprocess DDL demo, filling some properties:
//   input.max_pixels if string
//   input.max_weight if string
// default values for:
//   general.crop_maxsize
//   general.thumbnail_size
// set array of strings if single string for
//   general.input_description
//   general.param_description
// default value for 
//    params_layout
// 
function PreprocessDemo(demo) {
    //
    console.info("PreprocessDemo")
    console.info(demo)
    if (demo != undefined) {
        for (input in demo.inputs) {
            // do some pre-processing
            if ($.type(input.max_pixels) === "string") {
                input.max_pixels = scope.$eval(input.max_pixels)
            }
            if ($.type(input.max_weight) === "string") {
                input.max_weight = scope.$eval(input.max_weight)
            }
        }
    }
    //

    if (demo.general.crop_maxsize == undefined) {
        // setting the crop_maxsize string to a non integer value with 
        // disable its behavior, so no limit by default
        demo.general.crop_maxsize = "NaN";
    }

    if (demo.general.thumbnail_size == undefined) {
        demo.general.thumbnail_size = 128;
    }

    if ($.type(demo.general.input_description) === "string") {
        demo.general.input_description = [demo.general.input_description];
    }
    if ($.type(demo.general.param_description) === "string") {
        demo.general.param_description = [demo.general.param_description];
    }

    // create default params_layout property if it is not defined
    if (demo.params_layout == undefined) {
        demo.params_layout = [
            ["Parameters:", range(demo.params.length)]
        ];
    }
};




//------------------------------------------------------------------------------
// initialization of the parameters obtained from the DDL json file
function initParams(  demo, params) {
    console.info("initParams");
    
    // add pensize parameter for inpainting
    if (params['pensize']==undefined) {
        demo.params.pensize = 5;
    } else {
        demo.params.pensize = params['pensize'];
    }

    // initialize input loading status
    angular.forEach(demo.inputs, 
        function(res) {
        res.status = "trying";
        }
    );

    // initialize parameter values
    angular.forEach(demo.params, 
        function(param) {
        console.info(param.type);
        // range type
        if (param.type=='range') {
            if (params[param.id]==undefined) {
            param.value = param.values.default;
            } else {
            param.value = params[param.id];
            }
        }
        // range_scientic type
        if (param.type=='range_scientific') {
            if (params[param.id]==undefined) {
            param.value = param.values.default;
            } else {
            param.value = params[param.id];
            }
            // initialize the slider position
            param.value_slider = num2sci(param.value,param.values.digits);
        }
        // selection_collapsed type
        if (param.type=='selection_collapsed') {
            if (params[param.id]==undefined) {
            param.value = param.default_value;
            } else {
            param.value = params[param.id].toString();
            }
        }
        // selection_radio type
        if (param.type=='selection_radio') {
            if (params[param.id]==undefined) {
            param.value = param.default_value;
            } else {
            param.value = params[param.id].toString();
            }
        }
        // checkbox type
        if (param.type=='checkbox') {
            // if the variable xxx_checked (hidden input) is
            // not defined: use default value, otherwise, use
            // its value (we need this variable because checkboxes
            // are only returned if they are checked in html)
            if (params[param.id+"_checked"]==undefined) {
            param.value = param.default_value;
            } else {
            param.value = params[param.id+"_checked"];
            }
        }
        // checkboxes type
        if (param.type=='checkboxes') {
            // create one boolean value per checkbox ...
            param.cb_values = {};
            angular.forEach(param.values, 
            function(checkboxes_info) {
                angular.forEach(checkboxes_info, 
                function(value,key)
                {
                    // if the variable xxx_checked (hidden input) is
                    // not defined: use default value, otherwise, use
                    // its value (we need this variable because checkboxes
                    // are only returned if they are checked in html)
                    if (params[param.id+"_"+key+"_checked"]==undefined) {
                    param.cb_values[key]=(param.default.indexOf(key)>-1);
                    } else {
                    param.cb_values[key]=params[param.id+"_"+key+"_checked"];
                    }
                }
                );
            }
            );
        }
        if (param.type=='readonly') {
            param.value='';
        }
        //console.info(param.cb_values);
        }
    );
}


//------------------------------------------------------------------------------
function OnDemoList(demolist)
{
    if (demolist.status == "OK") {
        var str = JSON.stringify(demolist.demo_list, undefined, 4);
        $("#tabs-demos pre").html(syntaxHighlight(str))
        dl = demolist;
        console.info(dl);
    }

    // create a demo selection
    html_selection = "<select>";
    for (var i=0; i<dl.demo_list.length; i++) {
        html_selection += '<option value = "'+i+'">'
        html_selection += dl.demo_list[i].editorsdemoid + 
                          '  '+ dl.demo_list[i].title
        html_selection += '</option>'
    }
    html_selection += "</select>";
    $("#demo-select").html(html_selection);
    $("#demo-select").change(
        function() {
            var pos =$( "#demo-select option:selected" ).val();
            InputController(dl.demo_list[pos].editorsdemoid,dl.demo_list[pos].id);
        });

}

//------------------------------------------------------------------------------
// List all demos and select one
//
function ListDemosController() {
    
    console.info("get demo list from server");
    var dl;

    ModuleService(
        'demoinfo',
        'demo_list',
        '',
        OnDemoList
    );
    
    
}

//------------------------------------------------------------------------------
function CreateBlobSetDisplay(demoblobs)
{
    var blobsets_html = "";
    
    var thumbnail_size   = $("#ThumbnailSize option:selected").text();
    var display_credits = $("#ShowCreditsCheckbox").is(':checked');
    
    console.info("ThumbailSize is  ",$("#ThumbnailSize option:selected").text());
    
    // loop over blobsets
    for(var i=0;i<demoblobs.blobs.length;i++)
    {
        var blobset = demoblobs.blobs[i];
        // represent the blob set within a HTML table
        var blobset_html = "";
        blobset_html += '<div  ';
        // set div id for click selection
        blobset_html += ' id="blobset_'+i+'"';
        blobset_html += ' style="display:inline-block;vertical-align: top;">';
        blobset_html += "<table  style='background-color:#EEEEEE;margin:5px;text-align:center;'>";
        blobset_html += "<tr>";
        for(var idx=1;idx<blobset[0].size+1;idx++)
        {
            // blob display could be disabled ...
            blobset_html += "<td style='margin:2px;padding:2px;'>"
            // apply the selection ???
//         <a  style=' margin:0;padding:0;' 
//             ng-href="/{{demo_id}}/input_select_angular?{{blob_set[0].html_params}}">

            blobset_html += '<div';
            blobset_html += '  class="select_input"';
            blobset_html += '  style="margin:4px 0;padding:0;float:left;';
//             blobset_html += '         width:'       +thumbnail_size+'px;';
            blobset_html += '         height:'      +thumbnail_size+'px;';
            blobset_html += '         line-height:' +thumbnail_size+'px;';
            blobset_html += '         text-align:center" > ';
            // needed to add at least one character (here &nbsp;) to get it vertically centered on chrome ... !!!
            blobset_html += '&nbsp;<img';
            blobset_html += '   style=" max-width:'  +thumbnail_size+'px;';
            blobset_html += '           max-height:' +thumbnail_size+'px;';
            blobset_html += '           vertical-align:middle;"';
            blobset_html += '   src="'+demoblobs.url_thumb+
                                '/thumbnail_'+blobset[idx].hash+blobset[idx].extension+'" ';
            blobset_html += '   alt='   +blobset[idx].title;
            blobset_html += '   title="'+blobset[idx].title+
                                ' (credits: '+blobset[idx].credit+
                                ', tags:'+blobset[idx].tag+')" >&nbsp;';
            blobset_html += "</div> ";
            blobset_html += "</td>";
        }
        blobset_html += "</tr>";
        blobset_html += '<tr style="background-color:#EEEEEE;">';
        blobset_html += '<th colspan="'+blobset[0].size+'" ';
        blobset_html +=   'style="max-width:'+(blobset[0].size*thumbnail_size)+'px" >';
        //          We could use the blob name but in general each image has the same title
        //             which is a better name <span>{{blob_set[0].set_name}}</span>
        blobset_html += blobset[1].title;
        if (display_credits) {
          blobset_html += '<br/> <font size="-2"><i> <pre> &copy; '+blobset[1].credit+' </pre></i></font>'
        }
        blobset_html += "</th>";
        blobset_html += "</tr>";
        blobset_html += "</table>";
        blobset_html += '</div>';
        blobsets_html += blobset_html;
    }
    
//     console.info(blobsets_html);
    return blobsets_html;
//     </tr>
//     <tr style="background-color:#EEEEEE;">
//         <th colspan="{{blob_set[0].size}}" ng-style="{'max-width':demo.general.thumbnail_size*blob_set[0].size+'px' }">
//         {{blob_set[1].title}}
//         <span ng-if="ShowCredits">
//             <br/> <font size="-2"><i> <pre> &copy; {{blob_set[1].credit}} </pre></i></font>
//         </span>
//         </th>
//     </tr>
//     </table>
}


//------------------------------------------------------------------------------
class BlobsContainer {
    constructor(demoblobs) {
        console.info("constructor : ", demoblobs);
        this.demoblobs = demoblobs;
        console.info("this.demoblobs : ", this.demoblobs);
    }
    
    append_blobs(db) {
        console.info("append_blobs ", this.demoblobs, " -- ", db);
        this.demoblobs.blobs = this.demoblobs.blobs.concat(db.blobs);
        UpdateDemoBlobs(this.demoblobs);
    }
}

//------------------------------------------------------------------------------
function OnDemoBlobs(demoblobs) {
    
    console.info("*** demoblobs");
    console.info(demoblobs)
    
    if (demoblobs.status=="KO") {
        return;
    }
    
    
    
    bc = new BlobsContainer(demoblobs);
    
    // Check for template
    if (demoblobs.use_template.hasOwnProperty('name')) {
        // get template blobs
        var template_name = demoblobs.use_template.name;
        console.info("getting template ***")
        ModuleService(
            "blobs",
            "get_blobs_from_template_ws",
            "template="+template_name,
            function(db){bc.append_blobs(db)}
        );
    } else {
        UpdateDemoBlobs(demoblobs);
    }
    
    
}


//------------------------------------------------------------------------------
function UpdateDemoBlobs(demoblobs) {

    console.info("demoblobs.blobs.length=",demoblobs.blobs.length);
    
    // preprocess HTML parameters string
    // for each blob set, in the form
    // html_params="url=XXXX&0:blob&1:blob&2:blob,blob etc ..."
    for(var i=0;i<demoblobs.blobs.length;i++)
    {
        var blobset = demoblobs.blobs[i];
        blobset[0].html_params = "url=" + demoblobs.url + "&"
            // extract only contents of interest
        var blobset_contents = blobset.slice(1);
        blobset_contents.sort(function(a, b) {
            return (a.id_in_set < b.id_in_set ? -1 : (a.id_in_set > b.id_in_set ? 1 : 0));
        });
        var current_id = ""
        for (var idx = 0; idx < blobset_contents.length; idx++) {
            if (idx == 0) {
                blobset[0].html_params += blobset_contents[idx].id_in_set + ":";
            } else {
                // if same id, separate by comma ...
                if (blobset_contents[idx].id_in_set == current_id) {
                    blobset[0].html_params += ",";
                } else {
                    // else separate arguments
                    blobset[0].html_params += "&" + blobset_contents[idx].id_in_set + ":";
                }
            }
            current_id = blobset_contents[idx].id_in_set;
            blobset[0].html_params += blobset_contents[idx].hash +
                blobset_contents[idx].extension;
        }
    }
    
    var str = JSON.stringify(demoblobs, undefined, 4);
    $("#tabs-blobs pre").html(syntaxHighlight(str))

    
    $("#ThumbnailSize" ).change( function() {
        $("#displayblobs").html(CreateBlobSetDisplay(demoblobs));
        // set click events on blobsets
        for(var i=0;i<demoblobs.blobs.length;i++) {
            $("#blobset_"+i).click( {blobset_id: i}, function(event) {
                console.info("blobset "+event.data.blobset_id+" clicked");
            }
            )
        }
    }
    );
    
    $("#ShowCreditsCheckbox" ).change( function() {
        $("#displayblobs").html(CreateBlobSetDisplay(demoblobs));
        // set click events on blobsets
        for(var i=0;i<demoblobs.blobs.length;i++) {
            $("#blobset_"+i).click( {blobset_id: i}, function(event) {
                console.info("blobset "+event.data.blobset_id+" clicked");
            }
            )
        }
    }
    );
    
    
    $("#displayblobs"  ).html(CreateBlobSetDisplay(demoblobs));
    //$("#displayblobs2").html(CreateBlobSetDisplay(demoblobs)).css('float','left');

    // set click events on blobsets
    for(var i=0;i<demoblobs.blobs.length;i++) {
        $("#blobset_"+i).click( {blobset_id: i}, function(event) {
            console.info("blobset "+event.data.blobset_id+" clicked");
        }
        )
    }
    
    
}
    
//------------------------------------------------------------------------------
// Starts everything needed for demo input tab
//
function InputController(demo_id,internal_demoid) {



    console.info("internal demo id = ", internal_demoid);
    if (internal_demoid > 0) {
        ModuleService(
            'demoinfo',
            'read_last_demodescription_from_demo',
            'demo_id=' + internal_demoid + '&returnjsons=True',
            function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);
                if (demo_ddl.status == "OK") {
                    var ddl_json = DeserializeJSON(demo_ddl.last_demodescription.json);
                    var str = JSON.stringify(ddl_json, undefined, 4);
                    $("#tabs-ddl pre").html(syntaxHighlight(str));
                }
                PreprocessDemo(ddl_json);
                // Create Parameters tab
                CreateParams(ddl_json);
            });
    }
    
    // Get demo blobs
    ModuleService(
        "blobs",
        "get_blobs_of_demo_by_name_ws",
        "demo_name=" + demo_id,
        OnDemoBlobs);

}
    
//------------------------------------------------------------------------------
function AddLabel(param) {
    var html = "";
    html += '<td style="border:0px;max-width:34em">';
    html += '<label>'+param.label+'</label>';
    html += '</td>';
    return html;
}
    
//------------------------------------------------------------------------------
function AddComments(param) {
    var html = "";
    if (param.comments!=undefined) {
        html += '<td   style="border:0px;max-width:34em">';
        html += '<label>'+param.comments+'</label>';
        html += '</td>';
    }
    return html;
}

//------------------------------------------------------------------------------
function CreateSelectionCollapsed(param) {
    var html = "";
    html += AddLabel(param);
    html += '<td style="border:0px;" colspan="2">';
    html += '<select name="'+param.id+'">';
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
function CreateSelectionRadio(param) {
    var html = "";
    html += AddLabel(param);
    html += '<td style="border:0px;" colspan="2">';
    jQuery.each( param.values, function( key, value ) {

        html += '<label>';
        html += '<input type="radio"';
        html += ' name="'+param.id+'">';
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
    html += '<td style="border:0px;width:24em">';
    html += '<input  style="width:100%"  type="range"';
    html += ' id="'+range_id+'"';
    html += ' name="'+param.id+'" '+limits + ' >';
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
    console.info("exponent = ", exponent);
    var mantissa = value / Math.pow(10, exponent - numDigits);
    console.info("mantissa = ", mantissa);
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
    console.info("sci2str ", exponent, mantissa, value, value.toExponential(numDigits))
    return value.toExponential(numDigits);
}

//------------------------------------------------------------------------------
function CreateSelectionRangeScientific(param) {
    var html = "";
    html += AddLabel(param);

    var limits= '';
    console.info("num2sci ", param.values.min, param.values.digits, num2sci(param.values.min,param.values.digits))
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
         + '</td>'
         + '<td style="border:0px;width:24em">'
         + '<input  style="width:100%"  type="range"'
         + ' id="'+range_id+'"'
         + ' name="'+param.id+'" '+limits + ' >'
         + '</td>';
    html += AddComments(param);

    return html;
}

//------------------------------------------------------------------------------
function CreateSelectionRangeEvents(param, ddl_json) {

    var number_id = 'number_'+param.id;
    var range_id  = 'range_' +param.id;
    $('#'+range_id).on('input', function(){
        $('#'+number_id).val($('#'+range_id).val());
        UpdateParams(ddl_json);
    });

    $('#'+number_id).on('input', function(){
        $('#'+range_id).val($('#'+number_id).val());
        UpdateParams(ddl_json);
    });
    
}

//------------------------------------------------------------------------------
function CreateSelectionRangeScientificEvents(param,ddl_json) {
    console.info("CreateSelectionRangeScientificEvents");
    var number_id = 'number_'+param.id;
    var range_id  = 'range_' +param.id;
    $('#'+range_id).on('input', function(){
        var value_slider = $('#'+range_id).val();
        $('#'+number_id).val(
                sci2str(value_slider,param.values.digits)
            );
        UpdateParams(ddl_json);
    }.bind(this));

}

//------------------------------------------------------------------------------
function CreateReadOnly(param) {

    var html = "";
    html = 
        "<td style='border:0;max-width:34em'>" +
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
function UpdateReadOnly(param) {
    try {
        $("input[name='"+param.id+"']").val(eval(param.value_expr_new.join('')));
    } catch(err) {
        console.info("UpdateReadOnly ", param, " error:",err.message);
    }
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
            'name="'+param.id+'"' +
//         '<input  type="text" '+
//             'name="'+param.id+'_checked" ' +
//             'value="{{demo.params[pos].value==true}}" hidden />' +
        '</td>';
    html += AddComments(param);
    return html;
    
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
                    'name="'+param.id+'_'+id+'" id="'+id+'"'+ ' />';
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
    
    $("#ParamDescription").html(ddl_json.general.param_description.join(' '));
    
    var params_html = "";
    if (ddl_json.params.length>0) {
        // for each param group
        for(var pg=0;pg<ddl_json.params_layout.length;pg++) {
            var param_group = ddl_json.params_layout[pg];
            params_html += '<fieldset style="display: inline-block;">';
            params_html += '<legend>'+param_group[0]+'</legend>';
            
            params_html += '<table  style="float:left;border:0px;">';
            for(var n=0;n<param_group[1].length;n++) {
                params_html += '<tr style="border:0px;">';
                var pos=param_group[1][n]; 
                var param = ddl_json.params[pos];
                if (param.visible_new===undefined||eval(param.visible_new)) {
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
                }
                params_html += '</tr>';
            }
            params_html += '</table>';
            params_html += '</fieldset>';
        }
    }
    
    $("#DisplayParams").html(params_html);

    // add events
    for(var pg=0;pg<ddl_json.params_layout.length;pg++) {
        var param_group = ddl_json.params_layout[pg];
        for(var n=0;n<param_group[1].length;n++) {
            var pos=param_group[1][n]; 
            var param = ddl_json.params[pos];
            
            if (param.visible_new===undefined||eval(param.visible_new)) {
                switch(param.type) {
                    case "selection_collapsed":
                        break;
                    case "selection_radio":
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
                        break;
                    case "checkboxes":
                        break;
                } // end switch
            } // end if param.visible
        } // end for param_group
    } // end for params_layout

    UpdateParams(ddl_json);
    
}

//------------------------------------------------------------------------------
function UpdateParams(ddl_json) {
    // add events
    for(var pg=0;pg<ddl_json.params_layout.length;pg++) {
        var param_group = ddl_json.params_layout[pg];
        for(var n=0;n<param_group[1].length;n++) {
            var pos=param_group[1][n]; 
            var param = ddl_json.params[pos];
            
            if (param.visible_new===undefined||eval(param.visible_new)) {
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
            } // end if param.visible
        } // end for param_group
    } // end for params_layout
}

    
// 
//     // upload is done by python
//     //$scope.uploaded_images = [];
// 
//     $scope.DisableBlobDisplay = function(blob_set, index) {
//         if (blob_set[index].extension != ".png") {
//             //             // first try png extension if it is not already the case
//             //             blob_set[index].extension = ".png";
//             //         } else {
//             blob_set[index].extension = "disabled";
//         }
//     }
// 
// }

function DocumentReady() {

    $("#tabs").tabs({
            activate: function(event, ui) {
                var active = $('#tabs').tabs('option', 'active');
            }
        }

    );
    
//     $.ajax({
//         crossOrigin: true,
//         url: "http://localhost:8000/test_input.html",
//         success: function(data) {
//             console.log(data);
//         }
//     });
        
//     $("#tabs-input").load("http://localhost:8000/test_input.html");
//     $("#tabs-params").load("http://localhost:8000/test_params.html");

    ListDemosController();
    var demo_id = 20;
    

}
$(document).ready(DocumentReady);