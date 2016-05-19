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


"use strict";


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
    var link =  servers.proxy + 
                '/?module='+ module +
                '&service='+ service +
                '&'+params;
    var params_str = ""+params;
                
    console.info("--- ModuleService() --- "+ module + " -- "+ service+ " -- "+ 
                     params_str.slice(0,40) +(params_str.length>40?"...":""));

    return $.getJSON(link).done(func);
}

// //------------------------------------------------------------------------------
// //
// function DemoRunnerService(service,params,func) {
//     var link =  servers.proxy + 
//                 '/?module=demorunner'+ 
//                 '&service='+ service +
//                 '&'+params;
//     console.info("---- DemoRunnerService() ---- "+link.slice(0,80)+(link.length>80?"...":""));
//     return $.getJSON(link).done(func);
// };


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
function joinHtml(html_code)
{
    if ($.isArray(html_code)) {
        return html_code.join(' ');
    } else {
        return html_code;
    }
};


//------------------------------------------------------------------------------
// adds .naturalWidth() and .naturalHeight() methods to jQuery
// for retreaving a normalized naturalWidth and naturalHeight.
(function($){
var
props = ['Width', 'Height'],
prop;

while (prop = props.pop()) {
(function (natural, prop) {
    $.fn[natural] = (natural in new Image()) ? 
    function () {
    return this[0][natural];
    } : 
    function () {
    var 
    node = this[0],
    img,
    value;

    if (node.tagName.toLowerCase() === 'img') {
    img = new Image();
    img.src = node.src,
    value = img[prop];
    }
    return value;
    };
}('natural' + prop, prop.toLowerCase()));
}
}(jQuery));

//
// found in http://stackoverflow.com/questions/1068834/object-comparison-in-javascript
//

function countProps(obj) {
    var count = 0;
    for (var k in obj) {
        if (obj.hasOwnProperty(k)) {
            count++;
        }
    }
    return count;
};

function objectEquals(v1, v2) {

    if (typeof(v1) !== typeof(v2)) {
        return false;
    }

    if (typeof(v1) === "function") {
        return v1.toString() === v2.toString();
    }

    if (v1 instanceof Object && v2 instanceof Object) {
        if (countProps(v1) !== countProps(v2)) {
            return false;
        }
        var r = true;
        for (var k in v1) {
            r = objectEquals(v1[k], v2[k]);
            if (!r) {
                return false;
            }
        }
        return true;
    } else {
        return v1 === v2;
    }
}
