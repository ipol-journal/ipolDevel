
    /*-----------------------------------------Variables-----------------------------------------*/
    var csrftoken = getCookie('csrftoken');
    var numPageNext;
    var numPagePrev;
    var nbPage;
    var filter;
    var section = document.querySelector('section');
    var get_demo_blobs = new XMLHttpRequest();

    /*-----------------------------------------HomePage-----------------------------------------*/

    $(document).ready(function(){
        get_demo_blobs.open('GET', '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=1');
        get_demo_blobs.responseType = 'json';
        get_demo_blobs.send();
        get_demo_blobs.onload = function() {
            var data = get_demo_blobs.response;
            showDemos(data['demo_list']);
            paginationDemo(data);
        }
        /*------Initialisation for document get ready---------*/


        if (!numPagePrev) {
            document.getElementById('previous_page').style.visibility= 'hidden';
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "5px 0 0 5px";
        } 

        $("#ButtonAddDemo").click(addDemos);
        $('#show').click(function (event) {
            event.preventDefault();
            showModal();
            addDemos();
        });
        $(window).resize(function () {
            resizeModal()
        });
    });
    /*-----------------------------------------JS Functions-----------------------------------------*/

    function showDemos(demoList) {
        for (var i = 0; i < demoList.length; i++) {
            var container = document.createElement('div');
            var demo = document.createElement('a');
            demo.setAttribute("href", "/cp2/showDemo?demo_id=" + demoList[i].editorsdemoid);
            container.setAttribute("class", "listOfDemo");
            var demoId = document.createElement('ul');
            demoId.setAttribute("class", "identity");
            var demoInformation = document.createElement('div');
            demoInformation.setAttribute("class", "DemoInformation");
            var lastModification = document.createElement('li');
            var state = document.createElement('li');
            var title = document.createElement('li');
            title.setAttribute("style", "width : 80%")
            var demoTitle = document.createElement('b');
            demoTitle.setAttribute("style", "color: black");
            var date = new Date(demoList[i].modification);
            var monthArray = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];


            demoId.textContent = 'ID:  ' + demoList[i].editorsdemoid;
            lastModification.textContent = 'last modification: ' + date.getDate() +"  "+ monthArray[date.getMonth()]+"  "+date.getFullYear();
            state.textContent = 'State: ' + demoList[i].state;
            title.textContent = 'Title: ';
            demoTitle.textContent =  demoList[i].title;

            demo.appendChild(demoId);
            demo.appendChild(demoInformation);
            demoInformation.appendChild(lastModification);
            demoInformation.appendChild(state);
            demoInformation.appendChild(title);
            title.appendChild(demoTitle);

            section.appendChild(container);
            container.appendChild(demo);
        };
    }

    function cleanDemos() {
        $(".listOfDemo").remove();
    }

    function cleanPagination() {
        $('#next_page p').remove();
        $('#previous_page p').remove();
        $('.pageCount').remove();
    }

    function paginationDemo(data) {
        $('#next_page').append('<p><b>' + data.next_page_number + '</b></p>');
        if (!data.number) {
            $('pageMax').remove()
            $('#previous_page').append('<p><b> ' + data.previous_page_number + '</b></p>');
        }
        else {
            $('#pageMax').append( '<p class="pageCount">'+data.number+'</p>');
            $('#previous_page').append('<p><b> ' + data.previous_page_number + '</b></p>');
        }
        numPageNext = data.next_page_number;
        numPagePrev = data.previous_page_number;
        nbPage = data.number;
    }

    function checkPrevious() {
        return numPagePrev ? true : false;
    };

    function checkNext() {
        return numPageNext ? true : false;
    }

    function showHideNext() {
        if (numPagePrev == (nbPage - 1) && !numPageNext) {
            document.getElementById('next_page').style.visibility= 'hidden';
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "0 5px 5px 0";
            }
        else {
            document.getElementById('next_page').style.visibility= 'visible';            
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "0";
        }
    }

    function HideButtonPage() {
        if (!numPageNext && !numPagePrev) {
            document.getElementById('next_page').style.visibility='hidden';
            document.getElementById('previous_page').style.visibility='hidden';
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "5px 5px 5px 5px";
        }
        else {
            showHideNext();
            showHidePrev();
        }
    }

    function showHidePrev() {
        if ( numPageNext == "2" ) {
            document.getElementById('previous_page').style.visibility= 'hidden';
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "5px 0 0 5px";
            }
        else {
            document.getElementById('previous_page').style.visibility= 'visible';
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "0";
        }
    }

    function checkFilter() {
        return filter ? true : false;
    }
    /*-----------------------------------------Request AJAX-----------------------------------------*/

    /*Request AJAX for searching Demos*/

    $(function() {
        $("#action").click(function(event) {
            event.preventDefault();
            filter = $("#demo_selector").val();
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=1&qfilter=' + filter,
                success: function(data) {
                    cleanDemos();
                    cleanPagination();
                    showDemos(data['demo_list']);
                    paginationDemo(data);
                    HideButtonPage();
                },
            });
        });



    /* Request AJAX for next page */

        $("#next_page").click(function(event) {
            event.preventDefault();
            $.ajax({
                beforeSend: function(xhr, settings) {
                    if (checkFilter()) {
                        settings.url += '&qfilter=' + filter;
                    }
                    return checkNext();
                },
                type: 'GET',
                dataType: 'json',
                url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=' + numPageNext,
                success: function(data) {
                    cleanDemos();
                    cleanPagination();
                    showDemos(data['demo_list']);
                    paginationDemo(data);
                    showHideNext();
                    showHidePrev();
                },
            });
        });

    /* Request AJAX for previous page */

        $("#previous_page").click(function(event) {
            event.preventDefault();
            $.ajax({
                beforeSend: function(xhr, settings) {
                    if (checkFilter()) {
                        settings.url += '&qfilter=' + filter;
                    }
                    return checkPrevious();
                },
                type: 'GET',
                dataType: 'json',
                url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=' + numPagePrev,
                success: function(data) {
                    cleanDemos();
                    cleanPagination();
                    showDemos(data['demo_list']);
                    paginationDemo(data);
                    showHideNext();
                    showHidePrev();
                },
            });
        });


        $("#pageMax").click(function(event) {
            event.preventDefault();
            $.ajax({
                beforeSend : function(xhr, settings) {
                    if (checkFilter()) {
                        settings.url += '&qfilter=' + filter;
                        }
                        return true;
                },
                type: 'GET',
                dataType: 'json',
                url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=' + nbPage,
                success: function(data) {
                    cleanDemos();
                    cleanPagination();
                    showDemos(data['demo_list']);
                    paginationDemo(data);
                    showHideNext();
                    showHidePrev();
                    HideButtonPage();
                },
            });
        });
    });



function showModal(){
   var id = '#modal';
   $(id).html('<br><a >New Demo Data</a></br><select form="DemoForm" id="SelectDemoState"><option>Preprint</option><option>Published</option><option>Test</option><option>Workshop</option></select><form id="DemoForm"><p><label>Demo ID</label><input type="text" id="id_DemoId"></p><p><label>Title</label><input type="text" id="id_Title"></p></form><button id="ButtonAddDemo">SAVE</button><button class="close">CLOSE</button>');
   resizeModal();
   
   $('#fond').fadeIn(1000)   
   $('#fond').fadeTo("slow",0.7);
   $(id).fadeIn(1000);
   
   $('.popup .close').click(function (event) {
      event.preventDefault();
      hideModal();
    });
}

function resizeModal(){
   var modal = $('#modal');
   var winH = $(document).height();
   var winW = $(document).width();
   
   $('#fond').css({'width':winW,'height':winH});
   
   modal.css('top', winH/2 - modal.height()/2);
   modal.css('left', winW/2 - modal.width()/2);
}

function hideModal(){
   $('#fond, .popup').hide();
   $('.popup').html('');
}

function addDemos() {
    $("#ButtonAddDemo").click(function () {
        $State = $("#SelectDemoState").val();
        $DemoId = $("#id_DemoId").val();
        $Title = $("#id_Title").val();
        $.ajax({
            url: 'addDemo/ajax',
            data: ({
                Title: $Title,
                DemoId: $DemoId,
                State: $State,
                csrfmiddlewaretoken: csrftoken
            }),
            type: 'POST',
            success: function(data) {
                if (data.status === 'OK') {
                    document.location.href = "/cp2/showDemo?demo_id="+ $DemoId
                } else {
                    alert("Problem to add this Demo")
                }
            },
        });
    });
};