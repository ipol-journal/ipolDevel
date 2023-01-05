$(document).ready(function () {
    let form = document.querySelectorAll('#editDemoExtras')[0];
    let input		 = form.querySelector('input[type="file"]'),
        label		 = form.querySelector('label'),
        errorMsg	 = form.querySelector('.file-upload-error'),
        droppedFiles = false,
        showFiles	 = function(files) {
            label.textContent = files[ 0 ].name;
        };

    [ 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop' ].forEach(function(event) {
        form.addEventListener(event, function(e) {
            // preventing the unwanted behaviours
            e.preventDefault();
            e.stopPropagation();
        });
    });
    [ 'dragover', 'dragenter' ].forEach(function(event) {
        form.addEventListener(event, function() {
            form.classList.add('is-dragover');
        });
    });
    [ 'dragleave', 'dragend', 'drop' ].forEach(function(event) {
        form.addEventListener(event, function() {
            form.classList.remove('is-dragover');
        });
    });
    form.addEventListener('drop', function(e) {
        showUploadingMessage()
        droppedFiles = e.dataTransfer.files;
        showFiles(droppedFiles);

        const formData = new FormData(form);
        if(droppedFiles) {
            Array.prototype.forEach.call(droppedFiles, function(file) {
                if (input.getAttribute('name')) {
                    formData.append(input.getAttribute('name'), file)
                }
            });

            let url = form.getAttribute('action')
            fetch(url, {
                method: 'POST',
                body: formData
            })
                .then(() => window.location.reload())
                .catch(() => {
                    showErrorMessage()
                })
        }
    });

    showErrorMessage = () => {
        $('.file-upload-error').removeClass('di-none');
        $('.extras-input-container').removeClass('di-none');
        $('.file-upload-uploading').addClass('di-none');
    }
    showUploadingMessage = (errorMsg) => {
        $('.extras-input-container').addClass('di-none');
        $('.file-upload-uploading').removeClass('di-none');
        $('.file-upload-error').addClass('di-none');
    }
});