/////// PERFORMANCE MONITORING
var stats = new Stats();            // performance monitor
stats.setMode(0);                   // 0 - FPS, 1 - milliseconds / frame
document.getElementById("myDiv").appendChild(stats.domElement);
stats.begin();
/////// PERFORMANCE MONITORING END


var gui, camera, scene, renderer, brain, controls, timeSteps = 0, currentTimeStep = 0,
    minActivity, maxActivity, activityData, vertexMapping, fr = 0.0, speed = 20;

var myInt = -1;

function init_data(urlVertices, urlTriangles, urlNormals, baseDatatypeUrl, minAct, maxAct) {
    var verticesData = readFloatData($.parseJSON(urlVertices), true);
    console.log("slices: " + verticesData.length);
    console.log("points: " + verticesData[0].length + " vertices: " + verticesData[0].length / 3);
    verticesData = verticesData[0];

    var trianglesData = HLPR_readJSONfromFile($.parseJSON(urlTriangles));
    console.log("triangles: " + trianglesData.length / 3);

    var normalsData   = HLPR_readJSONfromFile($.parseJSON(urlNormals));

    console.log("base datatype url: " + baseDatatypeUrl);
    console.log("overall min activity: " + minActivity);
    console.log("overall max activity: " + maxActivity);

    activityData = HLPR_readJSONfromFile("http://localhost:8080/flow/read_datatype_attribute/34192c94-e3c0-11e2-983b-1803739fd931/read_data_page?from_idx=0&to_idx=500");
    timeSteps = activityData.length;
    minActivity = minAct;
    maxActivity = maxAct;
    console.log("activity slices: " + activityData.length);
    console.log("activity slice length: " + activityData[0].length);

    vertexMapping = HLPR_readJSONfromFile("http://localhost:8080/flow/read_datatype_attribute/f68e21c8-e3be-11e2-bea8-1803739fd931/array_data");
    console.log("vertexMapping.size: " + vertexMapping.length);

    var brainGeometry = new THREE.Geometry();
    var normals = [];
    for (var i = 0; i * 3 < verticesData.length; ++i) {
        brainGeometry.vertices.push(new THREE.Vector3(verticesData[3 * i], verticesData[3 * i + 1], verticesData[3 * i + 2]));
        normals.push(new THREE.Vector3(normalsData[3 * i], normalsData[3 * i + 1], normalsData[3 * i + 2]));
    }

    var face, index1, index2, index3;
    for (var i = 0; i * 3 < trianglesData.length; ++i) {
        index1 = trianglesData[3 * i];
        index2 = trianglesData[3 * i + 1];
        index3 = trianglesData[3 * i + 2];
        face = new THREE.Face3(index1, index2, index3);
        face.vertexNormals = [normals[index1], normals[index2], normals[index3]];
        face.color = new THREE.Color(0x777777);
        brainGeometry.faces.push(face);
    }

    var material = new THREE.MeshLambertMaterial({
//                            side : THREE.DoubleSide,
                            vertexColors: THREE.FaceColors,
                            color: 0xFEBEBE
                        });

    brain = new THREE.Mesh(brainGeometry, material);


    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
    camera.position.z = 200;
    scene = new THREE.Scene();
    scene.add(brain);

    // add subtle ambient lighting
    var ambientLight = new THREE.AmbientLight(0x222222);
    scene.add(ambientLight);

    // directional lighting
    var directionalLight = new THREE.DirectionalLight(0xffffff);
    // link it to camera position so that object is always illuminated, regardless of orientation
    directionalLight.position = camera.position;
    scene.add(directionalLight);

    renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth * 3 / 4, window.innerHeight * 3 / 4);
    document.getElementById("myDiv").appendChild(renderer.domElement);

    // controls, for moving and zooming
    controls = new THREE.TrackballControls(camera, renderer.domElement);
    controls.rotateSpeed = 1.0;
    controls.zoomSpeed = 1.2;
    controls.panSpeed = 0.8;
    controls.noZoom = false;
    controls.noPan = true;



    var params = function () { this.speed = 20; };
    var p = new params();
    gui = new dat.GUI();
    gui.add(p, "speed", 2, 30).name("Speed (fps)").onChange(function (value) {
        speed = value;
        clearInterval(myInt);
        myInt = setInterval( function () {
                requestAnimationFrame( animate );
                }, 1000 / speed );
    });

    document.getElementById("myDiv").appendChild(gui.domElement);
//    window.addEventListener( 'resize', onWindowResize, false );

    myInt = setInterval( function () {
                requestAnimationFrame( animate );
                }, 1000 / speed );
}

function animate() {
//    requestAnimationFrame(animate);

//    fr++;
//    if (fr % 100 == 0.0)
        updateVertexColors();
    renderer.render(scene, camera);
    controls.update();
    stats.update();
}


function updateVertexColors() {
    if (currentTimeStep >= timeSteps)
        currentTimeStep = 0;
//    console.log("updating...");
    var face, levelA, n;
//  var levelB, levelC, colour = new THREE.Color(0x000000);
    for (var i = 0, iMax = brain.geometry.faces.length; i < iMax; ++i) {
        face = brain.geometry.faces[i];
        levelA = activityData[currentTimeStep][vertexMapping[face.a]];
//        levelB = activityData[currentTimeStep][vertexMapping[face.b]];
//        levelC = activityData[currentTimeStep][vertexMapping[face.c]];
        n = (levelA - minActivity) / (maxActivity - minActivity);
        brain.geometry.faces[i].color.r = (n - 1) * 0.6 + 1;
    }

    currentTimeStep++;
    brain.geometry.colorsNeedUpdate = true;
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    renderer.setSize( window.innerWidth, window.innerHeight );

    controls.handleResize();
}


function readFloatData(data_url_list, staticFiles) {
    var result = [];
    for (var i = 0; i < data_url_list.length; i++) {
        var data_json = HLPR_readJSONfromFile(data_url_list[i], staticFiles);
        if (staticFiles) {
            for (var j = 0; j < data_json.length; j++) {
                data_json[j] = parseFloat(data_json[j]);
            }
        }
        result.push(data_json);
        data_json = null;
    }
    return result;
}

/**
 * Initiate a HTTP GET request for a given file name and return its content, parsed as a JSON object.
 * When staticFiles = True, return without evaluating JSON from response.
 */
function HLPR_readJSONfromFile(fileName, staticFiles) {
    oxmlhttp = null;
    try {
        oxmlhttp = new XMLHttpRequest();
        oxmlhttp.overrideMimeType("text/plain");
    } catch(e) {
        try {
            oxmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
        } catch(e) {
            return null;
        }
    }
    if (!oxmlhttp) return null;
    try {
        oxmlhttp.open("GET", fileName, false);
        oxmlhttp.send(null);
    } catch(e) {
        return null;
        console.log("Couldn't get file: " + filename);
    }
    if (staticFiles) {
    	var fileData = oxmlhttp.responseText;
    	fileData = fileData.replace(/\n/g, " ").replace(/\t/g, " ").replace(/    /g, " ").replace(/   /g, " ").replace(/  /g, " ").replace('[', '').replace(']', '');
		return $.trim(fileData).split(" ");
    }
    return jQuery.parseJSON(oxmlhttp.responseText);
}