PCAViewer = function (root, fractions, weights_raw, width, height) {
	this.root = root;
	this.fractions = fractions.mul(2 * Math.PI);
	this.weights_raw = weights_raw;
	this.width = width || 800;
	this.height = height || 400;
	this.fromChan = 0;
	this.toChan = 10;
	this.nComp = this.fractions.length();
	this.linesSpacing = 1.5;
	this.colorMap = d3.scale.category10();
	this.pieInnerRadius = 50;
	this.pieOuterRadius = 150;
}

PCAViewer.prototype.plot = function() {
	// create different groups we'll use (not best strategy...)
	var w = this.width;
	var h = this.height;
    this.root.selectAll("g").data([
            {id: "pie", x: w / 8, h: h / 2.2},
            {id: "bars", x: w / 2, h: h / 2},
            {id: "text", x: 0.1 * w, h: 0.95 * h}
        ])
        .enter().append("g").attr("id", function (d) {
            return d.id;
        })
        .attr("transform", function (d) {
            return "translate(" + d.x + ", " + d.h + ")"
        })
        
    // text displaying info on mouse over
    this.root.select("g#text").append("text").classed("pca-text", true).text("");
	this.draw_pie_chart(this.root.select("g#pie"))
	this.draw_vectors_plot(this.root.select("g#bars"));  
}

PCAViewer.prototype.draw_pie_chart = function(root) {
	// process slices
	var self = this;
    var slices = this.fractions.slice(this.fromChan, this.toChan).data;
    slices.push(this.fractions.slice(this.toChan, this.nComp).sum());
    var slice_specs = [];
    var slice_acc = 0;
    for (var i = 0; i < slices.length; i++) {
        slice_specs[i] = {startAngle: slice_acc};
        slice_acc += slices[i];
        slice_specs[i].endAngle = slice_acc - 0.01;
    }
    this.piePlot = root.selectAll("path").data(slice_specs).enter();
	this.piePlot.append("path")
			        .style("fill", function (d, i) {
			            return i === (self.fromChan - self.toChan) ? "#ddd" : self.colorMap(i);
			        })
			        .attr("d", d3.svg.arc().innerRadius(this.pieInnerRadius).outerRadius(this.pieOuterRadius))
			        .on("mouseover", function (d, i) {
			            var u = self.fractions.data
			            var txt;
			            if (i < self.toChan && i > self.fromChan) {
			                var ord = tv.util.ord_nums[i + 1], v = u[i] * 100;
			                txt = ord.slice(0, 1).toUpperCase() + ord.slice(1, ord.length)
			                    + " component explains " + v.toPrecision(3) + " % of the variance.";
			            }
			            else {
			                var v = tv.ndar.from(u.slice((self.toChan - self.fromChan), u.length)).sum() * 100;
			                txt = "Other " + (self.nComp - (self.toChan - self.fromChan)) + " components explain " + v.toPrecision(3) + " % of the variance.";
			            }
			            self.root.select("g#text").select("text").text(txt);
			            self.axesPlot.select("path").style("stroke-width", function (e, j) {
			                return i === j ? 3 : 1;
			            });
			        })
			        .on("mouseout", function (d, i) {
			            self.root.select("g#text").select("text").text("");
			            self.axesPlot.select("path").style("stroke-width", 1);
			        });
}

PCAViewer.prototype.draw_vectors_plot = function(root) {
	/*
	 * Draw the right side visualization, having weights for individual nodes.
	 */
	// draw labels
	var self = this;
	var nrNodes = this.nComp;
	var w = this.width;
    var h = this.height;
    var linesSpace = this.linesSpacing;
    var weights_raw = this.weights_raw;
    
    var labels = root.append("g").selectAll("text").data(tv.ndar.range(nrNodes).data).enter();
    labels.append("text")
    				.classed("node-labels", true)
	                .attr("transform", function (d) {
	                    return "translate(" + (w / linesSpace / nrNodes) * (d - nrNodes / 3) + ", " + -h / 2.4 + ") rotate(-60) ";
	                })
	                .text(function (d) {
	                    return "node " + d;
	                }) // TODO use real node labels

    // draw vertical grid lines
    var gridLines = root.append("g").attr("transform", "translate(" + -w / 4.5 + "," + (-h / 3 - 15) + ")").selectAll("line").data(tv.ndar.range(nrNodes).data).enter();
    gridLines.append("line").attr("x1",function (d) { return w / linesSpace / nrNodes * d })
    						.attr("x2", function (d) { return w / linesSpace / nrNodes * d })
        					.attr("y2", 2 * h / 3)
        					.attr("y1", -15)
        					.attr("stroke", function (d) { return d % 5 === 0 ? "#ccc" : "#eee"; });

    // organize the data (TODO: there's gotta be a better way of doing this)
    var weights_data = [];
    var weights_scl = Math.max(-weights_raw.min(), weights_raw.max());

    for (var i = 0; i < (this.toChan - this.fromChan); i++) {
        weights_data[i] = [];
        for (var j = 0; j < this.nComp; j++) {
            weights_data[i][j] = [ j * w / linesSpace / nrNodes, 
            					  ( 2 * h / 3 / (this.toChan - this.fromChan) / 2 / weights_scl) * weights_raw.data[i * this.nComp + j]
            					  ];
        }
    }

    // setup axes groups, add zero lines, vector curves and plus/minus signs
    this.axesPlot = root.append("g").selectAll("g").data(weights_data).enter().append("g").attr("transform", function (d, i) {
            return "translate(" + -w / 4.5 + ", " + (i / (self.toChan - self.fromChan) * 2 * h / 3 - h / 3) + ")";
        });

    this.axesPlot.append("line").attr("x2", w / linesSpace).style("stroke", "black");
    this.axesPlot.append("path").attr("d", d3.svg.line())
    					  .attr("fill", "transparent").attr("stroke", function (d, i) {
        return self.colorMap(i);
    });
    this.axesPlot.append("text").classed("vt-pm-sign", true).attr("x", -6).text("+")
    this.axesPlot.append("text").classed("vt-pm-sign", true).attr("x", -5).attr("y", 5).text("-")
}

