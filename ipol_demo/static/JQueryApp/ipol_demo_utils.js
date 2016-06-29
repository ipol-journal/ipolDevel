/**
 * @file Contains the utility functions associated with ipol_demo.html and
 * ipol_demo*.js, part of the IPOL journal demo system, CMLA ENS Cachan
 * @author  Karl Krissian
 * @version 0.1
 */


"use strict";

/**
 * utilities
 * @namespace
 */
ipol_utils = {};

//------------------------------------------------------------------------------
/** 
 * Creates the path based on a blob hash, for example if the hash is 
 * abcdef and the depth 3, will return a/b/c/ path.
 * @param {string} blob_hash blob hash
 * @param {number} depth directory depth
 * @returns {string} blob path
 */
ipol_utils.blobhash_subdir = function ( blob_hash, depth) {
    if (depth===undefined) {
        depth=2;
    }
    return blob_hash.substring(0,depth).split('').join("/")+'/';
}

//------------------------------------------------------------------------------
/**
 * This function creates syntax highlight for pretty display of json files
 * @param {object|string} input json object
 * @returns {string} syntax highlighted representation of the json object
 */
ipol_utils.syntaxHighlight = function(json) {
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
/** 
 * Deserializes a json file 
 * @param {string} json_str serialized json object
 * @returns {object} deserialized object
 */
ipol_utils.DeserializeJSON = function(json_str)
{
    // need to deserialize twice: TODO: fix this problem
    var json_obj = jQuery.parseJSON(json_str);
    json_obj = jQuery.parseJSON(json_obj);
    return json_obj
}


//------------------------------------------------------------------------------
/**
 * Calls a module service with its parameters and executes the function func
 * @param module  {string} module name
 * @param service {string} web service name
 * @param params  {string} list of url parameters
 * @param func    {callback} function to call when the service returns
 * @returns       {Object.jqXHR} jqXHR object
 */
ipol_utils.ModuleService = function(module,service,params,func)
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
/**
 * Returns an array of integer values, if only one parameter is given, returns
 * [0...max-1], otherwise returns [min...max-1] with step
 * @param {number} min minimal value
 * @param {number} max maximal value (not included)
 * @param {number} step interval step between values
 * @returns {number[]}
 */
ipol_utils.range = function(min, max, step) {
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
/**
 * If input is an array of strings, join the strings, otherwise return the 
 * original string
 * @param {(string|string[])}html_code
 * @return {string}
 */
ipol_utils.joinHtml = function(html_code)
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

//------------------------------------------------------------------------------
//
// found in http://stackoverflow.com/questions/1068834/object-comparison-in-javascript
//
/**
 * Counts object properties
 * @param {object} input object
 * @returns {number} number of object properties
 */
ipol_utils.countProps = function(obj) {
    var count = 0;
    for (var k in obj) {
        if (obj.hasOwnProperty(k)) {
            count++;
        }
    }
    return count;
};

//------------------------------------------------------------------------------
/**
 * Check object equalities
 * @param {object} v1 first object
 * @param {object} v2 second object
 * @returns {boolean} if objects are equal
 */
ipol_utils.objectEquals = function(v1, v2) {

    if (typeof(v1) !== typeof(v2)) {
        return false;
    }

    if (typeof(v1) === "function") {
        return v1.toString() === v2.toString();
    }

    if (v1 instanceof Object && v2 instanceof Object) {
        if (ipol_utils.countProps(v1) !== ipol_utils.countProps(v2)) {
            return false;
        }
        var r = true;
        for (var k in v1) {
            r = ipol_utils.objectEquals(v1[k], v2[k]);
            if (!r) {
                return false;
            }
        }
        return true;
    } else {
        return v1 === v2;
    }
}
