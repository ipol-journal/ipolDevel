var parametersType = parametersType || {};

// In this file there are only the different params types that parameters section will print.

$.fn.range = function(param, index) {
  var values = param.values;
  var step = param.values.step || param.values.min;

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $(this).append('<input id=range_' + param.id + ' class=range-slider__range type=' + param.type + ' min=' + values.min + ' max=' + values.max + ' value=' + values.default+' step=' + step + ' />');
  $(this).append('<input id=number_' + param.id + ' class=range-slider__value type=number min=' + values.min + ' max=' + values.max + ' value=' + values.default+' step=' + step + ' />');

  $('#number_' + param.id).on('change input', function() {
    $('#range_' + param.id).val($(this).val());
    updateParamsArrayValue(param.id, $(this).val());
  });
  $('#range_' + param.id).on('change input', function() {
    $('#number_' + param.id).val($(this).val());
    updateParamsArrayValue(param.id, $(this).val());
  });
}

$.fn.checkbox = function(param, index) {
  var value = param.default_value ? "checked" : "";

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $(this).append('<input class=checkbox-param id=' + param.id + ' type=checkbox ' + value + ' />');
  $(param.id).prop('checked', param.default_value);

  $(this).change(function(event) {
    updateParamsArrayValue(param.id, $('#' + param.id).is(":checked"));
  });
}

$.fn.selection_radio = function(param, index) {
  var label = param.comments ? param.comments : param.label;
  var keys = Object.keys(param.values);
  var values = Object.values(param.values);

  $('.param-' + index).prepend('<span class=param-label >' + label + '</span>');
  $(this).append('<div id=param-' + param.id + '></div>');
  for (var i = 0; i < keys.length; i++) {
    $('#param-' + param.id).append('<input class=hand type=radio name=' + param.id + ' id=' + param.id + '_' + i + ' value=' + values[i] + '>');
    $('#param-' + param.id).append('<label class=hand for=' + param.id + '_' + i + ' >' + keys[i] + '</label>');
    if (param.default_value == values[i]) $('#' + param.id + '_' + i).prop('checked', true);
  }
  $('#param-' + param.id + ' > label').addClass('m-r-10');

  $('input[name=' + param.id + ']').change(function() {
    updateParamsArrayValue(param.id, $('input[name=' + param.id + ']:checked').val());
  });
}

$.fn.selection_collapsed = function(param, index) {
  var keys = Object.keys(param.values);
  var values = Object.values(param.values);
  var default_value = "";

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $(this).append('<select id=select-' + param.id + ' class=select-param ></select>');
  for (var i = 0; i < keys.length; i++) {
    if (param.default_value == values[i]) default_value = 'selected=selected';
    else default_value = "";
    $('#select-' + param.id).append('<option value=' + values[i] + ' ' + default_value + '>' + keys[i] + '</option>');
  }

  $('#select-' + param.id).change(function() {
    updateParamsArrayValue(param.id, $('#select-' + param.id).val());
  });
}

$.fn.numeric = function(param, index) {
  var values = param.values;

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $(this).append('<input id=number_' + param.id + ' class=range-slider__value type=number' + ' min=' + values.min + ' max=' + values.max + ' value=' + values.default+' step=' + values.step + ' />');

  $('#number_' + param.id).change(function(event) {
    updateParamsArrayValue(param.id, $('#number_' + param.id).val());
  });
}

$.fn.text = function(param, index) {
  var values = param.values;

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $('<input id=text_' + param.id + ' class=range-slider__value type=text />').appendTo(this).addClass('input-text-param');
  $("#text_" + param.id).val(param.values.default);

  $('#text_' + param.id).change(function(event) {
    updateParamsArrayValue(param.id, $('#text_' + param.id).val());
  });
}

$.fn.label = function(param, index) {
  $('.param-' + index).prepend(param.label);
  $('.param-' + index).first().addClass('label-param');
}
