<template>
  <div id="line-draw-handler"></div>
</template>

<script>
export default {
  name: "LineDrawHandler",
  props: [
    "active",
    "graph_class",
    "line_drawn",
  ],
  async mounted() {
    await window.plotlyPromise;
    this.getElement();
  },
  data() {
    return {
      element: null,
      dragLayer: null,
      lineDrawn: false,
      mouseDown: false,
      movingLine: false,
      lastEndpoint: null,
      hoveringEndpoint: false,
      lineTraceIndex: 0,
      endpointTraceIndex: 0,
      endpointSize: 10,
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
    worldToScreen(worldX, worldY) {
      const layout = this.element._fullLayout;
      const rect = this.element.getBoundingClientRect();
      const xScreen = layout.xaxis.c2p(worldX) + layout.margin.l + rect.left;
      const yScreen = layout.yaxis.c2p(worldY) + layout.margin.t + rect.top;
      return [xScreen, yScreen];
    },
    addLineTrace() {
      Plotly.addTraces(this.element, [
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
      ]);
    },
    removeLineTrace() {
      Plotly.deleteTraces(this.element, [this.lineTraceIndex, this.endpointTraceIndex]);
    },
    updateLine(event) {
      const [xWorld, yWorld] = this.screenToWorld(event);
      Plotly.update(
        this.element,
        { 'x.1': xWorld, 'y.1': yWorld },
        {},
        [this.lineTraceIndex]
      );
    },
    getElement() {
      this.element = document.querySelector(`.${this.graph_class}`);
    },
    mouseMoveHandler(event) {
      if (this.movingLine) {
        this.updateLine(event);
      }
    },
    mouseDownHandler(event) {
      this.mouseDown = true;
    },
    mouseUpHandler(event) {
      this.mouseDown = false;
      if (this.movingLine) {
        this.movingLine = false;
        this.drawEndpoint(event);
        this.lineDrawn = true;
        const cursor = this.overEndpoint(event) ? "grab" : "default";
        this.setCursor(cursor);
        if (this.line_drawn) {
          this.line_drawn();
        }
      }
    },
    plotlyClickHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        this.movingLine = true;
        this.clearEndpoint();
      }
    },
    plotlyHoverHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        this.setCursor("grab");
      }
    },
    plotlyUnhoverHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        let cursor;
        if (this.movingLine) {
          cursor = this.lineDrawn ? "grabbing" : "default";
        } else {
          cursor = "crosshair";
        }
        this.setCursor(cursor);
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
          Plotly.deleteTraces(this.element, this.endpointTraceIndex);
        } catch (e) {
          console.warn(e);
        }
      }
    },
    overEndpoint(event) {
      if (this.lastEndpoint === null) {
        return false;
      }
      const layout = this.element._fullLayout;
      const rect = this.element.getBoundingClientRect();
      const x = event.clientX;
      const y = event.clientY;
      const endpointScreen = this.worldToScreen(...this.lastEndpoint);
      const relX = x - endpointScreen[0];
      const relY = y - endpointScreen[1];
      return Math.pow(relX, 2) + Math.pow(relY, 2) <= Math.pow(this.endpointSize / 2, 2);
    },
    drawEndpoint(event) {
      // If the mouse is moving quickly, it's possible for the endpoint to be
      // a bit off from the line if we just use the screen coordinates of the event.
      // So instead, just draw the endpoint at the end of the line
      const line = this.element.data[this.lineTraceIndex];
      const x = line.x[1];
      const y = line.y[1];
      Plotly.addTraces(this.element, { x: [x], y: [y], type: "scatter", mode: "markers", marker: { size: this.endpointSize, color: "#000000" }, hoverinfo: "none" });
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
    setupPlotlyHandlers(active) {
      if (active) {
        this.element.on("plotly_click", this.plotlyClickHandler);
        this.element.on("plotly_hover", this.plotlyHoverHandler);
        this.element.on("plotly_unhover", this.plotlyUnhoverHandler);
      } else {
        this.element.removeListener("plotly_click", this.plotlyClickHandler);
        this.element.removeListener("plotly_hover", this.plotlyHoverHandler);
        this.element.removeListener("plotly_unhover", this.plotlyUnhoverHandler);
      }
    },

  },
  watch: {
    active(value) {
      if (!this.element) {
        this.getElement();
      }
      if (this.element) {
        this.movingLine = value && this.lastEndpoint === null;
        Plotly.update(this.element, { visible: true }, {}, [this.lineTraceIndex]);
        this.setupMouseHandlers(value);
        this.setupPlotlyHandlers(value);
        console.log("Setup listeners");
        console.log(value);
      }
    },
    element(el) {
      if (!el) {
        return;
      }
      console.log(el);
      const nTraces = this.element.data.length;
      this.lineTraceIndex = nTraces;
      this.endpointTraceIndex = nTraces + 1;
      this.addLineTrace();
      this.dragLayer = this.element.querySelector(".nsewdrag");
      this.setupMouseHandlers(this.active);
      this.setupPlotlyHandlers(this.active);
    },
    movingLine(value) {
      if (value) {
        const cursor = this.lineDrawn ? "grabbing" : "default";
        this.setCursor(cursor);
      }
    }
  }
}
</script>
