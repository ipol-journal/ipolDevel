var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var results = clientApp.results ||  {};

var demoInfo, run_response, ddl_results, work_url, post_params, info;

results.draw = function(response)  {
  demoInfo = helpers.getFromStorage('demoInfo');
  run_response = response;
  ddl_results = demoInfo.results;
  work_url = run_response.work_url;
  post_params = run_response.params;
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
  if(!checkResultVisibility(result)) return;
  $('.results-container').append('<div class=result_' + index + ' ></div>');
  $('.result_' + index)[result.type](result, index);
}

function checkResultVisibility(result){
  return result.visible ? eval(result.visible) : true;
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
    $(this).append('<h3>' + result.label + '</h3>');
    $(this).children().addClass('file_download_title');
    $(this).append('<div class=file_download_content_' + index + ' ></div>');

    if (typeof result.contents == "string"){
      $('.file_download_content_' + index).append('<div class=download_' + index + ' ></div>');
      $('.download_' + index).addClass('file_download');
      $('.download_' + index).append('<a href=' + work_url + result.contents + ' download><img src=./file.svg class=file-icon >' + result.contents + '</a>')
    } else {
      var contentKeys = Object.keys(result.contents);
      for (let i = 0; i < contentKeys.length; i++) {
        $('.file_download_content_' + index).append('<div class=download_' + index + '_' + i + ' ></div>');
        $('.download_' + index + '_' + i).addClass('file_download');
        $('.download_' + index + '_' + i).append('<a href=' + work_url + result.contents[contentKeys[i]] + ' download><img src=./file.svg class=file-icon >' + contentKeys[i] + '</a>')
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

  for (let i = 0; i < result.contents.length; i++) {
    text += result.contents[i];
  }

  if (text.charAt(0) == '\'') text = eval(text);
  else text = eval('\'' + text + '\'');

  $('.html_text_' + index).html(text);
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
