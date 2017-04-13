'use strict'

var clientApp = clientApp || {};
var helpers = helpers || {};
clientApp.helpers = helpers;

clientApp.helpers.getFromAPI = function(module, method, parameters, funct){
    var url = "/api/" + module + "/" + method + "?" + parameters;
    $.get(url).done(funct);
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
