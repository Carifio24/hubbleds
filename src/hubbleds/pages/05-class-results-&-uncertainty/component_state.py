import enum
from pydantic import BaseModel, field_validator
import solara
from typing import List, Any

from cosmicds.state import BaseState
from hubbleds.base_marker import BaseMarker
from hubbleds.base_component_state import BaseComponentState
from hubbleds.state import LOCAL_STATE


class Marker(enum.Enum, BaseMarker):
    ran_var1 = enum.auto()
    fin_cla1 = enum.auto()
    cla_res1 = enum.auto()
    rel_age1 = enum.auto() # MC age-slope-trend
    cla_age1 = enum.auto()
    cla_age2 = enum.auto()
    cla_age3 = enum.auto()
    cla_age4 = enum.auto()
    lea_unc1 = enum.auto()
    mos_lik1 = enum.auto()
    age_dis1 = enum.auto()
    mos_lik2 = enum.auto()
    mos_lik3 = enum.auto()
    mos_lik4 = enum.auto()
    con_int1 = enum.auto()
    con_int2 = enum.auto()
    con_int3 = enum.auto()

    cla_dat1 = enum.auto()
    tre_lin2c = enum.auto()
    bes_fit1c = enum.auto()
    you_age1c = enum.auto()
    cla_res1c = enum.auto()
    cla_age1c = enum.auto()
    age_dis1c = enum.auto()
    con_int2c = enum.auto()
    
    two_his1 = enum.auto()
    two_his2 = enum.auto() # MC histogram-range
    two_his3 = enum.auto() # MC histogram-percent-range
    two_his4 = enum.auto() # MC histogram-distribution
    two_his5 = enum.auto()
    mor_dat1 = enum.auto()


class UncertaintyState(BaseModel):
    step: int = 0


class MMMState(BaseModel):
    step: int = 0
    length: int = 3
    titles: List[str] = ["Mean", "Median", "Mode"]


class AgeCalcState(BaseModel):
    hint1_dialog: bool = False
    hint2_dialog: bool = False
    hint3_dialog: bool = False


class ComponentState(BaseComponentState, BaseState):
    current_step: Marker = Marker.first()
    stage_id: str = "class_results_and_uncertainty"
    student_low_age: int = 0
    student_high_age: int = 0
    class_low_age: int = 0
    class_high_age: int = 0
    uncertainty_state: UncertaintyState = UncertaintyState()
    uncertainty_slideshow_finished: bool = False
    mmm_state: MMMState = MMMState()
    age_calc_state: AgeCalcState = AgeCalcState()
    percentage_selection: str | None = None
    statistics_selection: str | None = None
    percentage_selection_class: str | None = None
    statistics_selection_class: str | None = None

    links_setup: bool = False
    class_data_loaded: bool = False
    all_data_loaded: bool = False
    student_data_added: bool = False
    class_data_added: bool = False
    

    @field_validator("current_step", mode="before")
    def convert_int_to_enum(cls, v: Any) -> Marker:
        if isinstance(v, int):
            return Marker(v)
        return v

    @property
    def mos_lik_gate(self) -> bool:
        return self.uncertainty_slideshow_finished

    # TODO: Implement other gates that require checking MC status


COMPONENT_STATE = solara.reactive(ComponentState())
