var zoomController = zoomController || {};

// Single blob zoom with cropper
zoomController.singleBlob = function() {
  $("#editor-zoom").on('input' ,function() {
    let zoomValue = $(this).val();
    var $img = $("#editor-blob-left");
    $img.cropper('zoomTo', zoomValue);
    $("#editor-zoom-value").html(zoomValue + "x");
  });
}

// Zoom controller for multime blob sets
zoomController.multiBlob = function() {
  $("#editor-zoom").on('input', function() {
    zoomController.changeImageZoom("left");
    zoomController.changeImageZoom("right");
  });
}

// Change zoom value for editor images
zoomController.changeImageZoom = function(side) {
  var zoomValue = $("#editor-zoom").val();
  var element = $("#editor-blob-" + side);
  $("#editor-zoom-value").html(zoomValue + "x");  
  if (element[0].naturalHeight || element[0].naturalWidth) {
    sideWidth = element[0].naturalWidth * zoomValue;
    sideHeight = element[0].naturalHeight * zoomValue;
    $("#editor-blob-" + side).css({'width': sideWidth, 'height' : sideHeight});
  }
}
