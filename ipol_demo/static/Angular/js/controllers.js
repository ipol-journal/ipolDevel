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
                              ['$scope', '$sce', '$http','demo_id', 'blob_server', 
                               'Demo', 'Params', 
    function($scope, $sce, $http, demo_id, blob_server, Demo, Params ) {

      $scope.demo_id     = demo_id;
      $scope.blob_server = blob_server;
      $scope.demo = Demo.get( { demoId: $scope.demo_id }, 
            function(demo) { 
              $scope.PreprocessDemo($scope,demo)
              $scope.ThumbnailSize = demo.general.thumbail_size;
            } );
      
      $scope.renderHtml = function(html_code)
      {
        if (angular.isArray(html_code)) {
          return $sce.trustAsHtml(html_code.join(' '));
        } else {
          return $sce.trustAsHtml(html_code);
        }
      };
        $http.get(blob_server+'/get_blobs_of_demo_by_name_ws?demo_name='+demo_id)
        .success(function(demoblobs) {
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
                //console.info("html_params:",blobset[0].html_params);
              }
            )
            $scope.demoblobs=demoblobs;
          }
        );
      
      $scope.uploaded_images = [];
      
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
          
          if (typeof $scope.selected_image === "object") {
              $scope.selected_image_link = $scope.blob_server+'/blob_directory/'+ 
                $scope.selected_image.hash + $scope.selected_image.extension;
          }
//           else {
//             if ($scope.selected_image.indexOf('.png') > -1) {
//               $scope.selected_image_link = 'img/demos/' + $scope.demo.id + 
//                                               '/uploaded/' +
//                                               $scope.selected_image;
//             } else {
//               $scope.selected_image_link = 'img/demos/' + $scope.demo.id + '/' + 
//                                               $scope.selected_image+'.png';
//             }
//           }
        }
      }

  }
  ]
);

/*---------------- DemoParamCtrl ---------------------------------------------*/
IPOLDemoControllers.controller('DemoParamCtrl', 
                              ['$scope', '$sce', '$location', 'demo_id', 'demo_key', 'Demo', 'Meta', 'Params', 
    function($scope, $sce, $location, demo_id, demo_key, Demo, Meta, Params ) {
      $scope.current_scope = $scope;
      $scope.demo_key = demo_key;
      $scope.demo_id = demo_id;
      $scope.Math = window.Math;
      $scope.maxdim=768;
//       $scope.imwidth=1024;
//       $scope.imheight=1024;
      $scope.display_ratio=1;
      //$scope.InputCropped=false;
      $scope.CropInfo = { enabled:false, coord:{ x: 0, y:0, w :100, h:100 } , 
                          minsize:{w:50,h:50} };
      $scope.got_meta = false;
      $scope.got_param= false;
      $scope.got_demo = false;
      $scope.demo     = {};
      $scope.params   = {};
      
      $scope.initParams = function($scope) {
        console.info("initParams");

        // initialize input loading status
        angular.forEach($scope.demo.inputs, 
          function(res) {
            res.status = "trying";
          }
        );

        // initialize parameter values
        angular.forEach($scope.demo.params, 
          function(param) {
            console.info(param.type);
            // range type
            if (param.type=='range') {
              if ($scope.params[param.id]==undefined) {
                param.value = param.values.default;
              } else {
                param.value = $scope.params[param.id];
              }
            }
            // selection_collapsed type
            if (param.type=='selection_collapsed') {
              if ($scope.params[param.id]==undefined) {
                param.value = param.default_value;
              } else {
                param.value = $scope.params[param.id].toString();
              }
            }
            // checkbox type
            if (param.type=='checkbox') {
              // if the variable xxx_checked (hidden input) is
              // not defined: use default value, otherwise, use
              // its value (we need this variable because checkboxes
              // are only returned if they are checked in html)
              if ($scope.params[param.id+"_checked"]==undefined) {
                param.value = param.default_value;
              } else {
                param.value = $scope.params[param.id+"_checked"];
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
                      if ($scope.params[param.id+"_"+key+"_checked"]==undefined) {
                        param.cb_values[key]=(param.default.indexOf(key)>-1);
                      } else {
                        param.cb_values[key]=$scope.params[param.id+"_"+key+"_checked"];
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

      $scope.updateCropInfo = function($scope) {
        if ($scope.params.x0!=undefined)
        {
          $scope.CropInfo.coord = {
            x:Math.round($scope.params.x0*$scope.display_ratio),
            y:Math.round($scope.params.y0*$scope.display_ratio),
            w:Math.round(($scope.params.x1-$scope.params.x0)*$scope.display_ratio),
            h:Math.round(($scope.params.y1-$scope.params.y0)*$scope.display_ratio)
          };

          // automatically enable/disable input InputCropped
          // NOTE: comparing to imwidth and imweight is not always correct since
          // they are the maximal dimensions over all inputs ...
          $scope.CropInfo.enabled = ($scope.params.x0!=0) ||
                                    ($scope.params.y0!=0) ||
                                    ($scope.params.x1!=$scope.imwidth) ||
                                    ($scope.params.y1!=$scope.imheight);
          
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
          console.info("params=",params);
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
        if (angular.isArray(html_code)) {
          return $sce.trustAsHtml(html_code.join(' '));
        } else {
          return $sce.trustAsHtml(html_code);
        }
      };
      
      $scope.DisableImage = function(inputinfo) { inputinfo.status = "failed";}
      $scope.LoadedImage  = function(inputinfo) { inputinfo.status = "loaded";}
      
      $scope.CheckString = function(v)
      {
        return angular.isString(v);
      };

      $scope.CheckArray = function(v)
      {
        return angular.isArray(v);
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
  [ '$scope', '$sce', '$parse', 'demo_id', 'demo_key', 
    'work_url', 'Demo', 'Meta', 'Params', 'Info',
    function($scope, $sce, $parse, demo_id, demo_key, work_url, Demo, Meta ,Params, Info ) 
    {

      $scope.initResults = function($scope) {
        console.info("initResults");
        // initialize parameter values
        angular.forEach($scope.demo.results, 
          function(res) {
            // range type
            if (res.type=='gallery') {
              var size = Object.keys(res.contents).length;
              res.status = new Array(size);
              for(var i=0;i<size;i++){
                  res.status[i] = "trying";
              }
            }
          }
        );
      }

      $scope.idx = 0;
      $scope.maxdim=768;
      $scope.current_scope = $scope;
      $scope.Math = window.Math;
      $scope.demo_id = demo_id;
      $scope.work_url = work_url;
      $scope.ZoomFactor = 1;
      // give some parameters to the demos for their own use
      $scope.display = { param1:'', param2:'', param3:''};
      Demo.get( { demoId: $scope.demo_id }, 
        function(demo) { 
          $scope.PreprocessDemo($scope,demo)
          $scope.demo = demo;
          $scope.initResults($scope);
          console.info($scope.demo)
        } 
      );
      $scope.params = Params.get( { key: demo_key },
        function(params) {  
          $scope.sizeX = params.x1-params.x0;
          $scope.sizeY = params.y1-params.y0;
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
        if (angular.isArray(html_code)) {
          return $sce.trustAsHtml(html_code.join(' '));
        } else {
          return $sce.trustAsHtml(html_code);
        }
      };
      
      $scope.CheckString = function(v)
      {
        return angular.isString(v);
      };

      $scope.CheckArray = function(v)
      {
        return angular.isArray(v);
      };
      
      $scope.CheckObject = function(v)
      {
        return angular.isObject(v);
      };
      
      $scope.DisableImage     = function(status,index) { status[index] = "failed"; }
      $scope.LoadedImage      = function(status,index) { status[index] = "loaded";}
      
      $scope.CheckLabelCondition = function(label, scope)
      {
          if(label.indexOf('?') === -1) return true;
          var c = label.split('?')[0];
          var value = $parse(c)(scope)
          return value;
      }
      
      $scope.GetLabel = function(label)
      {
          if(label.indexOf('?') === -1) 
              return label;
          else 
              return label.split('?')[1];
      }
    }
  ]
);

