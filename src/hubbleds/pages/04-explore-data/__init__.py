import asyncio
from cosmicds.utils import empty_data_from_model_class, DEFAULT_VIEWER_HEIGHT
from cosmicds.viewers import CDSScatterView
from glue.core import Data
from glue_jupyter import JupyterApplication
from hubbleds.base_component_state import transition_next, transition_previous
from ipywwt import WWTWidget
import numpy as np
from pathlib import Path
import reacton.ipyvuetify as rv
import solara
from solara.toestand import Ref
from typing import Dict, List, Tuple

from cosmicds.components import ScaffoldAlert, StateEditor, ViewerLayout
from hubbleds.components import DataTable, HubbleExpUniverseSlideshow, LineDrawViewer, PlotlyLayerToggle
from hubbleds.state import LOCAL_STATE, GLOBAL_STATE, StudentMeasurement, get_multiple_choice, get_free_response, mc_callback, fr_callback
from hubbleds.viewers.hubble_scatter_viewer import HubbleScatterView
from .component_state import COMPONENT_STATE, Marker
from hubbleds.remote import LOCAL_API
from hubbleds.utils import AGE_CONSTANT, models_to_glue_data, PLOTLY_MARGINS

from cosmicds.logger import setup_logger

logger = setup_logger("STAGE 4")

GUIDELINE_ROOT = Path(__file__).parent / "guidelines"


@solara.component
def Page():

    StateEditor(Marker, COMPONENT_STATE, LOCAL_STATE, LOCAL_API)


    loaded_component_state = solara.use_reactive(False)

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

    def load_class_data():
        logger.info("Loading class data")
        class_measurements = LOCAL_API.get_class_measurements(GLOBAL_STATE, LOCAL_STATE)
        logger.info(len(class_measurements))
        measurements = Ref(LOCAL_STATE.fields.class_measurements)
        student_ids = Ref(LOCAL_STATE.fields.stage_4_class_data_students)
        if class_measurements and not student_ids.value:
            ids = [int(id) for id in np.unique([m.student_id for m in class_measurements])]
            student_ids.set(ids)
        measurements.set(class_measurements)
    
        class_data_points = [m for m in class_measurements if m.student_id in student_ids.value]
        # Ref(LOCAL_STATE.fields.enough_students_ready).set(len(class_data_points) >= min(100, 5 * GLOBAL_STATE.value.classroom.size))
        Ref(LOCAL_STATE.fields.enough_students_ready).set(len(class_data_points) >= 100)
            
        return class_data_points

    async def keep_checking_class_data():
        count = 0
        enough_students_ready = Ref(LOCAL_STATE.fields.enough_students_ready)
        while not enough_students_ready.value:
            points = load_class_data()
            count += 1
            ready = len(points) >= 100 - 10 * count
            if ready != enough_students_ready.value:
                enough_students_ready.set(ready)
            await asyncio.sleep(10)

    solara.lab.use_task(keep_checking_class_data, dependencies=[])

    if COMPONENT_STATE.value.current_step == Marker.wwt_wait:
        with rv.Card():
            WWTWidget.element()
            solara.Button(label="Advance",
                          on_click=lambda: transition_next(COMPONENT_STATE),
                          disabled=not LOCAL_STATE.value.enough_students_ready)
        return


    class_plot_data = solara.use_reactive([])

    student_plot_data = solara.use_reactive(LOCAL_STATE.value.measurements)
    async def _load_student_data():
        if not LOCAL_STATE.value.measurements_loaded:
            logger.info("Loading measurements")
            measurements = LOCAL_API.get_measurements(GLOBAL_STATE, LOCAL_STATE)
            student_plot_data.set(measurements)
    solara.lab.use_task(_load_student_data)

    def glue_setup() -> Tuple[JupyterApplication, Dict[str, CDSScatterView]]:
        gjapp = JupyterApplication(
            GLOBAL_STATE.value.glue_data_collection, GLOBAL_STATE.value.glue_session
        )

        race_viewer = gjapp.new_data_viewer(HubbleScatterView, show=False)
        race_data = Data(**{
            "label": "Hubble Race Data",
            "Distance (km)": [12, 24, 30],
            "Velocity (km/hr)": [4, 8, 10],
        })
        race_data = GLOBAL_STATE.value.add_or_update_data(race_data)
        race_data.style.color = "#111111"
        race_data.style.alpha = 1
        race_data.style.markersize = 14
        race_viewer.add_data(race_data)
        race_viewer.state.x_att = race_data.id["Distance (km)"]
        race_viewer.state.y_att = race_data.id["Velocity (km/hr)"]
        race_viewer.state.x_max = 1.1 * race_viewer.state.x_max
        race_viewer.state.y_max = 1.1 * race_viewer.state.y_max
        race_viewer.state.x_min = 0
        race_viewer.state.y_min = 0
        race_viewer.state.title = "Race Data"

        layer_viewer = gjapp.new_data_viewer(HubbleScatterView, show=False)

        viewers = {
            "race": race_viewer,
            "layer": layer_viewer,
        }

        return gjapp, viewers

    gjapp, viewers = solara.use_memo(glue_setup, dependencies=[])

    def _on_class_data_loaded(class_data_points: List[StudentMeasurement]):
        logger.info("Setting up class glue data")
        if not class_data_points:
            return

        class_data = models_to_glue_data(class_data_points, label="Stage 4 Class Data")
        if not class_data.components:
            class_data = empty_data_from_model_class(StudentMeasurement, label="Stage 4 Class Data")
        class_data = GLOBAL_STATE.value.add_or_update_data(class_data)
        class_data.style.color = "#3A86FF"
        class_data.style.alpha = 1
        class_data.style.markersize = 14

        layer_viewer = viewers["layer"]
        layer_viewer.add_data(class_data)
        layer_viewer.state.x_att = class_data.id['est_dist_value']
        layer_viewer.state.y_att = class_data.id['velocity_value']
        layer_viewer.state.x_axislabel = "Distance (Mpc)"
        layer_viewer.state.y_axislabel = "Velocity (km/s)"
        layer_viewer.state.title = "Our Data"

        class_plot_data.set(class_data_points)

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
                event_fr_callback = lambda event: fr_callback(event, LOCAL_STATE, lambda: LOCAL_API.put_story_state(GLOBAL_STATE, LOCAL_STATE)),
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
                    colors = ("#3A86FF", "#FB5607")
                    sizes = (8, 12)
                    layers_visible = (False, True)
                    with rv.Col(class_="no-padding"):
                        PlotlyLayerToggle(chart_id="line-draw-viewer",
                                          layer_indices=(3, 4),
                                          initial_selected=(1, 1),
                                          colors=colors,
                                          labels=("Class Data", "My Data"))
                    with rv.Col(class_="no-padding"):
                        if student_plot_data.value and class_plot_data.value:
                            # Note the ordering here - we want the student data on top
                            layers = (class_plot_data.value, student_plot_data.value)

                            plot_data=[
                                {
                                    "x": [t.est_dist_value for t in data],
                                    "y": [t.velocity_value for t in data],
                                    "mode": "markers",
                                    "marker": { "color": color, "size": size },
                                    "visible": visibility,    
                                    "hoverinfo": "none"
                                } for data, color, size, visibility in zip(layers, colors, sizes, layers_visible)
                            ]

                            best_fit_slope = Ref(LOCAL_STATE.fields.best_fit_slope)
                            def line_fit_cb(slopes: list[float]):
                                # The student data is second in our tuple above
                                best_fit_slope.set(slopes[1])
                            LineDrawViewer(chart_id="line-draw-viewer",
                                           title="Our Data",
                                           plot_data=plot_data,
                                           on_line_fit=line_fit_cb,
                                           x_axis_label="Distance (Mpc)",
                                           y_axis_label="Velocity (km/s)",
                                           viewer_height=DEFAULT_VIEWER_HEIGHT,
                                           plot_margins=PLOTLY_MARGINS)

            with rv.Col(cols=10, offset=1):
                if COMPONENT_STATE.value.current_step_at_or_after(
                Marker.hub_exp1):
                    dialog = Ref(COMPONENT_STATE.fields.show_hubble_slideshow_dialog)
                    step = Ref(COMPONENT_STATE.fields.hubble_slideshow_state.step)
                    max_step_completed = Ref(COMPONENT_STATE.fields.hubble_slideshow_state.max_step_completed)
                    slideshow_finished = Ref(COMPONENT_STATE.fields.hubble_slideshow_finished)

                    HubbleExpUniverseSlideshow(
                        race_viewer=ViewerLayout(viewer=viewers["race"]),
                        layer_viewer=ViewerLayout(viewers["layer"]),

                        dialog=COMPONENT_STATE.value.show_hubble_slideshow_dialog,
                        step=COMPONENT_STATE.value.hubble_slideshow_state.step,
                        max_step_completed=COMPONENT_STATE.value.hubble_slideshow_state.max_step_completed,
                        state_view={
                            "mc_score": get_multiple_choice(LOCAL_STATE, "race-age"),
                            "score_tag": "race-age"
                        },
                        
                        event_set_dialog=dialog.set,
                        event_set_step=step.set,
                        event_set_max_step_completed=max_step_completed.set,
                        event_mc_callback=lambda event: mc_callback(event, LOCAL_STATE),
                        event_on_slideshow_finished=lambda _: slideshow_finished.set(True),
                    )
