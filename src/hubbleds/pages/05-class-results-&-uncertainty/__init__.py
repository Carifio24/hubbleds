from echo import delay_callback
from glue.core import Data
from glue.core.message import NumericalDataChangedMessage
from glue.core.subset import RangeSubsetState
from glue_jupyter import JupyterApplication
from glue_plotly.viewers import PlotlyBaseView
import numpy as np
import solara
from solara.toestand import Ref

from functools import partial
from pathlib import Path
import reacton.ipyvuetify as rv
from typing import Dict, Tuple

from cosmicds.components import PercentageSelector, ScaffoldAlert, StateEditor, StatisticsSelector, ViewerLayout
from cosmicds.utils import empty_data_from_model_class
from cosmicds.viewers import CDSHistogramView, CDSScatterView
from hubbleds.base_component_state import transition_next, transition_previous
from hubbleds.components import UncertaintySlideshow, IdSlider
from hubbleds.state import LOCAL_STATE, GLOBAL_STATE, StudentMeasurement, get_free_response, get_multiple_choice, mc_callback, fr_callback
from hubbleds.utils import make_summary_data, models_to_glue_data
from .component_state import COMPONENT_STATE, Marker
from hubbleds.remote import LOCAL_API

from cosmicds.logger import setup_logger

logger = setup_logger("STAGE 5")


GUIDELINE_ROOT = Path(__file__).parent / "guidelines"


@solara.component
def Page():
    loaded_component_state = solara.use_reactive(False)

    async def _load_component_state():
        # Load stored component state from database, measurement data is
        # considered higher-level and is loaded when the story starts
        LOCAL_API.get_stage_state(GLOBAL_STATE, LOCAL_STATE, COMPONENT_STATE)

        # TODO: What else to we need to do here?
        logger.info("Finished loading component state for stage 4.")
        loaded_component_state.set(True)

    solara.lab.use_task(_load_component_state)

    # async def _write_component_state():
    #     if not loaded_component_state.value:
    #         return

    #     # Listen for changes in the states and write them to the database
    #     LOCAL_API.put_stage_state(GLOBAL_STATE, LOCAL_STATE, COMPONENT_STATE)

    #     logger.info("Wrote stage 5 component state to database.")

    # solara.lab.use_task(_write_component_state, dependencies=[COMPONENT_STATE.value])
    
    class_data_loaded = solara.use_reactive(False)
    async def _load_class_data():
        class_measurements = LOCAL_API.get_class_measurements(GLOBAL_STATE, LOCAL_STATE)
        measurements = Ref(LOCAL_STATE.fields.class_measurements)
        student_ids = Ref(LOCAL_STATE.fields.stage_5_class_data_students)
        if class_measurements and not student_ids.value:
            ids = list(np.unique([m.student_id for m in class_measurements]))
            student_ids.set(ids)
        measurements.set(class_measurements)
        class_data_loaded.set(True)

    solara.lab.use_task(_load_class_data)


    all_data_loaded = solara.use_reactive(False)
    async def _load_all_data():

        all_measurements, student_summaries, class_summaries = LOCAL_API.get_all_data(LOCAL_STATE)
        measurements = Ref(LOCAL_STATE.fields.all_measurements)
        stu_summaries = Ref(LOCAL_STATE.fields.student_summaries)
        cls_summaries = Ref(LOCAL_STATE.fields.class_summaries)
        measurements.set(all_measurements)
        stu_summaries.set(student_summaries)
        cls_summaries.set(class_summaries)

        all_data_loaded.set(True)

    solara.lab.use_task(_load_all_data)

    async def _load_student_data():
        if not LOCAL_STATE.value.measurements_loaded:
            print("Getting measurements for student")
            LOCAL_API.get_measurements(GLOBAL_STATE, LOCAL_STATE)
    solara.lab.use_task(_load_student_data)


    default_color = "#3A86FF"
    highlight_color = "#FF5A00"

    def glue_setup() -> Tuple[JupyterApplication, Dict[str, PlotlyBaseView]]:
        # NOTE: use_memo has to be part of the main page render. Including it
        #  in a conditional will result in an error.
        gjapp = JupyterApplication(
            GLOBAL_STATE.value.glue_data_collection, GLOBAL_STATE.value.glue_session
        )

        layer_viewer = gjapp.new_data_viewer(CDSScatterView, show=False)
        student_slider_viewer = gjapp.new_data_viewer(CDSScatterView, show=False)
        class_slider_viewer = gjapp.new_data_viewer(CDSScatterView, show=False)
        student_hist_viewer = gjapp.new_data_viewer(CDSHistogramView, show=False)
        class_hist_viewer = gjapp.new_data_viewer(CDSHistogramView, show=False)
        viewers = {
            "layer": layer_viewer,
            "student_slider": student_slider_viewer,
            "class_slider": class_slider_viewer,
            "student_hist": student_hist_viewer,
            "class_hist": class_hist_viewer
        }

        def _update_bins(viewer, *args):
            props = ('hist_n_bin', 'hist_x_min', 'hist_x_max')
            with delay_callback(viewer.state, *props):
                if not viewer.layers:
                    return
                layer = viewer.layers[0] # only works cuz there is only one layer 
                component = viewer.state.x_att                   
                values = layer.layer.data[component]
                try:
                    xmin = round(values.min(), 0) - 0.5
                    xmax = round(values.max(), 0) + 0.5
                except:
                    return
                viewer.state.hist_n_bin = int(xmax - xmin)
                viewer.state.hist_x_min = xmin
                viewer.state.hist_x_max = xmax
        
        for viewer in (student_hist_viewer, class_hist_viewer):
            gjapp.data_collection.hub.subscribe(gjapp.data_collection, NumericalDataChangedMessage,
                                                handler=partial(_update_bins, viewer))

        return gjapp, viewers

    gjapp, viewers = solara.use_memo(glue_setup, dependencies=[])


    links_setup = solara.use_reactive(False)
    def _setup_links(_value: bool):
        if not (class_data_added.value and student_data_added.value):
            return
        student_data = gjapp.data_collection["My Data"]
        class_data = gjapp.data_collection["Class Data"]
        for component in ("est_dist_value", "velocity_value"):
            gjapp.add_link(student_data, component, class_data, component)
        links_setup.set(True)
        print("_setup_links")
        viewers["layer"].add_data(student_data)

    class_data_added = solara.use_reactive(False)
    def _on_class_data_loaded(value: bool):
        if not value:
            return
        
        class_ids = LOCAL_STATE.value.stage_5_class_data_students
        class_data_points = [m for m in LOCAL_STATE.value.class_measurements if m.student_id in class_ids]
        class_data = models_to_glue_data(class_data_points, label="Class Data")
        class_data = GLOBAL_STATE.value.add_or_update_data(class_data)

        layer_viewer = viewers["layer"]
        layer_viewer.state.x_axislabel = "Distance (Mpc)"
        layer_viewer.state.y_axislabel = "Velocity"
        layer_viewer.add_data(class_data)
        layer_viewer.state.x_att = class_data.id['est_dist_value']
        layer_viewer.state.y_att = class_data.id['velocity_value']

        if len(class_data.subsets) == 0:
            student_slider_subset = class_data.new_subset(label="student_slider_subset", alpha=1, markersize=10)
        else:
            student_slider_subset = class_data.subsets[0]
        slider_viewer = viewers["student_slider"]
        slider_viewer.add_data(class_data)
        slider_viewer.state.x_att = class_data.id['est_dist_value']
        slider_viewer.state.y_att = class_data.id['velocity_value']
        slider_viewer.state.title = "Stage 5 Class Data Viewer"
        slider_viewer.add_subset(student_slider_subset)
        slider_viewer.layers[0].state.visible = False

        class_summary_data = make_summary_data(class_data,
                                               input_id_field="student_id",
                                               output_id_field="id",
                                               label="Class Summaries")
        class_summary_data = GLOBAL_STATE.value.add_or_update_data(class_summary_data)
        class_data_added.set(True)

        hist_viewer = viewers["student_hist"]
        hist_viewer.add_data(class_summary_data)
        hist_viewer.state.x_att = class_summary_data.id['age_value']
        hist_viewer.state.title = "My class ages (5 galaxies each)"
        hist_viewer.layers[0].state.color = "red"

    class_data_loaded.subscribe(_on_class_data_loaded)

    measurements_loaded = Ref(LOCAL_STATE.fields.measurements_loaded)
    student_data_added = solara.use_reactive(False)
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


    if measurements_loaded.value:
        _on_student_data_loaded(True)
    else:
        measurements_loaded.subscribe(_on_student_data_loaded)

    all_data_added = solara.use_reactive(False)
    def _on_all_data_loaded(value):
        if not value:
            return

        all_measurements = LOCAL_STATE.value.all_measurements
        student_summaries = LOCAL_STATE.value.student_summaries
        class_summaries = LOCAL_STATE.value.class_summaries

        all_data = models_to_glue_data(all_measurements, label="All Measurements")
        all_data = GLOBAL_STATE.value.add_or_update_data(all_data)

        student_summ_data = models_to_glue_data(student_summaries, label="All Student Summaries")
        student_summ_data = GLOBAL_STATE.value.add_or_update_data(student_summ_data)

        all_class_summ_data = models_to_glue_data(class_summaries, label="All Class Summaries")
        all_class_summ_data = GLOBAL_STATE.value.add_or_update_data(all_class_summ_data)

        if len(all_data.subsets) == 0:
            class_slider_subset = all_data.new_subset(label="class_slider_subset", alpha=1, markersize=10)
        else:
            class_slider_subset = all_data.subsets[0]

        all_data_added.set(True)

        slider_viewer = viewers["class_slider"]
        slider_viewer.add_data(all_data)
        slider_viewer.state.x_att = all_data.id['est_dist_value']
        slider_viewer.state.y_att = all_data.id['velocity_value']
        slider_viewer.state.title = "Stage 5 All Classes Data Viewer"
        slider_viewer.layers[0].state.visible = False
        slider_viewer.add_subset(class_slider_subset)

        hist_viewer = viewers["class_hist"]
        hist_viewer.add_data(all_class_summ_data)
        hist_viewer.state.x_att = all_class_summ_data.id['age_value']
        hist_viewer.state.title = "All class ages (5 galaxies each)"
        hist_viewer.layers[0].state.color = "blue"

    all_data_loaded.subscribe(_on_all_data_loaded)
    student_data_added.subscribe(_setup_links)
    class_data_added.subscribe(_setup_links)

    @solara.lab.computed
    def data_ready():
        return student_data_added.value and class_data_added.value and all_data_added.value

    if not data_ready.value:
        rv.ProgressCircular(
            width=3,
            color="primary",
            indeterminate=True,
            size=100,
        )
        return

    StateEditor(Marker, COMPONENT_STATE, LOCAL_STATE, LOCAL_API)

    #--------------------- Row 1: OUR DATA HUBBLE VIEWER -----------------------
    if (
            COMPONENT_STATE.value.current_step_between(Marker.ran_var1, Marker.fin_cla1) \
                    or \
            COMPONENT_STATE.value.current_step_between(Marker.cla_dat1, Marker.you_age1c)
    ):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineRandomVariability.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    allow_back=False,
                    show=COMPONENT_STATE.value.is_current_step(Marker.ran_var1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineFinishedClassmates.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.fin_cla1),
                    state_view={
                        "class_data_size": 10  # TODO: This is a placeholder
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassData.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_dat1),
                    state_view={
                        "class_data_size": 10  # TODO: This is a placeholder
                    }                    
                )
                ScaffoldAlert(
                    # TODO: This will need to be wired up once viewer is implemented
                    GUIDELINE_ROOT / "GuidelineTrendLinesDraw2c.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.tre_lin2c),
                )
                ScaffoldAlert(
                    # TODO: This will need to be wired up once viewer is implemented
                    GUIDELINE_ROOT / "GuidelineBestFitLinec.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.bes_fit1c),
                )
                ScaffoldAlert(
                    # TODO: This will need to be wired up once viewer is implemented
                    GUIDELINE_ROOT / "GuidelineYourAgeEstimatec.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.you_age1c),
                    state_view={
                        "low_guess": get_free_response(LOCAL_STATE, "likely-low-age").get("response"),
                        "high_guess": get_free_response(LOCAL_STATE, "likely-high-age").get("response"),
                        "best_guess": get_free_response(LOCAL_STATE, "best-guess-age").get("response"),
                    }                    
                )

            with rv.Col():
                ViewerLayout(viewer=viewers["layer"])

    # --------------------- Row 2: SLIDER VERSION: OUR DATA HUBBLE VIEWER -----------------------
    if COMPONENT_STATE.value.current_step_between(Marker.cla_res1, Marker.con_int3):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassmatesResults.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_res1),
                    state_view={
                        "class_data_size": 10  # TODO: This is a placeholder
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineRelationshipAgeSlopeMC.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.rel_age1),
                    event_mc_callback=lambda event: mc_callback(event, LOCAL_STATE),
                    state_view={
                        "mc_score": get_multiple_choice(LOCAL_STATE, "age-slope-trend"),
                        "score_tag": "age-slope-trend"
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_age1),
                    state_view={
                        "student_low_age": COMPONENT_STATE.value.student_low_age,
                        "student_high_age": COMPONENT_STATE.value.student_high_age,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange2.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_age2),
                    state_view={
                        "student_low_age": COMPONENT_STATE.value.student_low_age,
                        "student_high_age": COMPONENT_STATE.value.student_high_age,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange3.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_age3),
                    state_view={
                        "student_low_age": COMPONENT_STATE.value.student_low_age,
                        "student_high_age": COMPONENT_STATE.value.student_high_age,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange4.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _:transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_age4),
                    state_view={
                        "student_low_age": COMPONENT_STATE.value.student_low_age,
                        "student_high_age": COMPONENT_STATE.value.student_high_age,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineLearnUncertainty1.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.lea_unc1),
                    state_view={
                        "uncertainty_slideshow_finished": COMPONENT_STATE.value.uncertainty_slideshow_finished,
                    },
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineMostLikelyValue1.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.mos_lik1),
                )

            def update_student_slider_subset(id, highlighted):
                class_data = gjapp.data_collection["Class Data"]
                student_slider_subset = class_data.subsets[0]
                student_slider_subset.subset_state = RangeSubsetState(id, id, class_data.id['student_id'])
                color = highlight_color if highlighted else default_color
                student_slider_subset.style.color = color

            with rv.Col(class_="no-padding"):
                ViewerLayout(viewer=viewers["student_slider"])
                class_summary_data = gjapp.data_collection["Class Summaries"]
                IdSlider(
                    gjapp=gjapp,
                    data=class_summary_data,
                    on_id=update_student_slider_subset,
                    highlight_ids=[GLOBAL_STATE.value.student.id],
                    id_component=class_summary_data.id['id'],
                    value_component=class_summary_data.id['age_value'],
                    default_color=default_color,
                    highlight_color=highlight_color
                )

        if COMPONENT_STATE.value.current_step_between(Marker.lea_unc1, Marker.you_age1c):
            with solara.ColumnsResponsive(12, large=[5,7]):
                with rv.Col():
                    pass
                with rv.Col():
                    with rv.Col(cols=10, offset=1):
                        UncertaintySlideshow(
                            event_on_slideshow_finished=lambda _: Ref(COMPONENT_STATE.fields.uncertainty_slideshow_finished).set(True),
                            step=COMPONENT_STATE.value.uncertainty_state.step,
                            age_calc_short1=get_free_response(LOCAL_STATE, "shortcoming-1").get("response"),
                            age_calc_short2=get_free_response(LOCAL_STATE, "shortcoming-2").get("response"),
                            age_calc_short_other=get_free_response(LOCAL_STATE, "other-shortcomings").get("response"),    
                            event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                            free_responses=[get_free_response(LOCAL_STATE,'shortcoming-4'), get_free_response(LOCAL_STATE,'systematic-uncertainty')]   
                        )
            
    #--------------------- Row 3: ALL DATA HUBBLE VIEWER - during class sequence -----------------------

    if COMPONENT_STATE.value.current_step_at_or_after(Marker.cla_res1c):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassmatesResultsc.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_res1c),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRangec.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.cla_age1c),
                    state_view={
                        "class_low_age": COMPONENT_STATE.value.class_low_age,
                        "class_high_age": COMPONENT_STATE.value.class_high_age,
                    }
                )

            def update_class_slider_subset(id, highlighted):
                all_data = gjapp.data_collection["All Measurements"]
                class_slider_subset = all_data.subsets[0]
                class_slider_subset.subset_state = RangeSubsetState(id, id, all_data.id['class_id'])
                color = highlight_color if highlighted else default_color
                class_slider_subset.style.color = color

            with rv.Col():
                ViewerLayout(viewer=viewers["class_slider"])
                all_summary_data = gjapp.data_collection["All Class Summaries"]
                IdSlider(
                    gjapp=gjapp,
                    data=all_summary_data,
                    on_id=update_class_slider_subset,
                    highlight_ids=[GLOBAL_STATE.value.classroom.class_info.get("id", 0)],
                    id_component=all_summary_data.id['class_id'],
                    value_component=all_summary_data.id['age_value'],
                    default_color=default_color,
                    highlight_color=highlight_color
                )

                with rv.Col(cols=10, offset=1):
                    UncertaintySlideshow(
                        event_on_slideshow_finished=lambda _: Ref(COMPONENT_STATE.fields.uncertainty_slideshow_finished).set(True),
                        step=COMPONENT_STATE.value.uncertainty_state.step,
                        age_calc_short1=get_free_response(LOCAL_STATE, "shortcoming-1").get("response"),
                        age_calc_short2=get_free_response(LOCAL_STATE, "shortcoming-2").get("response"),
                        age_calc_short_other=get_free_response(LOCAL_STATE, "other-shortcomings").get("response"),  
                        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                        free_responses=[get_free_response(LOCAL_STATE, 'shortcoming-4'), get_free_response(LOCAL_STATE, 'systematic-uncertainty')]
                )

    #--------------------- Row 4: OUR CLASS HISTOGRAM VIEWER -----------------------
    if COMPONENT_STATE.value.current_step_between(Marker.age_dis1, Marker.con_int3):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                with rv.Row():
                    if class_data_added.value:
                        class_summary_data = gjapp.data_collection["Class Summaries"]
                        with rv.Col():
                            if COMPONENT_STATE.value.current_step_between(Marker.mos_lik2, Marker.con_int3):
                                statistics_selected = Ref(COMPONENT_STATE.fields.statistics_selection)
                                StatisticsSelector(
                                    viewers=[viewers["student_hist"]],
                                    glue_data=[class_summary_data],
                                    units=["counts"],
                                    transform=round,
                                    selected=statistics_selected,
                                )

                        with rv.Col():
                            if COMPONENT_STATE.value.current_step_between(Marker.con_int2, Marker.con_int3):
                                percentage_selected = Ref(COMPONENT_STATE.fields.percentage_selection)
                                PercentageSelector(
                                    viewers=[viewers["student_hist"]],
                                    glue_data=[class_summary_data],
                                    selected=percentage_selected
                                )

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeDistribution.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.age_dis1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineMostLikelyValue2.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.mos_lik2),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineMostLikelyValue3.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.mos_lik3),
                )

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineConfidenceInterval.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.con_int1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineConfidenceInterval2.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.con_int2),
                )

            with rv.Col():
                ViewerLayout(viewer=viewers["student_hist"])

    ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineMostLikelyValueReflect4.vue",
        event_next_callback=lambda _: transition_next(COMPONENT_STATE),
        event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
        can_advance=COMPONENT_STATE.value.can_transition(next=True),
        show=COMPONENT_STATE.value.is_current_step(Marker.mos_lik4),
        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
        state_view={
            'free_response_a': get_free_response(LOCAL_STATE,'best-guess-age'),
            'best_guess_answered': LOCAL_STATE.value.question_completed("best-guess-age"),
            'free_response_b': get_free_response(LOCAL_STATE,'my-reasoning')
        }
    )

    ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineConfidenceIntervalReflect3.vue",
        event_next_callback=lambda _: transition_next(COMPONENT_STATE),
        event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
        can_advance=COMPONENT_STATE.value.can_transition(next=True),
        show=COMPONENT_STATE.value.is_current_step(Marker.con_int3),
        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
        state_view={
            'free_response_a': get_free_response(LOCAL_STATE,'likely-low-age'),
            'free_response_b': get_free_response(LOCAL_STATE,'likely-high-age'),
            'high_low_answered': LOCAL_STATE.value.question_completed("likely-low-age") and LOCAL_STATE.value.question_completed("likely-high-age"),
            'free_response_c': get_free_response(LOCAL_STATE,'my-reasoning-2'),
        }
    )

    #--------------------- Row 5: ALL DATA HISTOGRAM VIEWER -----------------------

    if COMPONENT_STATE.value.current_step_between(Marker.age_dis1c):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                with rv.Row():
                    all_class_summary_data = gjapp.data_collection["All Class Summaries"]
                    with rv.Col():
                        statistics_class_selected = Ref(COMPONENT_STATE.fields.statistics_selection_class)
                        StatisticsSelector(
                            viewers=[viewers["class_hist"]],
                            glue_data=[all_class_summary_data],
                            units=["counts"],
                            transform=round,
                            selected=statistics_class_selected
                        )

                    with rv.Col():
                        percentage_class_selected = Ref(COMPONENT_STATE.fields.percentage_selection_class)
                        PercentageSelector(
                            viewers=[viewers["class_hist"]],
                            glue_data=[all_class_summary_data],
                            selected=percentage_class_selected
                        )

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeDistributionc.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.age_dis1c),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistograms1.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.two_his1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsMC2.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.two_his2),
                    event_mc_callback=lambda event: mc_callback(event, LOCAL_STATE),
                    state_view = {
                        "mc_score": get_multiple_choice(LOCAL_STATE, "histogram-range"),
                        "score_tag": "histogram-range"
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsMC3.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.two_his3),
                    event_mc_callback=lambda event: mc_callback(event, LOCAL_STATE),
                    state_view = {
                        "mc_score": get_multiple_choice(LOCAL_STATE, "histogram-percent-range"),
                        "score_tag": "histogram-percent-range"
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsMC4.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.two_his4),
                    event_mc_callback=lambda event: mc_callback(event, LOCAL_STATE),
                    state_view = {
                        "mc_score": get_multiple_choice(LOCAL_STATE, "histogram-distribution"),
                        "score_tag": "histogram-distribution"
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsReflect5.vue",
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.two_his5),
                    event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                    state_view={
                        'free_response': get_free_response(LOCAL_STATE,'unc-range-change-reasoning'),
                    }
                )
                ScaffoldAlert(
                    # TODO: event_next_callback should go to next stage but I don't know how to set that up.
                    GUIDELINE_ROOT / "GuidelineMoreDataDistribution.vue",
                    event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                    can_advance=COMPONENT_STATE.value.can_transition(next=True),
                    show=COMPONENT_STATE.value.is_current_step(Marker.mor_dat1),
                )

            with rv.Col():
                if COMPONENT_STATE.value.current_step_between(Marker.two_his1):
                    ViewerLayout(viewers["student_hist"])

                ViewerLayout(viewers["class_hist"]) 

        ScaffoldAlert(
            GUIDELINE_ROOT / "GuidelineConfidenceIntervalReflect2c.vue",
            event_next_callback=lambda _: transition_next(COMPONENT_STATE),
            event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
            can_advance=COMPONENT_STATE.value.can_transition(next=True),
            show=COMPONENT_STATE.value.is_current_step(Marker.con_int2c),
            event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
            state_view={
                "low_guess": get_free_response(LOCAL_STATE, "likely-low-age").get("response"),
                "high_guess": get_free_response(LOCAL_STATE, "likely-high-age").get("response"),
                "best_guess": get_free_response(LOCAL_STATE, "best-guess-age").get("response"),
                'free_response_a': get_free_response(LOCAL_STATE, 'new-most-likely-age'),
                'free_response_b': get_free_response(LOCAL_STATE, 'new-likely-low-age'),
                'free_response_c': get_free_response(LOCAL_STATE, 'new-likely-high-age'),
                'free_response_d': get_free_response(LOCAL_STATE, 'my-updated-reasoning'),
            }
        )
