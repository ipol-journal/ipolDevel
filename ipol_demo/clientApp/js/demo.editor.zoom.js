var zoomController = zoomController || {};

// Single blob zoom with cropper
zoomController.singleBlob = function() {
  $("#editor-zoom").on('change input' ,function() {
    let zoomValue = $(this).val();
    let selector = "#canvas-container > canvas, .blobEditorImage, .cropper-container img";
    helpers.checkInterpolation(zoomValue, selector);

    var $img = $("#editor-blob-left");

    if (ddl.inputs[0].type == "image") $img.cropper('zoomTo', zoomValue)
    else zoomController.changeImageZoom("left")

    $("#editor-zoom-value").html(zoomValue + "x");
    if ($("#crop-btn").prop('checked')) {
      let croppedImage = $("#left-container > img").cropper('getCroppedCanvas');
      $("#canvas-container").html($(croppedImage));
    }
  });
}

// Zoom controller for multiple blob sets
zoomController.multiBlob = function() {
  $("#editor-zoom").on('change input', function() {
    zoomController.changeImageZoom("left");
    zoomController.changeImageZoom("right");
  });
}

zoomController.inpaintingBlob = () => {
  $("#zoom-container").removeClass("di-none");
  $("#editor-zoom").on('change input', function () {
    let zoomValue = $("#editor-zoom").val();
    let selector = "#canvas-container > canvas, .blobEditorImage";
    helpers.checkInterpolation(zoomValue, selector);

    let element = $("#editor-blob-left");
    $("#editor-zoom-value").html(zoomValue + "x");
    if (element[0].height || element[0].width) {
      sideWidth = element[0].width * zoomValue;
      sideHeight = element[0].height * zoomValue;
      $("#editor-blob-left").css({ 'width': sideWidth, 'height': sideHeight });
    }
  });
}
// Change zoom value for editor images
zoomController.changeImageZoom = function(side) {
  var zoomValue = $("#editor-zoom").val();
  let selector = "#canvas-container > canvas, .blobEditorImage";
  helpers.checkInterpolation(zoomValue, selector);
    
  var element = $("#editor-blob-" + side);
  $("#editor-zoom-value").html(zoomValue + "x");
  if (element[0].naturalHeight || element[0].naturalWidth) {
    sideWidth = element[0].naturalWidth * zoomValue;
    sideHeight = element[0].naturalHeight * zoomValue;
    $("#editor-blob-" + side).css({'width': sideWidth, 'height' : sideHeight});
  }
}
