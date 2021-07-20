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
  $(this).append('<input class=checkbox-param id=checkbox_' + param.id + ' type=checkbox ' + value + ' />');
  $(param.id).prop('checked', param.default_value);

  $(this).change(function(event) {
    updateParamsArrayValue(param.id, $('#checkbox_' + param.id).is(":checked"));
  });
}

$.fn.selection_radio = function(param, index) {
  var label = param.label ? param.label : "";
  var keys = Object.keys(param.values);
  var values = Object.keys(param.values).map(function(e) {
    return param.values[e];
  });

  $('.param-' + index).prepend('<span class=param-label >' + label + '</span>');
  $(this).append('<div id=param-' + param.id + '></div>');
  for (var i = 0; i < keys.length; i++) {
    $('#param-' + param.id).append('<div class="radio-option-' + i + '"></div>')
    $('#param-' + param.id + " > .radio-option-" + i).append('<input class=hand type=radio name=' + param.id + ' id=selection_radio_' + param.id + '_' + i + ' value=' + values[i] + '>')
    $('#param-' + param.id + " > .radio-option-" + i).append('<label class=hand for=' + param.id + '_' + i + ' >' + keys[i] + '</label>');
    if (param.default_value == values[i]) $('#' + param.id + '_' + i).prop('checked', true);
  }
  $('#param-' + param.id + ' > label').addClass('m-r-10');

  $('input[name=' + param.id + ']').change(function() {
    updateParamsArrayValue(param.id, $('input[name=' + param.id + ']:checked').val());
  });
}

$.fn.selection_collapsed = function(param, index) {
  var keys = Object.keys(param.values);
  var values = Object.keys(param.values).map(function(e) {
    return param.values[e];
  });

  var default_value = "";

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $(this).append('<select id=selection_collapsed_' + param.id + ' class=select-param ></select>');
  for (var i = 0; i < keys.length; i++) {
    if (param.default_value == values[i]) default_value = 'selected=selected';
    else default_value = "";
    $('#selection_collapsed_' + param.id).append('<option value=' + values[i] + ' ' + default_value + '>' + keys[i] + '</option>');
  }

  $('#selection_collapsed_' + param.id).change(function() {
    updateParamsArrayValue(param.id, $('#selection_collapsed_' + param.id).val());
  });
}

$.fn.numeric = function(param, index) {
  var values = param.values;

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $(this).append('<input id=numeric_' + param.id + ' class=range-slider__value type=number' + ' min=' + values.min + ' max=' + values.max + ' value=' + values.default+' step=' + values.step + ' />');

  $('#numeric_' + param.id).change(function(event) {
    updateParamsArrayValue(param.id, $('#numeric_' + param.id).val());
  });
}

$.fn.text = function(param, index) {
  var values = param.values;

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $('<input id=text_' + param.id + ' class=range-slider__value type=text />').appendTo(this).addClass('input-text-param');
  if(values && values.default) $("#text_" + param.id).val(values.default);

  $('#text_' + param.id).change(function(event) {
    updateParamsArrayValue(param.id, $('#text_' + param.id).val());
  });
}

$.fn.textarea = function(param, index) {
  var default_value = param.default_value;
  var width = param.width || '100%';
  var height = param.height || 200;
  var white_space = param.wrap === false ? "pre" : "";

  $('.param-' + index).prepend('<span class=param-label >' + param.label + '</span>');
  $('<textarea id=textarea_' + param.id + ' ></textarea>').appendTo(this)
    .css({
        width: width, 
        height: height, 
        "white-space": white_space
    });

  if (default_value) $("#textarea_" + param.id).val(default_value.replace('\n', "\r\n"));

  $('#textarea_' + param.id).change(function (event) {
    updateParamsArrayValue(param.id, $('#textarea_' + param.id).val().replace("\r\n", '\n'));
  });
}

$.fn.label = function(param, index) {
  $('.param-' + index).attr('id', param.id ||  "").prepend(param.label);
  $('.param-' + index + " > .param-content").remove();
  $('.param-' + index).first().addClass('label-param');
}
