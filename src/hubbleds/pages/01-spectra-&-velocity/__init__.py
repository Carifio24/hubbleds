import solara
from hubbleds.state import LOCAL_STATE, GLOBAL_STATE
from .component_state import COMPONENT_STATE, Marker
from hubbleds.remote import LOCAL_API
from glue_jupyter import JupyterApplication
import asyncio
from pathlib import Path
from cosmicds.components import ScaffoldAlert, StateEditor
import reacton.ipyvuetify as rv
from hubbleds.base_component_state import (
    transition_to,
    transition_previous,
    transition_next,
)
from hubbleds.components import (
    SelectionTool,
    DataTable,
    DopplerSlideshow,
    SpectrumViewer,
    SpectrumSlideshow,
    DotplotViewer,
    ReflectVelocitySlideshow,
    DotplotTutorialSlideshow,
)
from hubbleds.state import GalaxyData, StudentMeasurement
# from solara.lab import Ref
from solara.toestand import Ref
from cosmicds.logger import setup_logger

logger = setup_logger("STAGE")

GUIDELINE_ROOT = Path(__file__).parent / "guidelines"


@solara.lab.computed
def selected_example_measurement():
    return LOCAL_STATE.value.get_example_measurement(
        COMPONENT_STATE.value.selected_example_galaxy
    )


@solara.lab.computed
def selected_measurement():
    return LOCAL_STATE.value.get_measurement(COMPONENT_STATE.value.selected_galaxy)


@solara.lab.computed
def selected_redshift():
    galaxy_data = LOCAL_STATE.value.get_galaxy_data(COMPONENT_STATE.value.selected_galaxy)
    return galaxy_data.z if galaxy_data is not None else None


@solara.component
def Page():
    loaded_component_state = solara.use_reactive(False)

    async def _load_component_state():
        # Load stored component state from database, measurement data is
        #   considered higher-level and is loaded when the story starts.
        LOCAL_API.get_stage_state(GLOBAL_STATE, LOCAL_STATE, COMPONENT_STATE)

        total_galaxies = Ref(COMPONENT_STATE.fields.total_galaxies)

        if len(LOCAL_STATE.value.measurements) != total_galaxies.value:
            logger.error(
                "Detected mismatch between stored measurements and current "
                "recorded number of galaxies."
            )
            total_galaxies.set(len(LOCAL_STATE.value.measurements))

        logger.info("Finished loading component state.")
        loaded_component_state.set(True)

    solara.lab.use_task(_load_component_state)
    # solara.use_memo(_load_component_state)

    async def _write_local_global_states():
        # Listen for changes in the states and write them to the database
        LOCAL_API.put_story_state(GLOBAL_STATE, LOCAL_STATE)

        # Be sure to write the measurement data separately since it's stored
        #  in another location in the database
        LOCAL_API.put_measurements(GLOBAL_STATE, LOCAL_STATE)
        LOCAL_API.put_sample_measurements(GLOBAL_STATE, LOCAL_STATE)

        logger.info("Wrote state to database.")

    solara.lab.use_task(
        _write_local_global_states, dependencies=[GLOBAL_STATE.value, LOCAL_STATE.value]
    )

    async def _write_component_state():
        if not loaded_component_state.value:
            return

        # Listen for changes in the states and write them to the database
        LOCAL_API.put_stage_state(GLOBAL_STATE, LOCAL_STATE, COMPONENT_STATE)

        logger.info("Wrote component state to database.")

    solara.lab.use_task(_write_component_state, dependencies=[COMPONENT_STATE.value])

    def _glue_setup() -> JupyterApplication:
        # NOTE: use_memo has to be part of the main page render. Including it
        #  in a conditional will result in an error.
        gjapp = JupyterApplication(
            GLOBAL_STATE.value.glue_data_collection, GLOBAL_STATE.value.glue_session
        )

        return gjapp

    gjapp = solara.use_memo(_glue_setup)

    def _state_callback_setup():
        # We want to minize duplicate state handling, but also keep the states
        #  independent. We'll set up observers for changes here so that they
        #  automatically keep the states in sync.
        measurements = Ref(LOCAL_STATE.fields.measurements)
        total_galaxies = Ref(COMPONENT_STATE.fields.total_galaxies)
        measurements.subscribe_change(
            lambda *args: total_galaxies.set(len(measurements.value))
        )

    solara.use_memo(_state_callback_setup)

    # Load selected galaxy spectrum data in the background to avoid hitched
    #  in the front-end user experience.
    async def _load_example_spectrum():
        if selected_example_measurement.value is None:
            return False

        return selected_example_measurement.value.galaxy.spectrum_as_data_frame

    example_spec_data_task = solara.lab.use_task(
        _load_example_spectrum,
        dependencies=[COMPONENT_STATE.value.selected_example_galaxy],
    )

    async def _load_spectrum():
        if selected_measurement.value is None:
            return False

        return selected_measurement.value.galaxy.spectrum_as_data_frame

    spec_data_task = solara.lab.use_task(
        _load_spectrum,
        dependencies=[COMPONENT_STATE.value.selected_galaxy],
    )

    # solara.Text(f"{GLOBAL_STATE.value.dict()}")
    # solara.Text(f"{LOCAL_STATE.value.dict()}")
    # solara.Text(f"{COMPONENT_STATE.value.dict()}")

    # Flag to show/hide the selection tool. TODO: we shouldn't need to be
    #  doing this here; revisit in the future and implement proper handling
    #  in the ipywwt package itself.
    show_selection_tool, set_show_selection_tool = solara.use_state(False)

    async def _delay_selection_tool():
        await asyncio.sleep(3)
        set_show_selection_tool(True)

    solara.lab.use_task(_delay_selection_tool)

    StateEditor(Marker, COMPONENT_STATE, LOCAL_STATE, LOCAL_API)

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineIntro.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.mee_gui1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies1.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.sel_gal1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies2.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.sel_gal2),
                state_view={
                    "total_galaxies": COMPONENT_STATE.value.total_galaxies,
                    "selected_galaxy": bool(COMPONENT_STATE.value.selected_galaxy),
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies3.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.sel_gal3),
                state_view={
                    "total_galaxies": COMPONENT_STATE.value.total_galaxies,
                    "selected_galaxy": bool(COMPONENT_STATE.value.selected_galaxy),
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSelectGalaxies4.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.sel_gal4),
            )

        with rv.Col(cols=8):

            def _galaxy_added_callback(galaxy_data: GalaxyData):
                already_exists = galaxy_data.id in [
                    x.galaxy_id for x in LOCAL_STATE.value.measurements
                ]

                if already_exists:
                    return

                if len(LOCAL_STATE.value.measurements) == 5:
                    show_snackbar = Ref(LOCAL_STATE.fields.show_snackbar)
                    snackbar_message = Ref(LOCAL_STATE.fields.snackbar_message)

                    show_snackbar.set(True)
                    snackbar_message.set(
                        "You've already selected 5 galaxies. Continue forth!"
                    )
                    return

                logger.info("Adding galaxy `%s` to measurements.", galaxy_data.id)

                measurements = Ref(LOCAL_STATE.fields.measurements)

                measurements.set(
                    measurements.value
                    + [
                        StudentMeasurement(
                            student_id=GLOBAL_STATE.value.student.id,
                            galaxy=galaxy_data,
                        )
                    ]
                )

            def _galaxy_selected_callback(galaxy_data: GalaxyData | None):
                if galaxy_data is None:
                    return

                selected_galaxy = Ref(COMPONENT_STATE.fields.selected_galaxy)
                selected_galaxy.set(galaxy_data.id)

            SelectionTool(
                show_galaxies=COMPONENT_STATE.value.current_step_in(
                    [Marker.sel_gal2, Marker.sel_gal3]
                ),
                galaxy_selected_callback=_galaxy_selected_callback,
                galaxy_added_callback=_galaxy_added_callback,
                selected_measurement=(
                    selected_measurement.value.dict()
                    if selected_measurement.value is not None
                    else None
                ),
            )

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineNoticeGalaxyTable.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.not_gal_tab),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineChooseRow.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.cho_row1),
            )

            def _on_validated_transition(validated):
                if validated:
                    transition_next(COMPONENT_STATE)

                show_doppler_dialog = Ref(COMPONENT_STATE.fields.show_doppler_dialog)
                show_doppler_dialog.set(validated)

            validation_4_failed = Ref(
                COMPONENT_STATE.fields.doppler_state.validation_4_failed
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc4.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.current_step_in(
                    [Marker.dop_cal4, Marker.dop_cal5]
                ),
                state_view={
                    "lambda_obs": COMPONENT_STATE.value.obs_wave,
                    "lambda_rest": (
                        selected_example_measurement.value.rest_wave_value
                        if selected_example_measurement.value is not None
                        else None
                    ),
                    "failed_validation_4": validation_4_failed.value,
                },
                event_failed_validation_4_callback=validation_4_failed.set,
                event_on_validated_transition=_on_validated_transition,
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineCheckMeasurement.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.che_mea1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence12.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq12),
                event_remeasure_example_galaxy=lambda _: transition_to(
                    COMPONENT_STATE, Marker.dot_seq13, force=True
                ),
                event_continue_to_galaxies=lambda _: transition_to(
                    COMPONENT_STATE, Marker.rem_gal1, force=True
                ),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence13.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq13),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRemainingGals.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.rem_gal1),
                state_view={
                    "obswaves_total": COMPONENT_STATE.value.obs_wave_total,
                    "has_bad_velocities": COMPONENT_STATE.value.has_bad_velocities,
                    "has_multiple_bad_velocities": COMPONENT_STATE.value.has_multiple_bad_velocities,
                    "selected_galaxy": (
                        selected_measurement.value.dict()
                        if selected_measurement.value is not None
                        else None
                    ),
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc6.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dop_cal6),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineReflectVelValues.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.ref_vel1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineEndStage1.vue",
                event_next_callback=lambda _: print("Transition next stage."),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.end_sta1),
                state_view={
                    "has_bad_velocities": COMPONENT_STATE.value.has_bad_velocities,
                    "has_multiple_bad_velocities": COMPONENT_STATE.value.has_multiple_bad_velocities,
                },
            )

        with rv.Col(cols=8):
            show_example_data_table = COMPONENT_STATE.value.current_step_between(
                Marker.cho_row1, Marker.dot_seq14
            )

            if show_example_data_table:
                selected_example_galaxy = Ref(
                    COMPONENT_STATE.fields.selected_example_galaxy
                )

                DataTable(
                    title="Example Galaxy",
                    items=[x.dict() for x in LOCAL_STATE.value.example_measurements],
                    show_select=COMPONENT_STATE.value.current_step_at_or_after(
                        Marker.cho_row1
                    ),
                    event_on_row_selected=lambda row: selected_example_galaxy.set(
                        LOCAL_STATE.value.get_example_measurement(
                            row["item"]["galaxy_id"]
                        ).galaxy_id
                    ),
                )
            else:
                selected_galaxy = Ref(COMPONENT_STATE.fields.selected_galaxy)

                def _on_table_row_selected(row):
                    galaxy_measurement = LOCAL_STATE.value.get_measurement(
                        row["item"]["galaxy_id"]
                    )
                    if galaxy_measurement is not None:
                        selected_galaxy.set(galaxy_measurement.galaxy_id)

                    obs_wave = Ref(COMPONENT_STATE.fields.obs_wave)
                    obs_wave.set(0)

                def _on_calculate_velocity():
                    for i in range(len(LOCAL_STATE.value.measurements)):
                        measurement = Ref(LOCAL_STATE.fields.measurements[i])
                        velocity = round(
                            3e5
                            * (
                                measurement.value.obs_wave_value
                                / measurement.value.rest_wave_value
                                - 1
                            )
                        )
                        measurement.set(
                            measurement.value.model_copy(
                                update={"velocity_value": velocity}
                            )
                        )

                        velocities_total = Ref(COMPONENT_STATE.fields.velocities_total)
                        velocities_total.set(velocities_total.value + 1)

                DataTable(
                    title="My Galaxies",
                    items=[x.dict() for x in LOCAL_STATE.value.measurements],
                    show_select=COMPONENT_STATE.value.current_step_at_or_after(
                        Marker.cho_row1
                    ),
                    show_velocity_button=COMPONENT_STATE.value.is_current_step(
                        Marker.dop_cal6
                    ),
                    event_on_row_selected=_on_table_row_selected,
                    event_calculate_velocity=lambda _: _on_calculate_velocity(),
                )

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineIntroDotplot.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.int_dot1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence01.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq1),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence02.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence03.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq3),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence05.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq5),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence06.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq6),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence07.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq7),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence08.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq8),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence09.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq9),
            )

        with rv.Col(cols=8):
            if COMPONENT_STATE.value.current_step_between(
                Marker.mee_spe1, Marker.che_mea1
            ):
                show_doppler_dialog = Ref(COMPONENT_STATE.fields.show_doppler_dialog)
                step = Ref(COMPONENT_STATE.fields.doppler_state.step)
                validation_5_failed = Ref(
                    COMPONENT_STATE.fields.doppler_state.validation_5_failed
                )
                max_step_completed_5 = Ref(
                    COMPONENT_STATE.fields.doppler_state.max_step_completed_5
                )
                velocity_calculated = Ref(
                    COMPONENT_STATE.fields.doppler_state.velocity_calculated
                )
                light_speed = Ref(COMPONENT_STATE.fields.doppler_state.light_speed)

                def _velocity_calculated_callback(value):
                    example_measurement_index = (
                        LOCAL_STATE.value.get_example_measurement_index(
                            COMPONENT_STATE.value.selected_example_galaxy
                        )
                    )
                    example_measurement = Ref(
                        LOCAL_STATE.fields.example_measurements[
                            example_measurement_index
                        ]
                    )
                    example_measurement.set(
                        example_measurement.value.model_copy(
                            update={"velocity_value": round(value)}
                        )
                    )

                DopplerSlideshow(
                    dialog=COMPONENT_STATE.value.show_doppler_dialog,
                    titles=COMPONENT_STATE.value.doppler_state.titles,
                    step=COMPONENT_STATE.value.doppler_state.step,
                    length=COMPONENT_STATE.value.doppler_state.length,
                    lambda_obs=COMPONENT_STATE.value.obs_wave,
                    lambda_rest=(
                        selected_example_measurement.value.rest_wave_value
                        if selected_example_measurement.value is not None
                        else None
                    ),
                    max_step_completed_5=COMPONENT_STATE.value.doppler_state.max_step_completed_5,
                    failed_validation_5=COMPONENT_STATE.value.doppler_state.validation_5_failed,
                    interact_steps_5=COMPONENT_STATE.value.doppler_state.interact_steps_5,
                    student_vel=COMPONENT_STATE.value.velocity,
                    student_c=COMPONENT_STATE.value.doppler_state.light_speed,
                    student_vel_calc=COMPONENT_STATE.value.doppler_state.velocity_calculated,
                    event_set_dialog=show_doppler_dialog.set,
                    event_set_step=step.set,
                    event_set_failed_validation_5=validation_5_failed.set,
                    event_set_max_step_completed_5=max_step_completed_5.set,
                    event_set_student_vel_calc=velocity_calculated.set,
                    event_set_student_c=light_speed.set,
                    event_set_student_vel=_velocity_calculated_callback,
                    event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                )

            if COMPONENT_STATE.value.current_step_between(
                Marker.int_dot1, Marker.dot_seq14
            ):
                dotplot_tutorial_finished = Ref(
                    COMPONENT_STATE.fields.dotplot_tutorial_finished
                )

                DotplotTutorialSlideshow(
                    dialog=COMPONENT_STATE.value.show_dotplot_tutorial_dialog,
                    step=COMPONENT_STATE.value.dotplot_tutorial_state.step,
                    length=COMPONENT_STATE.value.dotplot_tutorial_state.length,
                    max_step_completed=COMPONENT_STATE.value.dotplot_tutorial_state.max_step_completed,
                    dotplot_viewer=DotplotViewer(gjapp),
                    event_tutorial_finished=lambda _: dotplot_tutorial_finished.set(
                        True
                    ),
                )

                DotplotViewer(gjapp)

            if COMPONENT_STATE.value.is_current_step(Marker.ref_dat1):
                reflection_completed = Ref(COMPONENT_STATE.fields.reflection_complete)

                ReflectVelocitySlideshow(
                    reflection_complete=COMPONENT_STATE.value.reflection_complete,
                    event_on_reflection_completed=lambda _: reflection_completed.set(
                        True
                    ),
                )

    with rv.Row():
        with rv.Col(cols=4):
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineSpectrum.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.mee_spe1),
                state_view={
                    "spectrum_tutorial_opened": COMPONENT_STATE.value.spectrum_tutorial_opened
                },
            )

            selected_example_galaxy_data = LOCAL_STATE.value.get_example_measurement(
                COMPONENT_STATE.value.selected_example_galaxy
            )
            if selected_example_galaxy_data is not None:
                selected_example_galaxy_data = (
                    selected_example_galaxy_data.galaxy.dict()
                )

            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineRestwave.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.res_wav1),
                state_view={
                    "selected_example_galaxy": selected_example_galaxy_data,
                    "lambda_on": COMPONENT_STATE.value.obs_wave_tool_activated,
                    "lambda_used": COMPONENT_STATE.value.obs_wave_tool_used,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineObswave1.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.obs_wav1),
                state_view={"selected_example_galaxy": selected_example_galaxy_data},
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineObswave2.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.obs_wav2),
                state_view={
                    "selected_example_galaxy": selected_example_galaxy_data,
                    "zoom_tool_activate": COMPONENT_STATE.value.zoom_tool_activated,
                },
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc0.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dop_cal0),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDopplerCalc2.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dop_cal2),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence04.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq4),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence10.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq10),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineDotSequence11.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.dot_seq11),
            )
            ScaffoldAlert(
                GUIDELINE_ROOT / "GuidelineReflectOnData.vue",
                event_next_callback=lambda _: transition_next(COMPONENT_STATE),
                event_back_callback=lambda _: transition_previous(COMPONENT_STATE),
                can_advance=COMPONENT_STATE.value.can_transition(next=True),
                show=COMPONENT_STATE.value.is_current_step(Marker.ref_dat1),
            )

        with rv.Col(cols=8):
            show_example_spectrum = COMPONENT_STATE.value.current_step_between(
                Marker.mee_spe1, Marker.che_mea1
            ) or COMPONENT_STATE.value.current_step_between(
                Marker.dot_seq4, Marker.dot_seq14
            )

            show_galaxy_spectrum = COMPONENT_STATE.value.current_step_at_or_after(
                Marker.rem_gal1
            )

            if show_example_spectrum:
                with solara.Column():

                    def _example_wavelength_measured_callback(value):
                        example_measurement_index = (
                            LOCAL_STATE.value.get_example_measurement_index(
                                COMPONENT_STATE.value.selected_example_galaxy
                            )
                        )
                        example_measurement = Ref(
                            LOCAL_STATE.fields.example_measurements[
                                example_measurement_index
                            ]
                        )
                        example_measurement.set(
                            example_measurement.value.model_copy(
                                update={"obs_wave_value": value}
                            )
                        )
                        obs_wave_tool_used.set(True)
                        obs_wave = Ref(COMPONENT_STATE.fields.obs_wave)
                        obs_wave.set(value)

                    obs_wave_tool_used = Ref(COMPONENT_STATE.fields.obs_wave_tool_used)
                    obs_wave_tool_activated = Ref(
                        COMPONENT_STATE.fields.obs_wave_tool_activated
                    )
                    zoom_tool_activated = Ref(
                        COMPONENT_STATE.fields.zoom_tool_activated
                    )

                    SpectrumViewer(
                        data=(
                            example_spec_data_task.value
                            if example_spec_data_task.finished
                            else None
                        ),
                        obs_wave=COMPONENT_STATE.value.obs_wave,
                        redshift=selected_redshift.value,
                        spectrum_click_enabled=COMPONENT_STATE.value.current_step_at_or_after(
                            Marker.obs_wav1
                        ),
                        on_obs_wave_measured=_example_wavelength_measured_callback,
                        on_obs_wave_tool_clicked=lambda: obs_wave_tool_activated.set(
                            True
                        ),
                        on_zoom_tool_clicked=lambda: zoom_tool_activated.set(True),
                    )

                    spectrum_tutorial_opened = Ref(
                        COMPONENT_STATE.fields.spectrum_tutorial_opened
                    )

                    SpectrumSlideshow(
                        event_dialog_opened_callback=lambda _: spectrum_tutorial_opened.set(
                            True
                        )
                    )
            elif show_galaxy_spectrum:
                with solara.Column():

                    def _wavelength_measured_callback(value):
                        measurement_index = LOCAL_STATE.value.get_measurement_index(
                            COMPONENT_STATE.value.selected_galaxy
                        )
                        measurement = Ref(
                            LOCAL_STATE.fields.measurements[measurement_index]
                        )
                        measurement.set(
                            measurement.value.model_copy(
                                update={"obs_wave_value": value}
                            )
                        )

                        obs_wave = Ref(COMPONENT_STATE.fields.obs_wave)
                        obs_wave.set(value)

                        obs_wave_total = Ref(COMPONENT_STATE.fields.obs_wave_total)
                        obs_wave_total.set(obs_wave_total.value + 1)

                    SpectrumViewer(
                        data=(
                            spec_data_task.value if spec_data_task.finished else None
                        ),
                        obs_wave=COMPONENT_STATE.value.obs_wave,
                        spectrum_click_enabled=COMPONENT_STATE.value.current_step_at_or_after(
                            Marker.obs_wav1
                        ),
                        on_obs_wave_measured=_wavelength_measured_callback,
                    )

                    spectrum_tutorial_opened = Ref(
                        COMPONENT_STATE.fields.spectrum_tutorial_opened
                    )

                    SpectrumSlideshow(
                        event_dialog_opened_callback=lambda _: spectrum_tutorial_opened.set(
                            True
                        )
                    )
