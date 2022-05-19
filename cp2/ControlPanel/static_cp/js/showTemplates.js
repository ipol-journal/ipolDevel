var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var get_demo_blobs = new XMLHttpRequest();
var get_demo_using_the_template = new XMLHttpRequest();
var template_id = getParameterByName('template_id');
var template_name = getParameterByName('template_name');

get_demo_blobs.open('GET', '/api/blobs/get_template_blobs?template_id='+template_id);
get_demo_using_the_template.open('GET','/api/blobs/get_demos_using_the_template?template_id='+template_id);
get_demo_blobs.responseType = 'json';
get_demo_using_the_template.responseType = 'json';
get_demo_blobs.send();
get_demo_using_the_template.send();
get_demo_blobs.onload = function() {
    var templates = get_demo_blobs.response;
    var demo = get_demo_using_the_template.response;
    var sets = templates['sets'];
    // showTemplates(sets);
    // deleteBlob();
    // deleteTemplates();
    // var demos = demo?.['demos'] || null;
    // if (demos) show_demo_using_template(demos);
}


function showTemplates(sets) {
   $("#addBlob").attr('href', `/cp2/createBlob?template_id=${template_id}&template_name=${template_name}`);

   
    for (var i = 0; i < sets.length; i++) {
        var Blobs = sets[i].blobs;
        var set_keys = Object.keys(Blobs);
            var block = document.createElement('div');
            block.setAttribute("class","block");
            var titleSet = document.createElement('h3');
            titleSet.setAttribute("id", sets[i].name)
            titleSet.textContent = "Title SET : "+sets[i].name;
            section.appendChild(titleSet);
            section.appendChild(block);
            for (let blob_pos of set_keys ) {
            detailsBlob = Blobs[blob_pos];
            var image = document.createElement('div');
            image.setAttribute("class","image_files");
            var blobDetails = document.createElement('a');
            blobDetails.setAttribute("href", `/cp2/detailsBlob?&template_id=${template_id}&template_name=${template_name}&set=${sets[i].name}&pos=${blob_pos}`);
            var image_src = document.createElement('img');
            image_src.setAttribute("src",detailsBlob.thumbnail);
            image_src.setAttribute("onError", "setBrokenImage(this)");
            image_src.setAttribute("style", "margin-right: 25px");
            var removeBlobs = document.createElement('div');
            var button = document.createElement('button');
            button.setAttribute("class","buttonDelete");
            button.setAttribute('blobName', sets[i].name);
            button.setAttribute('blobSet', blob_pos)
            titleSet.textContent = "Title SET : "+sets[i].name;
            button.textContent = "Delete blob";
            block.appendChild(image)
            image.appendChild(blobDetails);
            blobDetails.appendChild(image_src);
            image.appendChild(removeBlobs);
            removeBlobs.appendChild(button);
        };
    };
    var demos = document.createElement('h2');
    demos.textContent = "Demos using this template"
        .appendChild(demos);   
};

function show_demo_using_template(demos){
    for (var i = 0; i < demos.length; i++) {
        var demoUsingTemplate = document.createElement('div');
        demoUsingTemplate.setAttribute("class", "demoUsingTemplate");
        var showBlobsDemo = document.createElement('a');
        showBlobsDemo.setAttribute("href", "/cp2/showBlobsDemo?demo_id="+demos[i]);

        showBlobsDemo.textContent = "ID: "+demos[i];
        section.appendChild(demoUsingTemplate);
        demoUsingTemplate.appendChild(showBlobsDemo);
    };  
};



function deleteBlob() {
    $("button.buttonDelete").click(function () {
        var blobSelection = $(this).attr('blobName');
        var $pos_set = $(this).attr('blobSet')
        $.ajax({
            beforeSend: function(xhr, settings) {
                return (confirm("Are you sure?"))
                },
            data : ({
                blob_set : blobSelection,
                template_id : template_id,
                pos_set : $pos_set,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            dataType: 'json',
            url: 'showTemplates/ajax',
            success: function(data) {
                if (data.status === 'OK') {
                    document.location.href = `/cp2/showTemplates?template_id=${template_id}&template_name=${template_name}`
                } else {
                    alert("Error to delete this Blob");
                }
            },
        })
    });
};


$("button#deleteTemplate").click(function () {
    $.ajax({
        beforeSend: function (xhr, settings) {
            return (confirm("Are you sure?"))
        },
        data : ({
            template_id : template_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        type : 'POST',
        dataType : 'json',
        url : 'showTemplates/ajax_delete_template',
        success : function (data) {
            if (data.status === 'OK') {
                document.location.href = "/cp2/templates"
            } else {
                alert("Error to delete this template")
            }
        },
    });
});