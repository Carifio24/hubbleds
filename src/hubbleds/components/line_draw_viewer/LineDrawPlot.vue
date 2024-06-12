<script>
export default {
  name: "LineDrawPlot",
  props: ["active", "line_drawn", "plot_data"],
  async mounted() {
    await window.plotlyPromise;

    let xmin = 0;
    let xmax = 0;
    let ymin = 0;
    let ymax = 0;
    this.plot_data?.forEach(trace => {
      // NB: We can't call e.g. Math.min.apply because of the observer object that Vue puts into the array
      xmin = Math.min(xmin, Math.min(...trace.x));
      ymin = Math.min(ymin, Math.min(...trace.y));
      xmax = Math.max(xmax, Math.max(...trace.x));
      ymax = Math.max(ymax, Math.max(...trace.y));
    });
    const layout = this.chart.layout;
    layout.xaxis.range = [xmin, xmax];
    layout.yaxis.range = [ymin, ymax];

    Plotly.newPlot(this.$refs[this.chart.uuid], this.chart.traces, layout, this.chart.config)
      .then(() => {
        this.element = document.getElementById(this.chart.uuid);
        this.dragLayer = this.element.querySelector(".nsewdrag");
        if (this.plot_data) {
          this.plotDataCount = this.plot_data.length;
          Plotly.addTraces(this.chart.uuid, this.plot_data);
        }
        this.setupMouseHandlers(this.active);
        this.setupPlotlyHandlers(this.active);
      });
  },
  data() {
    const baseAxis = {
      showspikes: false,
      zeroline: false,
      mirror: true,
      ticks: "outside",
      showline: true,
      showgrid: false,
      showticklabels: true,
      autorange: false,
      automargin: true,
    };

    const xaxis = { ...baseAxis, range: [0, 1] };
    const yaxis = { ...baseAxis, range: [0, 1] };
    return {
      chart: {
        uuid: "abcde",
        traces: [
          {
            x: [0, 0],
            y: [0, 0],
            line: {
              color: "#000000",
              width: 4,
              shape: "line"
            },
            visible: false,
            hoverinfo: "skip"
          }
        ],
        layout: { xaxis, yaxis, hovermode: "none", dragmode: false, showlegend: false },
        config: { displayModeBar: false, responsive: true },
      },
      element: null,
      lineDrawn: false,
      mouseDown: false,
      movingLine: false,
      lastEndpoint: null,
      plotDataCount: 0,
      lineTraceIndex: 0,
    };
  },
  methods: {
    screenToWorld(event) {
      const layout = this.element._fullLayout;
      const rect = this.element.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const xWorld = layout.xaxis.p2c(x - layout.margin.l);
      const yWorld = layout.yaxis.p2c(y - layout.margin.t);
      return [xWorld, yWorld];
    },
    updateLine(event) {
      const [xWorld, yWorld] = this.screenToWorld(event);
      Plotly.update(
        this.chart.uuid,
        { 'x.1': xWorld, 'y.1': yWorld },
        {},
        [this.lineTraceIndex]
      );
    },
    mouseMoveHandler(event) {
      if (this.movingLine) {
        this.updateLine(event);
      }
    },
    mouseDownHandler(event) {
      this.mouseDown = true;
      if (this.movingLine) {
        this.movingLine = false;
        this.drawEndpoint(event);
        this.lineDrawn = true;
        if (this.line_drawn) {
          this.line_drawn();
        }
      }
    },
    mouseUpHandler(_event) {
      this.mouseDown = false;
    },
    plotlyClickHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        if (this.hoveringEndpoint) {
          this.hoveringEndpoint = false;
          this.movingLine = true;
          this.clearEndpoint();
        }
      }
    },
    plotlyHoverHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        this.hoveringEndpoint = true;
        this.setCursor("move");
      }
    },
    plotlyUnhoverHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        this.hoveringEndpoint = false;
        this.setCursor(this.movingLine ? "grabbing" : "crosshair");
      }
    },
    setCursor(type) {
      this.element.style.cursor = type;
      this.dragLayer.style.cursor = type;
      // This class sets the cursor to be the crosshair on Plotly
      // so we need a bit of special handling here
      if (type === "crosshair") {
        this.dragLayer.classList.add("cursor-crosshair");
      } else {
        this.dragLayer.classList.remove("cursor-crosshair");
      }
    },
    clearEndpoint() {
      const dataTracesCount = this.plot_data?.length ?? 0;
      if (this.element.data.length > dataTracesCount + 1) {
        try {
          Plotly.deleteTraces(this.chart.uuid, this.endpointTraceIndex);
        } catch (e) {
          console.warn(e);
        }
      }
    },
    drawEndpoint(event) {
      const [x, y] = this.screenToWorld(event);
      Plotly.addTraces(this.chart.uuid, { x: [x], y: [y], type: "scatter", mode: "markers", marker: { size: 10, color: "#000000" }, hoverinfo: "none" });
      this.lastEndpoint = [x, y];
    },
    setupMouseHandlers(active) {
      // Using document as the event listener for mouseup is intentional
      // See this thread here: https://community.plotly.com/t/plotly-onmousedown-and-onmouseup/4812
      // For some reason, mousedown works fine on the Plotly graph, but not mouseup
      // Any ideas on how to not need to do this would be great!
      if (active) {
        this.element.addEventListener("mousemove", this.mouseMoveHandler);
        this.element.addEventListener("mousedown", this.mouseDownHandler);
        document.addEventListener("mouseup", this.mouseUpHandler);
      } else if (this.element != null) {
        this.element.removeEventListener("mousemove", this.mouseMoveHandler);
        this.element.removeEventListener("mousedown", this.mouseDownHandler);
        document.removeEventListener("mouseup", this.mouseUpHandler);
      }
    },
    addPlotlyHandlers() {
      this.element.on("plotly_click", this.plotlyClickHandler);
      this.element.on("plotly_hover", this.plotlyHoverHandler);
      this.element.on("plotly_unhover", this.plotlyUnhoverHandler);
    },
    removePlotlyHandlers() {
      this.element.removeListener("plotly_click", this.plotlyClickHandler);
      this.element.removeListener("plotly_hover", this.plotlyHoverHandler);
      this.element.removeListener("plotly_unhover", this.plotlyUnhoverHandler);
    },
    setupPlotlyHandlers(active) {
      if (active) {
        this.addPlotlyHandlers();
      } else {
        this.removePlotlyHandlers();
      }
    }
  },
  computed: {
    endpointTraceIndex() {
      return (this.plot_data?.length ?? 0) + 1;
    }
  },
  watch: {
    chart() {
      Plotly.react(
        this.$refs["chart"],
        this.chart.traces,
        this.chart.layout
      );
    },
    active(value) {
      if (value && this.lastEndpoint === null) {
        this.movingLine = true;
      }
      Plotly.update(this.chart.uuid, { visible: true }, {}, [this.lineTraceIndex]);
      this.setupMouseHandlers(value);
      if (!value) {
        this.movingLine = false;
      }
    },
    movingLine(value) {
      const cursor = value ? "grabbing" : "move";
      this.setCursor(cursor);
      if (this.lastEndpoint !== null) {
        this.setupPlotlyHandlers(!value);
      }
    }
  }
}
</script>

<template>
<div
  :ref="chart.uuid"
  :id="chart.uuid"
></div>
</template>

<style>
.svg-container {
  width: 100% !important;
}

.main-svg {
  width: 100% !important;
  border-bottom-left-radius: 5px;
  border-bottom-right-radius: 5px;
}
</style>
