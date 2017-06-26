'use strict'

var clientApp = clientApp || {};
var helpers = helpers || {};
clientApp.helpers = helpers;

clientApp.helpers.getFromAPI = function(url, funct){
    $.getJSON(url).done(funct);
};

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

clientApp.helpers.base64ToBlob = function(base64Img) {
  var binary = atob(base64Img.split(',')[1]);
  var type = base64Img.split('data:')[1].split(';base64')[0];
  var len = binary.length;
  var buffer = new ArrayBuffer(len);
  var view = new Uint8Array(buffer);
  for (var i = 0; i < len; i++) {
    view[i] = binary.charCodeAt(i);
  }
  return new Blob([view], { type: type });;
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
