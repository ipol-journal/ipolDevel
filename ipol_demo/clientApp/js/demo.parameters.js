var clientApp = clientApp || {};
var editor = editor || {};
var helpers = clientApp.helpers || {};
var upload = clientApp.upload || {};
var parameters = parameters || {};

var editorBlobs;
var params = helpers.getFromStorage('demoInfo').params;
clientApp.parameters = parameters;



parameters.printParameters = function() {
  $('.param-container').remove();
  for (var i = 0; i < params.length; i++) {
    $('#parameters-container').append('<div class=param-' + i +'></div>');
    $('.param-' + i).addClass('param-container');

    var param = params[i];
    var values = param.values;
    var $paramElement = $('.param-' + i);

    var functionName = $.fn[param.type];
    if ($.isFunction(functionName)) {
      $paramElement[param.type](param);
    } else {
      console.error(param.type + ' param type is not correct');
    }
  }
}

$.fn.range = function(param) {
  var values = param.values;
  $(this).append('<span>' + param.label + '</span>');
  $(this).append('<input id=number-' + param.id + ' type=number min=' + values.min + ' max=' + values.max + ' value=' + values.default + ' />');
  $(this).append('<input id=range-' + param.id + ' type=' + param.type + ' min=' + values.min + ' max=' + values.max + ' value=' + values.default + ' step=' + values.step + ' />');
  $('#number-' + param.id).on('change', function() {
    $('#range-' + param.id).assignValue($(this).val());
  });
  $('#range-' + param.id).on('change input', function() {
    $('#number-' + param.id).assignValue($(this).val());
  });
}

$.fn.checkbox = function(param) {
  $(this).append('<span>' + param.label + '</span>');
  $(this).append('<input id=' + param.id + ' type=checkbox />');
  $(param.id).prop('checked', param.default_value);
}

$.fn.selection_radio = function(param) {
  $(this).append('<span>' + param.label + '</span>');
  var keys = Object.keys(param.values);
  var values = Object.values(param.values);
  $(this).append('<div id=param-' + param.id + '></div>');
  for (var i = 0; i < keys.length; i++) {
    $('#param-' + param.id).append('<input type=radio value=' + values[i] + '>' + keys[i] + '<br>');
  }
}

$.fn.selection_collapsed = function(param) {
  $(this).append('<span>' + param.label + '</span>');
  var keys = Object.keys(param.values);
  var values = Object.values(param.values);
  $(this).append('<select id=select-' + param.id + '></select>');
  var default_value = "";
  for (var i = 0; i < keys.length; i++) {
    if (param.default_value == values[i]) default_value = 'selected=selected';
    else default_value = "";
    $('#select-' + param.id).append('<option value=' + values[i] + ' ' + default_value + '>' + keys[i] + '</option>');
  }
}

$.fn.assignValue = function(value) {
  $(this).val(value);
}
