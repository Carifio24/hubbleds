from pydantic import BaseModel, computed_field, field_validator, Field
from solara import Reactive
from cosmicds.state import BaseState, GLOBAL_STATE, BaseLocalState
from typing import Optional
import solara
import datetime
from functools import cached_property
from astropy.table import Table
from pydantic import Field

from solara.toestand import Ref

from .free_response import FreeResponses
from .mc_score import MCScoring

from typing import Callable, Tuple

ELEMENT_REST = {"H-α": 6562.79, "Mg-I": 5176.7}

from cosmicds.logger import setup_logger

logger = setup_logger("HUBBLEDS-STATE")

class SpectrumData(BaseModel):
    name: str
    wave: list[float]
    flux: list[float]
    ivar: list[float]


class GalaxyData(BaseModel):
    id: int
    name: str
    ra: float
    decl: float
    z: float
    type: str
    element: str

    @cached_property
    def spectrum(self):
        from hubbleds.remote import LOCAL_API

        return LOCAL_API.load_spectrum_data(self, LOCAL_STATE)

    @cached_property
    def spectrum_as_data_frame(self):
        from hubbleds.remote import LOCAL_API

        spec_data = LOCAL_API.load_spectrum_data(self, LOCAL_STATE)

        return Table({"wave": spec_data.wave, "flux": spec_data.flux}).to_pandas()


class StudentMeasurement(BaseModel):
    student_id: int
    rest_wave_unit: str = "angstrom"
    obs_wave_value: float | None = None
    obs_wave_unit: str = "angstrom"
    velocity_value: float | None = None
    velocity_unit: str = "km/s"
    ang_size_value: float | None = None
    ang_size_unit: str = "arcsecond"
    est_dist_value: float | None = None
    est_dist_unit: str = "Mpc"
    measurement_number: str | None = None
    brightness: float = 0
    galaxy: Optional[GalaxyData] = None

    @computed_field
    @property
    def galaxy_id(self) -> int:
        return self.galaxy.id

    @computed_field
    @property
    def rest_wave_value(self) -> float:
        return round(ELEMENT_REST[self.galaxy.element])

    @computed_field
    @property
    def last_modified(self) -> str:
        return f"{datetime.datetime.now(datetime.UTC)}"


class LocalState(BaseLocalState):
    title: str = "Hubble's law"
    story_id: str = "hubbles_law"
    measurements: list[StudentMeasurement] = []
    example_measurements: list[StudentMeasurement] = []
    calculations: dict = {}
    validation_failure_counts: dict = {}
    has_best_fit_galaxy: bool = False
    enough_students_ready: bool = False
    class_data_students: list = []
    class_data_info: dict = {}
    mc_scoring: MCScoring = Field(default_factory=MCScoring)
    free_responses: FreeResponses = Field(default_factory=FreeResponses)
    show_snackbar: bool = False
    snackbar_message: str = ""

    @cached_property
    def galaxies(self) -> list[GalaxyData]:
        from hubbleds.remote import LOCAL_API

        return LOCAL_API.get_galaxies(LOCAL_STATE)

    def get_measurement(self, galaxy_id: int) -> StudentMeasurement | None:
        return next((x for x in self.measurements if x.galaxy_id == galaxy_id), None)

    def get_example_measurement(self, galaxy_id: int) -> StudentMeasurement | None:
        return next(
            (x for x in self.example_measurements if x.galaxy_id == galaxy_id), None
        )

    def get_measurement_index(self, galaxy_id: int) -> int | None:
        return next(
            (i for i, x in enumerate(self.measurements) if x.galaxy_id == galaxy_id),
            None,
        )

    def get_example_measurement_index(self, galaxy_id: int) -> int | None:
        return next(
            (
                i
                for i, x in enumerate(self.example_measurements)
                if x.galaxy_id == galaxy_id
            ),
            None,
        )

    def get_galaxy_data(self, galaxy_id: int) -> GalaxyData | None:
        return next(
            (
                galaxy for galaxy in self.galaxies if galaxy.id == galaxy_id
            ),
            None,
        )
    
    def question_completed(self, tag: str) -> bool:
        if tag in self.free_responses:
            return self.free_responses[tag].completed
        elif tag in self.mc_scoring:
            return self.mc_scoring[tag].completed
        
        return False

LOCAL_STATE = solara.reactive(LocalState())


def get_free_response(local_state: Reactive[LocalState], tag: str):
    # get question as serializable dictionary
    # also initializes the question by using get_or_create method
    free_responses = local_state.value.free_responses
    return  free_responses.get_or_create(tag).model_dump()
        
def get_multiple_choice(local_state: Reactive[LocalState], tag: str):
    # get question as serializable dictionary
    # also initializes the question by using get_or_create method
    multiple_choices = local_state.value.mc_scoring
    return multiple_choices.get_model_dump(tag)



def mc_callback(
        event, 
        local_state: Reactive[LocalState], 
        callback: Optional[Callable[[MCScoring], None]] = None):
    """
    Multiple Choice callback function
    """
    
    mc_scoring = Ref(local_state.fields.mc_scoring)    
    new = mc_scoring.value.model_copy(deep=True)
    logger.info(f"MC Callback Event: {event[0]}")
    logger.info(f"Current mc_scoring: {new}")

    # mc-initialize-callback returns data which is a string
    if event[0] == "mc-initialize-response":
        if event[1] not in new:
            new.add(event[1])
            mc_scoring.set(new)
            if callback is not None:
                callback(new)
            
    # mc-score event returns a data which is an mc-score dictionary (includes tag)
    elif event[0] == "mc-score":
        new.update_mc_score(**event[1])
        mc_scoring.set(new)
        if callback is not None:
            callback(new)

    else:
        raise ValueError(f"Unknown event in mc_callback: <<{event}>> ")


def fr_callback(
    event: Tuple[str, dict[str, str]],
    local_state: Reactive[LocalState],
    callback: Optional[Callable[[FreeResponses], None]] = None,
):
    """
    Free Response callback function
    """
    
    free_responses = Ref(local_state.fields.free_responses)
    new = free_responses.value.model_copy(deep=True)
    
    logger.info(f"Free Response Callback Event: {event[0]}")
    logger.info(f"Current fr_response value: {free_responses}")
    if event[0] == "fr-initialize":
        if event[1]["tag"] not in free_responses.value:
            new.add(event[1]["tag"])
            free_responses.set(new)
            if callback is not None:
                callback(new)

    elif event[0] == "fr-update":
        new.update(event[1]["tag"], response=event[1]["response"])
        free_responses.set(new)
        if callback is not None:
            if (len(event) > 1) and ("response" in event[1]):
                callback(new)
    else:
        raise ValueError(f"Unknown event in fr_callback: <<{event}>> ")
