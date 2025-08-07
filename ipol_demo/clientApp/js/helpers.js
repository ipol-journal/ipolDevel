'use strict'

var clientApp = clientApp || {};
var helpers = helpers || {};
clientApp.helpers = helpers;

clientApp.helpers.getJSON = function(json){
    return jQuery.parseJSON(json);
};

clientApp.helpers.getFromStorage = function(id) {
    return JSON.parse(sessionStorage.getItem(id));
}

clientApp.helpers.addToStorage = function(id, value) {
    sessionStorage.setItem(id, JSON.stringify(value));
}

clientApp.helpers.removeItem = function(id) {
    sessionStorage.removeItem(id);
}

clientApp.helpers.checkInterpolation = function(zoomRatio, selector) {
    if (zoomRatio <= 1){
        $(selector).removeClass("imageRendering");
        $(selector).css({ "image-rendering": "" });
    } 
    else $(selector).addClass('imageRendering');
}

clientApp.helpers.base64ToBlob = function(base64Img) {
  var binary = atob(base64Img.split(',')[1]);
  var type = base64Img.split('data:')[1].split(';base64')[0];
  var len = binary.length;
  var buffer = new ArrayBuffer(len);
  var view = new Uint8Array(buffer);
  for (var i = 0; i < len; i++) {
    view[i] = binary.charCodeAt(i);
  }
  return new Blob([view], { type: type });
};

clientApp.helpers.setOrigin = function(origin) {
    helpers.addToStorage("origin", origin);
}

clientApp.helpers.getOrigin = function() {
    return helpers.getFromStorage("origin");
}

$.fn.exists = function () {
    return this.length !== 0;
}

function loadJs(url) {
    return new Promise(function(resolve, reject) {
        var script = document.createElement('script');
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
};

function loadCss(url) {
    return new Promise(function(resolve, reject) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.onload = resolve;
        link.onerror = reject;
        document.head.appendChild(link);
    });
};
