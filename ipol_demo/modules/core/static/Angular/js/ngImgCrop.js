'use strict';

//inject angular file upload directives and services.
var IPOLImgCrop = angular.module('IPOLImgCrop', ['ngImgCrop']);

IPOLImgCrop.controller('ImgCropCtrl', ['$scope', function($scope) {
  $scope.size='small';
  $scope.type='rectangle';
  $scope.resImageDataURI='';
  $scope.resImgFormat='image/png';
  $scope.resImgQuality=1;
  $scope.selMinSize=100;
  $scope.resImgSize=200;
  
  $scope.myImage='';
  $scope.myCroppedImage='';
  
}]);


