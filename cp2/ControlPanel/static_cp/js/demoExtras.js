$(document).ready(function () {
    $('#file').on('change', function() {
        let label = document.querySelector('.file-label');
        let filename = $(this).prop('files')[0].name;
        label.textContent = filename;
        $('#save-btn').prop('disabled', false);
    })

    // feature detection for drag&drop upload
    let isAdvancedUpload = function() {
        let div = document.createElement('div');
        return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window;
    }();

    let form = document.querySelectorAll('#editDemoExtras')[0];
    let input		 = form.querySelector('input[type="file"]'),
        label		 = form.querySelector('label'),
        errorMsg	 = form.querySelector('.file-upload-error'),
        droppedFiles = false,
        showFiles	 = function(files) {
            label.textContent = files[ 0 ].name;
        };

    // // automatically submit the form on file select
    // input.addEventListener('change', function(e) {
    //     showFiles(e.target.files);
    // });

    // drag&drop files if the feature is available
    if(isAdvancedUpload) {
        form.classList.add('has-advanced-upload'); // letting the CSS part to know drag&drop is supported by the browser

        [ 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop' ].forEach(function(event) {
            form.addEventListener(event, function(e)
            {
                // preventing the unwanted behaviours
                e.preventDefault();
                e.stopPropagation();
            });
        });
        [ 'dragover', 'dragenter' ].forEach(function(event)
        {
            form.addEventListener(event, function()
            {
                form.classList.add('is-dragover');
            });
        });
        [ 'dragleave', 'dragend', 'drop' ].forEach(function(event)
        {
            form.addEventListener(event, function() {
                form.classList.remove('is-dragover');
            });
        });
        form.addEventListener('drop', function(e) {
            $('#save-btn').prop('disabled', false);
            droppedFiles = e.dataTransfer.files; // the files that were dropped
            showFiles(droppedFiles);
        });
    }


    // if the form was submitted
    form.addEventListener('submit', function(e) {

        if(isAdvancedUpload) {
            e.preventDefault();

            const formData = new FormData(form);
            if(droppedFiles)
            {
                Array.prototype.forEach.call(droppedFiles, function(file) {
                    formData.append(input.getAttribute('name'), file)
                });

                const queryString = window.location.search;
                const urlParams = new URLSearchParams(queryString);
                formData.append('demo_id', urlParams.get('demo_id'))
                formData.append('title', urlParams.get('title'))
            }

            let url = form.getAttribute('action')
            fetch(url, {
                method: 'POST',
                body: formData
            })
                .then(response => {
                    console.log(response)
                    window.location.replace(response.url)
                })
        }
    });
});