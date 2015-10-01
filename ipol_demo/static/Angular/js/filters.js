'use strict';

/* Filters */

angular.module('IPOLDemoFilters', []).filter('checkmark', function() {
  return function(input) {
    return input ? '\u2713' : '\u2718';
  };
});


angular.module('IPOLDemoFilters', []).filter('withvalue', function() {
  return function(items, val) {
        var result = {};
        angular.forEach(items, function(value, key) {
            if (value==val) {
                result[key] = value;
            }
        });
        return result;
    };
});