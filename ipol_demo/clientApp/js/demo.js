"use strict"

var demo_id = "20";

$(document).ready(function() {
    $( "#header-container" ).load( "header.html" );
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

    clientApp.printInputSection();

});
