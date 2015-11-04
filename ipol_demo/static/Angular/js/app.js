'use strict';

/* App Module */

var IPOLDemosApp = angular.module('IPOLDemosApp', [
  'ngRoute',
  'ngSanitize',
  'IPOLDemoAnimations',
  'IPOLDemoControllers',
  'IPOLDemoFilters',
  'IPOLDemoServices',
  'IPOLFileUpload',
  'IPOLImgCrop'
]);

IPOLDemosApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/demos', {
        templateUrl: 'partials/demos-list.html',
        controller: 'DemoListCtrl'
      }).
      when('/:demoId', {
        templateUrl: 'partials/demo-detail.html',
        controller: 'DemoDetailCtrl'
      }).
      when('/:demoId/:params*', {
        templateUrl: 'partials/demo-detail.html',
        controller: 'DemoDetailCtrl'
      }).
      otherwise({
        redirectTo: '/demoId'
      });
  }]);

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
      
      if (demo.general.thumbnail_size==undefined) {
        demo.general.thumbnail_size = 128;
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

IPOLDemosApp.directive('imageonfail', function() {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
//         element.bind('load', function() {
//           // do something
//           ;
//         });
        element.bind('error', function(){
          scope.$apply(attrs.imageonfail);
        });
    }
  };
});
