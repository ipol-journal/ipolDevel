var VRImage;
var csrftoken = getCookie('csrftoken');
var blobImage;
var template_id = getParameterByName('template_id');
var template_name = getParameterByName('template_name');
let files = new Map();
let vrs = new Map();

$(document).ready(function() {
	if (template_id) {
		var form = document.getElementById('editBlobForm');
		form.onsubmit = function(e) {
			e.preventDefault();
			let formData = new FormData();
			formData.append('Title', $('#title').val());
			formData.append('SET', $('#set').val());
			formData.append('PositionSet', $('#positionSet').val());
			formData.append('Credit', $('#credit').val());
			formData.append('Tags', $('#tags').val());
			formData.append('TemplateSelection', template_id);
			formData.append('Blobs', blobImage, blobImage.name);
			if (VRImage) {
				formData.append('VR', VRImage, VRImage.name);
			}
			formData.append('csrfmiddlewaretoken', csrftoken);
			$.ajax({
				url: 'createBlob/ajax',
				data: formData,
				cache: false,
				contentType: false,
				processData: false,
				type: 'POST',
				dataType: 'json',
				success: function(data) {
					if (data.status === 'OK') {
						document.location.href = `showTemplate?template_id=${template_id}&template_name=${template_name}`
					} else {
						alert("Error to add this Blob to the Template")
					}
				},
			})
		}
		// } else {
		//     let demo_id = getParameterByName('demo_id');
		//     update_edit_demo();
		//     var form = document.getElementById('editBlobForm');
		//     form.onsubmit = function(e) {
		//         e.preventDefault();
		//         var formData = new FormData();
		//         formData.append('SET', $('#set').val());
		//         formData.append('PositionSet', $('#positionSet').val());
		//         formData.append('Credit', $('#credit').val());
		//         formData.append('Tags', $('#tags').val());
		//         formData.append('demo_id', demo_id);
		//         formData.append('Blobs', blobImage, blobImage.name);
		//         if (VRImage) {
		//             formData.append('VR', VRImage, VRImage.name);
		//         }
		//         formData.append('csrfmiddlewaretoken', csrftoken);
		//         $.ajax({
		//             url: 'createBlob/ajax_demo',
		//             data: formData,
		//             cache: false,
		//             contentType: false,
		//             processData: false,
		//             type: 'POST',
		//             dataType: 'json',
		//             success: function(data) {
		//                 if (data.status === 'OK') {
		//                     document.location.href = `showBlobsDemo?demo_id=${demo_id}`
		//                 } else {
		//                     alert("Error to add this Blob to the demo")
		//                 }
		//             },
		//         })
		//     }
		
		function update_edit_demo() {
			$.ajax({
				data: ({
					demoID: demo_id,
					csrfmiddlewaretoken: csrftoken,
				}),
				dataType: 'json',
				type: 'POST',
				url: 'showDemo/ajax_user_can_edit_demo',
				success: function(data) {
					if (data.can_edit === 'NO') {
						alert("You are not allowed to edit this blob")
						$('#ButtonAddBlob').remove();
					}
					
				},
			});
		};
	}

	function handleFileSelect(event) {
		event.stopPropagation();
		event.preventDefault();
		
		let addBtn = document.querySelector('#add-blobs-btn');
		addBtn.disabled = false;
		addBtn.addEventListener("click", uploadBlobs, false);

		let blobs = event.dataTransfer.files;

		[...blobs].forEach((file, i) => {
			let reader = new FileReader();
			let filename = file.name.substring(0, file.name.lastIndexOf("."))
			reader.onload = (file) => {
				let uploadList = document.getElementById("upload-list");
				let nBlobs = uploadList.childElementCount;

				let uploadItem = document.createElement("div");
				uploadItem.classList.add("upload-item");
				uploadItem.id = `upload-item-${nBlobs}`;
				
				let details = document.createElement("div");
				details.classList.add("details");
				uploadItem.appendChild(details);
				
				let titleInput = document.createElement("input");
				titleInput.type = "text";
				titleInput.value = filename;
				titleInput.classList.add("title");
				titleInput.placeholder = "Title";
				details.appendChild(titleInput);
				
				let blobsetInput = document.createElement("input");
				blobsetInput.type = "text";
				blobsetInput.classList.add("set");
				blobsetInput.placeholder = "Set";
				details.appendChild(blobsetInput);
				
				let position = document.createElement("input");
				position.type = "number";
				position.classList.add("position");
				position.value = i;
				position.placeholder = "Position in set";
				details.appendChild(position);
				
				let creditInput = document.createElement("input");
				creditInput.type = "text";
				creditInput.classList.add("credit");
				creditInput.placeholder = "Credit";
				details.appendChild(creditInput);
				
				let vrInput = document.createElement("div");
				vrInput.id = nBlobs;
				vrInput.classList.add("vr-input");

				let preview = document.createElement("img");
				preview.classList.add("preview");
				preview.setAttribute("onError", "setBrokenImage(this)");
				preview.src = reader.result;
				uploadItem.appendChild(preview);
				
				let vrText = document.createElement("p");
				vrText.id = `vr-text-${nBlobs}`;
				vrText.classList.add = 'vr-text';
				vrText.textContent = 'Drop your Visual representation here';
				vrInput.append(vrText);
				
				let clearBtn = document.createElement("button");
				clearBtn.textContent = 'Clear';
				clearBtn.setAttribute('data-id', nBlobs);
				clearBtn.classList.add('di-none');
				clearBtn.addEventListener("click", clearPreview, false);
				vrInput.appendChild(clearBtn);
				
				uploadItem.appendChild(vrInput);
				vrInput.addEventListener("dragover", handleDragOver, false);
				vrInput.addEventListener("drop", handleVRSelected, false);

				uploadList.appendChild(uploadItem);
			}

			reader.readAsDataURL(file);
			files.set(files.size, file)
		})

	}
	
	function uploadBlobs() {
		let blobs = document.querySelectorAll('#upload-list > div');
		let blobUploads = [];
		blobs.forEach((blob, i) => {
			blobUploads[i] = sendBlob(blob, i);
		});
		Promise.allSettled(blobUploads)
			.then(response => {
				console.log(response);
			})
			.catch(error => console.log(error));
	}

	async function sendBlob(blob, i) {
		console.log(blob, blob.querySelector('.preview'));
		const formData = new FormData();

		formData.append('csrfmiddlewaretoken', csrftoken);
		formData.append('Title', blob.querySelector('.title').value);
		formData.append('SET', blob.querySelector('.set').value);
		formData.append('PositionSet', blob.querySelector('.position').value);
		formData.append('Credit', blob.querySelector('.credit').value);
		formData.append('demo_id', getParameterByName('demo_id'));
		formData.append('Blobs', files.get(i), 'asd');
		if (vrs.get(i)) {
			formData.append('VR', vrs.get(i), 'vr');
		}

		let url = 'createBlob/ajax_demo';
		return fetch(url, {
			method: 'POST',
			body: formData
		});
	}

	function clearPreview(event) {
		console.log(this);
		let id = parseInt(this.getAttribute('data-id'));
		document.querySelector(`#vr-${id}`).remove();
		vrs.delete(id);
		this.classList.add('di-none');
	}
	
	function handleVRSelected(event) {
		event.stopPropagation();
		event.preventDefault();
		
		let file = event.dataTransfer.files[0];
		let index = event.currentTarget.id;
		vrs.set(parseInt(index), file);
		let reader = new FileReader();
		reader.onload = (function(theFile) {
			return function(e) {
				let imgSource = e.target.result;
				let preview = document.createElement("img");
				preview.classList.add("vr-preview-img");
				preview.id = `vr-${index}`;
				preview.src = imgSource;
				event.target.appendChild(preview);
			}
		})(file);
		
		let btn = this.querySelector('button');
		btn.classList.remove('di-none');
		
		reader.readAsDataURL(file);
	}
	
	function handleDragOver(event) {
		event.stopPropagation();
		event.preventDefault();
		event.dataTransfer.dropEffect = "copy";
	}
	
	let dropZone = document.getElementById("upload-container");
	dropZone.addEventListener("dragover", handleDragOver, false);
	dropZone.addEventListener("drop", handleFileSelect, false);
});
