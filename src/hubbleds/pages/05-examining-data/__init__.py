import solara
from cosmicds import load_custom_vue_components
from cosmicds.components import ScaffoldAlert
from cosmicds.viewers import CDSScatterView
from cosmicds.widgets.viewer_layout import ViewerLayout
from glue.core import Data
from glue_jupyter import JupyterApplication
from glue_jupyter.bqplot.scatter import BqplotScatterView
from pathlib import Path
from reacton import ipyvuetify as rv

from ...state import GLOBAL_STATE, LOCAL_STATE
from .component_state import ComponentState, Marker


GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

component_state = ComponentState()


@solara.component
def ToolBar(viewer):
    solara.Row(
        children=[
            viewer.toolbar,
            solara.v.Spacer(),
        ],
        margin=2,
        style={"align-items": "center"},
    )


@solara.component
def GridViewer(viewer):
    viewer.figure_widget.layout.height = 600
    layout = solara.Column(
        children=[
            ToolBar(viewer),
            viewer.figure_widget,
        ],
        margin=0,
        style={
            "height": "100%",
            "box-shadow": "0 3px 1px -2px rgba(0,0,0,.2),0 2px 2px 0 rgba(0,0,0,.14),0 1px 5px 0 rgba(0,0,0,.12) !important;",
        },
        classes=["elevation-2"],
    )
    with solara.Card(
        title="Viewer Card",
        children=[layout]
    ):
        pass


@solara.component
def Page():

    def glue_setup():
        gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)
        test_data = Data(x=[1,2,3,4,5], y=[1,4,9,16,26])
        test_data.style.color = "red"
        gjapp.data_collection.append(test_data)
        viewer = gjapp.new_data_viewer(CDSScatterView, data=test_data, show=False)
        layer = viewer.layers[0]
        layer.state.size = 25
        return gjapp 
    gjapp = solara.use_memo(glue_setup, [])

    test = solara.use_reactive(False)

    # Custom vue-only components have to be registered in the Page element
    #  currently, otherwise they will not be available in the front-end
    load_custom_vue_components()

    # Solara's reactivity is often tied to the _context_ of the Page it's
    #  being rendered in. Currently, in order to trigger subscribed callbacks,
    #  state connections need to be initialized _inside_ a Page.
    # component_state.setup()

    solara.Text(
        f"Current step: {component_state.current_step.value}, "
        f"Next step: {Marker(component_state.current_step.value.value + 1)}"
        f"Can advance: {component_state.can_transition(next=True)}"
    )

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRandomVariability.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ran_var1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineFinishedClassmates.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.fin_cla1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineClassData.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.cla_dat1),
            )

        def toggle_viewer():
            test.value = not test.value

        with rv.Col(cols=8):
            if test.value:
                GridViewer(viewer=gjapp.viewers[0])
            solara.Button("Testing", on_click=toggle_viewer)
