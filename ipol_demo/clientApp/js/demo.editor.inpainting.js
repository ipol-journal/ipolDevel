var inpaintingController = inpaintingController || {};

let canvas, context;
let tool;
let tools = {};
let background;
let inpaintingControls = [];

inpaintingController.init = (index, blobSrc, side) => {
  canvas = $('#editor-blob-' + side)[0];
  context = canvas.getContext('2d');
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
  
  setBackgroundImage(blobSrc).then(() => {
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

const setBackgroundImage = async (path) => {
  background = await loadImage(path);
  canvas.height = background.height;
  canvas.width = background.width;
  context.drawImage(background, 0, 0);
  tool.push();
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

//########################################################################

tools.pencil = function () {
  let tool = this;
  this.started = false;
  this.lastX = 0;
  this.lastY = 0;
  let backwardsPoints = [document.getElementById('canvas').toDataURL()];
  let forwardPoints = new Array();

  this.mousedown = (ev) => {
    tool.started = true;
    tool.draw(ev._x, ev._y, false);
  };

  this.mousemove = (ev) => {
    if (tool.started) {
      tool.draw(ev._x, ev._y, true);
    }
  };

  this.mouseup = (ev) => {
    if (tool.started) {
      tool.mousemove(ev);
      tool.started = false;
      tool.push();
    }
  };

  this.push = () => {
    forwardPoints.length = 0;
    backwardsPoints.push(document.getElementById('canvas').toDataURL());
  }

  this.undo = () => {
    var last = backwardsPoints.pop();
    if (last && backwardsPoints.length > 0) {
      tool.drawStep(backwardsPoints[backwardsPoints.length - 1]);
      forwardPoints.push(last);
    }
  }

  this.redo = () => {
    if (forwardPoints.length > 0) {
      var last = forwardPoints.pop();
      tool.drawStep(last);
      backwardsPoints.push(last);
    }
  }

  this.reset = () => {
    forwardPoints.length = 0;
    backwardsPoints.length = 0;
  }

  this.drawStep = (step) => {
    var canvasPic = new Image();
    canvasPic.src = step;
    canvasPic.onload = () => context.drawImage(canvasPic, 0, 0);
  }

  this.draw = (x, y, started) => {
    if (started) {
      context.beginPath();
      context.moveTo(tool.lastX, tool.lastY);
      context.lineTo(x, y);
      context.closePath();
      context.stroke();
    }
    tool.lastX = x;
    tool.lastY = y;
  };

  this.eraseCoords = ev => { }
};

tools.line = function () {
  var tool = this;
  let nDots = $("#max-dots").val();
  let backwardsPoints = [];
  let forwardsPoints = [];
  
  this.mousedown = (ev) => {
    backwardsPoints.push([ev._x, ev._y]);
    tool.draw();
    forwardsPoints.length = 0;
  }

  this.undo = () => { 
    var lastPoint = backwardsPoints.pop();
    if (lastPoint) {
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
    if (backwardsPoints.length < 1) return;
    resetCanvas();
    context.beginPath();
    if (backwardsPoints.length > nDots) {
      backwardsPoints.shift();
    }
    for (const point of backwardsPoints) {
      context.lineTo(point[0], point[1]);
    }
    if ($("#closeFigure").prop('checked')) {
      var firstPoint = backwardsPoints[0];
      context.lineTo(firstPoint[0], firstPoint[1]);
    }
    context.stroke();
  }

  this.eraseCoords = ev => {
    backwardsPoints.length = 0;
    forwardsPoints.length = 0;
  }

  this.push = () => {}
  this.mousemove = ev => {}
  this.mouseup = ev => {}
};

tools.dots = function () {
  var tool = this;
  let nDots = $("#max-dots").val();
  let backwardsPoints = [];
  let forwardsPoints = [];

  this.mousedown = (ev) => {
    if (backwardsPoints.length >= nDots) backwardsPoints.shift();
    backwardsPoints.push([ev._x, ev._y]);
    tool.draw();
    forwardsPoints.length = 0;
  }

  this.undo = () => {
    var lastPoint = backwardsPoints.pop();
    if (lastPoint) {
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
    if (backwardsPoints.length < 1) return;
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

  this.push = ev => {}
  this.mousemove = ev => {}
  this.mouseup = ev => {}
};

function save() {
  document.getElementById("clone").style.border = "2px solid";
  var dataURL = canvas.toDataURL();
  document.getElementById("clone").src = dataURL;
  document.getElementById("clone").style.display = "inline";
}

function resetCanvas() {
  context.beginPath();
  // Use the identity matrix while clearing the canvas
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(background, 0, 0);
}

function erase() {
  context.beginPath();
  // Use the identity matrix while clearing the canvas
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(background, 0, 0);
  tool.eraseCoords();
  setBackgroundImage();
}