var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var results = clientApp.results ||  {};

var demoInfo, run_response, ddl_results, work_url, post_params;

results.draw = function(response)  {
  demoInfo = helpers.getFromStorage('demoInfo');
  run_response = response;
  ddl_results = demoInfo.results;
  work_url = run_response.work_url;
  post_params = run_response.params;

  $('.results').removeClass('di-none');
  $('.results-container').empty();

  for (let i = 0; i < ddl_results.length; i++) {
    var functionName = $.fn[ddl_results[i].type];
    if ($.isFunction(functionName)) printResult(ddl_results[i], i);
    // else console.error(ddl_results[i].type + ' result type is not defined');
  }
}

function printResult(result, index) {
  $('.results-container').append('<div class=result_' + index + ' ></div>');
  $('.result_' + index)[result.type](result, index);
}

$.fn.gallery = function(result, index)  {
  var contentKeys = Object.keys(result.contents);

  $(this).append(result.label);
  $(this).append("<div class=gallery_" + index + " ></div>");

  // Evaluate key conditional.
  for (let i = 0; i < contentKeys.length; i++) {
    $('.gallery_' + index).append('<img src=' + work_url + result.contents[contentKeys[i]] + '></img>');
  }

  checkOptions(result.type, index);
}

$.fn.file_download = function(result, index) {
  if (result.repeat) {
    var repeat = result.repeat;
    $(this).append('<div class=file_download_content_' + index + ' ></div>');
    for (let idx = 0; idx < repeat; idx++) {
      var content = eval(result.contents);

      $('.file_download_content_' + index).append('<div class=download_' + index + '_' + idx + ' ></div>');
      $('.download_' + index + '_' + idx).addClass('file_download');
      $('.download_' + index + '_' + idx).append('<a href=' + work_url + content + ' download><img src=./file.svg class=file-icon >' + eval(result.label) + '</a>')
    }
  } else {
    $(this).append(result.label);
    $(this).children().addClass('file_download_title');
    $(this).append('<div class=file_download_content_' + index + ' ></div>');

    var contentKeys = Object.keys(result.contents);
    for (let i = 0; i < contentKeys.length; i++) {
      $('.file_download_content_' + index).append('<div class=download_' + index + '_' + i + ' ></div>');
      $('.download_' + index + '_' + i).addClass('file_download');
      $('.download_' + index + '_' + i).append('<a href=' + work_url + result.contents[contentKeys[i]] + ' download><img src=./file.svg class=file-icon >' + contentKeys[i] + '</a>')
    }
  }
}

$.fn.html_text = function(result, index) {
  $(this).append("<div class=html_text_" + index + " ></div>");
  $('.html_text_' + index).append(result.contents);
}

function checkOptions(resultType, index) {
  //Default values are 300 for both. check it.
  if (ddl_results[index].options) {
    if (ddl_results[index].options.minwidth) $('.' + resultType + "_" + index + " > img").css({
      minWidth: (ddl_results[index].options.minwidth.toString() + "px")
    });
    if (ddl_results[index].options.minheight) $('.' + resultType + "_" + index + " > img").css({
      minHeight: (ddl_results[index].options.minheight.toString() + "px")
    });
  }
}
