
    var templates_used = [];
    var csrftoken = getCookie('csrftoken');
    var section = document.querySelector('section');
    var request = new XMLHttpRequest();
    var request1 = new XMLHttpRequest();
    var request2 = new XMLHttpRequest();
    var demo_id = getParameterByName('demo_id');
    var title = getParameterByName('title');
    var modification = getParameterByName('modification');
    var state = getParameterByName('state');
    var templateSelection;
    document.getElementById("demo_id").innerHTML = demo_id;
    request.open('GET', '/api/blobs/get_demo_owned_blobs?demo_id=' + demo_id);
    request2.open('GET', '/api/blobs/get_all_templates');
    request2.send();
    request2.responseType = 'json';
    request1.open('GET', '/api/blobs/get_demo_templates?demo_id='+ demo_id);
    request1.responseType = 'json';
    request1.send();

    request1.onload = function() {
        var templates = request1.response;
        templates_used = templates['templates'];
        request.send();
        request.responseType = 'json';
        return templates_used;
    }

    request2.onload = function() {
        var allTemplatesList = request2.response;
        showTemplatesList(allTemplatesList);
    }

    request.onload = function() {
        var blobs = request.response;
        showBlobsAndTemplatesDemo(blobs, templates_used);
    }


    function add_the_template_to_DOM(){
        var H4 = document.createElement('h4');
        var href = document.createElement('a');
        href.setAttribute("href", "showTemplates?template="+templateSelection);
        href.textContent= templateSelection;
        blockTemplates.appendChild(H4);
        H4.appendChild(href);
        var buttonDelete = document.createElement('button');
        buttonDelete.textContent = "Unlink";
        buttonDelete.setAttribute("class", "buttonDelete")
        buttonDelete.setAttribute('id', templateSelection);
        buttonDelete.setAttribute("onclick", "remove_template_to_demo(this)");
        H4.appendChild(buttonDelete);
        templates_used.push(templateSelection);
        return templates_used;
    }


    function showBlobsAndTemplatesDemo(jsonObj, templates_used_for_demo) {
        var div = document.createElement('div');
        div.setAttribute("id", "blockTemplates");
        section.appendChild(div);
        for (var h=0; h< templates_used_for_demo.length; h++) {
            var H4 = document.createElement('h4');
            var href = document.createElement('a');
            href.setAttribute("href", "/cp2/showTemplates?template="+templates_used_for_demo[h] );
            href.textContent = templates_used_for_demo[h];
            var buttonDelete = document.createElement('button');
            buttonDelete.textContent = "Unlink";
            buttonDelete.setAttribute("class", "buttonDelete");
            buttonDelete.setAttribute('id', templates_used_for_demo[h]);
            buttonDelete.setAttribute("onclick", "remove_template_to_demo(this)")
            div.appendChild(H4);
            H4.appendChild(href);
            H4.appendChild(buttonDelete)
        }
        var blobsDemo = jsonObj['sets']
        for (var i = 0; i < blobsDemo.length; i++) {
            var Blobs = blobsDemo[i].blobs;
            var set_keys = Object.keys(Blobs);
            var myDiv1 = document.createElement('div');
            myDiv1.setAttribute("class", "block");
            var myH3 = document.createElement('h3');
            myH3.setAttribute("id", blobsDemo[i].name)
            myH3.textContent = "Title SET : " + blobsDemo[i].name;
            section.appendChild(myDiv1);
            myDiv1.appendChild(myH3);
            for (let blob_pos of set_keys) {
                blob = Blobs[blob_pos];
                var myDiv2 = document.createElement('div');
                myDiv2.setAttribute("class", "image_files");
                var myHref = document.createElement('a');
                myHref.setAttribute("href", "/cp2/detailsBlob?title=" + Blobs[blob_pos].title + "&set=" + blobsDemo[i].name + "&pos=" + blob_pos + "&credit=" + blob.credit + "&tags=" + blob.tags + "&thumbnail=" + blob.thumbnail + "&blob=" + blob.blob);
                var image_src = document.createElement('img');
                image_src.setAttribute("src", blob.thumbnail);
                var myPara2 = document.createElement('p');
                var removeBlobs = document.createElement('div');
                var button = document.createElement('button');
                button.setAttribute("class", "ButtonDelete");
                button.setAttribute('blobName', blobsDemo[i].name);
                button.setAttribute('blobSet', blob_pos)

                myPara2.textContent = "Credit: " + blob.credit;
                button.textContent = "Delete blob";

                myDiv1.appendChild(myDiv2);
                myDiv2.appendChild(myHref);
                myHref.appendChild(image_src);
                myDiv2.appendChild(myPara2);
                myDiv2.appendChild(removeBlobs);
                removeBlobs.appendChild(button);
            };
        };
    };

    function showTemplatesList(jsonObj) {
        templatesList = jsonObj['templates'];
        var dataList = document.createElement('datalist');
        dataList.setAttribute("id", "TemplateToDemo");
        var input = document.createElement('input');
        var label = document.createElement('label')
        label.setAttribute('for', 'TemplateToDemo');
        input.setAttribute("list", "TemplateToDemo");
        input.setAttribute("placeholder", "Add Template");
        input.setAttribute("id", "templateSelection");
        input.setAttribute("type", "text");
        for (var i = 0; i < templatesList.length; i++) {
            var option = document.createElement('option');
            option.textContent = templatesList[i];
            option.setAttribute("value", templatesList[i]);

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
            beforeSend: function(xhr, settings) {
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
                    alert("Template added to this demo")
                    add_the_template_to_DOM();
                } else {
                    alert("Error to added this demo to the template or any template selected")
                }
            },
        })
    };

        function remove_template_to_demo(monID) {
        templateSelection = monID.id;
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
                    document.location.href = "/cp2/showBlobsDemo?demo_id="+demo_id+"&title="+title+"&modification="+modification+"&state="+state;
                } else {
                    alert("Error to delete this template to the demo");
                }
            },
        })
    };