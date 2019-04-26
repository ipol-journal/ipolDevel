var inpaintingController = inpaintingController || {};

let canvas, context;
let tool;
let tools = {};
let inpaintingControls = [];
let background;
let nDots;

inpaintingController.init = async (index, blobSrc, canvasElement) => {
  canvas = canvasElement;
  context = canvas.getContext('2d');
  if (ddl.inputs[index].max_dots) nDots = ddl.inputs[index].max_dots;
  if (!inpaintingControls[index]) {
    tool = new tools[ddl.inputs[index].control];
    inpaintingControls[index] = tool;
  } else {
    tool = inpaintingControls[index];
  }
  
  $(canvas).mousedown(canvas_event);
  $(canvas).mousemove(canvas_event);
  $(canvas).mouseup(canvas_event);
  $(canvas).mouseout(canvas_event);
  
  $('#color-picker').change(setStyle);
  $('#size-selector').change(setStyle);
  $("#closeFigure").change(tool.draw);
  addEraseEvent();
  
  background = await loadImage(blobSrc);
  canvas.height = background.height;
  canvas.width = background.width;
  setStyle();
  tool.draw();
}

addEraseEvent = () => {
  $('#erase-btn').click(function () {
    if ($(this).hasClass('activated')) {
      $(this).removeClass('activated');
      context.globalCompositeOperation = 'source-over';
    } else {
      $(this).addClass('activated');
      context.globalCompositeOperation = 'destination-out';
    }
  });
}

canvas_event = (ev) => {
  if (ev.layerX || ev.layerX == 0) { // Firefox
    ev._x = ev.layerX;
    ev._y = ev.layerY;
  } else if (ev.offsetX || ev.offsetX == 0) { // Chrome Opera
    ev._x = ev.offsetX;
    ev._y = ev.offsetY;
  }

  // Call the event handler of the tool.
  var tool_handler = tool[ev.type];
  if (tool_handler) {
    tool_handler(ev);
  }
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

tools.mask = function () {
  let tool = this;
  this.started = false;
  this.lastX = 0;
  this.lastY = 0;
  let state = [$('#editor-blob-left')[0].toDataURL()];
  let idx = 0;

  this.mousedown = (ev) => {
    if (state.length > idx + 1) state.splice(idx + 1);
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

  this.mouseout = (ev) => {
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
    idx++;
    state.push($('#editor-blob-left')[0].toDataURL());
  }

  this.undo = () => {
    if (idx > 0) {
      idx--;
      tool.draw();
    }
  }

  this.redo = () => {
    if (state[idx + 1]) {
      idx++;
      tool.draw();
    }
  }

  this.draw = () => {
    var canvasPic = new Image();
    canvasPic.src = state[idx];
    canvasPic.onload = function() {
      resetCanvas();
      context.drawImage(canvasPic, 0, 0);
    }
  }

  this.getData = () => {
    let dataURL = canvas.toDataURL();
    return dataURLtoBlob(dataURL);
  }

  this.clear = ev => {
    resetCanvas();
    tool.push();
  }
};

tools.lines = function () {
  var tool = this;
  let currentState = [];
  let state = [currentState.map(x => ([...x]))];
  let idx = 0;

  this.mousedown = (ev) => {
    if (state.length > idx + 1) {
      state.splice(idx + 1);
    }
    currentState.push([ev._x, ev._y]);
    if (currentState.length > nDots) {
      currentState.shift();
    }
    state.push(currentState.map(x => ([...x])));
    idx++;
    tool.draw();
  }

  this.undo = () => {
    if (idx > 0) {
      idx--;
      tool.draw();
    }
  }
  
  this.redo = () => {
    if (state[idx + 1]) {
      idx++;
      tool.draw();
    }
  }

  this.draw = () => {
    if (state[idx]) currentState = state[idx].map(x => ([...x]));
    resetCanvas();
    context.beginPath();
    for (const point of currentState) {
      context.lineTo(point[0], point[1]);
    }
    if ($("#closeFigure").prop('checked') && currentState[0]) {
      var firstPoint = currentState[0];
      context.lineTo(firstPoint[0], firstPoint[1]);
    }
    context.stroke();
  }

  this.clear = ev => {
    state.push([]);
    idx++;
    resetCanvas();
  }

  this.getData = index => {
    return state.slice(state.length - nDots, state.length);
  }

  this.push = () => {}
  this.mousemove = ev => {}
  this.mouseup = ev => {}
  this.mouseout = ev => {}
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

  this.clear = ev => {
    backwardsPoints.length = 0;
    forwardsPoints.length = 0;
    resetCanvas();
  }

  this.getData = index => {
    return backwardsPoints.slice(backwardsPoints.length - nDots, backwardsPoints.length);
  }

  this.push = ev => {}
  this.mousemove = ev => {}
  this.mouseup = ev => {}
  this.mouseout = ev => {}
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
