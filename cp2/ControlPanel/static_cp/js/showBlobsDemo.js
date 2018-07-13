
    var templates_used = [];
    var csrftoken = getCookie('csrftoken');
    var section = document.querySelector('section');
    var demo_id = getParameterByName('demo_id');
    var templateSelection;
    
    $(document).ready(function(){
        var get_demo_blobs = new XMLHttpRequest();
        var get_demo_using_the_template = new XMLHttpRequest();
        var get_all_templates = new XMLHttpRequest();
        document.getElementById("demo_id").innerHTML = demo_id;
        var previousPage = document.getElementById("goPreviousPage");
        previousPage.setAttribute("href", "/cp2/showDemo?demo_id="+demo_id);
        get_demo_blobs.open('GET', '/api/blobs/get_demo_owned_blobs?demo_id=' + demo_id);
        get_all_templates.open('GET', '/api/blobs/get_all_templates');
        get_all_templates.send();
        get_all_templates.responseType = 'json';
        get_demo_using_the_template.open('GET', '/api/blobs/get_demo_templates?demo_id='+ demo_id);
        get_demo_using_the_template.responseType = 'json';
        get_demo_using_the_template.send();

        get_demo_using_the_template.onload = function() {
            var templates = get_demo_using_the_template.response;
            templates_used = templates['templates'];
            get_demo_blobs.send();
            get_demo_blobs.responseType = 'json';
            return templates_used;
        }

        get_all_templates.onload = function() {
            var allTemplatesList = get_all_templates.response;
            var templates = allTemplatesList['templates'];
            showTemplatesList(templates);
        }

        get_demo_blobs.onload = function() {
            var blobs = get_demo_blobs.response;
            var sets = blobs['sets'];
            showBlobsAndTemplatesDemo(sets, templates_used);
            update_edit_demo();
            deleteBlob();
        }
    });

    function add_the_template(){
        var templateName = document.createElement('h4');
        var templateRef = document.createElement('a');
        templateRef.setAttribute("href", "showTemplates?template="+templateSelection);
        templateRef.textContent= templateSelection;
        blockTemplates.appendChild(templateName);
        templateName.appendChild(templateRef);
        var buttonDelete = document.createElement('button');
        buttonDelete.textContent = "Unlink";
        buttonDelete.setAttribute("class", "buttonDelete")
        buttonDelete.setAttribute('id', templateSelection);
        buttonDelete.setAttribute("onclick", "remove_template_to_demo(this)");
        templateName.appendChild(buttonDelete);
        templates_used.push(templateSelection);
        //return templates_used;
    }


    function showBlobsAndTemplatesDemo(sets, templates_used) {
        var blockTemplates = document.createElement('div');
        blockTemplates.setAttribute("id", "blockTemplates");
        section.appendChild(blockTemplates);
        for (var i=0; i< templates_used.length; i++) {
            var templateName = document.createElement('h4');
            var templateRef = document.createElement('a');
            templateRef.setAttribute("href", "/cp2/showTemplates?template="+templates_used[i] );
            templateRef.textContent = templates_used[i];
            var buttonDelete = document.createElement('button');
            buttonDelete.textContent = "Unlink";
            buttonDelete.setAttribute("class", "buttonDelete");
            buttonDelete.setAttribute('id', templates_used[i]);
            buttonDelete.setAttribute("onclick", "remove_template_to_demo(this)")
            blockTemplates.appendChild(templateName);
            templateName.appendChild(templateRef);
            templateName.appendChild(buttonDelete)
        }
        for (var i = 0; i < sets.length; i++) {
            var Blobs = sets[i].blobs;
            var set_keys = Object.keys(Blobs);
            var block = document.createElement('div');
            block.setAttribute("class", "block");
            var titleSet = document.createElement('h3');
            titleSet.setAttribute("id", sets[i].name)
            titleSet.textContent = "Title SET : " + sets[i].name;
            section.appendChild(block);
            block.appendChild(titleSet);
            for (let blob_pos of set_keys) {
                blob = Blobs[blob_pos];
                var image = document.createElement('div');
                image.setAttribute("class", "image_files");
                var imageRef = document.createElement('a');
                imageRef.setAttribute("href", "/cp2/detailsBlob?demo_id="+demo_id+"&set="+ sets[i].name+"&pos="+blob_pos)
                //console.log("set="+sets[i].name+"\npos="+blob_pos);
                var image_src = document.createElement('img');
                image_src.setAttribute("src", blob.thumbnail);
                var credit = document.createElement('p');
                var removeBlobs = document.createElement('div');
                var remobeBlobsButton = document.createElement('button');
                remobeBlobsButton.setAttribute("class", "buttonDelete");
                remobeBlobsButton.setAttribute('blobName', sets[i].name);
                remobeBlobsButton.setAttribute('blobSet', blob_pos)

                credit.textContent = "Credit: " + blob.credit;
                remobeBlobsButton.textContent = "Delete blob";

                block.appendChild(image);
                image.appendChild(imageRef);
                imageRef.appendChild(image_src);
                image.appendChild(credit);
                image.appendChild(removeBlobs);
                removeBlobs.appendChild(remobeBlobsButton);
            };
        };
    };

    function showTemplatesList(templates) {
        var dataList = document.createElement('datalist');
        dataList.setAttribute("id", "templateToDemo");
        var input = document.createElement('input');
        var label = document.createElement('label')
        label.setAttribute('for', 'templateToDemo');
        input.setAttribute("list", "templateToDemo");
        input.setAttribute("placeholder", "Add Template");
        input.setAttribute("id", "templateSelection");
        input.setAttribute("type", "text");
        for (var i = 0; i < templates.length; i++) {
            var option = document.createElement('option');
            option.textContent = templates[i];
            option.setAttribute("value", templates[i]);
            section.appendChild(label);
            section.appendChild(input);
            section.appendChild(dataList);
            dataList.appendChild(option);
        };
        var inputValidation = document.createElement('button');
        inputValidation.setAttribute("id", "buttonAddTemplate");
        inputValidation.setAttribute("onclick", "add_template_to_demo()");
        inputValidation.textContent = "SAVE";
        section.appendChild(inputValidation);
    }

    function add_template_to_demo() {
        templateSelection = document.getElementById("templateSelection").value;
        $.ajax({
            beforeSend: function() {
                if (templates_used.includes(templateSelection)){
                    alert("This demo is already used")
                    return false
                }
                else {
                    return true
                }
            },
            data: ({
                demoId: demo_id,
                template_name: templateSelection,
                csrfmiddlewaretoken: csrftoken,
            }),
            url: 'showBlobsDemo/ajax_add_template_to_demo',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                if (data.status === 'OK') {
                    add_the_template();
                } else {
                    alert("Error to added the template to this demo or any template selected")
                }
            },
        })
    };

        function remove_template_to_demo(template) {
        templateSelection = template.id;
        $.ajax({
            data: ({
                demoId: demo_id,
                template_name: templateSelection,
                csrfmiddlewaretoken: csrftoken,
            }),
            url: 'showBlobsDemo/ajax_remove_template_to_demo',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                if (data.status === 'OK') {
                    document.location.href = "/cp2/showBlobsDemo?demo_id="+demo_id;
                } else {
                    alert("Error to delete this template from the demo");
                }
            },
        })
    };



    function update_edit_demo() {
        $.ajax({
            data: ({
                demoID: demo_id,
                csrfmiddlewaretoken: csrftoken,
            }),
            dataType : 'json',
            type: 'POST',
            url: 'showDemo/ajax_user_can_edit_demo',
            success: function(data) {
                if (data.can_edit === 'NO') {
                    var not_allowed = document.createElement('h3');
                    not_allowed.textContent = "You are not allowed to edit this demo"
                    can_edit.appendChild(not_allowed);
                    $('#buttonAddTemplate').remove(); 
                    $('.buttonDelete').remove();
                }
            },
        });
    };


    function deleteBlob() {
        $("button.buttonDelete").click(function () {
            var blobSelection = $(this).attr('blobName');
            var $pos_set = $(this).attr('blobSet')
            $.ajax({
                beforeSend: function() {
                    return (confirm("Are you sure to deleted this blob?"))
                    },
                data : ({
                    blob_set : blobSelection,
                    demo_id : demo_id,
                    pos_set : $pos_set,
                    csrfmiddlewaretoken: csrftoken,
                }),
                type: 'POST',
                dataType: 'json',
                url: 'showBlobsDemo/ajax',
                success: function(data) {
                    if (data.status === 'OK') {
                        document.location.href = "showBlobsDemo?demo_id="+demo_id
                    } else {
                        alert("Error to delete this blob");
                    }
                },
            })
        });
    };