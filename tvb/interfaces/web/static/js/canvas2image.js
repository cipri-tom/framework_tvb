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


/**
 * If you want ot preview a webGl canvas you have to set
 * the flag 'webGlCanvas' to true for that canvas.
 */
function previewCanvas(canvasId, exportType) {
    var canvas = document.getElementById(canvasId);
    var isWebGlCanvas = canvas.webGlCanvas;
    if (isWebGlCanvas != undefined && isWebGlCanvas) {
        C2I_shouldPreviewCanvas = true;
        C2I_exportType = exportType;
    } else {
        var strData = __exportCanvas(canvasId, exportType);
        window.open(strData, "_blank", "location=no,menubar=no,status=no,scrollbars=no,titlebar=no,toolbar=no");
    }
}


/**
 * If you want ot export webGl canvases you have to set
 * the flag 'webGlCanvas' to true for that canvases.
 */
function exportCanvases(operationId) {
    if ($("canvas, svg").length == 0) {
        displayMessage("Invalid action. Please report to your TVB technical contact.", "errorMessage");
        return;
    }
    $("canvas").each(function () {
        if (this.id)
            __storeCanvas(this.id, operationId)
    });

    $("svg").attr({ version: '1.1' , xmlns:"http://www.w3.org/2000/svg"});
    $("svg").each(function () {
        __storeSVG(this, operationId)
    });
}

/**
 *This method save the svg html. Before this it also adds the required css styles.
 */
function __storeSVG(svgElement, operationId) {
	// Wrap the svg element as to get the actual html and use that as the src for the image

	var wrap = document.createElement('div');
	wrap.appendChild(svgElement.cloneNode(true));
	var data = wrap.innerHTML;

    // get the styles for the svg
    $.get( "/static/style/tvbviz.css", function (stylesheet) {
                                                                         // strip all
        var re = new RegExp("[\\s\\n^]*\\/\\*(.|[\\r\\n])*?\\*\\/" +     // block style comments
                            "|([\\s\\n]*\\/\\/.*)" +                     // single line comments
                            "|(^\\s*[\\r\\n])", "gm");                   // empty lines

        var svgStyle = "<defs><style type='text/css'><![CDATA["
                     +  stylesheet.replace(re,"")
                     + "]]></style></defs>";

        // embed the styles in svg
        var startingTag = data.substr(0, data.indexOf(">") + 1);
        var restOfSvg = data.substr(data.indexOf(">") + 1, data.length + 1)
        var styleAddedData = startingTag + svgStyle + restOfSvg;


        // send it to server
        $.ajax({  type: "POST", url: '/project/figure/storeresultfigure/svg/' + operationId,
            data: {"export_data": styleAddedData},
            success: function(r) {
                displayMessage("Figure successfully saved!<br/> See Project section, Image archive sub-section.",
                               "infoMessage")
            } ,
            error: function(r) {
                displayMessage("Could not store preview image, sorry!", "warningMessage")
            }
        });

    } );
}

/**
 * This function sends canvas' snapshot to server, after it has been prepared by <code>__storeCanvas()</code>
 *
 * NOTE: Some canvases (MPLH5) set <code>canvas.notReadyForExport</code> flag to indicate that their resize is not done
 * yet; if such flag exists, exporting continues only when it is set to <code>false</code> or after
 * <code>remainingTrials</code> trials
 *
 * @param canvas The **RESIZED** canvas whose snapshot is to be stored
 * @param operationId Current operation id, associated with this storage
 * @param originalWidth Width of <code>canvas</code> before resizing
 * @param originalHeight Height of <code>canvas</code> before resizing
 * @param remainingTrials The number of times to poll for <code>canvas.notReadyForExport</code> flag
 * @private
 */
function __tryExport(canvas, operationId, remainingTrials) {
    if (canvas.notReadyForExport && remainingTrials > 0)
        // the mplh5 canvases will set this flag to TRUE after they finish resizing, so they can be exported at Hi Res
        // undefined or FALSE means it CAN BE exported
        setTimeout(function() { __tryExport(canvas, operationId, remainingTrials - 1) }, 200)

    else {              // canvas is ready for export
        var data = canvas.toDataURL("image/png");

        if (data)       // don't store empty images
            $.ajax({  type: "POST", url: '/project/figure/storeresultfigure/png/' + operationId,
                        data: {"export_data": data.replace('data:image/png;base64,', '')},
                        success: function(r) {
                            displayMessage("Figure successfully saved!<br/> See Project section, " +
                                           "Image archive sub-section.", "infoMessage")
                        } ,
                        error: function(r) {
                            displayMessage("Could not store preview image, sorry!", "warningMessage")
                        }
                    });
        else            // there was no image data
            displayMessage("Canvas contains no image data. Try again or report to your TVB technical contact",
                           "warningMessage")

        // restore original canvas size; non-webGL canvases (EEG, mplh5, JIT) have custom resizing methods
        if (canvas.afterImageExport)
            canvas.afterImageExport();
    }

    }

/**
 * This function deals with canvas storage. First it prepares it by calling its resize method
 * (<code>canvas.drawForImageExport</code>), then tries to save it
 * @param canvasId The canvas whose image is to be stored
 * @param operationId Current operation id, associated with this storage
 * @private
 */
function __storeCanvas(canvasId, operationId) {
    var canvas = document.getElementById(canvasId);

    if (!canvas.drawForImageExport)     // canvases which didn't set this method should not be saved
        return;

    canvas.drawForImageExport();        // interface-like function that redraws the canvas at bigger dimension

    __tryExport(canvas, operationId, 5);
}