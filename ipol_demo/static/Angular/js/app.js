'use strict';

/* App Module */

//   'IPOLDemoAnimations',
var IPOLDemosApp = angular.module('IPOLDemosApp', [
  'ngSanitize',
  'IPOLDemoControllers',
  'IPOLDemoFilters',
  'IPOLDemoServices',
  'IPOLImgCrop'
]);



IPOLDemosApp.run(['$rootScope', function($rootScope) {

    /* adding range function to simplify interations on numbers */
    $rootScope.range = function(min, max, step) {
        // parameters validation for method overloading
        if (max == undefined) {
            max = min;
            min = 0;
        }
        step = Math.abs(step) || 1;
        if (min > max) {
            step = -step;
        }
        // building the array
        var output = [];
        for (var value=min; value<max; value+=step) {
            output.push(value);
        }
        // returning the generated array
        return output;
    };
    $rootScope.Utils = {
      keys : Object.keys
    };

    /* adding PreprocessDemo function as global */
    $rootScope.PreprocessDemo = function(scope,demo) {
        //
        console.info("PreprocessDemo")
        console.info(demo)
        if (demo!=undefined) {
            angular.forEach(demo.inputs, 
                function(input) {
                    // do some pre-processing
                    if (angular.isString(input.max_pixels)) {
                        input.max_pixels = scope.$eval(input.max_pixels)
                    }
                    if (angular.isString(input.max_weight)) {
                        input.max_weight = scope.$eval(input.max_weight)
                    }
                }
            )
            //
            
            if (demo.general.crop_maxsize==undefined) {
                // setting the crop_maxsize string to a non integer value with 
                // disable its behavior, so no limit by default
                demo.general.crop_maxsize = "NaN";
            }

            if (demo.general.thumbnail_size==undefined) {
                demo.general.thumbnail_size = 128;
            }
            
            if (angular.isString(demo.general.input_description)) {
                demo.general.input_description = [ demo.general.input_description ];
            }
            if (angular.isString(demo.general.param_description)) {
                demo.general.param_description = [ demo.general.param_description ];
            }
            
            // create default params_layout property if it is not defined
            if (demo.params&&(demo.params_layout==undefined)) {
                demo.params_layout= [ [ "Parameters:", scope.range(demo.params.length) ] ];
            } else {
                demo.params_layout= [];
            }
        }
    };
  
    // function used by the range_scientific parameter type
    // computes the slider position of a given value
    $rootScope.num2sci = function(value, numDigits)
    {
    var exponent = Math.floor(Math.log(value) / Math.log(10));
    var mantissa = value / Math.pow(10, exponent - numDigits);
    return Math.round(mantissa + (9*exponent - 1)*Math.pow(10, numDigits));
    }

    // function used by the range_scientific parameter type
    // computes the number value from the slider position
    $rootScope.sci2str = function(sci, numDigits)
    {
    var exponent = Math.floor(sci / (9*Math.pow(10, numDigits)));
    var mantissa = sci/Math.pow(10, numDigits) - (9*exponent - 1);
    var value = Math.pow(10, exponent) * mantissa;
    return value.toExponential(numDigits);
    }

  
    // initialization of the parameters obtained from the DDL json file
    $rootScope.initParams = function(scope,demo,params) {
        console.info("initParams");
        
        // add pensize parameter for inpainting
        if (demo.params) {
            if (params['pensize']==undefined) {
            demo.params.pensize = 5;
            } else {
            demo.params.pensize = params['pensize'];
            }
        }

        // initialize input loading status
        angular.forEach(demo.inputs, 
          function(res) {
            res.status = "trying";
          }
        );

        // initialize parameter values
        if (demo.params) {
            angular.forEach(demo.params, 
            function(param) {
                console.info(param.type);
                // range type
                if (param.type=='range') {
                if (params[param.id]==undefined) {
                    param.value = param.values.default;
                } else {
                    param.value = params[param.id];
                }
                }
                // range_scientic type
                if (param.type=='range_scientific') {
                if (params[param.id]==undefined) {
                    param.value = param.values.default;
                } else {
                    param.value = params[param.id];
                }
                // initialize the slider position
                param.value_slider = scope.num2sci(param.value,param.values.digits);
                }
                // selection_collapsed type
                if (param.type=='selection_collapsed') {
                if (params[param.id]==undefined) {
                    param.value = param.default_value;
                } else {
                    param.value = params[param.id].toString();
                }
                }
                // selection_radio type
                if (param.type=='selection_radio') {
                if (params[param.id]==undefined) {
                    param.value = param.default_value;
                } else {
                    param.value = params[param.id].toString();
                }
                }
                // checkbox type
                if (param.type=='checkbox') {
                // if the variable xxx_checked (hidden input) is
                // not defined: use default value, otherwise, use
                // its value (we need this variable because checkboxes
                // are only returned if they are checked in html)
                if (params[param.id+"_checked"]==undefined) {
                    param.value = param.default_value;
                } else {
                    param.value = params[param.id+"_checked"];
                }
                }
                // checkboxes type
                if (param.type=='checkboxes') {
                // create one boolean value per checkbox ...
                param.cb_values = {};
                angular.forEach(param.values, 
                    function(checkboxes_info) {
                    angular.forEach(checkboxes_info, 
                        function(value,key)
                        {
                        // if the variable xxx_checked (hidden input) is
                        // not defined: use default value, otherwise, use
                        // its value (we need this variable because checkboxes
                        // are only returned if they are checked in html)
                        if (params[param.id+"_"+key+"_checked"]==undefined) {
                            param.cb_values[key]=(param.default.indexOf(key)>-1);
                        } else {
                            param.cb_values[key]=params[param.id+"_"+key+"_checked"];
                        }
                        }
                    );
                    }
                );
                }
                if (param.type=='readonly') {
                param.value='';
                }
                //console.info(param.cb_values);
            }
            );
        }
    }
  
}]);


/* should go to the directoves.js file ... */
IPOLDemosApp.directive('floatsaving', function () {
    return {
        restrict: 'A',
        require: '?ngModel',
        scope: {
            model: '=ngModel'
        },
        link: function (scope, element, attrs, ngModelCtrl) {
            if (!ngModelCtrl) {
                return;
            }
            ngModelCtrl.$parsers.push(function (value) {
                if (!value || value==='' || isNaN(parseFloat(value)) ) {
                    value='0';
                }
                return parseFloat(value);
            });
        }
    };
});

// trying to get image dimensions into variables: not working yet
IPOLDemosApp.directive('styleParent', function(){ 
   return {
     restrict: 'A',
     link: function(scope, elem, attr) {
         elem.on('load', function() {
            var w = $(this).width(),
                h = $(this).height();

            var div = elem.parent();
            console.log("styleParent directive");
            console.log(w);
            console.log(h);

            //check width and height and apply styling to parent here.
         });
     }
   };
});


IPOLDemosApp.directive('bindHtmlCompile', ['$compile', function ($compile) {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      scope.$watch(function () {
        return scope.$eval(attrs.bindHtmlCompile);
      }, function (value) {
        // In case value is a TrustedValueHolderType, sometimes it
        // needs to be explicitly called into a string in order to
        // get the HTML string.
        if (angular.isArray(value)) {
            element.html(value && value.join(' ').toString());
        } else {
            element.html(value && value.toString());
        }
        // If scope is provided use it, otherwise use parent scope
        var compileScope = scope;
        if (attrs.bindHtmlScope) {
          compileScope = scope.$eval(attrs.bindHtmlScope);
        }
        
        $compile(element.contents())(compileScope);
      });
    }
  };
}]);


// trying to display different images while loading, not used at the moment
IPOLDemosApp.directive('imgWithLoading', function () {
    return {
        restrict: 'E',
        template: '<div/>',
        transclude: false,
        replace: true,
        scope: {
          imgSrc: '@'
        },
        link: function (scope, element, attrs) {
            console.log('imgWithLoading init: source="' + scope.imgSrc + '"');

            setHeight();

            var img = angular.element(new Image());

            var unbind1 = img.on('load', function (evt) {
                console.log('image loaded: ' + img.attr('src'));
                stopLoadingCSS( );
            });
            var unbind2 = img.on('error', function(evt) {
                console.log('imgWithLoading error Loading ' + scope.imgSrc);
                element.removeClass(attrs.spinnerClass);
            });
            //only define src here, after binding events
            //notice src is retrieve from attrs because scope.imgSrc may be undefined yet
            img.attr('src', attrs.imgSrc);
            startLoadingCSS( );
            element.append(img);
            element.addClass('imgWithLoading');

                                                    //watch for changes
            var unbind3 = scope.$watch('imgSrc', function(newVal, oldVal) {
                if ( newVal===img.attr('src') ) return;
                startLoadingCSS( );
                setHeight();
                img.attr('src', newVal);
                console.log('imgWithLoading: imgSrc mudou: ' + newVal );
                console.log('imgWithLoading: imgSrc antigo: ' + oldVal );
            });

            scope.$on('destroy', function() {
                console.log('imgWithLoading: unbinding...');
                unbind1(); unbind2(); unbind3(); });

            // ------- LOCAL FUNCTIONS --------------------------------
            function startLoadingCSS( ) {
                img.css({
                    visibility: 'hidden'
                });
                element.addClass(attrs.spinnerClass);
            }
            function stopLoadingCSS( ) {
                img.css({visibility: 'visible'});
                element.removeClass(attrs.spinnerClass);
            }
            function setHeight( ) {
                var w = element.prop('offsetWidth');
                var h = attrs.heightMultiplier * w;
                if (w && h) {
                    element.css('height', h + 'px');
                    //if (!scope.$$phase) scope.$apply();
                    console.log('imgWithLoading: [width x height] set to [' + w + ' x ' + h + ']');
                } else {
                    console.log('imgWithLoading: height NOT set');
                }
            }
        }
    };
});


IPOLDemosApp.directive('imageonload', function() {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
        element.bind('load', function() {
           scope.$apply(attrs.imageonload);
        });
    }
  };
});


IPOLDemosApp.directive('imageonfail', function() {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
        element.bind('error', function(){
          scope.$apply(attrs.imageonfail);
        });
    }
  };
});
