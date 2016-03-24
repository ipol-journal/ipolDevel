//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_blobs.js
// date: march 2016
// author: Karl Krissian
//
// description:
// this file contains the utility functions
// associated with ipol_demo.html and ipol_demo*.js
//




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
