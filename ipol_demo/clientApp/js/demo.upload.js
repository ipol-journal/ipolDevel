var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var upload = upload || {};
var editor = editor || {};

// Upload dialog initialization.
$(".upload-dialog").dialog({
    autoOpen: false,
    width: 1100,
    maxHeight:500,
    modal: true,
    // Click outside of dialog to close
    open: function () {
        $('.ui-widget-overlay').bind('click',function(){
                $('.upload-dialog').dialog('close');
            })
    },
    buttons : {
        Apply: function() {
            if (checkRequiredInputs()) {
                $(this).dialog("close");
                helpers.setOrigin("upload");
                $( "#inputEditorContainer" ).load( "editor.html" , function(){
                    editor.printEditor();
                });
            }
        },
        Clear: function() {
            clearUploads();
        },
        Cancel: function() {
            $(this).dialog("close");
        }
    }
});

$(".upload-btn").click(function(){
    $(".upload-dialog").dialog( "open");
});

// Print uploads dialog.
upload.printUploads = function (inputs) {
    var uploadMaxSize = 0;
    for (var i = 0; i < inputs.length; i++) {
        var input = inputs[i];
        var input_weight = eval(input.max_weight)/1024/1024;
        uploadMaxSize += input_weight;
        $(".upload-dialog").append("<div class=input-upload-" + i + "></div>");
        var uploadRow = $(".input-upload-" + i);
        var uploadRowArray = [];
        uploadRow.addClass("upload-row");
        uploadRowArray += "<span class=upload-description>" + input.description + "</span>";
        uploadRowArray += "<input type=file id=file-" + i + " name=file-" + i + " class=upload-btn-" + i +"/>";
        uploadRowArray += "<img id=img-" + i + " src=# />";
        uploadRowArray += "<span class=upload-resolution-" + i + ">" + getMaxPixels(input) + getMaxWeight(input_weight) + "</span>";
        uploadRow.html(uploadRowArray);
        $(".input-upload-" + i).children().addClass("upload-element m-x-10");
        appendRequired(input, i);
        drawThumbnail(i);
        addInputListener(i);
    }
    printUploadFooter(uploadMaxSize);
}

// Get input max pixels.
function getMaxPixels(input) {
    if (!input.max_pixels) {
        return "";
    } else {
        return "&le; " + input.max_pixels + " pixels. ";
    }
}

// Get input max weight.
function getMaxWeight(weight) {
    if (!weight) {
        return "";
    } else {
        return "&le; " + weight +" Mb";
    }
}

// Add required or optional to input.
function appendRequired(input, index) {
    var required = $(".upload-resolution-" + index);
    if (input.required || typeof(input.required) == 'undefined') {
        required.append(document.createTextNode(" (Required)"));
    } else if (!input.required) {
        required.append(document.createTextNode(" (Optional)"));
    }
}

// Add event to upload files.
function addInputListener(index) {
    var input = document.getElementById("file-" + index);
    input.addEventListener('change', function() {
        var demoInfo = helpers.getFromStorage("demoInfo");
        var inputs = demoInfo.inputs;
        upload = $("#file-" + index);
        var file = upload[0].files[0];
        var fileReader = new FileReader();
        if (file) {
            blob = new Blob([file], {type: file.type});
            // onload needed since Google Chrome doesn't support addEventListener for FileReader
            fileReader.onload = function (evt) {
                helpers.addToStorage(inputs[index].description, evt.target.result);
            };
            fileReader.readAsDataURL(blob);
        }
    });
}

// Check if all required inputs are uploaded before continue.
function checkRequiredInputs() {
    var demoInfo = helpers.getFromStorage("demoInfo");
    var inputs = demoInfo.inputs;
    var upload;
    for (var i = 0; i < inputs.length; i++) {
        upload = $("#file-" + i);
        var file = upload[0].files[0];
        if ((inputs[i].required || typeof(inputs[i].required) == 'undefined') && !file) {
            alert("Please upload all required files.");
            return false;
        }
    }
    return true;
}

// Draw thumbnail after upload.
function drawThumbnail(index) {
    document.getElementById("file-" + index).addEventListener("change", readFile, false);
}

// Add src to image.
function readFile(data) {
    var id = data.target.id;
    var file = id.split("-");
    var id = "img-" + file[1];
    if (this.files && this.files[0]) {
        var FR= new FileReader();
        FR.addEventListener("load", function(e) {
            document.getElementById(id).style.display = "inline";
            document.getElementById(id).src       = e.target.result;
        });
        FR.readAsDataURL( this.files[0] );
    }
}

// Print upload dialog footer.
function printUploadFooter(size) {
    var uploadDialog = $(".upload-dialog");
    uploadDialog.append("<p>Upload size is limited to <b>" + size + "MB</b> for the whole upload set.</p>");
    uploadDialog.append("<p>The uploaded will be publicly archived unless you switch to private mode on the result page.</p>");
    uploadDialog.append("<p>Only upload <a href=\"https://tools.ipol.im/wiki/ref/demo_input/\">suitable images</a>. See the <a href=\"https://tools.ipol.im/wiki/ref/demo_input/\">copyright and legal conditions</a> for details.</p>");
}

// Clear inputs.
function clearUploads() {
    var demoInfo = helpers.getFromStorage("demoInfo");
    var inputs = demoInfo.inputs;
    var imgElement;
    for (var i = 0; i < inputs.length; i++) {
        imgElement = $("#img-" + i);
        imgElement.attr("src", "#");
        imgElement.css("display", "none");
        $("#file-" + i).val("");
        helpers.removeItem(inputs[i].description);
    }
    helpers.removeItem("origin");
}
