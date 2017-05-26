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

// Convert upload image to Base64.
clientApp.helpers.getBase64Image = function(img) {
    var canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;

    var ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);

    var dataURL = canvas.toDataURL("image/png");

    return dataURL.replace(/^data:image\/(png|jpg);base64,/, "");
}

clientApp.helpers.setOrigin = function(origin) {
    helpers.addToStorage("origin", origin);
}

clientApp.helpers.getOrigin = function() {
    return helpers.getFromStorage("origin");
}

$.fn.exists = function () {
    return this.length !== 0;
}
