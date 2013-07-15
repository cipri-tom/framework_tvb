/////// PERFORMANCE MONITORING
var stats = new Stats();            // performance monitor
stats.setMode(0);                   // 0 - FPS, 1 - milliseconds / frame
var myDiv = document.getElementById("myDiv");
myDiv.appendChild(stats.domElement);
stats.begin();
/////// PERFORMANCE MONITORING END

var vertexBuf, normalsBuf, trianglesBuf;

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

    var canvas = document.createElement("canvas");
    canvas.webGlCanvas = true;
    canvas.width = 800;
    canvas.height = 600;
    myDiv.appendChild(canvas);

    initGL(canvas);

    basicInitShaders("benchFS", "benchVS");

    gl.useProgram(shaderProgram);

//    shaderProgram.vertexColor = gl.getAttribLocation(shaderProgram, "aVertexColor");
//    gl.enableVertexAttribArray(shaderProgram.vertexColor);

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
    trianglesBuf.numItems = trianglesData[0].length / 3;
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, trianglesBuf);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(trianglesData[0]), gl.STATIC_DRAW);


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

    mvTranslate([0.0, 0.0, -300.0]);
    mvRotate(180, [0, 0, 1]);


    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuf);
    gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ARRAY_BUFFER, normalsBuf);
    gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, trianglesBuf);
    setMatrixUniforms();
    gl.drawElements(gl.TRIANGLES, trianglesBuf.numItems, gl.UNSIGNED_SHORT, 0);
}


function getShader(gl, id) {
    var shaderScript = document.getElementById(id);
    if (!shaderScript) {
        return null;
    }
    var str = "";
    var k = shaderScript.firstChild;
    while (k) {
        if (k.nodeType == 3) {
            str += k.textContent;
        }
        k = k.nextSibling;
    }
    var shader;
    if (shaderScript.type == "x-shader/x-fragment") {
        shader = gl.createShader(gl.FRAGMENT_SHADER);
    } else if (shaderScript.type == "x-shader/x-vertex") {
        shader = gl.createShader(gl.VERTEX_SHADER);
    } else {
        return null;
    }

    gl.shaderSource(shader, str);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        displayMessage(gl.getShaderInfoLog(shader), "warningMessage");
        return null;
    }
    return shader;
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