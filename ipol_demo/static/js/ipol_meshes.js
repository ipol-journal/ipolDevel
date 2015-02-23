// IPOL meshes API
// By Miguel Colom, 2014

// Global variables
var container, stats;
var camera_light;

var camera, scene, renderer;

var mouseX = 0, mouseY = 0;

var windowHalfX = window.innerWidth;
var windowHalfY = window.innerHeight;

var init_cam_pos = [0, 0, 0];

// Mesh initialization
function init_mesh(div_id, init_cam_pos, obj_filename) {
  //container = document.createElement( 'div' );
  container = document.getElementById(div_id);
  //document.body.appendChild( container );

  scene = new THREE.Scene();

  var aspect_ratio = 1;

  //camera = new THREE.PerspectiveCamera( 45, aspect_ratio, 1, 2000);
  camera = new THREE.PerspectiveCamera( 35, aspect_ratio, 0.1, 10000);

                
  // These variables set the camera behaviour and sensitivity.
  controls = new THREE.TrackballControls( camera, container );
  controls.rotateSpeed = 0.5;
  controls.zoomSpeed = 5;
  controls.panSpeed = 2;
  controls.noZoom = false;
  controls.noPan = true;
  controls.staticMoving = true;
  controls.dynamicDampingFactor = 0.3;
                
  scene.add( camera );

  var ambient = new THREE.AmbientLight(0x080808);
  scene.add(ambient);
  scene.add(ambient.target);


  light_intensity = 0.6;
  light_distance = 0;
  camera_light = new THREE.PointLight(0xffffff, light_intensity, light_distance);
  camera_light.position.set( 0, 0, 1 ).normalize();
  scene.add( camera_light );
  scene.add( camera_light.target );

  var loader = new THREE.OBJLoader();
  //var loader = new THREE.PLYLoader();
  loader.load( obj_filename, function ( object ) {
               scene.add( object );
                } );

  // RENDERER
  renderer = window.WebGLRenderingContext ? new THREE.WebGLRenderer() : new THREE.CanvasRenderer();

  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild( renderer.domElement );

  // Event listeners
  //window.addEventListener('resize', onWindowResize, false );

  camera.position.x = init_cam_pos[0];
  camera.position.y = init_cam_pos[1];
  camera.position.z = init_cam_pos[2];

  //camera.lookAt(scene.position);
  camera.lookAt([0,0,0]);
}


// Scene animation
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  render();
}

// Scene rendering
function render() {
  //camera.position.x += ( mouseX - camera.position.x ) * .05;
  //camera.position.y += ( - mouseY - camera.position.y ) * .05;

  camera_light.position = camera.position;

  renderer.render(scene, camera);
}

// API

// Reset camera position
function camera_reset() {
  camera.position.x = init_cam_pos[0];
  camera.position.y = init_cam_pos[1];
  camera.position.z = init_cam_pos[2];
}

// Getter for the camera position
function get_camera_position() {
  return camera.position;
}

// Functions to control camera and scene positions
function camera_add_x(inc) {
  camera.position.x += inc;
}

function camera_add_y(inc) {
  camera.position.y += inc;
}

function camera_add_z(inc) {
  camera.position.z += inc;
}

function scene_add_x(inc) {
  scene.position.x += inc;
}

function scene_add_y(inc) {
  scene.position.y += inc;
}

function scene_add_z(inc) {
  scene.position.z += inc;
}

// Event listener
function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  
  renderer.setSize( window.innerWidth, window.innerHeight );
  controls.handleResize();
}

// IPOL entry point
function ipol_start_mesh(div_id, pinit_cam_pos, obj_filename) {
  init_cam_pos = pinit_cam_pos;

  init_mesh(div_id, pinit_cam_pos, obj_filename);
  animate();
}

