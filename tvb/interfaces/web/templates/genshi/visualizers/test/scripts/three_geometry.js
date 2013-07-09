
var stats = new Stats();            // performance monitor
stats.setMode(0);                   // 0 - FPS, 1 - milliseconds / frame
document.getElementById("myDiv").appendChild(stats.domElement);
stats.begin();


var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);

var renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);


// get the shaders
var vertexSh = $("#shader-vs");
var fragmentsSh = $("#shader-fs");

var attributes = {
        displacement: {
            type: 'f',       // a float
            value: []
        }
};

var shaderMaterial = new THREE.ShaderMaterial({
                            attributes: attributes,
                            vertexShader: vertexSh.text(),
                            fragmentShader: fragmentsSh.text()
                         });

// vertices for the pyramid faces
var vertices = [
         0.0,  10.0,  0.0,          // top
         10.0, -10.0,  10.0,        // right front
         10.0, -10.0, -10.0,        // right back
        -10.0, -10.0, -10.0,        // left back
        -10.0, -10.0,  10.0];       // left front

var geometry = new THREE.Geometry();

for (var i = 0; i <= 4; ++i) {
    geometry.vertices.push(new THREE.Vector3(vertices[i * 3], vertices[i * 3 + 1], vertices[i *  3 + 2]));
    if (i > 0)
        geometry.faces.push(new THREE.Face3(0, (i % 4) || 4, i % 4 + 1));
}

geometry.computeFaceNormals();
geometry.computeVertexNormals();

var verts = geometry.vertices;
var values = attributes.displacement.value;

for (var v = 0; v < verts.length; ++v)
    values.push(Math.random() * 10);

/*
var cubeGeometry = new THREE.CubeGeometry(5, 5, 5);
cubeGeometry.applyMatrix(new THREE.Matrix4().makeTranslation(15, 0, 0));
cubeGeometry.applyMatrix(new THREE.Matrix4().makeRotationX(1));
cubeGeometry.applyMatrix(new THREE.Matrix4().makeRotationY(1));


// create a separate material for each face, for different colors
var cubeMaterialArray = [];
cubeMaterialArray.push(new THREE.MeshBasicMaterial( {color: 0xff0000} ));
cubeMaterialArray.push(new THREE.MeshBasicMaterial( {color: 0x00ff00} ));
cubeMaterialArray.push(new THREE.MeshBasicMaterial( {color: 0x0000ff} ));
cubeMaterialArray.push(new THREE.MeshBasicMaterial( {color: 0xffff00} ));
cubeMaterialArray.push(new THREE.MeshBasicMaterial( {color: 0xff00ff} ));
cubeMaterialArray.push(new THREE.MeshBasicMaterial( {color: 0x00ffff} ));

var cubeMaterials = new THREE.MeshFaceMaterial(cubeMaterialArray);

var cube = new THREE.Mesh(cubeGeometry, shaderMaterial);
scene.add(cube);
*/

var pyramid = new THREE.Mesh(geometry, shaderMaterial);

scene.add(pyramid);

camera.position.z = 25;
camera.position.y = -3;
camera.position.x = 17;


render_threeJS();

function render_threeJS() {
    requestAnimationFrame(render_threeJS);

//    pyramid.rotation.x += 0.1;
//    pyramid.rotation.y += 0.1;
    renderer.render(scene, camera);
    stats.update();
}


