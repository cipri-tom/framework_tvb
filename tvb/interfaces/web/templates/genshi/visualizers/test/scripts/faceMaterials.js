
var stats = new Stats();            // performance monitor
stats.setMode(0);                   // 0 - FPS, 1 - milliseconds / frame
document.getElementById("myDiv").appendChild(stats.domElement);
stats.begin();

var scene, camera, renderer, cube;

function init_data() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.z = 15;

    renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    var materials = [];
    for (var i = 0; i < 5; ++i)
        materials.push(new THREE.MeshBasicMaterial({ color: Math.random() * 0xffffff }));

    var geometry = new THREE.CubeGeometry(5, 5, 5, 5, 5, 5);
    var material = new THREE.MeshFaceMaterial(materials);

    for (var i = 0; i < geometry.faces.length; ++i)
        geometry.faces[i].materialIndex = Math.floor(Math.random() * 5);

    console.log(geometry.faces.length);

    cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

}

function animate() {
    requestAnimationFrame(animate);
    for (var i = 0; i < cube.geometry.faces.length; ++i)
        cube.geometry.faces[i].materialIndex = Math.floor(Math.random() * 5);

    cube.geometry.elementsNeedUpdate = true;
    renderer.render(scene, camera);
    stats.update();
}