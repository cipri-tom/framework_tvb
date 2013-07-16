/////// PERFORMANCE MONITORING
var stats = new Stats();            // performance monitor
stats.setMode(0);                   // 0 - FPS, 1 - milliseconds / frame
var myDiv = document.getElementById("myDiv");
myDiv.appendChild(stats.domElement);
stats.begin();
/////// PERFORMANCE MONITORING END

var vertexBuf, normalsBuf, trianglesBuf, colorBufs = [], currentTimeStep, totalTimeSteps;

function init_data(urlVertices, urlTriangles, urlNormals, timeSeriesGid, minAct, maxAct, isOneToOneMapping, regionMappingGid) {
    var verticesData = readFloatData($.parseJSON(urlVertices), true);
    console.log("vertex slices: " + verticesData.length);

    var trianglesData = readFloatData($.parseJSON(urlTriangles), true);

    var normalsData   = readFloatData($.parseJSON(urlNormals), true);

    var urlPrefix = "http://localhost:8080/flow/read_datatype_attribute/";

    var url = urlPrefix + timeSeriesGid + "/read_data_page?from_idx=0&to_idx=500";

    var activityData = HLPR_readJSONfromFile(url);
    totalTimeSteps = activityData.length;
    currentTimeStep = 0;

    if (isOneToOneMapping)
        console.log("Is one to one mapping...")
    else {
        console.log("Is region mapping...");

        url = urlPrefix + regionMappingGid + "/array_data/True";
        vertexMapping = HLPR_readJSONfromFile(url);
        console.log("vertexMapping.size: " + vertexMapping.length);
    }

    var canvas = document.createElement("canvas");
    canvas.webGlCanvas = true;
    canvas.width = 800;
    canvas.height = 600;
    myDiv.appendChild(canvas);

    initGL(canvas);

    myBasicInitShaders("benchFS", "benchVS");

    shaderProgram.vertexColorAttribute = gl.getAttribLocation(shaderProgram, "aVertexColor");
    gl.enableVertexAttribArray(shaderProgram.vertexColorAttribute);

    // fill the vertices buffer
    vertexBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(verticesData[0]), gl.STATIC_DRAW);

    // fill the normals buffer
    normalsBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, normalsBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(normalsData[0]), gl.STATIC_DRAW);

    // fill the triangles buffer
    trianglesBuf = gl.createBuffer();
    trianglesBuf.numItems = trianglesData[0].length;
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, trianglesBuf);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(trianglesData[0]), gl.STATIC_DRAW);

    // compute colors
    var level = 0, currentColors;
    for (var time = 0; time < activityData.length; time++) {
        currentColors = new Float32Array(vertexMapping.length * 3);
        for (var vertex = 0; vertex < vertexMapping.length; vertex++)
            currentColors[vertex * 3] = 0.3 + 0.7 * (activityData[time][vertexMapping[vertex]] - minAct)
                                                     / (maxAct - minAct);

        for (var vertex = 0; vertex < vertexMapping.length; vertex++)
            currentColors[vertex * 3 + 1] = currentColors[vertex * 3 + 2] = 0.3;

        colorBufs[time] = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, colorBufs[time]);
        gl.bufferData(gl.ARRAY_BUFFER, currentColors, gl.STATIC_DRAW);
    }


    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.clearDepth(1.0);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);

}

function animate() {
    requestAnimationFrame(animate);
    render();

    stats.update();
}

function render() {
    gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    loadIdentity();
    perspective(45, gl.viewportWidth / gl.viewportHeight, 0.1, 800.0);

    // pull out the camera from the scene center
    mvTranslate([0.0, 0.0, -300.0]);
    mvRotate(180, [0, 0, 1]);

    if (currentTimeStep >= totalTimeSteps)
        currentTimeStep = 0;

    // set the colors
    gl.bindBuffer(gl.ARRAY_BUFFER, colorBufs[currentTimeStep]);
    gl.vertexAttribPointer(shaderProgram.vertexColorAttribute, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuf);
    gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ARRAY_BUFFER, normalsBuf);
    gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, trianglesBuf);
    setMatrixUniforms();
    gl.drawElements(gl.TRIANGLES, trianglesBuf.numItems, gl.UNSIGNED_SHORT, 0);
//    gl.drawArrays(gl.TRIANGLES, 0, );
    currentTimeStep++;
}

function myBasicInitShaders(fsShader, vsShader) {
    var fragmentShader = getShader(gl, fsShader);
    var vertexShader = getShader(gl, vsShader);

    shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);

    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
        displayMessage("MY Could not initialise shaders" +  gl.getShaderInfoLog(shader), "errorMessage");
    }
    gl.useProgram(shaderProgram);

    shaderProgram.vertexPositionAttribute = gl.getAttribLocation(shaderProgram, "aVertexPosition");
    gl.enableVertexAttribArray(shaderProgram.vertexPositionAttribute);
    shaderProgram.vertexNormalAttribute = gl.getAttribLocation(shaderProgram, "aVertexNormal");
	gl.enableVertexAttribArray(shaderProgram.vertexNormalAttribute);

    shaderProgram.pMatrixUniform = gl.getUniformLocation(shaderProgram, "uPMatrix");
    shaderProgram.mvMatrixUniform = gl.getUniformLocation(shaderProgram, "uMVMatrix");
    shaderProgram.nMatrixUniform = gl.getUniformLocation(shaderProgram, "uNMatrix");
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