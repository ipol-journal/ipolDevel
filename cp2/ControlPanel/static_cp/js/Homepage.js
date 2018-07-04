
    /*-----------------------------------------Variables-----------------------------------------*/
    var csrftoken = getCookie('csrftoken');
    var numPageNext;
    var numPagePrev;
    var nbPage;
    var filter;
    var section = document.querySelector('section');
    var request = new XMLHttpRequest();

    /*-----------------------------------------HomePage-----------------------------------------*/

    

    request.open('GET', '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=1');
    request.responseType = 'json';
    request.send();
    request.onload = function() {
        var demo = request.response;
        showDemos(demo);
        paginationDemo(demo);
    }
    /*------Initialisation for document get ready---------*/
    if (!numPagePrev) {
        document.getElementById('previous_page').style.visibility= 'hidden';
        var ButtomNbPage = document.getElementById("pageMax");
        ButtomNbPage.style.borderRadius = "5px 0 0 5px";
    }

    /*-----------------------------------------JS Functions-----------------------------------------*/

    function showDemos(jsonObj) {
        var demoList = jsonObj['demo_list'];

        for (var i = 0; i < demoList.length; i++) {
            var Div = document.createElement('div');
            var myArticle = document.createElement('a');
            myArticle.setAttribute("href", "/cp2/showDemo?demo_id=" + demoList[i].editorsdemoid + "&title=" + demoList[i].title + "&modification=" + demoList[i].modification + "&state=" + demoList[i].state);
            Div.setAttribute("class", "listOfDemo");
            var myH2 = document.createElement('ul');
            myH2.setAttribute("class", "identity");
            var myDiv = document.createElement('div');
            myDiv.setAttribute("class", "DemoInformation");
            var myPara1 = document.createElement('li');
            var myPara2 = document.createElement('li');
            var myPara3 = document.createElement('li');
            myPara3.setAttribute("style", "width : 80%")
            var titleBold = document.createElement('b');
            titleBold.setAttribute("style", "color: black");
            var date = new Date(demoList[i].modification);
            var monthArray = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];


            myH2.textContent = 'ID:  ' + demoList[i].editorsdemoid;
            myPara1.textContent = 'last modification: ' + date.getDate() +"  "+ monthArray[date.getMonth()]+"  "+date.getFullYear();
            myPara2.textContent = 'State: ' + demoList[i].state;
            myPara3.textContent = 'Title: ';
            titleBold.textContent =  demoList[i].title;

            myArticle.appendChild(myH2);
            myArticle.appendChild(myDiv);
            myDiv.appendChild(myPara1);
            myDiv.appendChild(myPara2);
            myDiv.appendChild(myPara3);
            myPara3.appendChild(titleBold);

            section.appendChild(Div);
            Div.appendChild(myArticle);
        };
    }

    function cleanDemos() {
        $(".listOfDemo").remove();
    }

    function cleanPagination() {
        $('#next_page p').remove();
        $('#previous_page p').remove();
        $('.vider').remove();
    }

    function paginationDemo(jsonObj) {
        $('#next_page').append('<p><b>' + jsonObj.next_page_number + '</b></p>');
        if (!jsonObj.number) {
            $('pageMax').remove()
            $('#previous_page').append('<p><b> ' + jsonObj.previous_page_number + '</b></p>');
        }
        else {
            $('#pageMax').append( '<p class="vider">'+jsonObj.number+'</p>');
            $('#previous_page').append('<p><b> ' + jsonObj.previous_page_number + '</b></p>');
        }
        numPageNext = jsonObj.next_page_number;
        numPagePrev = jsonObj.previous_page_number;
        nbPage = jsonObj.number;
    }

    function checkPrevious() {
        if (!numPagePrev) {
            return false;
        } else {
            return true;
        }
    };

    function checkNext() {
        if (!numPageNext) {     
            return false;
        } else {
            return true;
        }
    }

    function showHideNext() {
        if (numPagePrev == (nbPage - 1) && !numPageNext) {
            document.getElementById('next_page').style.visibility= 'hidden';
            var ButtomNbPage = document.getElementById("pageMax");
            ButtomNbPage.style.borderRadius = "0 5px 5px 0";
            }
        else {
            document.getElementById('next_page').style.visibility= 'visible';            
            var ButtomNbPage = document.getElementById("pageMax");
            ButtomNbPage.style.borderRadius = "0";
        }
    }

    function HideButtonPage() {
        if (!numPageNext && !numPagePrev) {
            document.getElementById('next_page').style.visibility='hidden';
            document.getElementById('previous_page').style.visibility='hidden';
            var ButtomNbPage = document.getElementById("pageMax");
            ButtomNbPage.style.borderRadius = "5px 5px 5px 5px";
        }
        else {
            showHideNext();
            showHidePrev();
        }
    }

    function showHidePrev() {
        if ( numPageNext == "2" ) {
            document.getElementById('previous_page').style.visibility= 'hidden';
            var ButtomNbPage = document.getElementById("pageMax");
            ButtomNbPage.style.borderRadius = "5px 0 0 5px";
            }
        else {
            document.getElementById('previous_page').style.visibility= 'visible';
            var ButtomNbPage = document.getElementById("pageMax");
            ButtomNbPage.style.borderRadius = "0";
        }
    }

    function checkFilter() {
        if (!filter) {
            return false;
        } else {
            return true;
        }
    }

    $(document).ready(function() {
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
    /*-----------------------------------------Request AJAX-----------------------------------------*/

    /*Request AJAX for searching Demos*/

    $(function() {
        $("#action").click(function() {
            filter = $("#demo_selector").val();
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=1&qfilter=' + filter,
                success: function(data) {
                    cleanDemos();
                    cleanPagination();
                    showDemos(data);
                    paginationDemo(data);
                    HideButtonPage();
                    return filter;
                },
            });
            return false;
        });
    });


    /* Request AJAX for next page */

    $(function() {
        $("#next_page").click(function() {
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
                    showDemos(data);
                    paginationDemo(data);
                    showHideNext();
                    showHidePrev();
                },
            });
            return false;
        });
    });

    /* Request AJAX for previous page */

    $(function() {
        $("#previous_page").click(function() {
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
                    showDemos(data);
                    paginationDemo(data);
                    showHideNext();
                    showHidePrev();
                },
            });
            return false;
        });
    });


    $(function() {
        $("#pageMax").click(function() {
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
                    showDemos(data);
                    paginationDemo(data);
                    showHideNext();
                    showHidePrev();
                    HideButtonPage();
                },
            });
            return false;
        });
    });



function showModal(){
   var id = '#modal';
// $(id).html('<br><a >New Demo Data</a></br><input type="text" id="Template_name"/></br> <button class="close">Close</button> <button id="saveTemplate">Save</button>');
   $(id).html('<br><a >New Demo Data</a></br><select form="DemoForm" id="SelectDemoState"><option>Preprint</option><option>Published</option><option>Test</option><option>Workshop</option></select><form id="DemoForm"><p><label>Demo ID</label><input type="text" id="id_DemoId"></p><p><label>Title</label><input type="text" id="id_Title"></p></form><button id="ButtonAddDemo">SAVE</button><button class="close">CLOSE</button>');
   resizeModal();
   
   // Effet de transition     
   $('#fond').fadeIn(1000);   
   $('#fond').fadeTo("slow",0.7);
   // Effet de transition   
   $(id).fadeIn(2000);
   
   $('.popup .close').click(function (e) {
      // On désactive le comportement du lien
      e.preventDefault();
      // On cache la fenetre modale
      hideModal();
    });
}

function resizeModal(){
   var modal = $('#modal');
   // On récupère la largeur de l'écran et la hauteur de la page afin de cacher la totalité de l'écran
   var winH = $(document).height();
   var winW = $(document).width();
   
   // le fond aura la taille de l'écran
   $('#fond').css({'width':winW,'height':winH});
   
   // On récupère la hauteur et la largeur de l'écran
   // On met la fenêtre modale au centre de l'écran
   modal.css('top', winH/2 - modal.height()/2);
   modal.css('left', winW/2 - modal.width()/2);
}

function hideModal(){
   // On cache le fond et la fenêtre modale
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
                        alert("Redirection DemoList...")
                        document.location.href = "/cp2"
                    } else {
                        alert("Problem to add this Demo")
                    }
                },
            });
        });
    };