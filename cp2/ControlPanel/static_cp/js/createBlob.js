var VRImage;
var csrftoken = getCookie('csrftoken');
var blobImage;
var template_id = getParameterByName('template_id');
var template_name = getParameterByName('template_name');
var demo_id = getParameterByName('demo_id');
let files = new Map();
let vrs = new Map();

$(document).ready(function() {
	function handleFileSelect(event) {
		event.stopPropagation();
		event.preventDefault();
		
		let addBtn = document.querySelector('#add-blobs-btn');
		addBtn.disabled = false;
		addBtn.addEventListener("click", uploadBlobs, false);

		let blobs = event.dataTransfer?.files || [...document.querySelector("#upload-input").files];

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
			blobUploads[i] = sendBlobs(blob, i);
		});
		Promise.allSettled(blobUploads)
			.then(results => {
				if (template_id) {
					window.location.href = `showTemplate?template_id=${template_id}&template_name=${template_name}`;
				} else {
					window.location.href = `showBlobsDemo?demo_id=${demo_id}`;
				}
			})
			.catch(error => {
				console.log(error);
			});
	}

	async function sendBlobs(blob, i) {
		const formData = new FormData();

		formData.append('csrfmiddlewaretoken', csrftoken);
		formData.append('Title', blob.querySelector('.title').value);
		formData.append('SET', blob.querySelector('.set').value);
		formData.append('PositionSet', blob.querySelector('.position').value);
		formData.append('Credit', blob.querySelector('.credit').value);
		formData.append('Blobs', files.get(i), 'asd');
		if (vrs.get(i)) {
			formData.append('VR', vrs.get(i), 'vr');
		}
		let url = '';
		if (template_id) {
			url = 'createBlob/template'
			destination = 'TemplateSelection';
			id = template_id;
		} else {
			url = 'createBlob/demo';
			destination = 'demo_id';
			id = demo_id;
		}
		formData.append(destination, id);
		return fetch(url, {
			method: 'POST',
			body: formData
		});
	}

	function clearPreview(event) {
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
	let uploadButton = document.querySelector("#upload-input");
	uploadButton.addEventListener("change", handleFileSelect, false);
	dropZone.addEventListener("dragover", handleDragOver, false);
	dropZone.addEventListener("drop", handleFileSelect, false);
});
