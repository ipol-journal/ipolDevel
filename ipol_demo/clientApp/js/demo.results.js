var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var results = clientApp.results || {};

var ddl_results, work_url, info;

results.draw = function (run_response) {
  var ddl = helpers.getFromStorage('demoInfo');
  ddl_results = ddl.results;
  work_url = run_response.work_url;
  info = run_response.algo_info;

  $('.results').removeClass('di-none');
  $('.results-container').empty();

  for (let i = 0; i < ddl_results.length; i++) {
    var functionName = $.fn[ddl_results[i].type];
    if ($.isFunction(functionName)) printResult(ddl_results[i], i);
    else console.error(ddl_results[i].type + ' result type is not defined');
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

$.fn.gallery = function (result, index) {
  var contentKeys = Object.keys(result.contents);

  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = "gallery_" + index;
  $(this).append("<div class=" + gallerySelector + "></div>");
  $(this).append("<div class=gallery-" + index + "-zoom-container></div>");
  $("." + gallerySelector).addClass("gallery-container");

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  $("." + gallerySelector).append("<div class=" + leftItems + "></div>");

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append("<div class=" + blobsContainerSelector + "></div>");
  $("." + blobsContainerSelector).addClass("blobs-wrapper");

  $("." + gallerySelector).append("<div class=" + rightItems + "></div>");
  $("." + rightItems).addClass("di-none");
  $("." + leftItems).append("<div id=left-blobs-gallery-" + index + "></div>");
  $("." + rightItems).append("<div id=right-blobs-gallery-" + index + "></div>");
  $("#" + "left-blobs-gallery-" + index).addClass("gallery-item-list");
  $("#" + "right-blobs-gallery-" + index).addClass("gallery-item-list");

  var imgContainerLeft = "gallery-blob-container-left-" + index;
  var imgContainerRight = "gallery-blob-container-right-" + index;
  $("." + blobsContainerSelector).append("<div id=" + imgContainerLeft + "></div>");
  $("." + blobsContainerSelector).append("<div id=" + imgContainerRight + "></div>");
  $("#" + imgContainerLeft).addClass("gallery-blob-container");
  $("#" + imgContainerRight).addClass("gallery-blob-container di-none");

  // Evaluate key conditional.
  helpers.removeItem("gallery-" + index + "-left");
  for (let i = 0; i < contentKeys.length; i++) {
    var evalString = "";
    var value = "";
    if (contentKeys[i].indexOf('?') != -1) {
      evalString = contentKeys[i].split('?')[0];
      value = contentKeys[i].split('?')[1];
    } else if (contentKeys[i].indexOf('?') == -1 && contentKeys[i].indexOf('\'') != -1) {
      value = eval(contentKeys[i]);
      evalString = true;
    } else {
      value = contentKeys[i];
      evalString = true;
    }
    if (eval(evalString)) {
      if (value.indexOf('+') != -1) {
        let first = value.split('+')[0];
        let second = value.split('+')[1];
        value = eval(first) +" "+ eval(second);
      } else {
        value = eval("\"" + value + "\"");
      }
      $("#" + "left-blobs-gallery-" + index).append("<span id=gallery-" + index + "-item-left-" + i + " class=gallery-item-selector>" + value + "</span>");
      $("#" + "right-blobs-gallery-" + index).append("<span id=gallery-" + index + "-item-right-" + i + " class=gallery-item-selector>" + value + "</span>");
      var src = result.contents[contentKeys[i]];
      if (typeof src == "string") src = [src];
      $("#gallery-" + index + "-item-left-" + i).addHoverEvents(index, 'left', work_url, Object.keys(src).map(function(e) {
      return src[e];
      }));
      $("#gallery-" + index + "-item-right-" + i).addHoverEvents(index, 'right', work_url, Object.keys(src).map(function(e) {
      return src[e];
      }));
      if ($("#" + "left-blobs-gallery-" + index).children().length > 0 && !helpers.getFromStorage("gallery-" + index + "-left")) {
        let sources = [];
        var keys = Object.keys(src);
        if (typeof src == "object") {
          sources = Object.keys(src).map(function(e) {
            return src[e];
          });
          for (var l = 0; l < sources.length; l++) {
            sources[l] = work_url + sources[l];
          }
        } else if (typeof src == "array") {
          for (var k = 0; k < src.length; k++) {
            sources.push(work_url + src[k]);
          }
        }
        helpers.addToStorage("gallery-" + index + "-left", sources);
        helpers.addToStorage("gallery-" + index + "-right", sources);
      }

      $("." + gallerySelector).setGalleryMinHeight(work_url, src);

      if ($("#" + imgContainerLeft).children().length <= 0) {
        var content = result.contents[contentKeys[0]];
        var type = typeof (content);
        if (type != "string") {
          var keys = Object.keys(content);
          for (let j = 0; j < keys.length; j++) {
            $("#" + imgContainerLeft).append("<img src=" + work_url + content[keys[j]] + " class=gallery-img draggable=false></img>");
            $("#" + imgContainerRight).append("<img src=" + work_url + content[keys[j]] + " class=gallery-img draggable=false></img>");
            $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-flex");
          }
        } else {
          $("#" + imgContainerLeft).append("<img src=" + work_url + result.contents[contentKeys[i]] + " class=gallery-img draggable=false></img>");
          $("#" + imgContainerRight).append("<img src=" + work_url + result.contents[contentKeys[i]] + " class=gallery-img draggable=false></img>");
          $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-inline");
        }
      }
    }
  }

  $("#left-blobs-gallery-" + index).addClass('blobsList');
  $("#right-blobs-gallery-" + index).addClass('blobsList');
  
  $("#left-blobs-gallery-"+index).addMouseOutEvent(index, 'left');
  $("#right-blobs-gallery-" + index).addMouseOutEvent(index, 'right');
  $("." + leftItems + " span:first-child").addClass("gallery-item-selected");
  $("." + rightItems + " span:first-child").addClass("gallery-item-selected");
  
  $("#" + imgContainerLeft + " > img").addClass('gallery-' + index + '-blob-left');
  $("#" + imgContainerRight + " > img").addClass('gallery-' + index + '-blob-right');
  
  $(".gallery-" + index + "-zoom-container").appendZoom(index, leftItems);
  if ($("#left-blobs-gallery-" +index).children().length > 1) $("." + leftItems).appendCompare(index, rightItems, imgContainerRight);
  
  checkOptions(result.type, index);
}

// Set gallery min-height to avoid jump loops.
$.fn.setGalleryMinHeight = function(work_url, src) {
  var minHeight;
  var selector = $(this);
  if (!Array.isArray(src)) {
    src = Object.keys(src).map(function(e) {
      return src[e];
    });
  }
  for (let i = 0; i < src.length; i++) {
    let tmpImg = new Image();
    tmpImg.src = work_url + src[i];
    $(tmpImg).on("load", function() {
      minHeight = parseInt(selector.css("min-height"));
      if (minHeight < tmpImg.height) {
        minHeight = tmpImg.height < 580 ? tmpImg.height : 580;
        selector.css({ minHeight: minHeight + 20 + "px" });
      }
    });
  }
};

$.fn.appendCompare = function (galleryIndex, rightItems, imgContainerRight) {
  $(this).append("<div class=p-y-10><input type=checkbox id=compare-btn-gallery-" + galleryIndex + "><label for=compare-btn-gallery-" + galleryIndex + ">Compare</label></div>");
  $("#compare-btn-gallery-" + galleryIndex).on('click', function () {
    if ($(this).is(":checked")) {
      $("#gallery-blob-container-left-" + galleryIndex).css({ "flex-basis": "50%" });
      $("#gallery-blob-container-right-" + galleryIndex).css({ "flex-basis": "50%" });
      $(".gallery-blobs-container-" + galleryIndex).addClass('blobs-wrapper-compare');
      
    } else {
      $("#gallery-blob-container-left-" + galleryIndex).css({ "flex-basis": "" });
      $("#gallery-blob-container-right-" + galleryIndex).css({ "flex-basis": "" });
      $(".gallery-blobs-container-" + galleryIndex).removeClass("blobs-wrapper-compare");
    }
    $("#" + imgContainerRight).toggleClass("di-none");
    $(".gallery_" + galleryIndex).toggleClass("space-between");
    $("." + rightItems).toggleClass("di-none");
  });
}

$.fn.appendLabel = function(labelArray) {
  var html = "";
  for (var i = 0; i < labelArray.length; i++) html += labelArray[i];
  if (html.charAt(0) == "'") html = eval(html);

  $(this).html("<div class=m-b-20>" + html + "</div>");
};

// Add event listeners for gallery images lists
$.fn.addHoverEvents = function (galleryIndex, side, work_url, src) {
  var imgSelector = '.gallery-' + galleryIndex + '-blob-' + side;
  var selector = '#gallery-blob-container-' + side + '-' + galleryIndex;
  $(this).mouseover(function () {
    var keys = Object.keys(src);
    var nImagesInDOM = $(selector).children().length;
    for (var i = 0; i < src.length; i++) {
      if (i < nImagesInDOM) {
        $(selector + " > img:nth-child(" +(i + 1)+ ")").attr("src", work_url + src[keys[i]]);
        $(selector + " > img:nth-child(" +(i + 1)+ ")").on('load', function () {
          $("#gallery-" + galleryIndex + "-zoom > input").updateSize(galleryIndex, side);
        });
      } else {
        var elm = "<img src=" + work_url + src[keys[i]] + " class=gallery-img draggable=false></img>";
        $(elm).appendTo(selector);
        $(elm).on('load', function () {
          if(i == src.length) $("#gallery-" + galleryIndex + "-zoom > input").updateSize(galleryIndex, side);
        });
      }
    }
    for (var i = nImagesInDOM; i >= src.length; i--) {
      if (i > src.length) {
        $(selector + " > img:nth-child(" + i + ")").remove();
      }
    }
    $(selector).children().addClass("gallery-"+galleryIndex+"-blob-"+side);
  });
  $(this).on('click', function () {
    var listSelector = "#" + side + "-blobs-gallery-" + galleryIndex;
    $(listSelector + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    let saveSrc = [];
    $(imgSelector).each(function () {
      saveSrc.push($(this).attr("src"));
    });
    helpers.addToStorage("gallery-"+galleryIndex+"-"+side, saveSrc);
  });
}

$.fn.addMouseOutEvent = function(galleryIndex, side) {
  var selector = '#gallery-blob-container-' + side + '-' + galleryIndex;
  $(this).mouseout(function (event) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }

    var src = helpers.getFromStorage("gallery-"+galleryIndex+ "-" + side);
    $(selector).empty();
    for (var i = 0; i < src.length; i++) {
      var img = "<img src=" + src[i] + " class=gallery-img draggable=false></img>";
      $(img).appendTo(selector);
      $(img).on('load', function () {
        if (i >= src.length) $("#gallery-" + galleryIndex + "-zoom > input").updateSize(galleryIndex, side);
      });
    }
    
    var zoomValue = $("#gallery-" + galleryIndex + "-zoom > #editor-zoom").val();
    helpers.checkInterpolation(zoomValue, '.gallery_' + galleryIndex + ' img');
    
    $(selector).children().addClass("gallery-" + galleryIndex + "-blob-" + side);
  });
}

$.fn.updateSize = function (index, side)  {
  var zoomLevel = $(this).val();
  $("#gallery-blob-container-" + side + "-" + index).children('img').each(function (i) {
    $(this).height($(this)[0].naturalHeight * zoomLevel);
    $(this).width($(this)[0].naturalWidth * zoomLevel);
  });
}

$.fn.file_download = function (result, index) {
  if (result.repeat) {
    $(this).append('<div class=file_download_content_' + index + ' ></div>');
    for (let idx = 0; idx < eval(result.repeat); idx++) {
      var file = eval(result.contents);
      $('.file_download_content_' + index).append('<div class=download_' + index + '_' + idx + ' ></div>');
      $('.download_' + index + '_' + idx).addClass('file_download');
      $('.download_' + index + '_' + idx).append('<a href=' + work_url + file + ' download><img src=./assets/file.svg class=file-icon >' + eval(result.label) + '</a>')
    }
  } else {
    $(this).append('<h4>' + result.label + '</h4>');
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

$.fn.text_file = function (result, index) {
  var request = new XMLHttpRequest();
  request.open('GET', work_url + result.contents, true);
  request.responseType = 'blob';
  request.onload = function () {
    var reader = new FileReader();
    reader.readAsText(request.response);
    reader.onload = function (e) {
      $('.result_' + index).append('<h3>' + result.label + '</h3>');
      $('.result_' + index).append('<pre class=text_file_content id=text_file_' + index + ' >' + e.target.result + '</pre>');
      if (result.style) $('#text_file_' + index).css(result.style);
    };
  };
  request.send();
}

$.fn.html_text = function (result, index) {
  var text = '';
  var html_text = '';
  
  var content = []; 
  if (!Array.isArray(result.contents)) content.push(result.contents);
  else content = result.contents;
  
  for (let i = 0; i < content.length; i++)
  text += content[i];
  
  try {
    html_text = eval(text);
  } catch (e) {
    html_text = text;
  }
  
  $(this).append("<div class=html_text_" + index + " ></div>");
  $('.html_text_' + index).html(html_text);
}

$.fn.message = function (result, index) {
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
