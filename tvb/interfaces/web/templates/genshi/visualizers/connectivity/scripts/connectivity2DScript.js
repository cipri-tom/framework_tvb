/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and 
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General 
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0
 *
 **/

// with this factor will be changed the weights of the edges of all charts
var scaleFactor = 1;
// contains all the data needed for redrawing the charts
var cache = [];
// the index of the node which should be the root of the chart which contains the both hemispheres
var rootNode = 1;
// contains the points that were selected by the user. Only this points will be drawn in the main view.
// If the list is empty the all the points will be drawn in the main view.
var selectedPoints = [];
// used to see if the user switched to the view with disks of different colors and size
var shouldDisplayCustomView = false;

var C2D_selectedView = 'both';
var C2D_shouldRefreshNodes = true;
var C2D_canvasDiv = '';
/**
 * Used for drawing a chart from the given json
 *
 * @param json a string which contains all the data needed for drawing a chart
 * @param containerDivId the id of the container in which will be drawn the view
 * @param shouldRefreshNodes <code>true</code> if the drawn chart contains data related to both hemisphere
 */
function drawConnectivity(json, containerDivId, shouldRefreshNodes) {
    //init RGraph
    var rgraph = new $jit.RGraph({
        'injectInto': containerDivId,
        Node: {
            'overridable': true,
//            'color': '#cc0000',
            'alpha': 0.7
        },
        Edge: {
            'overridable': true,
            'color': '#cccc00'
        },
        //Set polar interpolation. Default's linear.
        interpolation: 'polar',
        //This method is called right before plotting an edge. This method is useful to change edge styles individually.
        onBeforePlotLine: function(adj) {
            if (!adj.data.$lineWidth)
                adj.data.$lineWidth = adj.data.weight * scaleFactor;
        },
        //Add node click handler and some styles. This method is called only once for each node/label crated.
        onCreateLabel: function(domElement, node) {
            domElement.innerHTML = node.name;
//            domElement.onclick = function () {
//                rgraph.onClick(node.id, { hideLabels: false });
//            };
            var style = domElement.style;
            style.cursor = 'default';
            style.fontSize = "0.8em";
            style.color = "#fff";
        },
        //This method is called when rendering/moving a label.
        //This is method is useful to make some last minute changes to node labels like adding some position offset.
        onPlaceLabel: function(domElement, node) {
            var style = domElement.style;
            var left = parseInt(style.left);
            var w = domElement.offsetWidth;
            style.left = (left - w / 2) + 'px';
        },
        onBeforePlotNode: function(node) {
            if (shouldDisplayCustomView) {
                node.data.$dim = node.data.customShapeDimension;
                node.data.$color = node.data.customShapeColor;
            }
        },

        onAfterCompute: function() {
        }

    });
    
    var selection_empty = true;
    var first_json_node = hasNodesInJson(json);
    if (first_json_node >= 0) {
    	selection_empty = false;
    	rootNode = first_json_node;
    }
    //load graph.
    if (shouldRefreshNodes) {
        rgraph.loadJSON(json, rootNode);
    } else {
        rgraph.loadJSON(json, 1);
    }

    // remove all the nodes that were not selected by the user
   
    if (selection_empty == false) {
	    rgraph.graph.eachNode(function(node) {
	        if (shouldRefreshNodes && selectedPoints.length > 0 && !isNodeSelected(node.id)) {
	            rgraph.graph.removeNode(node.id);
	        }
	    });    	
    }

    //compute positions and plot
    rgraph.refresh();
    rgraph.controller.onBeforeCompute(rgraph.graph.getNode(rgraph.root));
    rgraph.controller.onAfterCompute();

}

/**
 * Draws the slider which allows the user to change the weight af an edge.
 */
function drawSliderForWeightsScale() {
    $("#weightsScaleFactor").slider({
        value: 1,
        min: 1,
        max: 10
    });

    $("#weightsScaleFactor").slider({
        change: function(event, ui) {
            scaleFactor = $('#weightsScaleFactor').slider("option", "value");
            $("#display-weights-scale").html(" " + scaleFactor);
        	drawConnectivity(GVAR_hemisphere_jsons[C2D_selectedView], C2D_canvasDiv, C2D_shouldRefreshNodes);
        }
    });
}

/**
 * Add to cache all the data needed for drawing a chart
 *
 * @param divId the container id in which will be drawn the view
 * @param json a string which contains all the data needed for drawing a chart
 * @param shouldRefreshNodes if the drawn chart contains data related to both hemisphere
 */
function addToCache(divId, json, shouldRefreshNodes) {
    var existsInCache = false;
    for (var i = 0; i < cache.length; i++) {
        if (cache[i][0] == divId) {
            cache[i][1] = json;
            existsInCache = true;
            break;
        }
    }

    if (!existsInCache) {
        cache.push([divId, json, shouldRefreshNodes]);
    }
}

/**
 * Show/hide aasociated info in 2D displays.
 */
function change2DView() {
    shouldDisplayCustomView = !shouldDisplayCustomView;
	var btn = document.getElementById("change2DViewBtn");
    if (shouldDisplayCustomView) {
        btn.innerHTML ="Hide Details";
        btn.className = "action action-minus";
    } else {
        btn.innerHTML = "Show All";
        btn.className = "action action-plus";
    }
	
	C2D_displaySelectedPoints();
    //drawConnectivity(GVAR_hemisphere_jsons[C2D_selectedView], C2D_canvasDiv, C2D_shouldRefreshNodes);
}

/**
 * Each time when the user check/uncheck a check box this method will be called to redraw the main view.
 */
function C2D_displaySelectedPoints() {
	document.getElementById(C2D_canvasDiv).innerHTML = '';
    var setRoot = true;
    selectedPoints = [];
    rootNode = parseInt(GVAR_interestAreaNodeIndexes[0]);
	for (var i = 0; i < GVAR_interestAreaNodeIndexes.length; i++) {
		selectedPoints.push(GVAR_pointsLabels[GVAR_interestAreaNodeIndexes[i]]);
	}
	
    drawConnectivity(GVAR_hemisphere_jsons[C2D_selectedView], C2D_canvasDiv, C2D_shouldRefreshNodes);
    var canvas = $('#' + C2D_canvasDiv + "-canvas")[0];         // on each draw the canvas is replaced
    canvas.drawForImageExport = __resizeCanvasBeforeExport;     // so set the functions required for export
    canvas.afterImageExport   = __restoreCanvasAfterExport;
}

/**
 * The 2D canvas is drawn by JIT; therefore there is no access to its size, so its parent needs resizing before export
 * @private
 */
function __resizeCanvasBeforeExport() {
    var parent = $('#' + C2D_canvasDiv)
    var oldWidth  = parent.width(),
        oldHeight = parent.height();

    var scale = 1080 / oldHeight;
    // resize the container
    parent.width(oldWidth * scale);
    parent.height(oldHeight * scale);


    C2D_displaySelectedPoints();        // fill the resized container
}

/**
 * After canvas export, set its parent dimension back to normal
 * @private
 */
function __restoreCanvasAfterExport() {
    $('#' + C2D_canvasDiv).width("").height("");
    C2D_displaySelectedPoints();        // fill the resized container
}

/**
 * Removes from the cache (<code>selectedPoints</code> list) all the points that were selected by the user.
 * It also clears all the check boxes.
 */
function clearSelectedPoints() {
    selectedPoints = [];

	drawConnectivity(GVAR_hemisphere_jsons[C2D_selectedView], C2D_canvasDiv, C2D_shouldRefreshNodes);
}

function refresh2DTabs(selectedHref) {
	var allTabHeads = $(".tconn2DTabHead");
	for (var i = 0; i < allTabHeads.length; i++) {
		allTabHeads[i].style.color='#104120';
	}
	selectedHref.style.color='#00FF00';
}

/*
 * Check if any of the selected nodes are present in the json.
 */
function hasNodesInJson(json) {
	for (var i=0; i < json.length; i++) {
		if (isNodeSelected(json[i].id)) {
			return i;
		}
	}
	return -1;
}


/**
 * Checks to see if a certain node was selected by the user
 *
 * @param nodeId the id of the node to check. (A label of a point from the connectivity matrix)
 */
function isNodeSelected(nodeId) {
    var elemIdx = $.inArray(nodeId, selectedPoints);
    return elemIdx != -1;
}

function prepareConnectivity2D(left_json, full_json, right_json) {
    GVAR_hemisphere_jsons = {}
    GVAR_hemisphere_jsons['left'] = left_json;
    GVAR_hemisphere_jsons['both'] = full_json;
    GVAR_hemisphere_jsons['right'] = right_json;	
}
