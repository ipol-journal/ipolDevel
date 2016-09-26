// IPOL meshes API
// By Miguel Colom - http://mcolom.info

// Global variables
var container = [];
var camera_light = [];
var camera = [];
var scene = [];
var renderer = [];
var controls = [];

var mouseX = 0, mouseY = 0;
var current_i;

var windowHalfX = window.innerWidth;
var windowHalfY = window.innerHeight;

var init_cam_pos = [0, 0, 0];

function init(divs, init_cam_pos, obj_filenames) {
  var loader = new THREE.OBJLoader();

  for (i in divs) {
    container.push(document.getElementById(divs[i]));

    // New scene
    scene.push(new THREE.Scene());

    // Cameras
    camera.push(new THREE.PerspectiveCamera( 45, aspect_ratio, 0.001, 300000));
    scene[i].add( camera[i] );

    // These variables set the camera behaviour and sensitivity.
    var aspect_ratio = 1;
    controls.push(new THREE.TrackballControls( camera[i], container[0] ));
    controls[i].rotateSpeed = 1.0;
    controls[i].zoomSpeed = 5;
    controls[i].panSpeed = 2;
    controls[i].noZoom = false;
    controls[i].noPan = false;
    controls[i].staticMoving = true;
    controls[i].dynamicDampingFactor = 0.3;
    controls[i].maxPolarAngle = Math.PI*2;

    // Scene lights
    var ambient = new THREE.AmbientLight( 0x101030 );
    scene[i].add(ambient);

    var light_intensity = 0.5;
    var light_distance = 0;
    camera_light.push(new THREE.PointLight(0xffeedd, light_intensity, light_distance));
    camera_light[i].position.set( 0, 0, 1 ).normalize();
    scene[i].add( camera_light[i] );

    // ToDo: look for a way to do this in a while, instead of the following switch!
    /*loader.load( obj_filenames[i], function ( ojb ) {
                  ojb.position.y = - 0;
                  scene[i].add( ojb );
              } );*/
  }

  switch (obj_filenames.length) {
    case 4:
      loader.load( obj_filenames[3], function ( ojb ) {
                    ojb.position.y = - 0;
                    scene[3].add( ojb );
                } );
    case 3:
      loader.load( obj_filenames[2], function ( ojb ) {
                    ojb.position.y = - 0;
                    scene[2].add( ojb );
                } );
    case 2:
      loader.load( obj_filenames[1], function ( ojb ) {
                    ojb.position.y = - 0;
                    scene[1].add( ojb );
                } );
    case 1:
      loader.load( obj_filenames[0], function ( ojb ) {
                    ojb.position.y = - 0;
                    scene[0].add( ojb );
                } );
  }

  for (i in divs) {
    // Renderer
    renderer.push(new THREE.WebGLRenderer());
    renderer[i].setSize(container[i].clientWidth, container[i].clientHeight);
    container[i].appendChild( renderer[i].domElement );

    // Setup camera positions and make them look to the center of the scene
    camera[i].position.x = init_cam_pos[0];
    camera[i].position.y = init_cam_pos[1];
    camera[i].position.z = init_cam_pos[2];
    camera[i].lookAt(scene[0].position);
  }
}


function animate() {
  requestAnimationFrame(animate);
  for (i in container) {
    controls[i].update();
  }
  render();
}


function render() {
  for (var i in container) {
    camera_light[i].position = camera[0].position;
    renderer[i].render(scene[i], camera[i]);
  }
}


// API

function camera_reset() {
  for (var i in container) {
    camera[i].position.x = init_cam_pos[0];
    camera[i].position.y = init_cam_pos[1];
    camera[i].position.z = init_cam_pos[2];
  }
}

function get_camera_position(i) {
  return camera[i].position;
}

function camera_add_x(inc) {
  for (var i in container) {
    camera[i].position.x += inc;
  }
}

function camera_add_y(inc) {
  for (var i in container) {
    camera[i].position.y += inc;
  }
}

function camera_add_z(inc) {
  for (var i in containe) {
    camera[i].position.z += inc;
  }
}

function scene_add_x(inc) {
  for (var i in containe) {
    scene[i].position.x += inc;
  }
}

function scene_add_y(inc) {
  for (var i in containe) {
    scene[i].position.y += inc;
  }
}

function scene_add_z(inc) {
  for (var i in containe) {
    scene[i].position.z += inc;
  }
}

function ipol_start_mesh(divs, pinit_cam_pos, obj_filenames) {
  init_cam_pos = pinit_cam_pos;
  init(divs, pinit_cam_pos, obj_filenames);
  animate();
}

