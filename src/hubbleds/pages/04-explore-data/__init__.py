from glue_jupyter import JupyterApplication
from hubbleds.base_component_state import transition_next, transition_previous
import numpy as np
from pathlib import Path
import reacton.ipyvuetify as rv
import solara
from solara.toestand import Ref
from typing import Tuple, cast

from cosmicds.components import ScaffoldAlert, StateEditor, ViewerLayout
from cosmicds.utils import empty_data_from_model_class
from hubbleds.components import DataTable, HubbleExpUniverseSlideshow, LineDrawHandler
from hubbleds.state import LOCAL_STATE, GLOBAL_STATE, StudentMeasurement, get_multiple_choice, get_free_response, mc_callback, fr_callback
from hubbleds.viewers import HubbleFitLayerView
from hubbleds.viewers.tools import LineDrawTool
from .component_state import COMPONENT_STATE, Marker
from hubbleds.remote import LOCAL_API
from hubbleds.utils import AGE_CONSTANT, models_to_glue_data

from cosmicds.logger import setup_logger

logger = setup_logger("STAGE 4")

GUIDELINE_ROOT = Path(__file__).parent / "guidelines"


@solara.component
def Page():
    loaded_component_state = solara.use_reactive(False)


    ### Set up the loading and writing of the component state

    async def _load_component_state():
        # Load stored component state from database, measurement data is
        # considered higher-level and is loaded when the story starts
        LOCAL_API.get_stage_state(GLOBAL_STATE, LOCAL_STATE, COMPONENT_STATE)

        # TODO: What else to we need to do here?
        logger.info("Finished loading component state for stage 4.")
        loaded_component_state.set(True)

    solara.lab.use_task(_load_component_state)

    async def _write_component_state():
        if not loaded_component_state.value:
            return

        # Listen for changes in the states and write them to the database
        LOCAL_API.put_stage_state(GLOBAL_STATE, LOCAL_STATE, COMPONENT_STATE)

        logger.info("Wrote component state to database.")

    solara.lab.use_task(_write_component_state, dependencies=[COMPONENT_STATE.value])

    ### Load in any data that we need

    async def _load_student_data():
        if not LOCAL_STATE.value.measurements_loaded:
            print("Getting measurements for student")
            LOCAL_API.get_measurements(GLOBAL_STATE, LOCAL_STATE)
    solara.lab.use_task(_load_student_data)

    class_data_loaded = solara.use_reactive(False)
    async def _load_class_data():
        class_measurements = LOCAL_API.get_class_measurements(GLOBAL_STATE, LOCAL_STATE)
        measurements = Ref(LOCAL_STATE.fields.class_measurements)
        student_ids = Ref(LOCAL_STATE.fields.stage_4_class_data_students)
        if class_measurements and not student_ids.value:
            ids = [int(id) for id in np.unique([m.student_id for m in class_measurements])]
            student_ids.set(ids)
        measurements.set(class_measurements)
        class_data_loaded.set(True)

    solara.lab.use_task(_load_class_data)


    ## Set up glue viewers
    ## This is done in a use_memo so that it only happens once

    line_draw_active = solara.use_reactive(False)

    def glue_setup() -> Tuple[JupyterApplication, HubbleFitLayerView]:
        gjapp = JupyterApplication(
            GLOBAL_STATE.value.glue_data_collection, GLOBAL_STATE.value.glue_session
        )
        
        line_viewer = cast(HubbleFitLayerView, gjapp.new_data_viewer(HubbleFitLayerView, show=False))
        line_draw_tool = cast(LineDrawTool, line_viewer.toolbar.tools["hubble:linedraw"])
        line_draw_tool.on_activate(line_draw_active.set)

        return gjapp, line_viewer

    gjapp, line_viewer = solara.use_memo(glue_setup, dependencies=[])

    class_data_added = solara.use_reactive(False)
    student_data_added = solara.use_reactive(False)

    links_setup = solara.use_reactive(False)
    def _setup_links(_value: bool):
        if not (class_data_added.value and student_data_added.value):
            return
        student_data = gjapp.data_collection["My Data"]
        class_data = gjapp.data_collection["Class Data"]
        for component in ("est_dist_value", "velocity_value"):
            gjapp.add_link(student_data, component, class_data, component)
        line_viewer.add_data(student_data)

        links_setup.set(True)

    def _on_student_data_loaded(value: bool):
        if not value:
            return

        student_data = models_to_glue_data(LOCAL_STATE.value.measurements, label="My Data", ignore_components=["galaxy"])
        # NB: If there are no components, Data::size returns 1 (empty product)
        # so that can't be our check
        if not student_data.components:
            student_data = empty_data_from_model_class(StudentMeasurement, label="My Data")
        student_data = GLOBAL_STATE.value.add_or_update_data(student_data)
        student_data_added.set(True)

    
    measurements_loaded = Ref(LOCAL_STATE.fields.measurements_loaded)
    if measurements_loaded.value:
        _on_student_data_loaded(True)
    else:
        measurements_loaded.subscribe(_on_student_data_loaded)

    def _on_class_data_loaded(value: bool):
        if not value:
            return

        class_ids = LOCAL_STATE.value.stage_4_class_data_students
        class_data_points = [m for m in LOCAL_STATE.value.class_measurements if m.student_id in class_ids]
        class_data = models_to_glue_data(class_data_points, label="Class Data")
        class_data = GLOBAL_STATE.value.add_or_update_data(class_data)

        line_viewer.add_data(class_data)
        line_viewer.state.x_att = class_data.id['est_dist_value']
        line_viewer.state.y_att = class_data.id['velocity_value']
        line_viewer.state.x_axislabel = "Distance (Mpc)"
        line_viewer.state.y_axislabel = "Velocity"

        class_data_added.set(True)

    class_data_loaded.subscribe(_on_class_data_loaded)

    student_data_added.subscribe(_setup_links)
    class_data_added.subscribe(_setup_links)

    @solara.lab.computed
    def data_ready():
        return student_data_added.value and class_data_added.value

    if not data_ready.value:
        rv.ProgressCircular(
            width=3,
            color="primary",
            indeterminate=True,
            size=100,
        )
        return


    StateEditor(Marker, COMPONENT_STATE, LOCAL_STATE, LOCAL_API)

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineExploreData.vue",
                event_next_callback = lambda _: transition_next(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.exp_dat1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverseEstimate3.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.age_uni3),
                state_view={
                    "age_const": AGE_CONSTANT,
                    # TODO: Update these once real values are hooked up
                    "hypgal_distance": 100,
                    "hypgal_velocity": 8000,
                }
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverseEstimate4.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.age_uni4),
                state_view={
                    "age_const": AGE_CONSTANT,
                    # TODO: Update these once real values are hooked up
                    "hypgal_distance": 100,
                    "hypgal_velocity": 8000,
                }
            )

        with rv.Col():
            DataTable(
                title="My Galaxies",
                items=[x.model_dump() for x in LOCAL_STATE.value.measurements],
                headers=[
                    {
                        "text": "Galaxy Name",
                        "align": "start",
                        "sortable": False,
                        "value": "galaxy.name"
                    },
                    { "text": "Velocity (km/s)", "value": "velocity_value" },
                    { "text": "Distance (Mpc)", "value": "est_dist_value" },
                ]
            )

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineTrendsDataMC1.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.tre_dat1),
                event_mc_callback=lambda event: mc_callback(event=event, local_state=LOCAL_STATE),
                state_view={
                    "mc_score": get_multiple_choice(LOCAL_STATE, "tre-dat-mc1"),
                    "score_tag": "tre-dat-mc1"
                }
            )
            ScaffoldAlert(
                # TODO: This will need to be wired up once viewer is implemented
                GUIDELINE_ROOT / "GuidelineTrendsData2.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.tre_dat2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineTrendsDataMC3.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.tre_dat3),
                event_mc_callback=lambda event: mc_callback(event=event, local_state=LOCAL_STATE),
                state_view={
                    'mc_score': get_multiple_choice(LOCAL_STATE, 'tre-dat-mc3'),
                    'score_tag': 'tre-dat-mc3'
                }
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRelationshipVelDistMC.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.rel_vel1),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE),
                state_view={
                    'mc_score': get_multiple_choice(LOCAL_STATE, 'galaxy-trend'),
                    'score_tag': 'galaxy-trend'
                }
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineTrendLines1.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.tre_lin1),               
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once linedraw tool is implemented
                GUIDELINE_ROOT / "GuidelineTrendLinesDraw2.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.tre_lin2),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once best fit line tool is implemented
                GUIDELINE_ROOT / "GuidelineBestFitLine.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.bes_fit1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineHubblesExpandingUniverse1.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.hub_exp1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverse.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.age_uni1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineHypotheticalGalaxy.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.hyp_gal1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeRaceEquation.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.age_rac1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverseEquation2.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.age_uni2),
                state_view={
                    "age_const": AGE_CONSTANT
                },             
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineYourAgeEstimate.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.you_age1),
            )
            ScaffoldAlert(
                # TODO - add free response functionality
                GUIDELINE_ROOT / "GuidelineShortcomingsEstReflect1.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.sho_est1),
                event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                state_view={
                    'free_response_a': get_free_response(LOCAL_STATE, 'shortcoming-1'),
                    'free_response_b': get_free_response(LOCAL_STATE, 'shortcoming-2'),
                    'free_response_c': get_free_response(LOCAL_STATE, 'other-shortcomings'),
                }
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineShortcomingsEst2.vue",
                # TODO: event_next_callback should go to next stage but I don't know how to set that up.
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.sho_est2),
            )

        with rv.Col(class_="no-padding"):
            if COMPONENT_STATE.value.current_step_between(Marker.tre_dat1, Marker.sho_est2):
                with solara.Columns([3,9], classes=["no-padding"]):
                    with rv.Col(class_="no-padding"):
                        # TODO: LayerToggle should refresh when the data changes
                        # LayerToggle(viewer)
                        with solara.Card(style="background-color: var(--error);"):
                            solara.Markdown("Layer Toggle")
                    with rv.Col(class_="no-padding"):
                        LineDrawHandler(graph_class=line_viewer.unique_class, active=line_draw_active.value)
                        ViewerLayout(viewer=line_viewer)

            with rv.Col(cols=10, offset=1):
                if COMPONENT_STATE.value.current_step_at_or_after(
                Marker.hub_exp1):
                    slideshow_finished = Ref(COMPONENT_STATE.fields.hubble_slideshow_finished)
                    HubbleExpUniverseSlideshow(
                        event_on_slideshow_finished=lambda _: slideshow_finished.set(True),
                        dialog=COMPONENT_STATE.value.show_hubble_slideshow_dialog,
                        step=COMPONENT_STATE.value.hubble_slideshow_state.step,
                        max_step_completed=COMPONENT_STATE.value.hubble_slideshow_state.max_step_completed,
                    )
