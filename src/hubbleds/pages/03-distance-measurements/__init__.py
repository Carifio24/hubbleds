import solara
from cosmicds.widgets.table import Table
from cosmicds.components import ScaffoldAlert, StateEditor
import astropy.units as u
from cosmicds import load_custom_vue_components
from glue_jupyter.app import JupyterApplication
from reacton import component, ipyvuetify as rv
from pathlib import Path

from hubbleds.widgets.distance_tool.distance_tool import DistanceTool

from ...components import AngsizeDosDontsSlideshow, DataTable
from ...data_management import *
from ...utils import DISTANCE_CONSTANT, GALAXY_FOV
from ...state import GLOBAL_STATE, LOCAL_STATE, mc_callback, mc_serialize_score
from ...widgets.selection_tool import SelectionTool
from ...data_models.student import student_data, StudentMeasurement, example_data
from .component_state import ComponentState, Marker


GUIDELINE_ROOT = Path(__file__).parent / "guidelines"

gjapp = JupyterApplication(GLOBAL_STATE.data_collection, GLOBAL_STATE.session)

component_state = ComponentState()


def _update_angular_size(data, galaxy, angular_size, count):
    if bool(galaxy) and angular_size is not None:
        arcsec_value = int(angular_size.to(u.arcsec).value)
        data.update(galaxy["id"], {"angular_size": arcsec_value})
        count.value += 1


@solara.component
def DistanceToolComponent(galaxy, show_ruler, angular_size_callback):
    tool = DistanceTool.element()

    def set_selected_galaxy():
        widget = solara.get_widget(tool)
        if galaxy:
            widget.measuring = False
            widget.go_to_location(galaxy["ra"], galaxy["decl"], fov=GALAXY_FOV)
        widget.measuring_allowed = bool(galaxy)

    solara.use_effect(set_selected_galaxy, [galaxy])

    def update_show_ruler():
        widget = solara.get_widget(tool)
        widget.show_ruler = show_ruler

    solara.use_effect(update_show_ruler, [show_ruler])

    def update_angular_size(change):
        angle = change["new"]
        angular_size_callback(angle)

    def _define_callbacks():
        widget = solara.get_widget(tool)
        widget.observe(update_angular_size, ["angular_size"])

    solara.use_effect(_define_callbacks, [])


@solara.component
def Page():
    # Custom vue-only components have to be registered in the Page element
    #  currently, otherwise they will not be available in the front-end
    load_custom_vue_components()

    # Solara's reactivity is often tied to the _context_ of the Page it's
    #  being rendered in. Currently, in order to trigger subscribed callbacks,
    #  state connections need to be initialized _inside_ a Page.
    component_state.setup()

    mc_scoring, set_mc_scoring  = solara.use_state(LOCAL_STATE.mc_scoring.value)

    StateEditor(Marker, component_state) 

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
                GUIDELINE_ROOT / "GuidelineAngsizeMeas1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas2b.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz2b),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineAngsizeMeas3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz3),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineAngsizeMeas4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz4),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas5a.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz5a),
                state_view={
                    "dosdonts_tutorial_opened": component_state.dosdonts_tutorial_opened.value
                },
            )
            # This was skipped in voila version
            # ScaffoldAlert(
            #     GUIDELINE_ROOT / "GuidelineAngsizeMeas6.vue",
            #     event_next_callback=lambda *args: component_state.transition_next(),
            #     event_back_callback=lambda *args: component_state.transition_previous(),
            #     can_advance=component_state.can_transition(next=True),
            #     show=component_state.is_current_step(Marker.ang_siz6),
            # )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq5.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                event_force_transition=lambda *args: component_state.transition_to(Marker.rep_rem1),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineDotplotSeq5b.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5b),
            )

        with rv.Col():
            with rv.Col(cols=6, offset=3):
                if component_state.current_step.value.value >= Marker.ang_siz5a.value:
                    AngsizeDosDontsSlideshow(
                        event_on_dialog_opened=lambda *args: component_state.dosdonts_tutorial_opened.set(
                            True
                        )
                    )

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                # TODO This will need to be wired up once table is implemented
                GUIDELINE_ROOT / "GuidelineChooseRow1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.cho_row1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineAngsizeMeas5.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.ang_siz5),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEstimateDistance1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEstimateDistance2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis2),
                state_view={
                    "distance_const": DISTANCE_CONSTANT
                },
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once table is implemented
                GUIDELINE_ROOT / "GuidelineChooseRow2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.cho_row2),
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once measuring tool is implemented
                GUIDELINE_ROOT / "GuidelineEstimateDistance3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis3),
                state_view={
                    "distance_const": DISTANCE_CONSTANT,
                    "meas_theta": 10, # TODO pass student's value once we hook up angular size measurements
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEstimateDistance4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.est_dis4),
                state_view={
                    "distance_const": DISTANCE_CONSTANT,
                    "meas_theta": 10, # TODO pass student's value once we hook up angular size measurements
                },
            )
            ScaffoldAlert(
                # TODO This will need to be wired up once table is implemented
                GUIDELINE_ROOT / "GuidelineDotplotSeq5a.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5a),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq5c.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq5c),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRepeatRemainingGalaxies.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_to(Marker.dot_seq5),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.rep_rem1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineFillRemainingGalaxies.vue",
                # event_next_callback should go to next stage but I don't know how to set that up.
                event_back_callback=lambda *args: component_state.transition_previous(),
                show=component_state.is_current_step(Marker.fil_rem1),
            )

        with rv.Col():
            with rv.Card(class_="pa-0 ma-0", elevation=0):
            
                common_headers = [
                    {
                        "text": "Galaxy Name",
                        "align": "start",
                        "sortable": False,
                        "value": "name"
                    },
                    { "text": "&theta; (arcsec)", "value": "angular_size" },
                    { "text": "Distance (Mpc)", "value": "distance" },
                ]
            
            def update_show_ruler(marker):
                component_state.show_ruler.value = Marker.is_between(marker, Marker.ang_siz3, Marker.est_dis4) or \
                                                   Marker.is_between(marker, Marker.est_dis4, Marker.last())
                
            component_state.current_step.subscribe(update_show_ruler)

            @solara.lab.computed
            def on_example_galaxy_marker():
                return component_state.current_step.value.value < Marker.rep_rem1.value


            @solara.lab.computed
            def current_galaxy():
                galaxy = component_state.selected_galaxy.value
                example_galaxy = component_state.selected_example_galaxy.value
                return example_galaxy if on_example_galaxy_marker.value else galaxy

            def _ang_size_cb(angle):
                data = example_data if on_example_galaxy_marker.value else student_data
                count = component_state.example_angular_sizes_total if on_example_galaxy_marker.value else component_state.angular_sizes_total
                _update_angular_size(data, current_galaxy.value, angle, count)

            DistanceToolComponent(
                galaxy=current_galaxy.value,
                show_ruler=component_state.show_ruler.value,
                angular_size_callback=_ang_size_cb
            )

            if component_state.current_step.value.value < Marker.rep_rem1.value:
                def update_example_galaxy(galaxy):
                    flag = galaxy.get("value", True)
                    value = galaxy["item"] if flag else None
                    component_state.selected_example_galaxy.set(value)

                @solara.lab.computed
                def example_table_kwargs():
                    ang_size_tot = component_state.example_angular_sizes_total.value
                    return {
                        "title": "Example Galaxy",
                        "headers": common_headers + [{ "text": "Measurement Number", "value": "measurement_number" }],
                        "items": example_data.dict(exclude={'measurements': {'__all__': 'spectrum'}})["measurements"],
                        "highlighted": False,  # TODO: Set the markers for this,
                        "event_on_row_selected": update_example_galaxy
                    }

                DataTable(**example_table_kwargs.value)

            else:
                def update_galaxy(galaxy):
                    flag = galaxy.get("value", True)
                    value = galaxy["item"] if flag else None
                    component_state.selected_galaxy.set(value)

                @solara.lab.computed
                def table_kwargs():
                    ang_size_tot = component_state.angular_sizes_total.value
                    return {
                        "title": "My Galaxies",
                        "headers": common_headers + [{ "text": "Measurement Number", "value": "measurement_number" }],
                        "items": student_data.dict(exclude={'measurements': {'__all__': 'spectrum'}})["measurements"],
                        "highlighted": False,  # TODO: Set the markers for this,
                        "event_on_row_selected": update_galaxy
                    }

                DataTable(**table_kwargs.value)

    with solara.ColumnsResponsive(12, large=[4,8]):
        with rv.Col():
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq1.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq2.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq2),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('ang_meas_consensus')), 'score_tag': 'ang_meas_consensus'}
            )            
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq3.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq3),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq4.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq4),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq4a.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq4a),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('ang_meas_dist_relation')), 'score_tag': 'ang_meas_dist_relation'}
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq6.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq6),
                event_mc_callback=lambda event: mc_callback(event = event, local_state = LOCAL_STATE, callback=set_mc_scoring),
                state_view={'mc_score': mc_serialize_score(mc_scoring.get('ang_meas_consensus_2')), 'score_tag': 'ang_meas_consensus_2'}
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotplotSeq7.vue",
                event_next_callback=lambda *args: component_state.transition_next(),
                event_back_callback=lambda *args: component_state.transition_previous(),
                can_advance=component_state.can_transition(next=True),
                show=component_state.is_current_step(Marker.dot_seq7),
            )

        with rv.Col():
            solara.Markdown("blah blah")

