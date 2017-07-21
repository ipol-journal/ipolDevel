var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var results = clientApp.results ||  {};

var ddl_results, work_url, info;

results.draw = function(run_response)  {
  var ddl = helpers.getFromStorage('demoInfo');
  ddl_results = ddl.results;
  work_url = run_response.work_url;
  info = run_response.algo_info;

  $('.results').removeClass('di-none');
  $('.results-container').empty();

  for (let i = 0; i < ddl_results.length; i++) {
    var functionName = $.fn[ddl_results[i].type];
    if ($.isFunction(functionName)) printResult(ddl_results[i], i);
    // else console.error(ddl_results[i].type + ' result type is not defined');
  }
}

function printResult(result, index) {
  if (!isVisible(result)) return;

  $('<div class=result_' + index + ' ></div>').appendTo($('.results-container'));
  $('.result_' + index)[result.type](result, index);
}

function isVisible(result) {
  return result.visible ? eval(result.visible) : true;
}

$.fn.gallery = function(result, index)  {
  var contentKeys = Object.keys(result.contents);

  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = "gallery_" + index;
  $(this).append("<div class=" + gallerySelector + " ></div>");
  $("." + gallerySelector).addClass("gallery-container");

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  $("." + gallerySelector).append("<div class=" + leftItems + "></div>");
  $("." + leftItems).addClass("gallery-item-list");

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append("<div class=" + blobsContainerSelector + "></div>");
  $("." + blobsContainerSelector).addClass("blobs-wrapper");

  $("." + gallerySelector).append("<div class=" + rightItems + "></div>");
  $("." + rightItems).addClass("gallery-item-list di-none");

  // Evaluate key conditional.
  for (let i = 0; i < contentKeys.length; i++) {
    $("." + leftItems).append("<span id=gallery-" +index+ "-item-left-" +i+ " class=gallery-item-selector>" + contentKeys[i] + "</span>");
    $("." + rightItems).append("<span id=gallery-" +index+ "-item-right-" +i+ " class=gallery-item-selector>" + contentKeys[i] + "</span>");
    var src = result.contents[contentKeys[i]];
    if (typeof(src) == "string") src = {0: src};
    console.log(typeof(src));
    if (typeof(src) == "array") src = {0: src};

    $("#gallery-" +index+ "-item-left-" +i).addHoverEvents(index, 'left', work_url, src);
    $("#gallery-" +index+ "-item-right-" +i).addHoverEvents(index, 'right', work_url, src);
  }
  $("." +leftItems+ " span:first-child").addClass("gallery-item-selected");
  $("." +rightItems+ " span:first-child").addClass("gallery-item-selected");

  var imgContainerLeft = "gallery-blob-container-left-" + index;
  var imgContainerRight = "gallery-blob-container-right-" + index;
  $("." + blobsContainerSelector).append("<div id=" +imgContainerLeft+ "></div>");
  $("." + blobsContainerSelector).append("<div id=" +imgContainerRight+ "></div>");
  $("#" + imgContainerLeft).addClass("gallery-blob-container");
  $("#" + imgContainerRight).addClass("gallery-blob-container di-none");

  var content = result.contents[contentKeys[0]];
  var type = typeof(content);
  if (type != "string") {
    var obj = result.contents[contentKeys[0]];
    var keys = Object.keys(obj);
    for (var i = 0; i < keys.length; i++) {
      $("#" + imgContainerLeft).append('<img src=' + work_url + obj[keys[i]] + ' class=gallery-img draggable=false></img>');
      $("#" + imgContainerRight).append('<img src=' + work_url + obj[keys[i]] + ' class=gallery-img draggable=false></img>');
      $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-flex");
    }
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right');
  } else {
    $("#" + imgContainerLeft).append('<img src=' + work_url + result.contents[contentKeys[0]] + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerRight).append('<img src=' + work_url + result.contents[contentKeys[0]] + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right');
    $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-inline");
  }

  $("." + leftItems).appendZoom(index, leftItems);
  $("." + leftItems).appendGalleryControlls(index, rightItems, imgContainerRight);

  checkOptions(result.type, index);
}

$.fn.appendGalleryControlls = function(galleryIndex, rightItems, imgContainerRight) {
  $(this).append("<div><input type=checkbox id=compare-btn-gallery-" +galleryIndex+ "><label for=compare-btn-gallery-" +galleryIndex+ ">Compare</label></div>");
  $("#compare-btn-gallery-" + galleryIndex).on('click', function() {
    if ($(this).is(":checked")) {
      $(".gallery-blob-container-left-" + galleryIndex).css({"flex-basis": "50%"});
      $(".gallery-blob-container-right-" + galleryIndex).css({"flex-basis": "50%"});
    } else {
      $(".gallery-blob-container-left-" + galleryIndex).css({"flex-basis": ""});
      $(".gallery-blob-container-right-" + galleryIndex).css({"flex-basis": ""});
    }
    $("#" + imgContainerRight).toggleClass("di-none");
    $(".gallery_" + galleryIndex).toggleClass("space-between");
    $("." + rightItems).toggleClass("di-none");
  });
}

$.fn.appendLabel = function(labelArray) {
  var html = [""];
  for (var i = 0; i < labelArray.length; i++) {
    html += labelArray[i];
  }
  $(this).append(html);
}

// Add event listeners for gallery images lists
$.fn.addHoverEvents = function(galleryIndex, side, work_url, src) {
  var originalSrc = "";
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '.gallery-blob-container-' +side+ '-' + galleryIndex;
  var originalSrc = [];
  $(this).mouseover(function() {
    $(imgSelector).each(function(){
      originalSrc.push($(this).attr("src"));
    });
    var keys = Object.keys(src);
    $(imgSelector).each(function(i) {
      console.log(src[keys[i]]);
      $(this).attr("src", work_url + src[keys[i]]);
      $("#gallery-" +galleryIndex+ "-zoom > select").updateSize(galleryIndex);
    });
  });
  $(this).mouseout(function() {
    $(imgSelector).each(function(i){
      $(this).attr("src", originalSrc[i]);
      $("#gallery-" +galleryIndex+ "-zoom > select").updateSize(galleryIndex);
    });
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $(listSelector + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    originalSrc = [];
    $(imgSelector).each(function(){
      originalSrc.push($(this).attr("src"));
    });
  });
}

$.fn.appendZoom = function(index, leftItems) {
  var zoom = $("#zoom-container").clone();
  var newZoomID= "gallery-" +index+ "-zoom";
  zoom.attr("id", newZoomID).appendTo("." + leftItems);
  $("#" + newZoomID + " > select").addZoomEvents(index);
  synqScroll(index);
}

$.fn.addZoomEvents = function(index){
  $(this).on('change', function() {
    var zoomLevel = $(this).val();
    $("#gallery-blob-container-left-"+index + ", #gallery-blob-container-right-"+index).children('img').each(function(i){
      $(this).height($(this)[0].naturalHeight * zoomLevel);
      $(this).width($(this)[0].naturalWidth * zoomLevel);
    });
  });
}

$.fn.updateSize = function(index) {
  var zoomLevel = $(this).val();
  $("#gallery-blob-container-left-"+index + ", #gallery-blob-container-right-"+index).children('img').each(function(i){
    $(this).height($(this)[0].naturalHeight * zoomLevel);
    $(this).width($(this)[0].naturalWidth * zoomLevel);
  });
}

function synqScroll(index) {
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

$.fn.file_download = function(result, index) {
  if (result.repeat) {
    $(this).append('<div class=file_download_content_' + index + ' ></div>');
    for (let idx = 0; idx < eval(result.repeat); idx++) {
      var file = eval(result.contents);
      $('.file_download_content_' + index).append('<div class=download_' + index + '_' + idx + ' ></div>');
      $('.download_' + index + '_' + idx).addClass('file_download');
      $('.download_' + index + '_' + idx).append('<a href=' + work_url + file + ' download><img src=./assets/file.svg class=file-icon >' + eval(result.label) + '</a>')
    }
  } else {
    $(this).append('<h3>' + result.label + '</h3>');
    $(this).children().addClass('file_download_title');
    $(this).append('<div class=file_download_content_' + index + ' ></div>');

    if (typeof result.contents == "string") {
      $('.file_download_content_' + index).append('<div class=download_' + index + ' ></div>');
      $('.download_' + index).addClass('file_download');
      $('.download_' + index).append('<a href=' + work_url + result.contents + ' download><img src=./assets/file.svg class=file-icon >' + result.contents + '</a>')
    } else {
      var contentKeys = Object.keys(result.contents);
      for (let i = 0; i < contentKeys.length; i++) {
        $('.file_download_content_' + index).append('<div class=download_' + index + '_' + i + ' ></div>');
        $('.download_' + index + '_' + i).addClass('file_download');
        $('.download_' + index + '_' + i).append('<a href=' + work_url + result.contents[contentKeys[i]] + ' download><img src=./assets/file.svg class=file-icon >' + contentKeys[i] + '</a>')
      }
    }
  }
}

$.fn.text_file = function(result, index) {
  var request = new XMLHttpRequest();
  request.open('GET', work_url + result.contents, true);
  request.responseType = 'blob';
  request.onload = function() {
    var reader = new FileReader();
    reader.readAsText(request.response);
    reader.onload = function(e) {
      $('.result_' + index).append('<h3>' + result.label + '</h3>');
      $('.result_' + index).append('<pre class=text_file_content id=text_file_' + index + ' >' + e.target.result + '</pre>');
      if (result.style) $('#text_file_' + index).css(result.style);
    };
  };
  request.send();
}

$.fn.html_text = function(result, index) {
  $(this).append("<div class=html_text_" + index + " ></div>");
  var text = '';

  for (let i = 0; i < result.contents.length; i++)
    text += result.contents[i];

  if (text.charAt(0) == '\'') text = eval(text);
  else text = eval('\'' + text + '\'');

  $('.html_text_' + index).html(text);
}

$.fn.message = function(result, index) {
  $(this).append("<div class=message_" + index + " ></div>");
  $('.message_' + index).html(eval(result.contents));
  $('.message_' + index).addClass('result-msg-box');
  if (result.backgroundColor) $('.message_' + index).css({
    backgroundColor: result.backgroundColor
  });
  if (result.textColor) $('.message_' + index).css({
    color: result.textColor
  });
}

function checkOptions(resultType, index) {
  //Default values are 300 for both. check it.
  if (ddl_results[index].options) {
    if (ddl_results[index].options.minwidth)
      $('.' + resultType + "_" + index + " > img").css({
        minWidth: (ddl_results[index].options.minwidth.toString() + "px")
      });
    if (ddl_results[index].options.minheight)
      $('.' + resultType + "_" + index + " > img").css({
        minHeight: (ddl_results[index].options.minheight.toString() + "px")
      });
  }
}
