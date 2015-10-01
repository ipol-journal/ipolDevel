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
      $scope.demo = Demo.get(
         {
            demoId: $scope.demo_id }, 
            function(demo) {
              $scope.mainImageUrl = "";
            }
         );
      $scope.renderHtml = function(html_code)
      {
          return $sce.trustAsHtml(html_code);
      };
      $scope.demoblobs = DemoBlobs.get(
          {
             demoId: $scope.demo_id }
          );
      $scope.uploaded_images = [];
      $scope.setImage = function(imageUrl) {
          $scope.mainImageUrl = imageUrl;
      };
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
      $scope.display_ratio = 1;
      $scope.demo = Demo.get(
         {
            demoId: $scope.demo_id }, 
            function(demo) {
            }
         );
      $scope.meta = Meta.get(
        {
            demoId: $scope.demo_id , 
            key: demo_key },
            function(meta) {
              $scope.imwidth  = meta.max_width;
              $scope.imheight = meta.max_height;
              $scope.display_ratio=($scope.imwidth < $scope.maxdim)?1:$scope.maxdim/$scope.imwidth;
              // TODO: check also max height ...
            }
        );

      $scope.params = Params.get(
        {
            demoId: $scope.demo_id , 
            key: demo_key },
            function(params) { }
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
                              ['$scope', '$sce', 'demo_id', 'demo_key', 'Demo', 'Params', 
    function($scope, $sce, demo_id, demo_key, Demo, Params ) {
      $scope.demo_id = demo_id;
      $scope.demo = Demo.get(
         {
            demoId: $scope.demo_id }, 
            function(demo) {   }
         );
      $scope.params = Params.get(
        {
            demoId: $scope.demo_id , 
            key: demo_key },
            function(params) {  }
        );
      $scope.renderHtml = function(html_code)
      {
          return $sce.trustAsHtml(html_code);
      };
  }
  ]
);

