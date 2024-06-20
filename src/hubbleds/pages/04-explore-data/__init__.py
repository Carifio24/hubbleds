import dataclasses

import numpy as np
from hubbleds.remote import DatabaseAPI
import pandas as pd
import solara
from cosmicds.widgets.table import Table
from cosmicds.components import ScaffoldAlert, StateEditor, MathJaxSupport, PlotlySupport
from cosmicds import load_custom_vue_components
from glue_jupyter.app import JupyterApplication
from reacton import ipyvuetify as rv
from solara import Reactive
from pathlib import Path
from astropy.table import Table

from hubbleds.components.line_draw_viewer.line_draw_viewer import LineDrawViewer

from ...components import DataTable, HubbleExpUniverseSlideshow
from ...data_management import *
from ...state import GLOBAL_STATE, LOCAL_STATE, mc_callback, mc_serialize_score, get_free_response, fr_callback
from ...utils import AGE_CONSTANT
from ...widgets.selection_tool import SelectionTool
from ...data_models.student import student_data, StudentMeasurement, example_data, class_data
from .component_state import ComponentState, Marker


GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)

component_state = ComponentState()


# def _on_galaxy_selected(galaxy):
#     is_in = np.isin(
#         [x.name for x in student_data.measurements], galaxy["name"]
#     )  # Avoid duplicates
#     already_present = is_in.size > 0 and is_in[0]

#     if not already_present:
#         student_data.measurements.append(StudentMeasurement(**galaxy))
#         component_state.total_galaxies.value += 1


def _on_example_galaxy_table_row_selected(row):
    galaxy = row["item"]
    component_state.selected_example_galaxy.set(galaxy)
    component_state.lambda_rest.set(galaxy['rest_wave'])
    component_state.lambda_obs.subscribe(
        lambda *args: example_data.update(galaxy['id'], {'obs_wave': args[0]}))


def _on_galaxy_table_row_selected(row):
    galaxy = row["item"]
    component_state.selected_galaxy.set(galaxy)
    component_state.lambda_rest.set(galaxy['rest_wave'])
    component_state.lambda_obs.subscribe(
        lambda *args: student_data.update(galaxy['id'], {'obs_wave': args[0]}))


@solara.component
def Page():

    # Mount external javascript libraries
    def _load_math_jax():
        MathJaxSupport()
        PlotlySupport()

    solara.use_memo(_load_math_jax, dependencies=[])

    def _load_class_data():
        if LOCAL_STATE.stage_4_class_data_students.value:
            return
        class_measurements = DatabaseAPI.get_class_measurements()
        class_data.update_measurements(class_measurements)
        student_ids = list(np.unique([m["student_id"] for m in class_measurements]))
        LOCAL_STATE.stage_4_class_data_students.value = student_ids

    solara.use_memo(_load_class_data, dependencies=[])

    # Custom vue-only components have to be registered in the Page element
    #  currently, otherwise they will not be available in the front-end
    load_custom_vue_components()

    # Solara's reactivity is often tied to the _context_ of the Page it's
    #  being rendered in. Currently, in order to trigger subscribed callbacks,
    #  state connections need to be initialized _inside_ a Page.
    component_state.setup()

    mc_scoring, set_mc_scoring  = solara.use_state(LOCAL_STATE.mc_scoring.value)

    StateEditor(Marker, component_state)
    
    x = [0.1 * i for i in range(1, 11)]
    plot_data = [{ "x": x, "y": [1 / (1 + ((1-t)/t)**2) for t in x], "mode": "markers", "marker": { "color": "red", "size": 12 }, "hoverinfo": "none" }]
    LineDrawViewer(plot_data)

    # if LOCAL_STATE.debug_mode:

        # def _on_select_galaxies_clicked():
        #     gal_tab = Table(component_state.galaxy_data)
        #     gal_tab["id"] = [str(x) for x in gal_tab["id"]]
        #     for i in range(5 - component_state.total_galaxies.value):
        #         gal = dict(gal_tab[i])
        #         _on_galaxy_selected(gal)

        #     component_state.transition_to(Marker.sel_gal3, force=True)

        # solara.Button("Select 5 Galaxies", on_click=_on_select_galaxies_clicked)


    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineExploreData.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.exp_dat1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverseEstimate3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.age_uni3),
                state_view={
                    "age_const": AGE_CONSTANT,
                    # TODO - update these once real values are hooked up
                    "hypgal_distance": 100,
                    "hypgal_velocity": 8000,
                },     
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverseEstimate4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.age_uni4),
                state_view={
                    "age_const": AGE_CONSTANT,
                    # TODO - update these once real values are hooked up
                    "hypgal_distance": 100,
                    "hypgal_velocity": 8000,
                },   
            )

        with rv.Col():
            pass

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineTrendsDataMC1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.tre_dat1),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('tre-dat-mc1')), 'score_tag': 'tre-dat-mc1'}                
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once viewer is implemented
                GUIDELINE_ROOT / "GuidelineTrendsData2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.tre_dat2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineTrendsDataMC3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.tre_dat3),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('tre-dat-mc3')), 'score_tag': 'tre-dat-mc3'}   
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRelationshipVelDistMC.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.rel_vel1),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('galaxy-trend')), 'score_tag': 'galaxy-trend'} 
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineTrendLines1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.tre_lin1),               
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once linedraw tool is implemented
                GUIDELINE_ROOT / "GuidelineTrendLinesDraw2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.tre_lin2),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once best fit line tool is implemented
                GUIDELINE_ROOT / "GuidelineBestFitLine.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.bes_fit1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineHubblesExpandingUniverse1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.hub_exp1),
                state_view={
                    "hubble_slideshow_finished": component_state.hubble_slideshow_finished.value
                }, 
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverse.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.age_uni1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineHypotheticalGalaxy.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.hyp_gal1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeRaceEquation.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.age_rac1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAgeUniverseEquation2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.age_uni2),
                state_view={
                    "age_const": AGE_CONSTANT
                },             
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineYourAgeEstimate.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.you_age1),
            )
            ScaffoldAlert(
                # TODO - add free response functionality
                GUIDELINE_ROOT / "GuidelineShortcomingsEstReflect1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.sho_est1),
                event_fr_callback=lambda event: fr_callback(event=event, local_state=LOCAL_STATE),
                state_view={
                    'free_response_a': get_free_response(LOCAL_STATE.free_responses,'shortcoming-1'),
                    'free_response_b': get_free_response(LOCAL_STATE.free_responses,'shortcoming-2'),
                    'free_response_c': get_free_response(LOCAL_STATE.free_responses,'other-shortcomings'),
                }
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineShortcomingsEst2.vue",
                # TODO: event_next_callback should go to next stage but I don't know how to set that up.
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.sho_est2),
            )

        with rv.Col():
            with rv.Col(cols=10, offset=1):
                if component_state.current_step.value.value > Marker.rel_vel1.value:
                    HubbleExpUniverseSlideshow(
                        event_on_slideshow_finished=lambda *args: component_state.hubble_slideshow_finished.set(
                            True
                        ),
                        dialog=component_state.hubble_slideshow_dialog.value,
                        step=component_state.hubble_slideshow_state.step.value,
                        maxStepCompleted=component_state.hubble_slideshow_state.max_step_completed.value,
                    )

