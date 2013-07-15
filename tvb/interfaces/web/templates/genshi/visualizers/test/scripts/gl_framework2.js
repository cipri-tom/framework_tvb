/////// PERFORMANCE MONITORING
var stats = new Stats();            // performance monitor
stats.setMode(0);                   // 0 - FPS, 1 - milliseconds / frame
var myDiv = document.getElementById("myDiv");
myDiv.appendChild(stats.domElement);
stats.begin();
/////// PERFORMANCE MONITORING END


var gui, camera, scene, renderer, brain, controls, companionCube,
    currentTimeStep = 0,
    activityData, minActivity, maxActivity, vertexMapping, colors = []
    fr = 0.0, speed = 20;

function init_data(urlVertices, urlTriangles, urlNormals, timeSeriesGid, minAct, maxAct, isOneToOneMapping, regionMappingGid) {
    var verticesData = readFloatData($.parseJSON(urlVertices), true);
    console.log("vertex slices: " + verticesData.length);

    var trianglesData =readFloatData($.parseJSON(urlTriangles), true);

    var normalsData   = readFloatData($.parseJSON(urlNormals), true);

    var urlPrefix = "http://localhost:8080/flow/read_datatype_attribute/";

    if (isOneToOneMapping)
        console.log("Is one to one mapping...")
    else {
        console.log("Is region mapping...");

        url = urlPrefix + regionMappingGid + "/array_data/True";
        vertexMapping = HLPR_readJSONfromFile(url);
        console.log("vertexMapping.size: " + vertexMapping.length);
    }


    var brainGeometry = new THREE.Geometry();

    var normals = [], pointsNo = 0;
    for (var slice = 0; slice < verticesData.length; slice++) {
        for (var i = 0; i * 3 < verticesData[slice].length; ++i) {
            brainGeometry.vertices.push(new THREE.Vector3(verticesData[slice][3 * i], verticesData[slice][3 * i + 1],
                                                          verticesData[slice][3 * i + 2]));
            normals.push(new THREE.Vector3(normalsData[slice][3 * i], normalsData[slice][3 * i + 1], normalsData[slice][3 * i + 2]));
        }
        pointsNo += verticesData[slice].length;
    }
    console.log("points: " + pointsNo + " vertices: " + pointsNo / 3);

    var face, index1, index2, index3, facesNo = 0, offset = 0;
    for (var slice = 0; slice < trianglesData.length; slice++) {
        for (var i = 0; i * 3 < trianglesData[slice].length; ++i) {
            index1 = trianglesData[slice][3 * i] + offset;
            index2 = trianglesData[slice][3 * i + 1] + offset;
            index3 = trianglesData[slice][3 * i + 2] + offset;
            face = new THREE.Face3(index1, index2, index3);
            face.vertexNormals = [normals[index1], normals[index2], normals[index3]];
            brainGeometry.faces.push(face);
        }
        offset += verticesData[slice].length / 3;
        facesNo += trianglesData[slice].length / 3;
    }
    console.log("faces: " + facesNo);

    // set the faces normals for intersections to work
    brainGeometry.computeFaceNormals();

    console.log("time series gid: " + timeSeriesGid);
    console.log("overall min activity: " + minAct);
    console.log("overall max activity: " + maxAct);
    minActivity = minAct;
    maxActivity = maxAct;

    var url = urlPrefix + timeSeriesGid + "/read_data_page?from_idx=0&to_idx=500";

    activityData = HLPR_readJSONfromFile(url);
    console.log("activity slices: " + activityData.length);
    console.log("activity slice length: " + activityData[0].length);

    var currentColors, c = new THREE.Color(0x777777), j;
    for (var time = 0; time < activityData.length; ++time) {
        currentColors = [];
        j = 0;
        for (var vertexI = 0; vertexI < brainGeometry.vertices.length; ++vertexI) {
            c = new THREE.Color(0x777777);
            j = isOneToOneMapping ? vertexI : vertexMapping[vertexI];
            c.setRGB(0.5 + (activityData[time][j] - minAct) / (maxAct - minAct) * 0.5, 0.5, 0.5)
            currentColors.push(c);1
        }
        colors.push(currentColors);
    }

    // get the shaders
    var vertexSh = $("#shader-vs");
    var fragmentsSh = $("#shader-fs");

    var attributes = {
            customColor: {
                type: 'c',
                value: []
            }
    };

    var shaderMaterial = new THREE.ShaderMaterial({
                                attributes: attributes,
                                vertexShader: vertexSh.text(),
                                fragmentShader: fragmentsSh.text()
                             });

    brain = new THREE.Mesh(brainGeometry, shaderMaterial);

    updateColor();
    scene = new THREE.Scene();
    scene.add(brain);

    camera = new THREE.PerspectiveCamera(45, myDiv.clientWidth / myDiv.clientHeight, 0.1, 2000);
    camera.position.set(0, 150, 400);
    camera.lookAt(scene.position);


    renderer = new THREE.WebGLRenderer();
    renderer.setSize(myDiv.clientWidth, myDiv.clientHeight);
    renderer.domElement.addEventListener("dblclick", onDocumentClick, false);
    myDiv.appendChild(renderer.domElement);

    // controls, for moving and zooming
    controls = new THREE.TrackballControls(camera, renderer.domElement);
    controls.rotateSpeed = 1.0;
    controls.zoomSpeed = 1.2;
    controls.panSpeed = 0.8;
    controls.noZoom = false;
    controls.noPan = true;

    window.addEventListener( 'resize', onWindowResize, false );

}

function animate() {
    requestAnimationFrame(animate);

//    if (fr % 100 == 0)
        updateColor();
    fr++;

    renderer.render(scene, camera);
    controls.update();
    stats.update();
}

function updateColor() {

    if (currentTimeStep >= activityData.length)
        currentTimeStep = 0;
    var value = brain.material.attributes.customColor.value;
    for (var i = 0; i < colors[currentTimeStep].length; i++) {
        value[i] = colors[currentTimeStep][i];
    }

    currentTimeStep++;
    brain.material.attributes.customColor.needsUpdate = true;

}

function onDocumentClick(event) {
    event.preventDefault();
    var mouseX = myDiv.getBoundingClientRect().left;
    var mouseY = myDiv.getBoundingClientRect().top;
    mouseX = event.clientX - mouseX - renderer.domElement.offsetLeft;
    mouseY = event.clientY - mouseY - renderer.domElement.offsetTop;
    console.log("x: " + mouseX + "; y: " + mouseY);

    // http://stackoverflow.com/questions/11036106/three-js-projector-and-ray-objects?rq=1#comment14437076_11038479
    var vector = new THREE.Vector3( (mouseX / renderer.domElement.clientWidth) * 2 - 1,
                                  - (mouseY / renderer.domElement.clientHeight) * 2 + 1, 1);        // magic z = 0.5

    var projector = new THREE.Projector();
    projector.unprojectVector(vector, camera);

    var raycaster = new THREE.Raycaster(camera.position, vector.sub(camera.position).normalize());

    var intersects = raycaster.intersectObject(brain);
    console.log(intersects);

    if (intersects.length > 0) {
        var selectedColor = new THREE.Color(0x0000FF);
        for (var time = 0; time < activityData.length; time++)
            colors[time][intersects[0].face.a] = colors[time][intersects[0].face.b]
                                               = colors[time][intersects[0].face.c] = selectedColor;
    }
}

function onWindowResize() {
    camera.aspect = myDiv.clientWidth / myDiv.clientHeight;
    camera.updateProjectionMatrix();

    renderer.setSize( myDiv.clientWidth, myDiv.clientHeight );

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