var input = input || {};

input.printInput = function () {
    getBlobSets();
    getDemoinfo();
}

function getBlobSets(){
    clientApp.helpers.getFromAPI("blobs", "get_blobs", "demo_id=" + demo_id, function(blobs){
        printSets(blobs.sets);
    });
}

function getDemoinfo(){
    clientApp.helpers.getFromAPI("demoinfo", "read_last_demodescription_from_demo", "demo_id=" + demo_id + "&returnjsons=True", function(payload){
        var response = clientApp.helpers.getJSON(payload.last_demodescription.json);
        addInputDescription(response.general.input_description);
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
            $("." + blobClassName).append("<br><span class=blobTitle>" + set[blob].title + "</span>");
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

// Upload dialog
$(".upload-dialog").dialog({autoOpen: false, width: 600});
$(".upload-btn").click(function(){
    $(".upload-dialog").dialog( "open");
});
