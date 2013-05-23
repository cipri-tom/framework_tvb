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
 * Functions for BrainVisualizer in Double View (eeg-lines + 3D activity).
 */

function EX_initializeChannels() {
    if (isDoubleView) {
        $("#checkAllChannelsBtn").click(function() {
            $("input[id^='channelChk_']").each(function (i) {
                var index = this.id.split("channelChk_")[1];
                EX_changeColorBufferForMeasurePoint(index, this.checked);
            });
        });
        $("#clearAllChannelsBtn").click(function() {
            $("input[id^='channelChk_']").each(function (i) {
                var index = this.id.split("channelChk_")[1];
                EX_changeColorBufferForMeasurePoint(index, this.checked);
            });
        });
        $("input[id^='channelChk_']").change(function() {
            var index = this.id.split("channelChk_")[1];
            EX_changeColorBufferForMeasurePoint(index, this.checked);
        });
        $("#refreshChannelsButton").click(function() {
        	resetBrainToStart();
        });
    }
};


/**
 * In the extended view if a certain EEG channel was selected then we
 * have to draw the measure point corresponding to it with a different color.
 *
 * @param measurePointIndex the index of the measure point to which correspond the EEG channel
 * @param isPicked if <code>true</code> then the point will be drawn with the color corresponding
 * to the selected channels, otherwise with the default color
 */
function EX_changeColorBufferForMeasurePoint(measurePointIndex, isPicked) {
    var colorBufferIndex = measurePointsBuffers[measurePointIndex].length - 1;
    measurePointsBuffers[measurePointIndex][colorBufferIndex] = createColorBufferForCube(isPicked);
}


/**
 * Internal method, to reset all variable, for the Brain visualizer activity to be started from 0.
 */
function resetBrainToStart() {
	currentTimeInFrame = 0;
	if (activitiesDataUrls.length > 0) {
        //read the first file
        activitiesData = HLPR_readJSONfromFile(activitiesDataUrls[0]);
        currentActivitiesFileIndex = 0;
        currentActivitiesFileLength = activitiesData.length;
        totalPassedActivitiesData = 0;
    }
}


