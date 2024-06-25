from pymdownx.highlight import highlight
import solara
from cosmicds import load_custom_vue_components
from cosmicds.components import ScaffoldAlert, ViewerLayout, StateEditor, StatisticsSelector, PercentageSelector
from cosmicds.viewers import CDSHistogramView, CDSScatterView
from glue.core import Data
from glue.core.message import NumericalDataChangedMessage
from glue.core.subset import RangeSubsetState
from glue_jupyter import JupyterApplication
from pathlib import Path
from reacton import component, ipyvuetify as rv, value_component
from echo import delay_callback
import numpy as np
from functools import partial

from hubbleds.components.id_slider import IdSlider
from hubbleds.marker_base import MarkerBase
from hubbleds.remote import DatabaseAPI
from hubbleds.utils import make_summary_data, models_to_glue_data
from ...components import UncertaintySlideshow

from ...state import GLOBAL_STATE, LOCAL_STATE, mc_callback, mc_serialize_score, get_free_response, fr_callback
from .component_state import ComponentState, Marker
from ...data_models.student import class_data, student_data

from cosmicds.components import MathJaxSupport, PlotlySupport



GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

component_state = ComponentState()


@solara.component
def Page():

    default_color = "#3A86FF"
    highlight_color = "#FF5A00"

    def data_setup():
        class_measurements = DatabaseAPI.get_class_measurements()
        if not LOCAL_STATE.stage_5_class_data_students.value:
            student_ids = list(np.unique([m.student_id for m in class_measurements]))
            LOCAL_STATE.stage_5_class_data_students.value = student_ids
        class_data.update_measurements(class_measurements)

        student_glue_data = models_to_glue_data(student_data.measurements, label="My Data", ignore_components=["galaxy"])
        student_glue_data = GLOBAL_STATE.add_or_update_data(student_glue_data)

        gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)

        class_data_points = class_data.get_by_student_ids(LOCAL_STATE.stage_5_class_data_students.value)
        class_glue_data = models_to_glue_data(class_data_points, label="Class Data")
        class_glue_data = GLOBAL_STATE.add_or_update_data(class_glue_data)

        for component in ("est_dist", "velocity"):
            gjapp.add_link(student_glue_data, component, class_glue_data, component)

        layer_viewer = gjapp.new_data_viewer(CDSScatterView, data=class_glue_data, show=False)
        layer_viewer.state.x_att = class_glue_data.id['est_dist']
        layer_viewer.state.y_att = class_glue_data.id['velocity']
        layer_viewer.add_data(student_glue_data)
        layer_viewer.state.x_axislabel = "Distance (Mpc)"
        layer_viewer.state.y_axislabel = "Velocity"

        class_summ_data = make_summary_data(class_glue_data, input_id_field="student_id", output_id_field="id", label="Class Summaries")
        class_summ_data = GLOBAL_STATE.add_or_update_data(class_summ_data)

        if "All Measurements" in GLOBAL_STATE.data_collection:
            all_measurements, student_summaries, class_summaries = DatabaseAPI.get_all_data()
            all_data = models_to_glue_data(all_measurements, label="All Measurements")
            all_data = GLOBAL_STATE.add_or_update_data(all_data)
        
            student_summ_data = models_to_glue_data(student_summaries, label="All Student Summaries")
            student_summ_data = GLOBAL_STATE.add_or_update_data(student_summ_data)

            all_class_summ_data = models_to_glue_data(class_summaries, label="All Class Summaries")
            all_class_summ_data = GLOBAL_STATE.add_or_update_data(all_class_summ_data)
        else:
            all_data = GLOBAL_STATE.data_collection["All Measurements"]
            student_summ_data = GLOBAL_STATE.data_collection["All Student Summaries"]
            all_class_summ_data = GLOBAL_STATE.data_collection["All Class Summaries"]

        if len(class_glue_data.subsets) == 0:
            student_slider_subset = class_glue_data.new_subset(label="student_slider_subset", alpha=1, markersize=10)
        else:
            student_slider_subset = class_glue_data.subsets[0]
        slider_viewer = gjapp.new_data_viewer(CDSScatterView, data=class_glue_data, show=False)
        slider_viewer.state.x_att = class_glue_data.id['est_dist']
        slider_viewer.state.y_att = class_glue_data.id['velocity']
        slider_viewer.state.title = "Stage 5 Class Data Viewer"
        layer = slider_viewer.layers[0]
        layer.state.size = 25
        layer.state.visible = False
        slider_viewer.add_subset(student_slider_subset)
        
        if len(all_data.subsets) == 0:
            class_slider_subset = all_data.new_subset(label="class_slider_subset", alpha=1, markersize=10)
        else:
            class_slider_subset = all_data.subsets[0]
        class_slider_viewer = gjapp.new_data_viewer(CDSScatterView, data=all_data, show=False)
        class_slider_viewer.state.x_att = all_data.id['est_dist']
        class_slider_viewer.state.y_att = all_data.id['velocity']
        class_slider_viewer.state.title = "Stage 5 All Classes Data Viewer"
        class_layer = class_slider_viewer.layers[0]
        class_layer.state.size = 25
        class_layer.state.visible = False
        class_slider_viewer.add_subset(class_slider_subset)

        hist_viewer = gjapp.new_data_viewer(CDSHistogramView, data=class_summ_data, show=False)
        hist_viewer.state.x_att = class_summ_data.id['age_value']
        hist_viewer.state.title = "My class ages (5 galaxies each)"
        hist_viewer.layers[0].state.color = "red"

        class_hist_viewer = gjapp.new_data_viewer(CDSHistogramView, data=all_class_summ_data, show=False)
        class_hist_viewer.state.x_att = all_class_summ_data.id['age_value']
        class_hist_viewer.state.title = "All class ages (5 galaxies each)"
        class_hist_viewer.layers[0].state.color = "blue"

        def _update_bins(viewer, *args):
            props = ('hist_n_bin', 'hist_x_min', 'hist_x_max')
            with delay_callback(viewer.state, *props):
                layer = viewer.layers[0] # only works cuz there is only one layer 
                component = viewer.state.x_att                   
                xmin = round(layer.layer.data[component].min(), 0) - 0.5
                xmax = round(layer.layer.data[component].max(), 0) + 0.5
                viewer.state.hist_n_bin = int(xmax - xmin)
                viewer.state.hist_x_min = xmin
                viewer.state.hist_x_max = xmax
        
        for viewer in (hist_viewer, class_hist_viewer):
            _update_bins(viewer)
            gjapp.data_collection.hub.subscribe(gjapp.data_collection, NumericalDataChangedMessage,
                                                handler=partial(_update_bins, viewer))

        return gjapp, slider_viewer, hist_viewer, class_hist_viewer, class_slider_viewer, layer_viewer

    gjapp, slider_viewer, hist_viewer, class_hist_viewer, class_slider_viewer, layer_viewer = solara.use_memo(data_setup, [])
    
    # Mount external javascript libraries
    def _load_math_jax():
        MathJaxSupport()
        PlotlySupport()

    solara.use_memo(_load_math_jax, dependencies=[])

    mc_scoring, set_mc_scoring = solara.use_state(LOCAL_STATE.mc_scoring.value)

    test = solara.use_reactive(False)

    # Custom vue-only components have to be registered in the Page element
    #  currently, otherwise they will not be available in the front-end
    load_custom_vue_components()

    # Solara's reactivity is often tied to the _context_ of the Page it's
    #  being rendered in. Currently, in order to trigger subscribed callbacks,
    #  state connections need to be initialized _inside_ a Page.
    # component_state.setup()

    StateEditor(Marker, component_state)

    # solara.Text(
    #     f"Current step: {component_state.current_step.value}, "
    #     f"Next step: {Marker(component_state.current_step.value.value + 1)}"
    #     f"Can advance: {component_state.can_transition(next=True)}"
    # )

    def transition_next(*args):
        component_state.transition_next()

    def transition_previous(*args):
        component_state.transition_previous()

    #--------------------- Row 1: OUR DATA HUBBLE VIEWER -----------------------
    if (component_state.current_step_between(Marker.ran_var1, Marker.fin_cla1) or component_state.current_step_between(Marker.cla_dat1, Marker.you_age1c)):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineRandomVariability.vue",
                    event_next_callback=transition_next,
                    can_advance=component_state.can_transition(next=True),
                    allow_back=False,
                    show=component_state.is_current_step(Marker.ran_var1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineFinishedClassmates.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.fin_cla1),
                    state_view={
                        "class_data_size": 10  # TODO: This is a placeholder
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassData.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_dat1),
                    state_view={
                        "class_data_size": 10  # TODO: This is a placeholder
                    }                    
                )
                ScaffoldAlert(
                    # TODO: This will need to be wired up once viewer is implemented
                    GUIDELINE_ROOT / "GuidelineTrendLinesDraw2c.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.tre_lin2c),
                )
                ScaffoldAlert(
                    # TODO: This will need to be wired up once viewer is implemented
                    GUIDELINE_ROOT / "GuidelineBestFitLinec.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.bes_fit1c),
                )
                ScaffoldAlert(
                    # TODO: This will need to be wired up once viewer is implemented
                    GUIDELINE_ROOT / "GuidelineYourAgeEstimatec.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.you_age1c),
                    state_view={
                        "low_guess": get_free_response(LOCAL_STATE.free_responses, "likely-low-age").get("response"),
                        "high_guess": get_free_response(LOCAL_STATE.free_responses, "likely-high-age").get("response"),
                        "best_guess": get_free_response(LOCAL_STATE.free_responses, "best-guess-age").get("response"),
                    }                    
                )

            with rv.Col():
                ViewerLayout(viewer=layer_viewer)


# --------------------- Row 2: SLIDER VERSION: OUR DATA HUBBLE VIEWER -----------------------
    if component_state.current_step_between(Marker.cla_res1, Marker.con_int3):

        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassmatesResults.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_res1),
                    state_view={
                        "class_data_size": 10  # TODO: This is a placeholder
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineRelationshipAgeSlopeMC.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.rel_age1),
                    event_mc_callback=lambda event: mc_callback(event=event, local_state=LOCAL_STATE, callback=set_mc_scoring),
                    state_view = {"mc_score": mc_serialize_score(mc_scoring.get("age-slope-trend")), "score_tag": "age-slope-trend"}
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_age1),
                    state_view={
                        "student_low_age": component_state.student_low_age.value,
                        "student_high_age": component_state.student_high_age.value,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange2.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_age2),
                    state_view={
                        "student_low_age": component_state.student_low_age.value,
                        "student_high_age": component_state.student_high_age.value,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange3.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_age3),
                    state_view={
                        "student_low_age": component_state.student_low_age.value,
                        "student_high_age": component_state.student_high_age.value,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRange4.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_age4),
                    state_view={
                        "student_low_age": component_state.student_low_age.value,
                        "student_high_age": component_state.student_high_age.value,
                    }
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineLearnUncertainty1.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.lea_unc1),
                    state_view={
                        "uncertainty_slideshow_finished": component_state.uncertainty_slideshow_finished.value
                    },
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineMostLikelyValue1.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.mos_lik1),
                )


            def toggle_viewer():
                test.value = not test.value

            def update_student_slider_subset(id, highlighted):
                class_glue_data = gjapp.data_collection["Class Data"]
                student_slider_subset = class_glue_data.subsets[0]
                student_slider_subset.subset_state = RangeSubsetState(id, id, class_glue_data.id['student_id'])
                color = highlight_color if highlighted else default_color
                student_slider_subset.style.color = color

            with rv.Col():
                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("Our class comparison viewer with slider goes here")
                    if test.value:
                        ViewerLayout(viewer=slider_viewer)
                        class_summ_data = gjapp.data_collection["Class Summaries"]
                        IdSlider(gjapp=gjapp,
                                 data=class_summ_data,
                                 on_id=update_student_slider_subset,
                                 highlight_ids=[1],
                                 id_component=class_summ_data.id['id'],
                                 value_component=class_summ_data.id['age_value'],
                                 default_color=default_color,
                                 highlight_color=highlight_color,
                        )
                    solara.Button("test slider viewer", on_click=toggle_viewer)

    if component_state.current_step_between(Marker.lea_unc1, Marker.you_age1c):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                pass
            with rv.Col():
                with rv.Col(cols=10, offset=1):
                    UncertaintySlideshow(
                        event_on_slideshow_finished=lambda *args: component_state.uncertainty_slideshow_finished.set(
                            True
                        ),
                        step=component_state.uncertainty_state.step.value,
                        age_calc_short1=get_free_response(LOCAL_STATE.free_responses, "shortcoming-1").get("response"),
                        age_calc_short2=get_free_response(LOCAL_STATE.free_responses, "shortcoming-2").get("response"),
                        age_calc_short_other=get_free_response(LOCAL_STATE.free_responses, "other-shortcomings").get("response"),    
                        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                        free_responses=[get_free_response(LOCAL_STATE.free_responses,'shortcoming-4'), get_free_response(LOCAL_STATE.free_responses,'systematic-uncertainty')]   
                    )

    #--------------------- Row 3: ALL DATA HUBBLE VIEWER - during class sequence -----------------------

    if component_state.current_step_between(Marker.cla_res1c):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassmatesResultsc.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_res1c),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeRangec.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.cla_age1c),
                    state_view={
                        "class_low_age": component_state.class_low_age.value,
                        "class_high_age": component_state.class_high_age.value,
                    }
                )

            def update_class_slider_subset(id, highlighted):
                all_data = gjapp.data_collection["All Measurements"]
                class_slider_subset = all_data.subsets[0]
                class_slider_subset.subset_state = RangeSubsetState(id, id, all_data.id['class_id'])
                color = highlight_color if highlighted else default_color
                class_slider_subset.style.color = color

            with rv.Col():
                with solara.Card():
                    ViewerLayout(viewer=class_slider_viewer)
                    all_summ_data = gjapp.data_collection["All Class Summaries"]

                    IdSlider(gjapp=gjapp,
                             data=all_summ_data,
                             on_id=update_class_slider_subset,
                             highlight_ids=[1],
                             id_component=all_summ_data.id['id'],
                             value_component=all_summ_data.id['age_value'],
                             default_color=default_color,
                             highlight_color=highlight_color,
                    )


                with rv.Col(cols=10, offset=1):
                    UncertaintySlideshow(
                        event_on_slideshow_finished=lambda *args: component_state.uncertainty_slideshow_finished.set(
                            True
                        ),
                        step=component_state.uncertainty_state.step.value,
                        age_calc_short1=get_free_response(LOCAL_STATE.free_responses, "shortcoming-1").get("response"),
                        age_calc_short2=get_free_response(LOCAL_STATE.free_responses, "shortcoming-2").get("response"),
                        age_calc_short_other=get_free_response(LOCAL_STATE.free_responses, "other-shortcomings").get("response"),  
                        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                        free_responses=[get_free_response(LOCAL_STATE.free_responses,'shortcoming-4'), get_free_response(LOCAL_STATE.free_responses,'systematic-uncertainty')]               
                    )

    #--------------------- Row 4: OUR CLASS HISTOGRAM VIEWER -----------------------

    if component_state.current_step_between(Marker.age_dis1, Marker.con_int3):                
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                class_summ_data = GLOBAL_STATE.data_collection["Class Summaries"]
                if component_state.current_step_between(Marker.mos_lik2, Marker.con_int3):
                    StatisticsSelector(viewers=[hist_viewer],
                                       glue_data=[class_summ_data],
                                       units=["counts"],
                                       transform=round,
                                       selected=component_state.statistics_selection)
                if component_state.current_step_between(Marker.con_int2, Marker.con_int3):
                    PercentageSelector(viewers=[hist_viewer],
                                       glue_data=[class_summ_data],
                                       selected=component_state.percentage_selection)

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeDistribution.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.age_dis1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineMostLikelyValue2.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.mos_lik2),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineMostLikelyValue3.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.mos_lik3),
                )

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineConfidenceInterval.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.con_int1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineConfidenceInterval2.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.con_int2),
                )

            with rv.Col():
                ViewerLayout(hist_viewer)

    ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineMostLikelyValueReflect4.vue",
        event_next_callback=transition_next,
        event_back_callback=transition_previous,
        can_advance=component_state.can_transition(next=True),
        show=component_state.is_current_step(Marker.mos_lik4),
        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
        state_view={
            "hint1_dialog": component_state.age_calc_state.hint1_dialog.value,
            'free_response_a': get_free_response(LOCAL_STATE.free_responses,'best-guess-age'),
            'free_response_b': get_free_response(LOCAL_STATE.free_responses,'my-reasoning')
        }
    )

    ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineConfidenceIntervalReflect3.vue",
        event_next_callback=transition_next,
        event_back_callback=transition_previous,
        can_advance=component_state.can_transition(next=True),
        show=component_state.is_current_step(Marker.con_int3),
        event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
        state_view={
            "hint2_dialog": component_state.age_calc_state.hint2_dialog.value,
            'free_response_a': get_free_response(LOCAL_STATE.free_responses,'likely-low-age'),
            'free_response_b': get_free_response(LOCAL_STATE.free_responses,'likely-high-age'),
            'free_response_c': get_free_response(LOCAL_STATE.free_responses,'my-reasoning-2'),
        }
    )

    #--------------------- Row 5: ALL DATA HISTOGRAM VIEWER -----------------------

    if component_state.current_step_between(Marker.age_dis1c):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                all_class_summ_data = GLOBAL_STATE.data_collection["All Class Summaries"]
                StatisticsSelector(viewers=[class_hist_viewer],
                                   glue_data=[all_class_summ_data],
                                   units=["counts"],
                                   transform=round,
                                   selected=component_state.statistics_selection_class)

                PercentageSelector(viewers=[class_hist_viewer],
                                   glue_data=[all_class_summ_data],
                                   selected=component_state.percentage_selection_class)

                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineClassAgeDistributionc.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.age_dis1c),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistograms1.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.two_his1),
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsMC2.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.two_his2),
                    event_mc_callback=lambda event: mc_callback(event=event, local_state=LOCAL_STATE, callback=set_mc_scoring),
                    state_view = {"mc_score": mc_serialize_score(mc_scoring.get("histogram-range")), "score_tag": "histogram-range"}
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsMC3.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.two_his3),
                    event_mc_callback=lambda event: mc_callback(event=event, local_state=LOCAL_STATE, callback=set_mc_scoring),
                    state_view = {"mc_score": mc_serialize_score(mc_scoring.get("histogram-percent-range")), "score_tag": "histogram-percent-range"}
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsMC4.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.two_his4),
                    event_mc_callback=lambda event: mc_callback(event=event, local_state=LOCAL_STATE, callback=set_mc_scoring),
                    state_view = {"mc_score": mc_serialize_score(mc_scoring.get("histogram-distribution")), "score_tag": "histogram-distribution"}
                )
                ScaffoldAlert(
                    GUIDELINE_ROOT / "GuidelineTwoHistogramsReflect5.vue",
                    event_next_callback=transition_next,
                    event_back_callback=transition_previous,
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.two_his5),
                    event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                    state_view={
                        'free_response': get_free_response(LOCAL_STATE.free_responses,'unc-range-change-reasoning'),
                    }
                )
                ScaffoldAlert(
                    # TODO: event_next_callback should go to next stage but I don't know how to set that up.
                    GUIDELINE_ROOT / "GuidelineMoreDataDistribution.vue",
                    event_back_callback=lambda *args: component_state.transition_previous(),
                    can_advance=component_state.can_transition(next=True),
                    show=component_state.is_current_step(Marker.mor_dat1),
                )

            with rv.Col():
                if component_state.current_step_between(Marker.two_his1):
                    ViewerLayout(hist_viewer)

                ViewerLayout(class_hist_viewer) 
               
        ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineConfidenceIntervalReflect2c.vue",
            event_next_callback=transition_next,
            event_back_callback=transition_previous,
            can_advance=component_state.can_transition(next=True),
            show=component_state.is_current_step(Marker.con_int2c),
            event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
            state_view={
                "hint1_dialog": component_state.age_calc_state.hint1_dialog.value,
                "hint2_dialog": component_state.age_calc_state.hint2_dialog.value,
                "low_guess": get_free_response(LOCAL_STATE.free_responses, "likely-low-age").get("response"),
                "high_guess": get_free_response(LOCAL_STATE.free_responses, "likely-high-age").get("response"),
                "best_guess": get_free_response(LOCAL_STATE.free_responses, "best-guess-age").get("response"),
                'free_response_a': get_free_response(LOCAL_STATE.free_responses,'new-most-likely-age'),
                'free_response_b': get_free_response(LOCAL_STATE.free_responses,'new-likely-low-age'),
                'free_response_c': get_free_response(LOCAL_STATE.free_responses,'new-likely-high-age'),
                'free_response_d': get_free_response(LOCAL_STATE.free_responses,'my-updated-reasoning'),
            }
        )       
