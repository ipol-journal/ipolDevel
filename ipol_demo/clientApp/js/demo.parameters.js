var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var parameters = parameters ||  {};
var parametersType = parametersType || {};

var params = {};
var ddl_params = {};

parameters.printParameters = function() {
  params,
  ddl_params = {};
  printParamsInformationIcon(ddl);
  if (ddl.params && ddl.params.length != 0) {
    $('#parameters').removeClass('di-none');
    var ddlParams = ddl.params;
    addResetButton();
    $('.param-container').remove();
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
    if(param.type == "selection_collapsed" || param.type == "text"){
      $('#select-' + param.id).val(params_values[param.id]);
    }
    if(param.type == "checkbox"){
      $('#' + param.id).prop('checked', (params_values[param.id]));
    }
  }
}

function printParamsInformationIcon(){
  checkParamsDescriptionIconVisibility(ddl.general);
  $('#parameters-description').addDescription(ddl.general.param_description);
}

function printParameter(param, index) {
  $('<div class=param-' + index + '></div>').appendTo('#parameters-container').addClass('param-container');
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
  $('.params-buttons').append('<button class=param-reset-btn >Reset</button>');
  $('.param-reset-btn').addClass('btn');
  $('.param-reset-btn').click(function(event) {
    parameters.printParameters();
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

