var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var request = new XMLHttpRequest();
var request1 = new XMLHttpRequest();
var templateSelection = getParameterByName('template');
document.getElementById("nameOfTemplate").innerHTML = templateSelection;
nameOfTemplate.setAttribute("style", "text-decoration: underline");

// a faire quand on clique sur l'image du blob dans le template

request.open('GET', '/api/blobs/get_template_blobs?template_name='+templateSelection);
request1.open('GET','/api/blobs/get_demos_using_the_template?template_name='+templateSelection);
request.responseType = 'json';
request1.responseType = 'json';
request.send();
request1.send();
request.onload = function() {
    var templates = request.response;
    var demos = request1.response;
    showTemplates(templates);
    deleteBlob();
    deleteTemplates();
    show_demo_using_template(demos);   
}

//changer les noms de variable 

function showTemplates(jsonObj) {
    var blobsList = jsonObj['sets'];
   $("#addBlob").attr('href', '/cp2/createBlob?template='+templateSelection);

   
    for (var i = 0; i < blobsList.length; i++) {
        var Blobs = blobsList[i].blobs;
        var set_keys = Object.keys(Blobs);
            var myDiv1 = document.createElement('div');
            myDiv1.setAttribute("class","block");
            var myH3 = document.createElement('h3');
            myH3.setAttribute("id", blobsList[i].name)
            myH3.textContent = "Title SET : "+blobsList[i].name;
            section.appendChild(myH3);
            section.appendChild(myDiv1);
            for (let blob_pos of set_keys ) {
            blob = Blobs[blob_pos];
            var myDiv2 = document.createElement('div');
            myDiv2.setAttribute("class","image_files");
            var myHref = document.createElement('a');
            myHref.setAttribute("href", "/cp2/detailsBlob?title="+Blobs[blob_pos].title+"&set="+blobsList[i].name+"&pos="+blob_pos+"&credit="+blob.credit+"&tags="+blob.tags+"&thumbnail="+blob.thumbnail+"&template="+templateSelection+"&vr="+blob.vr+"&id="+blob.id+"&blob="+blob.blob);
            var image_src = document.createElement('img');
            image_src.setAttribute("src",blob.thumbnail);
            image_src.setAttribute("style", "margin-right: 25px");
            var removeBlobs = document.createElement('div');
            var button = document.createElement('button');
            button.setAttribute("class","ButtonDelete");
            button.setAttribute('blobName', blobsList[i].name);
            button.setAttribute('blobSet', blob_pos)
            myH3.textContent = "Title SET : "+blobsList[i].name;
            button.textContent = "Delete blob";
            myDiv1.appendChild(myDiv2)
            myDiv2.appendChild(myHref);
            myHref.appendChild(image_src);
            myDiv2.appendChild(removeBlobs);
            removeBlobs.appendChild(button);
        };
    };
    var myH2 = document.createElement('h2');
    myH2.textContent = "Demos using this template"
    section.appendChild(myH2);   
};

function show_demo_using_template(jsonObj){
    var demos_using_template = jsonObj['demos']
    for (var i = 0; i < demos_using_template.length; i++) {
        var myDiv = document.createElement('div');
        myDiv.setAttribute("class", "demoUsingTemplate");
        var myHref = document.createElement('a');
        myHref.setAttribute("href", "/cp2/showBlobsDemo?demo_id="+demos_using_template[i]);

        myHref.textContent = "ID: "+demos_using_template[i];
        section.appendChild(myDiv);
        myDiv.appendChild(myHref);
    };  
};



function deleteBlob() {
    $("button.ButtonDelete").click(function () {
        var blobSelection = $(this).attr('blobName');
        var $pos_set = $(this).attr('blobSet')
        $.ajax({
            beforeSend: function(xhr, settings) {
                return (confirm("Are you sure?"))
                },
            data : ({
                blob_set : blobSelection,
                template_name : templateSelection,
                pos_set : $pos_set,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            dataType: 'json',
            url: 'showTemplates/ajax',
            success: function(data) {
                if (data.status === 'OK') {
                    alert("Blob Deleted! ")
                    document.location.href = "/cp2/showTemplates?template="+templateSelection
                } else {
                    alert("Error to delete this Blob");
                }
            },
        })
    });
};

function deleteTemplates() {
    $("button#deleteTemplate").click(function () {
        $.ajax({
            beforeSend: function (xhr, settings) {
                return (confirm("Are you sure?"))
            },
            data : ({
                template_name : templateSelection,
                csrfmiddlewaretoken: csrftoken,
            }),
            type : 'POST',
            dataType : 'json',
            url : 'showTemplates/ajax_delete_template',
            success : function (data) {
                if (data.status === 'OK') {
                    alert("template deleted! ")
                    document.location.href = "/cp2/templates"
                } else {
                    alert("Error to delete this template")
                }
            },
        });
    });
};