import solara
from cosmicds import load_custom_vue_components
from cosmicds.components import ScaffoldAlert, ViewerLayout, StateEditor, StatisticsSelector, PercentageSelector
from cosmicds.viewers import CDSHistogramView, CDSScatterView
from glue.core import Data
from glue.core.subset import RangeSubsetState
from glue_jupyter import JupyterApplication
from pathlib import Path
from reacton import component, ipyvuetify as rv

from hubbleds.components.id_slider import IdSlider
from hubbleds.marker_base import MarkerBase
from ...components import UncertaintySlideshow

from ...state import GLOBAL_STATE, LOCAL_STATE, mc_callback, mc_serialize_score
from .component_state import ComponentState, Marker


GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

component_state = ComponentState()


@solara.component
def Page():

    default_color = "#3A86FF"
    highlight_color = "#FF5A00"

    def glue_setup():
        gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)
        test_data = Data(x=[1,2,3,4,5], y=[1,4,9,16,25], label="Stage 5 Test Data")
        test_data.style.color = "green"
        test_data.style.alpha = 0.5
    
        if len(test_data.subsets) == 0:
            test_subset = test_data.new_subset(label="test_subset", alpha=1, markersize=10)
        else:
            test_subset = test_data.subsets[0]
        if test_data not in gjapp.data_collection:
            gjapp.data_collection.append(test_data)
        viewer = gjapp.new_data_viewer(CDSScatterView, data=test_data, show=False)
        viewer.state.x_att = test_data.id['x']
        viewer.state.y_att = test_data.id['y']
        layer = viewer.layers[0]
        layer.state.size = 25
        layer.state.visible = False
        viewer.add_subset(test_subset)

        hist_viewer = gjapp.new_data_viewer(CDSHistogramView, data=test_data, show=False)
        return gjapp, viewer, test_data, test_subset, hist_viewer


    gjapp, viewer, test_data, test_subset, hist_viewer = solara.use_memo(glue_setup, [])

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

    ViewerLayout(hist_viewer)
    StatisticsSelector([hist_viewer], glue_data=[test_data], units=["counts"], transform=round)
    PercentageSelector([hist_viewer], glue_data=[test_data])

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
                        "low_guess": component_state.age_calc_state.low_guess.value,
                        "high_guess": component_state.age_calc_state.high_guess.value,
                        "best_guess": component_state.age_calc_state.best_guess.value,
                    }                    
                )

            with rv.Col():
                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("Our class layer viewer goes here")


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

            def update_test_subset(id, highlighted):
                test_subset.subset_state = RangeSubsetState(id, id, test_data.id['x'])
                color = highlight_color if highlighted else default_color
                test_subset.style.color = color

            with rv.Col():
                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("Our class comparison viewer with slider goes here")
                    if test.value:
                        ViewerLayout(viewer=gjapp.viewers[0])
                        test_data = gjapp.data_collection["Stage 5 Test Data"]
                        IdSlider(gjapp=gjapp,
                                data=test_data,
                                on_id=update_test_subset,
                                highlight_ids=[1],
                                id_component=test_data.id['x'],
                                value_component=test_data.id['y'],
                                default_color=default_color,
                                highlight_color=highlight_color,
                        )
                    solara.Button("test slider viewer", on_click=toggle_viewer)

                if component_state.current_step_between(Marker.lea_unc1, Marker.you_age1c):
                    UncertaintySlideshow(
                        event_on_slideshow_finished=lambda *args: component_state.uncertainty_slideshow_finished.set(
                            True
                        ),
                        step=component_state.uncertainty_state.step.value,
                        age_calc_short1=component_state.age_calc_state.short_one.value,
                        age_calc_short2=component_state.age_calc_state.short_two.value,
                        age_calc_short_other=component_state.age_calc_state.short_other.value,                    
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
            with rv.Col():
                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("All viewer with slider goes here")

                UncertaintySlideshow(
                    event_on_slideshow_finished=lambda *args: component_state.uncertainty_slideshow_finished.set(
                        True
                    ),
                    step=component_state.uncertainty_state.step.value,
                    age_calc_short1=component_state.age_calc_state.short_one.value,
                    age_calc_short2=component_state.age_calc_state.short_two.value,
                    age_calc_short_other=component_state.age_calc_state.short_other.value,                    
                )

    

    #--------------------- Row 4: OUR CLASS HISTOGRAM VIEWER -----------------------

    if component_state.current_step_between(Marker.age_dis1, Marker.con_int3):                
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                if component_state.current_step_between(Marker.mos_lik2, Marker.con_int3):
                    with solara.Card(style="background-color: #F06292;"):
                        solara.Markdown("my class statistics selector component goes here")
                if component_state.current_step_between(Marker.con_int2, Marker.con_int3):
                    with solara.Card(style="background-color: #F06292;"):
                        solara.Markdown("my class percentage selector component goes here")

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
                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("Our class data histogram goes here")

    ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineMostLikelyValueReflect4.vue",
        event_next_callback=transition_next,
        event_back_callback=transition_previous,
        can_advance=component_state.can_transition(next=True),
        show=component_state.is_current_step(Marker.mos_lik4),
        state_view={
            "hint1_dialog": component_state.age_calc_state.hint1_dialog.value
        }
    )

    ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineConfidenceIntervalReflect3.vue",
        event_next_callback=transition_next,
        event_back_callback=transition_previous,
        can_advance=component_state.can_transition(next=True),
        show=component_state.is_current_step(Marker.con_int3),
        state_view={
            "hint2_dialog": component_state.age_calc_state.hint2_dialog.value
        }
    )

    #--------------------- Row 5: ALL DATA HISTOGRAM VIEWER -----------------------

    if component_state.current_step_between(Marker.age_dis1c):
        with solara.ColumnsResponsive(12, large=[5,7]):
            with rv.Col():
                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("all statistics selector component goes here")

                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("allpercentage selector component goes here")

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
                    with solara.Card(style="background-color: #F06292;"):
                        solara.Markdown("all data student histogram goes here")

                with solara.Card(style="background-color: #F06292;"):
                    solara.Markdown("all data class histogram goes here")
               
        ScaffoldAlert(
        GUIDELINE_ROOT / "GuidelineConfidenceIntervalReflect2c.vue",
            event_next_callback=transition_next,
            event_back_callback=transition_previous,
            can_advance=component_state.can_transition(next=True),
            show=component_state.is_current_step(Marker.con_int2c),
            state_view={
                "hint1_dialog": component_state.age_calc_state.hint1_dialog.value,
                "hint2_dialog": component_state.age_calc_state.hint2_dialog.value,
                "low_guess": component_state.age_calc_state.low_guess.value,
                "high_guess": component_state.age_calc_state.high_guess.value,
                "best_guess": component_state.age_calc_state.best_guess.value,
            }
        )       
