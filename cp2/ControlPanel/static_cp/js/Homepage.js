
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
            // paginationDemo(data);
        }
        /*------Initialisation for document get ready---------*/
        $("#ButtonAddDemo").click(addDemos);
        $('#show').click(function (event) {
            event.preventDefault();
            showModal();
            addDemos();
        });
    });
    /*-----------------------------------------JS Functions-----------------------------------------*/

    function showDemos(demoList) {
        for (let demo of demoList) {
            let demoInfo = document.createElement('div');
            demoInfo.setAttribute("class", "demo-card");
            let editButton = document.createElement('a');
            editButton.setAttribute("href", "/cp2/showDemo?demo_id=" + demo.editorsdemoid);
            editButton.setAttribute('class', `btn`);
            editButton.textContent = `Edit demo`;
            let demoId = document.createElement('p');
            demoId.setAttribute("class", "demo-id");
            let lastModification = document.createElement('p');
            lastModification.setAttribute("class", "demo-date");
            let state = document.createElement('p');
            state.setAttribute("class", "demo-state");
            let demoTitle = document.createElement('h1');
            demoTitle.setAttribute("class", "demo-title");
            let seeDemoButton = document.createElement('a');
            seeDemoButton.setAttribute('href', `https://ipolcore.ipol.im/demo/clientApp/demo.html?id=${demo.editorsdemoid}`);
            seeDemoButton.setAttribute('class', `btn`);
            seeDemoButton.textContent =`Open demo`;
            seeDemoButton.target = '_blank';

            const date = new Date(demo.modification);
            const month = date.toLocaleString('default', { month: 'long' });

            demoId.textContent = `ID: ${demo.editorsdemoid}`;
            lastModification.textContent = `last modification: ${date.getDate()} ${month} ${date.getFullYear()}`;
            state.textContent = `State: ${demo.state}`;
            demoTitle.textContent = `Title: ${demo.title}`;

            demoInfo.appendChild(demoTitle);
            demoInfo.appendChild(demoId);
            demoInfo.appendChild(lastModification);
            demoInfo.appendChild(state);
            demoInfo.appendChild(seeDemoButton);
            demoInfo.appendChild(editButton);

            let demolistContainer = document.getElementById('demos-list');
            // demolistContainer.appendChild(demoInfo);
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
            }
        else {
            document.getElementById('next_page').style.visibility= 'visible';            
            var buttonNbPage = document.getElementById("pageMax");
        }
    }

    function HideButtonPage() {
        if (!numPageNext && !numPagePrev) {
            document.getElementById('next_page').style.visibility='hidden';
            document.getElementById('previous_page').style.visibility='hidden';
            var buttonNbPage = document.getElementById("pageMax");
            buttonNbPage.style.borderRadius = "5px";
        }
        else {
            showHideNext();
            showHidePrev();
        }
    }

    function checkFilter() {
        return filter ? true : false;
    }
    /*-----------------------------------------Request AJAX-----------------------------------------*/

    /*Request AJAX for searching Demos*/

    $(function() {
        // $("#action").click(function(event) {
        //     event.preventDefault();
        //     filter = $("#demo_selector").val();
        //     $.ajax({
        //         type: 'GET',
        //         dataType: 'json',
        //         url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=1&qfilter=' + filter,
        //         success: function(data) {
        //             cleanDemos();
        //             cleanPagination();
        //             showDemos(data['demo_list']);
        //             // paginationDemo(data);
        //             HideButtonPage();
        //         },
        //     });
        // });



    /* Request AJAX for next page */

        // $("#next_page").click(function(event) {
        //     event.preventDefault();
        //     $.ajax({
        //         beforeSend: function(xhr, settings) {
        //             if (checkFilter()) {
        //                 settings.url += '&qfilter=' + filter;
        //             }
        //             return checkNext();
        //         },
        //         type: 'GET',
        //         dataType: 'json',
        //         url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=' + numPageNext,
        //         success: function(data) {
        //             cleanDemos();
        //             cleanPagination();
        //             showDemos(data['demo_list']);
        //             paginationDemo(data);
        //         },
        //     });
        // });

    /* Request AJAX for previous page */

        // $("#previous_page").click(function(event) {
        //     event.preventDefault();
        //     $.ajax({
        //         beforeSend: function(xhr, settings) {
        //             if (checkFilter()) {
        //                 settings.url += '&qfilter=' + filter;
        //             }
        //             return checkPrevious();
        //         },
        //         type: 'GET',
        //         dataType: 'json',
        //         url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=' + numPagePrev,
        //         success: function(data) {
        //             cleanDemos();
        //             cleanPagination();
        //             showDemos(data['demo_list']);
        //             paginationDemo(data);
        //         },
        //     });
        // });


        // $("#pageMax").click(function(event) {
        //     event.preventDefault();
        //     $.ajax({
        //         beforeSend : function(xhr, settings) {
        //             if (checkFilter()) {
        //                 settings.url += '&qfilter=' + filter;
        //                 }
        //                 return true;
        //         },
        //         type: 'GET',
        //         dataType: 'json',
        //         url: '/api/demoinfo/demo_list_pagination_and_filter?num_elements_page=5&page=' + nbPage,
        //         success: function(data) {
        //             cleanDemos();
        //             cleanPagination();
        //             showDemos(data['demo_list']);
        //             // paginationDemo(data);
        //             HideButtonPage();
        //         },
        //     });
        // });
    });



function showModal(){
   var id = '#modal';
   $(id).html(`
        <h1>Create new demo</h1>
        <form id="DemoForm">
            <div id="newDemo-formFields">
                <label for="newDemoID">Demo ID: </label>
                <input type="text" id="newDemoID">
                <label for="newDemoTitle">Title: </label>
                <input type="text" id="newDemoTitle">
                <label for="SelectDemoState">State: </label>
                <select form="DemoForm" id="SelectDemoState">
                    <option>Preprint</option>
                    <option>Published</option>
                    <option>Test</option>
                    <option>Workshop</option>
                </select>
            </div>
            <div id="newDemo-buttons">
                <button id="ButtonAddDemo">Create</button>
                <button class="close">Cancel</button>
            </div>
        </form>
    `);

   
   $('#fond').fadeIn(500)   
   $('#fond').fadeTo("slow",0.7);
   $(id).fadeIn(300);
   
   $('.popup .close').click(function (event) {
      event.preventDefault();
      hideModal();
    });
}

function hideModal(){
   $('#fond, .popup').hide();
   $('.popup').html('');
}

function addDemos() {
    $("#ButtonAddDemo").click(function () {
        $State = $("#SelectDemoState").val();
        $DemoId = $("#newDemoID").val();
        $Title = $("#newDemoTitle").val();
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