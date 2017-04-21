var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var input = input || {};
var upload = upload || {};
var editor = editor || {};

// Print imput pannel.
input.printInput = function (blobs, demoInfo) {
    getBlobSets();
    getDemoinfo();
}

// Get blobsets from API.
function getBlobSets(){
    helpers.getFromAPI("/api/blobs/get_blobs?demo_id=" + demo_id, function(blobs){
        printSets(blobs.sets);
        helpers.addToStorage("blobs", blobs.sets);
    });
}

// Get demoinfo from API.
function getDemoinfo(){
    helpers.getFromAPI("/api/demoinfo/get_interface_ddl?demo_id=" + demo_id, function(payload){
        var response = helpers.getJSON(payload.last_demodescription.ddl);
        helpers.addToStorage("demoInfo", response);
        addInputDescription(response.general.input_description);
        upload.printUploads(response.inputs);
    });
}

// Print in the web Interface the sets.
function printSets(sets){
    for (var i = 0; i < sets.length; i++) {
        var set = sets[i].blobs;
        var blobs = Object.keys(set);
        var name = sets[i].name;

        $(".setContainer").append("<div class=blobSet_" + i + " id=" + name + "></div>");
        var blobSet = $(".blobSet_" + i);
        var blobSetArray = [];

        blobSet.addClass("blobSet")
               .on('click', function() {
                    helpers.addToStorage("demoSet", this.id);
                    helpers.setOrigin("demo");
                    editor.printEditor();
                });
        blobSetArray += "<img src=" + set[0].thumbnail + ">"; // first photo
        if (blobs.length == 3) { // Middle photo (3 photos)
            blobSetArray += "<img src=" + set[1].thumbnail + ">";
        }
        if (blobs.length >= 4) { // +3 photo set. ···
            blobSetArray += "<span>···</span>";
        }
        if (blobs.length > 1) { // +1 photo. last photo.
            blobSetArray += "<img src=" + set[blobs.length-1].thumbnail + ">";
        }
        $(".blobSet_" + i + "> img").addClass("blobThumbnail");
        if (blobs.length == 1) {
            blobSetArray += "<br><span class=blobTitle>" + set[blobs].title + "</span>";
        } else {
            blobSetArray += "<br><span class=blobTitle>" + sets[i].name + "</span>";
        }
        blobSet.html(blobSetArray);
    }
}

// Demo input description dialog
$(".description-dialog").dialog({autoOpen: false, width: 600});
$(".description-btn").click(function(){
    $(".description-dialog").dialog( "open");
});

// Add input description to dialog.
function addInputDescription(inputDescription) {
    $(".description-dialog").append(inputDescription);
}
