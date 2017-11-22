var helpers = clientApp.helpers || {};

$.fn.gallery_new = function(result, index)  {
  if (result.visible) {
    var visible = eval(result.visible);
    if (!visible) return;
  }

  var contentKeys = Object.keys(result.contents);

  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = "gallery-" + index;
  $(this).append('<div class="' + gallerySelector + ' gallery-container" ></div>');

  var blobsArray = getGalleryImages(result.contents, work_url);

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  renderGalleryBlobList(index, contentKeys, result, leftItems, 'left', blobsArray);

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append('<div class="' + blobsContainerSelector + ' blobs-wrapper"></div>');

  renderGalleryBlobList(index, contentKeys, result, rightItems, 'right', blobsArray);
  $("." + rightItems).addClass("gallery-item-list-right di-none");

  var imgContainerLeft = "gallery-blob-container-left-" + index;
  var imgContainerRight = "gallery-blob-container-right-" + index;
  $("." + blobsContainerSelector).append('<div id="'+ imgContainerLeft +'" class=gallery-blob-container></div>');
  $("." + blobsContainerSelector).append('<div id="'+ imgContainerRight +'" class="gallery-blob-container di-none"></div>');

  var firstVisibleBlobSet = blobsArray[0];
  for (var i = 0; i < firstVisibleBlobSet.length; i++) {
    $("#" + imgContainerRight).append(firstVisibleBlobSet[i].clone());
    $("#" + imgContainerLeft).append(firstVisibleBlobSet[i].clone());
  }
  
  var allSrc = getAllSrc(blobsArray);
  $("." + gallerySelector).setGalleryMinHeight(allSrc);
  $(this).append("<div id=gallery-" + index + "-zoom-container></div>");
  $("#gallery-" + index + "-zoom-container").appendZoom(index, leftItems);
  if (blobsArray.length > 1) $("." + leftItems).appendCompare(index, rightItems, imgContainerRight);
}

function getGalleryImages(contentArray, work_url) {
  var allSrc = [];
  var keys = Object.keys(contentArray);
  for (var i = 0; i < keys.length; i++) {
    var blobSetContent = contentArray[keys[i]];
    var visibleField = blobSetContent.hasOwnProperty('visible');
    if (!visibleField || (visibleField && eval(blobSetContent.visible))) {
      var imgField = blobSetContent.img;
      var repeat = blobSetContent.repeat !== undefined ? checkRepeat(blobSetContent.repeat) : 1;
      var blobs = [];
      for (var idx = 0; idx < repeat; idx++) {
        blobs = [];
        if (typeof(imgField) === 'string') {
          var img = '<img src=' + work_url + (imgField.indexOf("'") == -1 ? imgField : eval(imgField)) + ' class=gallery-img draggable=false></img>';
          blobs.push($(img));
        } else if (typeof (imgField) === 'object') {
          for (var k = 0; k < imgField.length; k++) {
            var img = '<img src=' + work_url + (imgField[k].indexOf("'") == -1 ? imgField[k] : eval(imgField[k])) + ' class=gallery-img draggable=false></img>';
            blobs.push($(img));
          }
        }
        allSrc.push(blobs);
      }
    }
  }
  return allSrc;
}

function getAllSrc(blobsArray) {
  let allSrc = [];
  for (var i = 0; i < blobsArray.length; i++) {
    for (var j = 0; j < blobsArray[i].length; j++) {
      allSrc.push(blobsArray[i][j].attr('src'));
    }
  }
  return allSrc;
}

function checkRepeat(expression) {
  if (expression.indexOf('+') === -1) return parseInt(eval(expression));
  var expressionArray = expression.split('+');
  var repeat = 0;
  for (var i = 0; i < expressionArray.length; i++) {
    repeat += parseInt(eval(expressionArray[i]));
  }
  return repeat;
}

function renderGalleryBlobList(index, contentKeys, result, itemSelector, side, blobsArray) {
  $(".gallery-" + index).append('<div class="' + itemSelector + '"></div>');
  $("." + itemSelector).append('<div id=gallery-' + index + '-blobList-' + side + ' class="gallery-blobList-left gallery-item-list"></div>');
  var contents = result.contents;
  var firstVisibleBlob = true;
  var itemIndex = 0;
  for (let i = 0; i < contentKeys.length; i++) {
    var visibleField = contents[contentKeys[i]].hasOwnProperty('visible');
    if (!visibleField || (visibleField && eval(contents[contentKeys[i]].visible))) {
      var content = result.contents[contentKeys[i]].img;
      if (typeof(content) === 'string') {
        content = [content];
      }
      if (firstVisibleBlob) {
        helpers.addToStorage('gallery-' + index + '-' + side, itemIndex);
        firstVisibleBlob = false;
      }
      var line = contents[contentKeys[i]];
      var repeat = line.repeat != undefined ? checkRepeat(line.repeat) : 1;
      for (var idx = 0; idx < repeat; idx++) {
        var text = getEvalText(contentKeys[i]);
        var spanId = 'gallery-' + index + '-item-' + side +'-'+ i + '-' + idx;
        $('#gallery-'+index+'-blobList-'+side).append('<span id=' +spanId+ ' class=gallery-item-selector>' + eval(text) + '</span>');
        $('#' + spanId).addHoverFeatures(index, side, blobsArray[itemIndex], itemIndex);
        itemIndex++;
      }
    }
  }
  $(this).addMouseOut(index, side, blobsArray);
  $("." +itemSelector+ " span:first-child").addClass("gallery-item-selected");
}

$.fn.addMouseOut = function (galleryIndex, side, blobsArray) {
  var selector = '#gallery-blob-container-' + side + '-' + galleryIndex;
  $("#gallery-" + galleryIndex + "-blobList-" + side).mouseout(function (event) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }
    var selectedSrc = helpers.getFromStorage("gallery-" + galleryIndex + "-" + side);
    $(selector).empty();
    var blobs = blobsArray[selectedSrc];
    for (var i = 0; i < blobs.length; i++) {
      $(selector).append(blobs[i].clone());
    }
    $("#gallery-" + galleryIndex + "-zoom > input").adjustSize(galleryIndex);
    $(selector + " > img").addClass('gallery-' + galleryIndex + '-blob-' + side);
    setInterpolation(galleryIndex);
  });
}

function getEvalText(str) {
  if (str.indexOf('+') != -1) {
    return str;
  } else {
    return "\'"+str+"\'";
  }
}

$.fn.addHoverFeatures = function(galleryIndex, side, src, itemIndex) {
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '#gallery-blob-container-' +side+ '-' + galleryIndex;
  $(this).mouseover(function() {
    $(selector).empty();
    for (var i = 0; i < src.length; i++) {
      $(selector).append($(src[i]));
    }
    $(selector + " > img").addClass('gallery-' +galleryIndex+ '-blob-'+side);
    var zoomValue = $("#gallery-" + galleryIndex + "-zoom > #editor-zoom").val();
    $("#gallery-" + galleryIndex + "-zoom > input").adjustSize(galleryIndex);
    setInterpolation(galleryIndex);
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $("#gallery-" + galleryIndex + "-blobList-" + side + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    helpers.addToStorage("gallery-" +galleryIndex + "-" + side, itemIndex);
  });
}

function setInterpolation(galleryIndex) {
  var zoomValue = $("#gallery-" + galleryIndex + "-zoom > #editor-zoom").val();
  helpers.checkInterpolation(zoomValue, ".gallery-" + galleryIndex + " img");
}

$.fn.appendZoom = function(index, leftItems) {
  var zoom = $("#zoom-container").clone();
  zoom.find('input').val('1.0');
  zoom.find('span').html('1x');
  var newZoomID= "gallery-" +index+ "-zoom";
  zoom.attr("id", newZoomID).appendTo($(this));
  zoom.removeClass("di-none");
  $("#" + newZoomID + " > .zoom-info > #editor-image-size").remove();
  $("#" + newZoomID + " > input").on('input', function() {
    var zoomLevel = $(this).val();
    let selector = ".gallery-" + index + " img";
    helpers.checkInterpolation(zoomLevel, selector);
    $(".gallery-" + index).css({ height: (parseInt($(".gallery-" + index).css('min-height')) || parseInt($(".gallery-" + index).css('height'))) * zoomLevel + "px" });
    $(this).adjustSize(index);
    $("#" + newZoomID + " > .zoom-info > #editor-zoom-value").html(zoomLevel + "x");
  });
  scrollSync(index);
}

$.fn.adjustSize = function(index) {
  var zoomLevel = $(this).val();
  $("#gallery-blob-container-left-"+index + ", #gallery-blob-container-right-"+index).children('img').each(function(i){
    if ($(this)[0].naturalHeight != 0 || $(this)[0].naturalWidth != 0) {
      $(this).height($(this)[0].naturalHeight * zoomLevel);
      $(this).width($(this)[0].naturalWidth * zoomLevel);
    }
  });
}

function scrollSync(index) {
  var isSyncingLeftScroll = false;
  var isSyncingRightScroll = false;
  var leftDiv = document.getElementById('gallery-blob-container-left-' + index);
  var rightDiv = document.getElementById('gallery-blob-container-right-' + index);
  $('#gallery-blob-container-left-' + index).attachDragger();
  $('#gallery-blob-container-right-' + index).attachDragger();

  leftDiv.onscroll = function() {
    if (!isSyncingLeftScroll) {
      isSyncingRightScroll = true;
      rightDiv.scrollTop = this.scrollTop;
      rightDiv.scrollLeft = this.scrollLeft;
    }
    isSyncingLeftScroll = false;
  }
  rightDiv.onscroll = function() {
    if (!isSyncingRightScroll) {
      isSyncingLeftScroll = true;
      leftDiv.scrollTop = this.scrollTop;
      leftDiv.scrollLeft = this.scrollLeft;
    }
    isSyncingRightScroll = false;
  }
}