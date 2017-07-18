var zoomController = zoomController || {};

// Single blob zoom with cropper
zoomController.singleBlob = function() {
  $(".zoom-select").change(function() {
    var $img = $("#editor-blob-left");
    var zoomValue = $(".zoom-select").val() || 1;
    $img.cropper('zoomTo', zoomValue);
  });
}

// Zoom controller for multime blob sets
zoomController.multiBlob = function() {
  $(".zoom-select").change(function() {
    zoomController.changeImageZoom("left");
    zoomController.changeImageZoom("right");
  });
}

// Change zoom value for editor images
zoomController.changeImageZoom = function(side) {
  var zoomValue = $(".zoom-select").val();
  var element = $("#editor-blob-" + side);
  if (element[0].naturalHeight || element[0].naturalWidth) {
    sideWidth = element[0].naturalWidth * zoomValue;
    sideHeight = element[0].naturalHeight * zoomValue;
    $("#editor-blob-" + side).css({'width': sideWidth, 'height' : sideHeight});
  }
}
