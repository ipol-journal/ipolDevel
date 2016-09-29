'use strict';

/* Filters */

angular.module('IPOLDemoFilters', [])
//
.filter('checkmark',
  function() {
    return function(input) {
      return input ? '\u2713' : '\u2718';
    };
  }
)
.filter('isArray', 
  function() {
    return function (input) {
      return angular.isArray(input);
    };
  }
)
.filter('isString', 
  function() {
    return function (input) {
      return angular.isString(input);
    };
  }
)
//
.filter('interpolate', 
  function($interpolate) {
    return function(expression, context) {
        return $interpolate(expression)(context);
    };
  }
)
//
.filter('interpolate_twice', 
  function($interpolate) {
    return function(expression, context) {
        return $interpolate($interpolate(expression)(context))(context);
    };
  }
)
//
.filter('interpolate_loop', 
  function($interpolate) {
    return function(expression, context, index) {
        context.idx = index;
        return $interpolate(expression)(context);
    };
  }
)
//
.filter('withvalue', 
  function() {
    return function(items, val) {
      var result = {};
      angular.forEach(items, function(value, key) {
          if (value==val) {
              result[key] = value;
          }
      });
      return result;
    };
  }
);



