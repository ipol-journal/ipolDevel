var inpaintingController = inpaintingController || {};

let canvas, context;
let tool;
let tools = {};
let inpaintingControls = [];
let nDots;

inpaintingController.init = (index, blobSrc, canvasElement) => {
  canvas = canvasElement;
  context = canvas.getContext('2d');
  nDots = ddl.inputs[index].max_dots;
  if (!inpaintingControls[index]) {
    tool = new tools[ddl.inputs[index].control];
    inpaintingControls[index] = tool;
  } else {
    tool = inpaintingControls[index];
  }
  
  $(canvas).mousedown(canvas_event);
  $(canvas).mousemove(canvas_event);
  $(canvas).mouseup(canvas_event);

  $('#color-picker').change(setStyle);
  $('#size-selector').change(setStyle);
  $("#closeFigure").change(tool.draw);
  
  getBlobData(blobSrc).then(() => {
    setStyle();
    if (inpaintingControls[index]) tool.draw();
  });
}

canvas_event = (ev) => {
  if (ev.layerX || ev.layerX == 0) { // Firefox
    ev._x = ev.layerX;
    ev._y = ev.layerY;
  } else if (ev.offsetX || ev.offsetX == 0) { // Opera
    ev._x = ev.offsetX;
    ev._y = ev.offsetY;
  }

  // Call the event handler of the tool.
  var tool_handler = tool[ev.type];
  if (tool_handler) {
    tool_handler(ev);
  }
}

const getBlobData = async (path) => {
  let background;
  if (!background) background = await loadImage(path);
  canvas.height = background.height;
  canvas.width = background.width;
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    var img = new Image();
    img.onload = () => resolve(img);
    img.src = src;
  });
}

function setStyle() {
  context.strokeStyle = $('#color-picker').val();
  context.lineWidth = $('#size-selector').val();
  context.lineCap = "round";
  context.lineJoin = "round";
  context.save();
}

function resetCanvas() {
  context.beginPath();
  // Use the identity matrix while clearing the canvas
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.clearRect(0, 0, canvas.width, canvas.height);
}

function erase() {
  resetCanvas();
  tool.eraseCoords();
}

//########################################################################
tools.mask = function () {
  let tool = this;
  this.started = false;
  this.lastX = 0;
  this.lastY = 0;
  let backwardsPoints = [$('#editor-blob-left')[0].toDataURL()];
  let forwardsPoints = [];

  this.mousedown = (ev) => {
    tool.started = true;
    tool.drawStroke(ev._x, ev._y, false);
  }

  this.mousemove = (ev) => {
    if (tool.started) {
      tool.drawStroke(ev._x, ev._y, true);
    }
  }

  this.mouseup = (ev) => {
    if (tool.started) {
      tool.mousemove(ev);
      tool.started = false;
      tool.push();
    }
  }

  this.drawStroke = (x, y, started) => {
    if (started) {
      context.beginPath();
      context.moveTo(tool.lastX, tool.lastY);
      context.lineTo(x, y);
      context.stroke();
    }
    tool.lastX = x;
    tool.lastY = y;
  }

  this.push = () => {
    forwardsPoints.length = 0;
    backwardsPoints.push($('#editor-blob-left')[0].toDataURL());
  }

  this.undo = () => {
    if (backwardsPoints.length > 1) {
      var lastPoint = backwardsPoints.pop();
      if (backwardsPoints.slice(-1)[0]) {
        tool.draw();
      }
      forwardsPoints.push(lastPoint);
    }
  }

  this.redo = () => {
    if (forwardsPoints.length > 0) {
      backwardsPoints.push(forwardsPoints.pop());
      tool.draw();
    }
  }

  this.draw = () => {
    var canvasPic = new Image();
    canvasPic.src = backwardsPoints[backwardsPoints.length - 1];
    canvasPic.onload = function() {
      resetCanvas();
      context.drawImage(canvasPic, 0, 0);
    }
  }

  this.getData = () => {
    let dataURL = canvas.toDataURL();
    return dataURLtoBlob(dataURL);
  }

  this.eraseCoords = ev => {
    backwardsPoints.length = 0;
    forwardsPoints.length = 0;
  }
};

tools.lines = function () {
  var tool = this;
  let backwardsPoints = [];
  let forwardsPoints = [];
  
  this.mousedown = (ev) => {
    backwardsPoints.push([ev._x, ev._y]);
    tool.draw();
    forwardsPoints.length = 0;
  }

  this.undo = () => { 
    if (backwardsPoints.length) {
      var lastPoint = backwardsPoints.pop();
      tool.draw();
      forwardsPoints.push(lastPoint);
    }
  }
  
  this.redo = () => {
    if (forwardsPoints.length > 0) {
      backwardsPoints.push(forwardsPoints.pop());
      tool.draw();
    }
  }

  this.draw = () => {
    resetCanvas();
    context.beginPath();
    if (backwardsPoints.length > nDots) {
      backwardsPoints.shift();
    }
    for (const point of backwardsPoints) {
      context.lineTo(point[0], point[1]);
    }
    if ($("#closeFigure").prop('checked') && backwardsPoints[0]) {
      var firstPoint = backwardsPoints[0];
      context.lineTo(firstPoint[0], firstPoint[1]);
    }
    context.stroke();
  }

  this.eraseCoords = ev => {
    backwardsPoints.length = 0;
    forwardsPoints.length = 0;
  }

  this.getData = index => {
    return backwardsPoints.slice(backwardsPoints.length - nDots, backwardsPoints.length);
  }

  this.push = () => {}
  this.mousemove = ev => {}
  this.mouseup = ev => {}
};

tools.dots = function () {
  var tool = this;
  let backwardsPoints = [];
  let forwardsPoints = [];

  this.mousedown = (ev) => {
    if (backwardsPoints.length >= nDots) backwardsPoints.shift();
    backwardsPoints.push([ev._x, ev._y]);
    tool.draw();
    forwardsPoints.length = 0;
  }

  this.undo = () => {
    if (backwardsPoints.length) {
      var lastPoint = backwardsPoints.pop();
      tool.draw();
      forwardsPoints.push(lastPoint);
    }
  }

  this.redo = () => {
    if (forwardsPoints.length > 0) {
      backwardsPoints.push(forwardsPoints.pop());
      tool.draw();
    }
  }

  this.draw = () => {
    resetCanvas();
    context.beginPath();
    for (const point of backwardsPoints) {
      context.moveTo(point[0], point[1]);
      context.lineTo(point[0], point[1]);
    }
    context.stroke();
  }

  this.eraseCoords = ev => {
    backwardsPoints.length = 0;
    forwardsPoints.length = 0;
  }

  this.getData = index => {
    return backwardsPoints.slice(backwardsPoints.length - nDots, backwardsPoints.length);
  }

  this.push = ev => {}
  this.mousemove = ev => {}
  this.mouseup = ev => {}
};

function dataURLtoBlob(dataURI) {
  // convert base64/URLEncoded data component to raw binary data held in a string
  let byteString;
  if (dataURI.split(',')[0].indexOf('base64') >= 0)
    // Decode base-64 encoded string
    byteString = atob(dataURI.split(',')[1]);

  // separate out the mime component
  let mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];

  // write the bytes of the string to a typed array
  let dataArray = new Uint8Array(byteString.length);
  for (var i = 0; i < byteString.length; i++) {
    dataArray[i] = byteString.charCodeAt(i);
  }

  return new Blob([dataArray], { type: mimeString });
}
