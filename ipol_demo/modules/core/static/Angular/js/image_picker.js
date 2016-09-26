
function ImagePickerCtrl($scope) {
    $scope.selectImage = function (image) {
        if($scope.selected_image === image) {
            $scope.selected_image = '';
        }
        else {
            $scope.selected_image = image;
        }
    }
}
