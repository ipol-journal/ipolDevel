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
      $scope.demo = Demo.get( { demoId: $scope.demo_id }, function(demo) { } );
      
      $scope.renderHtml = function(html_code)
      {
          return $sce.trustAsHtml(html_code);
      };
      $scope.demoblobs = DemoBlobs.get( { demoId: $scope.demo_id } );
      $scope.uploaded_images = [];
      
      $scope.GetBlobUrl =   function($sce, blob) {
        return $sce.trustAsResourceUrl("http://localhost:7777/thumbnail/thumbnail_"+ blob.hash + blob.extension);
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
      $scope.demo_id = demo_id;
      $scope.Math = window.Math;
      $scope.maxdim=768;
      $scope.imwidth=1024;
      $scope.imheight=1024;
      $scope.display_ratio=1;
      $scope.InputCropped=false;
      $scope.CropInfo = { coord:{ x: 0, y:0, w :100, h:100 } };
      $scope.got_meta=false;
      $scope.got_param=false;
      
      $scope.demo = Demo.get( { demoId: $scope.demo_id }, function(demo) { } );
      $scope.meta = Meta.get(
        { key: demo_key },
        function(meta) {
          console.info("getting meta");
          $scope.imwidth  = meta.max_width;
          $scope.imheight = meta.max_height;
          $scope.display_ratio=($scope.imwidth < $scope.maxdim)?1:$scope.maxdim/$scope.imwidth;
          // TODO: check also max height ...
          if (($scope.got_param)&&($scope.params.x0!=undefined))
          {
            $scope.CropInfo.coord = {
              x:Math.round($scope.params.x0*$scope.display_ratio),
              y:Math.round($scope.params.y0*$scope.display_ratio),
              w:Math.round(($scope.params.x1-$scope.params.x0+1)*$scope.display_ratio),
              h:Math.round(($scope.params.y1-$scope.params.y0+1)*$scope.display_ratio)
            };
          }
          $scope.got_meta = true;
        }
        );

      $scope.params = Params.get(
        { key: demo_key },
        function(params) { 
          console.info("getting param");
          $scope.InputCropped=(params.x0!=undefined);
          if ((params.x0!=undefined)&&($scope.got_meta))
          {
            $scope.CropInfo.coord = {
              x:Math.round(params.x0*$scope.display_ratio),
              y:Math.round(params.y0*$scope.display_ratio),
              w:Math.round((params.x1-params.x0+1)*$scope.display_ratio),
              h:Math.round((params.y1-params.y0+1)*$scope.display_ratio)
            };
          }
          $scope.got_param=true;
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


/*---------------- DemoResultCtrl --------------------------------------------*/
IPOLDemoControllers.controller('DemoResultCtrl', 
  [ '$scope', '$sce', 'demo_id', 'demo_key', 
    'work_url', 'Demo', 'Params', 'Info',
    function($scope, $sce, demo_id, demo_key, work_url, Demo, Params, Info ) 
    {
      $scope.demo_id = demo_id;
      $scope.work_url = work_url;
      $scope.demo = Demo.get( { demoId: $scope.demo_id }, function(demo) { } );
      $scope.params = Params.get( { key: demo_key },
        function(params) {  
          $scope.sizeX = params.x1-params.x0+1;
          $scope.sizeY = params.y1-params.y0+1;
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
    }
  ]
);

