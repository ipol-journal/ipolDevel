'use strict';

/* Controllers */

var IPOLDemoControllers = angular.module('IPOLDemoControllers', []);

IPOLDemoControllers.controller('DemoListCtrl', ['$scope', 'Demo',
  function($scope, Demo) {
    $scope.demos = Demo.query();
    $scope.orderProp = 'title';
  }]);

/*---------------- DemoInputCtrl ---------------------------------------------*/
IPOLDemoControllers.controller('DemoInputCtrl', 
                              ['$scope', '$sce', 'demo_id', 'Demo', 'DemoBlobs', 'Params', 
    function($scope, $sce, demo_id, Demo, DemoBlobs, Params ) {

      $scope.demo_id = demo_id;
      $scope.demo = Demo.get( { demoId: $scope.demo_id }, 
            function(demo) { 
              $scope.PreprocessDemo($scope,demo)
              $scope.ThumbnailSize = demo.general.thumbail_size;
            } );
      
      $scope.renderHtml = function(html_code)
      {
          return $sce.trustAsHtml(html_code);
      };
      $scope.demoblobs = DemoBlobs.get( { demoId: $scope.demo_id },
        function(demoblobs) {
          console.info("*** demoblobs");
          // preprocess HTML parameters string
          angular.forEach(demoblobs.blobs, 
            function(blobset) {
              blobset[0].html_params=""
              //console.info("set_name=",blobset[0].set_name);
              //console.info("size=",blobset[0].size);
              // extract only contents of interest
              var blobset_contents = blobset.slice(1);
              //console.info("contents:",blobset_contents);
              blobset_contents.sort( function(a,b) { 
                  return (a.id_in_set<b.id_in_set?-1: (a.id_in_set>b.id_in_set?1:0) );
                });
              //console.info("contents:",blobset_contents);
              var current_id=""
              for(var idx=0;idx<blobset_contents.length;idx++) {
                //console.info(blobset_contents[idx].title)
                if (idx==0) {
                  blobset[0].html_params += blobset_contents[idx].id_in_set + ":";
                } else  {
                  // if same id, separate by comma ...
                  if (blobset_contents[idx].id_in_set==current_id) {
                    blobset[0].html_params += ",";
                  } else {
                    // else separate arguments
                    blobset[0].html_params += "&" + blobset_contents[idx].id_in_set + ":";
                  }
                }
                current_id = blobset_contents[idx].id_in_set;
                blobset[0].html_params += blobset_contents[idx].hash+
                                          blobset_contents[idx].extension;
              }
              console.info("html_params:",blobset[0].html_params);
            }
          )
        }
      );
      $scope.uploaded_images = [];
      
      $scope.GetBlobUrl =   function($sce, blob) {
        return $sce.trustAsResourceUrl("http://localhost:7777/thumbnail/thumbnail_"+ blob.hash + blob.extension);
      }
      
      $scope.DisableBlobDisplay = function(blob_set,index)
      {
        blob_set[index].extension = "disabled";
      }
      
      $scope.ImagePickerCtrl =   function($scope) {
          $scope.selectImage = function (image) {
          if($scope.selected_image === image) {
              $scope.selected_image = '';
          }
          else {
              $scope.selected_image = image;
          }
          
          //$scope.InputCropped = false;
          
          if (typeof $scope.selected_image === "object") {
              $scope.selected_image_link = 'http://localhost:7777/blob_directory/'+ 
                $scope.selected_image.hash + $scope.selected_image.extension;
          } else {
            if ($scope.selected_image.indexOf('.png') > -1) {
              $scope.selected_image_link = 'img/demos/' + $scope.demo.id + 
                                              '/uploaded/' +
                                              $scope.selected_image;
            } else {
              $scope.selected_image_link = 'img/demos/' + $scope.demo.id + '/' + 
                                              $scope.selected_image+'.png';
            }
          }
        }
      }

  }
  ]
);

/*---------------- DemoParamCtrl ---------------------------------------------*/
IPOLDemoControllers.controller('DemoParamCtrl', 
                              ['$scope', '$sce', '$location', 'demo_id', 'demo_key', 'Demo', 'Meta', 'Params', 
    function($scope, $sce, $location, demo_id, demo_key, Demo, Meta, Params ) {
      $scope.demo_key = demo_key;
      $scope.demo_id = demo_id;
      $scope.Math = window.Math;
      $scope.maxdim=768;
      $scope.imwidth=1024;
      $scope.imheight=1024;
      $scope.display_ratio=1;
      $scope.InputCropped=false;
      $scope.CropInfo = { coord:{ x: 0, y:0, w :100, h:100 } };
      $scope.got_meta = false;
      $scope.got_param= false;
      $scope.got_demo = false;
      $scope.demo     = {};
      $scope.params   = {};
      
      $scope.initParams = function($scope) {
        console.info("initParams");
        // initialize parameter values
        angular.forEach($scope.demo.params, 
          function(param) {
            console.info(param.type);
            // range type
            if (param.type=='range') {
              if ($scope.params[param.id]==undefined) {
                param.value = param.values.default;
              } else {
                //console.info(param.id,$scope.params[param.id]);
                param.value = $scope.params[param.id];
              }
            }
            // selection_collapsed type
            if (param.type=='selection_collapsed') {
              if ($scope.params[param.id]==undefined) {
                param.value = param.default_value;
              } else {
                //console.info(param.id,$scope.params[param.id]);
                param.value = $scope.params[param.id].toString();
              }
            }
          }
        );
      }

      $scope.updateCropInfo = function($scope) {
        if ($scope.params.x0!=undefined)
        {
          $scope.CropInfo.coord = {
            x:Math.round($scope.params.x0*$scope.display_ratio),
            y:Math.round($scope.params.y0*$scope.display_ratio),
            w:Math.round(($scope.params.x1-$scope.params.x0+1)*$scope.display_ratio),
            h:Math.round(($scope.params.y1-$scope.params.y0+1)*$scope.display_ratio)
          };

          // automatically enable/disable input InputCropped
          // NOTE: comparing to imwidth and imweight is not always correct since
          // they are the maximal dimensions over all inputs ...
          $scope.InputCropped=($scope.params.x0!=0) ||
                              ($scope.params.y0!=0) ||
                              ($scope.params.x1!=$scope.imwidth-1) ||
                              ($scope.params.y1!=$scope.imheight-1);
          
        }
      }

      Demo.get( 
          { demoId: $scope.demo_id }, 
          function(demo) { 
            console.info("getting demo");
            $scope.PreprocessDemo($scope,demo)
            $scope.got_demo=true;
            $scope.demo = demo;
            // crop is applied to the first input image only for the moment
            // we need this string in a variable for the image crop module
            $scope.crop_image_url='tmp/'+demo_key+'/input_0.png';
            if ($scope.got_param) $scope.initParams($scope);
          } 
        );
      
      $scope.meta = Meta.get(
        { key: demo_key },
        function(meta) {
          console.info("getting meta");
          $scope.imwidth  = meta.max_width;
          $scope.imheight = meta.max_height;
          $scope.display_ratio=($scope.imwidth < $scope.maxdim)?1:$scope.maxdim/$scope.imwidth;
          // TODO: check also max height ...
          if ($scope.got_param) $scope.updateCropInfo($scope);
          $scope.got_meta = true;
        }
        );

      Params.get(
        { key: demo_key },
        function(params) { 
          console.info("getting param");
          $scope.got_param=true;
          $scope.params = params;
          if ($scope.got_meta) $scope.updateCropInfo($scope);
          if ($scope.got_demo) $scope.initParams($scope);
        }
        );

      $scope.page_params = $location.search();
      console.log($scope.page_params);
      $scope.renderHtml = function(html_code)
      {
          return $sce.trustAsHtml(html_code);
      };
  }
  ]
);

/*---------------- DemoWaitCtrl --------------------------------------------*/
IPOLDemoControllers.controller('DemoWaitCtrl',
  [ '$scope','$timeout',
    function($scope,$timeout) 
    {
      $scope.counter = 0;
      $scope.onTimeout = function(){
          $scope.counter++;
          mytimeout = $timeout($scope.onTimeout,1000);
      }
      var mytimeout = $timeout($scope.onTimeout,1000);
    }
  ]
);

/*---------------- DemoResultCtrl --------------------------------------------*/
IPOLDemoControllers.controller('DemoResultCtrl', 
  [ '$scope', '$sce', 'demo_id', 'demo_key', 
    'work_url', 'Demo', 'Meta', 'Params', 'Info',
    function($scope, $sce, demo_id, demo_key, work_url, Demo, Meta ,Params, Info ) 
    {
      $scope.idx = 0;
      $scope.maxdim=768;
      $scope.current_scope = $scope;
      $scope.Math = window.Math;
      $scope.demo_id = demo_id;
      $scope.work_url = work_url;
      $scope.ZoomFactor = 1;
      // give some parameters to the demos for their own use
      $scope.display = { param1:'', param2:'', param3:''};
      $scope.demo = Demo.get( { demoId: $scope.demo_id }, 
        function(demo) { 
          $scope.PreprocessDemo($scope,demo)
        } 
      );
      $scope.params = Params.get( { key: demo_key },
        function(params) {  
          $scope.sizeX = params.x1-params.x0+1;
          $scope.sizeY = params.y1-params.y0+1;
        }
      );
      
      $scope.meta = Meta.get(
        { key: demo_key },
        function(meta) {
          $scope.imwidth  = meta.max_width;
          $scope.imheight = meta.max_height;
          $scope.display_ratio=($scope.imwidth < $scope.maxdim)?1:$scope.maxdim/$scope.imwidth;
        }
      );
      
      $scope.info = Info.get( { key: demo_key }, function(info) { } );
      
      $scope.renderHtml = function(html_code)
      {
          return $sce.trustAsHtml(html_code);
      };
      
      $scope.CheckArray = function(v)
      {
        return angular.isArray(v);
      };
      
      $scope.CheckObject = function(v)
      {
        return angular.isObject(v);
      };
      
      $scope.DisableImage = function(contents,index)
      {
        contents[Object.keys(contents)[index]] = "-- disabled --";
      }
      
    }
  ]
);

