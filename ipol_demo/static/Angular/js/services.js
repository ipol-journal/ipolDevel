'use strict';

/* Services */

var IPOLDemoServices = angular.module('IPOLDemoServices', ['ngResource' ]);

IPOLDemoServices.factory('Demo', ['$resource',
  function($resource){
    return $resource('../JSON/:demoId.json', {}, {
      query: {method:'GET', params:{demoId:'demos'}, isArray:true}
    });
  }]);

// not really working, not used
IPOLDemoServices.factory('DemoBlobs', ['$resource', '$http',
  function($resource,$http){
    var blob_server = $http.get('../JSON/democonf.json')
      .success(function(data) {
        console.info("data=",data);
        return data.blob_server;
      });
    console.info("blob_server=",blob_server);
    //var blobServer = "http://localhost:7777";
    return $resource(blob_server+'/get_blobs_of_demo_by_name_ws?demo_name=:demoId', {}, {
      query: {method:'JSONP', params:{demoId:'demos'}, isArray:true}
    });
  }]);

IPOLDemoServices.factory('Params', ['$resource',
  function($resource){
    return $resource('tmp/:key/params.json', {}, {
      query: {method:'JSONP', params:{key:'key'}, isArray:true}
    });
  }]);

IPOLDemoServices.factory('Meta', ['$resource',
  function($resource){
    return $resource('tmp/:key/meta.json', {}, {
      query: {method:'JSONP', params:{key:'key'}, isArray:true}
    });
  }]);

IPOLDemoServices.factory('Info', ['$resource',
  function($resource){
    return $resource('tmp/:key/info.json', {}, {
      query: {method:'JSONP', params:{key:'key'}, isArray:true}
    });
  }]);

