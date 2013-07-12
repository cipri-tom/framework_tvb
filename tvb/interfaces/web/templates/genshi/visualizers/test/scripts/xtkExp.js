
var minActivity, maxActivity, activityData, vertexMapping, timeSteps;



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

    var renderer = new X.renderer3D();
    renderer.init();
    var brain = new X.mesh();
    brain.points = new X.triplets(verticesData.length / 3);
    console.log(brain.points);
    for (var i = 0; 3 * i < verticesData.length; ++i)
        brain.points.add(verticesData[3 * i], verticesData[3 * i + 1], verticesData[3 * i + 2]);

    brain.color = [1, 0, 0];


    renderer.add(brain);
    renderer.render();

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