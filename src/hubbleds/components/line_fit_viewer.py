import solara
import reacton.ipyvuetify as rv
import plotly.express as px
import plotly.graph_objects as go

from cosmicds.line_fit_handler import LineFitHandler


@solara.component
def LineFitViewer(data):

    fig = go.Figure()
    print(id(fig))
    for d in data:
        fig.add_scatter(x=d["x"], y=d["y"])        

    line_fit_handler = LineFitHandler(fig)

    activate_count = solara.use_reactive(0)

    def activate():
       line_fit_handler.activate() 
       print("component activate")
       print(fig.data)
       print(id(fig))
       activate_count.set(activate_count.value + 1)

    with rv.Card():
        with rv.Toolbar(color="primary", dense=True):
            with rv.ToolbarTitle():
                solara.Text("LINE FIT VIEWER")

            rv.Spacer()

            line_button = solara.IconButton(icon_name="mdi-chart-timeline-variant", on_click=activate)
            rv.BtnToggle(v_model="selected", children=[line_button], background_color="primary", borderless=True)

        solara.FigurePlotly(fig, dependencies=[line_fit_handler.active])
