var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var parameters = parameters ||  {};
var parametersType = parametersType || {};

var params = {};
var ddl_params = {};

parameters.printParameters = function() {
  params,
  ddl_params = {};
  if (ddl.general.param_description != undefined) displayParametersDescription()
  if (ddl.params && ddl.params.length != 0) {
    $('#parameters').removeClass('di-none');
    var ddlParams = ddl.params;
    addResetButton();
    $('.param-container').remove();
    $("#parameters-container").append('<form id="params-form"></form>');
    for (var i = 0; i < ddlParams.length; i++) {
      var param = ddlParams[i];
      var functionName = $.fn[param.type];
      ddl_params[param.id] = param;

      if ($.isFunction(functionName)) {
        addToParamsObject(param);
        printParameter(param, i);
      } else console.error(param.type + ' param type is not correct');
    }
  }
}

parameters.resetValues = () => {
  for (let [index, parameter] of ddl.params.entries()) {
    if (parameter.type == 'label') continue;
    const defaults = {
      'textarea': "",
      'text': "",
      'checkbox': false,
      'numeric': 0,
      'range': 0
    }
    const parameterSelector = `#${parameter.type}_${parameter.id}`;

    if (parameter.type == 'selection_radio'){
      $(`#param-${parameter.id} > div > input[value="${parameter.default_value}"]`).attr('checked', true);
    };

    let defaultValue = "";
    if (parameter.hasOwnProperty('default_value')) {
      defaultValue = parameter.default_value;
    } else if (parameter.hasOwnProperty('values')) {
      defaultValue = parameter.values.default || defaults[parameter.type];
    } else {
      defaultValue = defaults[parameter.type];
    }
    $(parameterSelector).val(defaultValue);
    updateParamsArrayValue(parameter.id, defaultValue);
  }
}

function displayParametersDescription() {
  $('.parameters-description').remove();
  $('#parameters-container').append(
    '<div class=parameters-description></div>');
  
  var text = typeof ddl.general.param_description != 'string' ? ddl.general.param_description.join('') : ddl.general.param_description;
  $('.parameters-description').append(text);
}

parameters.setParametersValues = function(params_values){
  for (var i = 0; i < ddl.params.length; i++) {
    var param = ddl.params[i];
    updateParamsArrayValue(param.id, params_values[param.id]);
    if(param.type == "range"){
      $('#number_' + param.id).val(parseFloat(params_values[param.id]));
      $('#range_' + param.id).val(parseFloat(params_values[param.id]));
    }
    if(param.type == "selection_radio"){
      var values_keys = Object.keys(param.values);
      for (let j = 0; j < values_keys.length; j++)
        if(param.values[values_keys[j]] == params_values[param.id])
          $('#' + param.id + '_' + j).prop('checked', true);
    }
    if(param.type == "selection_collapsed"){
      $('#select-' + param.id).val(params_values[param.id]);
    }
    if(param.type == "checkbox"){
      $('#' + param.id).prop('checked', (params_values[param.id]));
    }
    if(param.type == "text"){
      $('#text-' + param.id).val(params_values[param.id]);
    }
  }
}

function printParameter(param, index) {
  $('<div class="param-' + index + ' param-container"></div>').appendTo('#params-form');
  $('<div class=param-content-' + index + ' ></div>').appendTo('.param-' + index).addClass("param-content");

  $('.param-content-' + index)[param.type](param, index);

  $('.param-' + index).addClass(param.id);
  checkParamsVisibility();

  if (param.values) addMaxMin(param, index);
  var comment = param.comments || "";
  if(param.type != "label") $('.param-' + index).append("<div class=param-comments >" + comment + "</div>");
}

function addToParamsObject(param) {
  if (param.default_value != undefined ||  param.values != undefined)
    params[param.id] = param.default_value != undefined ? param.default_value : param.values.default;
  if (param.type == "checkbox" &&  !param.default_value)
    params[param.id] = false;
  if(param.type == "selection_radio")
    params[param.id] = (param.default_value != undefined ? param.default_value : param.values.default).toString();
}

function addMaxMin(param, index) {
  if (param.values.max || param.values.min) $('.param-content-' + index).append("<div id=maxmin-" + index + " class=maxmin ></div>");
  if (param.values.max) $('#maxmin-' + index).append("<span> Max: " + param.values.max + "</span>");
  if (param.values.min) $('#maxmin-' + index).append("<span> Min: " + param.values.min + "</span>");
}

function updateParamsArrayValue(param_id, value) {
  params[param_id] = value;
  checkParamsVisibility();
}

function checkParamsVisibility() {
  for (let i = 0; i < Object.keys(ddl_params).length; i++) {
    checkVisibility(ddl_params[Object.keys(ddl_params)[i]]);
  }
}

function addResetButton() {
  $('.params-buttons').remove();
  $('.params-header').append('<div class=params-buttons ></div>');
  $('.params-buttons').append('<input type="reset" class=param-reset-btn >');
  $('.param-reset-btn').addClass('btn');
  $('.param-reset-btn').click(function(event) {
    document.getElementById('params-form').reset();
    parameters.resetValues();
  });
}

function checkParamsDescriptionIconVisibility(ddl_general) {
  if (ddl_general.param_description != undefined) $('#parameters-description').removeClass('di-none');
}

function checkVisibility(param) {
  if (param.visible != undefined && !eval(param.visible))
    $('.' + param.id).addClass('di-none');
  else $('.' + param.id).removeClass('di-none');
}

