'use strict';

/* App Module */

var IPOLDemosApp = angular.module('IPOLDemosApp', [
  'ngSanitize',
  'IPOLDemoAnimations',
  'IPOLDemoControllers',
  'IPOLDemoFilters',
  'IPOLDemoServices',
  'IPOLFileUpload',
  'IPOLImgCrop'
]);


/* adding range function to simplify interations on numbers */
IPOLDemosApp.run(['$rootScope', function($rootScope) {
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
}]);


/* adding PreprocessDemo function as global */
IPOLDemosApp.run(['$rootScope', function($rootScope) {
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
    }
  };
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
        element.html(value && value.toString());
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
          ;
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
