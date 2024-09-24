from cosmicds.layout import BaseLayout

from hubbleds.utils import mathjax_input_callback, mathjax_input_setup
from .state import GLOBAL_STATE, LOCAL_STATE
import solara
from solara.toestand import Ref
from cosmicds.components import MathJaxSupport, PlotlySupport
from hubbleds.remote import LOCAL_API
from cosmicds.logger import setup_logger

logger = setup_logger("LAYOUT")


@solara.component
def Layout(children=[]):

    mjax_setup = mathjax_input_setup(LOCAL_STATE)
    mjax_cb = mathjax_input_callback(LOCAL_STATE)

    MathJaxSupport()
    PlotlySupport()
    logger.info("Mounted external libraries.")

    student_id = Ref(GLOBAL_STATE.fields.student.id)
    loaded_states = solara.use_reactive(False)

    async def _load_global_local_states():
        if not GLOBAL_STATE.value.student.id:
            logger.warning("Failed to load measurements: no student was found.")
            return

        logger.info(
            "Loading story stage and measurements for user `%s`.",
            GLOBAL_STATE.value.student.id,
        )

        # Retrieve the student's app and local states
        LOCAL_API.get_app_story_states(GLOBAL_STATE, LOCAL_STATE)
        Ref(GLOBAL_STATE.fields.update_db).set(True)

        # Load in the student's measurements
        measurements = LOCAL_API.get_measurements(GLOBAL_STATE, LOCAL_STATE)
        sample_measurements = LOCAL_API.get_sample_measurements(
            GLOBAL_STATE, LOCAL_STATE
        )

        logger.info("Finished loading state.")
        loaded_states.set(True)

        Ref(LOCAL_STATE.fields.measurements_loaded).set(True)

    solara.lab.use_task(_load_global_local_states, dependencies=[student_id.value])

    # solara.use_memo(_load_local_state, dependencies=[student_id.value])

    async def _write_local_global_states():
        if not loaded_states.value:
            return

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

    with BaseLayout(
        local_state=LOCAL_STATE,
        children=children,
        story_name=LOCAL_STATE.value.story_id,
        story_title=LOCAL_STATE.value.title,
    ):
        pass
