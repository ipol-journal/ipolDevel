var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var input = input || {};
var upload = upload || {};

input.printInput = function (blobs, demoInfo) {
    getBlobSets();
    getDemoinfo();
}

function getBlobSets(){
    helpers.getFromAPI("blobs", "get_blobs", "demo_id=" + demo_id, function(blobs){
        printSets(blobs.sets);
        helpers.addToStorage("blobs", blobs.sets);
        console.log(blobs.sets);
    });
}

function getDemoinfo(){
    helpers.getFromAPI("demoinfo", "get_ddl", "demo_id=" + demo_id, function(payload){
        var response = helpers.getJSON(payload.last_demodescription.json);
        helpers.addToStorage("demoInfo", response);
        addInputDescription(response.general.input_description);
        upload.printUploads(response.inputs);
        console.log(response);
    });
}

function printSets(sets){
    for (var i = 0; i < sets.length; i++) {
        var set = sets[i].blobs;
        var blobs = Object.keys(set);
        var blobClassName = "blobSet_" + i;
        $(".setContainer").append("<div class=blobSet_" + i + "></div>");
        $("." + blobClassName).addClass("blobSet");

        $("." + blobClassName).append("<img src=" + set[0].thumbnail + ">"); // first photo
        if (blobs.length == 3) { // Middle photo (3 photos)
            $("." + blobClassName).append("<img src=" + set[1].thumbnail + ">");
        }
        if (blobs.length >= 4) { // +3 photo set. ···
            $("." + blobClassName).append("<span>···</span>");
        }
        if (blobs.length > 1) { // +1 photo. last photo.
            $("." + blobClassName).append("<img src=" + set[blobs.length-1].thumbnail + ">");
        }

        $("." + blobClassName + "> img").addClass("blobThumbnail");
        if (blobs.length == 1) {
            $("." + blobClassName).append("<br><span class=blobTitle>" + set[blobs].title + "</span>");
        } else {
            $("." + blobClassName).append("<br><span class=blobTitle>" + sets[i].name + "</span>");
        }
    }
}

// Demo input description dialog
$(".description-dialog").dialog({autoOpen: false, width: 600});
$(".description-btn").click(function(){
    $(".description-dialog").dialog( "open");
});

function addInputDescription(inputDescription) {
    $(".description-dialog").append(inputDescription);
}
