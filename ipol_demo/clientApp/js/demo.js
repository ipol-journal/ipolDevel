"use strict"

var demo_id;

$(document).ready(function() {
    $( "#header" ).load( "header.html" );
    $( "#footer" ).load( "footer.html" );

    var clientApp = (function(){
        var demoInfo;

        var printInputSection = function(){
            input.printInput();
        };

        return {
            printInputSection: printInputSection
        };
    })();
    clearStorage();
    demo_id = getDemoId();
    clientApp.printInputSection();

});

function getDemoId() {
    var url = window.location.href;
    var id = url.split("?")[1];
    return id.split("=")[1];
}

function clearStorage() {
    Object.keys(sessionStorage).forEach(function(key) {
        sessionStorage.removeItem(key);
    });
}
