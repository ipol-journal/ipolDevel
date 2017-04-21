var clientApp = clientApp || {};
var editor = editor || {};
var helpers = helpers || {};

// Print editor pannel.
editor.printEditor = function(){
    printBlobs();
};

// Print blobs or uploads depends on Origin variable.
function printBlobs(){
    if(helpers.getOrigin() == "demo")  console.log("nein");
    else list = printUploads();
};

// Print uploads list and set image src with hover and click events.
function printUploads(){
    $(".editor-container").removeClass("di-none");
    var demoInfo = helpers.getFromStorage("demoInfo");
    var upload;
    var images = [];
    for (var i = 0; i < demoInfo.inputs.length; i++) {
        upload = helpers.getFromStorage(demoInfo.inputs[i].description); // Revisar
        if(upload){
            images.push({"name": demoInfo.inputs[i].description , "src":upload});
            $(".blobsList-left").append("<span class=editor-input-left-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
            $(".blobsList-right").append("<span class=editor-input-right-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
            loadInputEvents(i, "left");
            loadInputEvents(i, "right");
        };
    };
    $(".blobsList-left").append("<br><input type=checkbox id=compare-btn>Compare");
    $(".editor-image-left").attr("src", images[0].src);
    $(".editor-image-right").attr("src", images[0].src);
    helpers.addToStorage("selectedInput", images[0].src);

    // addScrollEvents();
    addCompareEvent();
};

function addCompareEvent() {
    $("#compare-btn").change(function() {
        $(".image-wrapper").toggleClass("image-grid-1");
        $(".image-wrapper").toggleClass("image-grid-2");
        $(".blobsList-right").toggleClass("di-inline");
        $("#right-container").toggleClass("di-none");
        $("#right-container").toggleClass("di-inline");
    });
}

function addScrollEvents() {
    var isSyncingLeftScroll = false;
    var isSyncingRightScroll = false;
    var leftDiv = document.getElementById("left-container");
    var rightDiv = document.getElementById("right-container");
    leftDiv.onscroll(scrollLeft());
    rightDiv.onscroll(scrollRight());
}

function scrollLeft() {
    if (!isSyncingLeftScroll) {
        isSyncingRightScroll = true;
        rightDiv.scrollTop = this.scrollTop;
        rightDiv.scrollLeft = this.scrollLeft;
    }
    isSyncingLeftScroll = false;
}

function scrollRight() {
    if (!isSyncingRightScroll) {
        isSyncingLeftScroll = true;
        leftDiv.scrollTop = this.scrollTop;
        leftDiv.scrollLeft = this.scrollLeft;
    }
    isSyncingRightScroll = false;
}

// Initialize input mouseover, mouseout and click event to switch input image.
function loadInputEvents(index, side) {
    var element = $(".editor-image-" + side);
    var selector = $(".editor-input-" + side + "-" + index);
    selector.on('mouseover', function() {
        element.attr("src", helpers.getFromStorage($(this).text()));
    });
    selector.on('mouseout', function() {
        element.attr("src", helpers.getFromStorage("selectedInput"));
    });
    selector.on('click', function() {
        element.attr("src", helpers.addToStorage("selectedInput", helpers.getFromStorage($(this).text())));
    });
}
