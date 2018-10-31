var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var results = clientApp.results || {};

var ddl_results, info;

results.draw = function (run_response) {
  ddl_results = ddl.results;
  work_url = run_response.work_url;
  info = run_response.algo_info;

  $('.results').removeClass('di-none');
  $('.results-container').empty();

  if (run_response.messages) run_response.messages.sort().forEach(printMessage);

  for (let i = 0; i < ddl_results.length; i++) {
    var functionName = $.fn[ddl_results[i].type];
    if ($.isFunction(functionName)) printResult(ddl_results[i], i);
    else console.error(ddl_results[i].type + ' result type is not defined');
  }
}

function printMessage(message, index, messages){
  printResult({
    'type': 'message',
    'contents': [message]
  }, 'msg-' + index);
}

function printResult(result, index) {
  if (!isVisible(result)) return;
  
  $('<div class=result_' + index + ' ></div>').appendTo($('.results-container'));
  $('.result_' + index)[result.type](result, index);
}

function getFileURL(file){
  if (!getParameterFromURL('archive')) return work_url + file;
  var images_ddl = $.extend({}, ddl.archive.files, ddl.archive.hidden_files);
  var images_ddl_keys = Object.keys(images_ddl);
  for (let i = 0; i < images_ddl_keys.length; i++) 
    for (let j = 0; j < experiment.files.length; j++)
      if (images_ddl[images_ddl_keys[i]] === experiment.files[j].name && images_ddl_keys[i] === file)
        return experiment.files[j].url; 

  return null;
}

function isVisible(result) {
  return result.visible ? eval(result.visible) : true;
}

$.fn.file_download = function (result, index) {
  if (result.repeat) {
    $(this).append('<div class=file_download_content_' + index + ' ></div>');
    for (let idx = 0; idx < eval(result.repeat); idx++) {
      var file = eval(result.contents);
      $('.file_download_content_' + index).append('<div class=download_' + index + '_' + idx + ' ></div>');
      $('.download_' + index + '_' + idx).addClass('file_download');
      $('.download_' + index + '_' + idx).append('<a href=' + getFileURL(file) + ' download><img src=./assets/file.svg class=file-icon >' + eval(result.label) + '</a>')
    }
  } else {
    $(this).append('<h4>' + result.label + '</h4>');
    $(this).children().addClass('file_download_title');
    $(this).append('<div class=file_download_content_' + index + ' ></div>');

    if (typeof result.contents == "string") {
      $('.file_download_content_' + index).append('<div class=download_' + index + ' ></div>');
      $('.download_' + index).addClass('file_download');
      $('.download_' + index).append('<a href=' + getFileURL(result.contents) + ' download><img src=./assets/file.svg class=file-icon >' + result.contents + '</a>')
    } else {
      var contentKeys = Object.keys(result.contents);
      for (let i = 0; i < contentKeys.length; i++) {
        $('.file_download_content_' + index).append('<div class=download_' + index + '_' + i + ' ></div>');
        $('.download_' + index + '_' + i).addClass('file_download');
        $('.download_' + index + '_' + i).append('<a href=' + getFileURL(result.contents[contentKeys[i]]) + ' download><img src=./assets/file.svg class=file-icon >' + contentKeys[i] + '</a>')
      }
    }
  }
}

$.fn.text_file = function (result, index) {
  var request = new XMLHttpRequest();
  request.open('GET', getFileURL(result.contents), true);
  request.responseType = 'blob';
  request.onload = function () {
    var reader = new FileReader();
    reader.readAsText(request.response);
    reader.onload = function (e) {
      $('.result_' + index).append('<h3>' + result.label + '</h3>');
      $('.result_' + index).append('<pre class=text_file_content id=text_file_' + index + ' >' + e.target.result + '</pre>');
 
      if (result.style) $('#text_file_' + index).css(JSON.parse(result.style.replace(/'/g, '"')));
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
