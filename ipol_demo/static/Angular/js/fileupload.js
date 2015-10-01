'use strict';

//inject angular file upload directives and services.
var IPOLFileUpload = angular.module('IPOLFileUpload', ['ngFileUpload']);

IPOLFileUpload.controller('FileUploadCtrl', ['$scope', 'Upload', function ($scope, Upload) {
    $scope.$watch('files', function () {
        $scope.upload($scope.files);
    });

    $scope.upload = function (files) {
        if (files && files.length) {
            for (var i = 0; i < files.length; i++) {
                var file = files[i];
                var demo_id = $scope.$parent.$parent.demo.id;
                $scope.$parent.$parent.uploaded_images.push(file.name);
                
                Upload.upload({
                    url: './upload.php',
                    fields: {'username': $scope.username, 'demo_id' : demo_id },
                    file: file
                }).progress(function (evt) {
                    var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
                    console.log('progress: ' + progressPercentage + '% ' + evt.config.file.name);
                }).success(function (data, status, headers, config) {
                    console.log('file ' + config.file.name + 'uploaded. Response: ' + data);
                }).error(function (data, status, headers, config) {
                    console.log('error status: ' + status);
                })
            }
        }
    };
}]);