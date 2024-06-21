from solara import Reactive
import solara
import enum
from ...marker_base import MarkerBase
from ...component_state_base import BaseComponentState
from ...decorators import computed_property
import dataclasses
from cosmicds.utils import API_URL
from ...state import GLOBAL_STATE, LOCAL_STATE
from ...data_models.student import example_data, StudentMeasurement, SpectrumData
from contextlib import closing
from io import BytesIO
from astropy.io import fits
from ...data_management import ELEMENT_REST


class Marker(enum.Enum, MarkerBase):
    exp_dat1 = enum.auto()
    tre_dat1 = enum.auto() # MC tre-dat-mc1
    tre_dat2 = enum.auto()
    tre_dat3 = enum.auto() # MC tre-dat-mc3
    rel_vel1 = enum.auto() # MC galaxy-trend
    hub_exp1 = enum.auto()
    tre_lin1 = enum.auto()
    tre_lin2 = enum.auto()
    bes_fit1 = enum.auto()
    age_uni1 = enum.auto()
    hyp_gal1 = enum.auto()
    age_rac1 = enum.auto()
    age_uni2 = enum.auto()
    age_uni3 = enum.auto()
    age_uni4 = enum.auto()
    you_age1 = enum.auto()
    sho_est1 = enum.auto()
    sho_est2 = enum.auto()


@dataclasses.dataclass
class HubbleSlideshowState:
    step: Reactive[int] = dataclasses.field(default=Reactive(0))
    max_step_completed: Reactive[int] = dataclasses.field(default=Reactive(0))

@dataclasses.dataclass
class ComponentState(BaseComponentState):
    current_step: Reactive[Marker] = dataclasses.field(
        default=Reactive(Marker.exp_dat1)
    )
    hubble_slideshow_dialog: Reactive[bool] = dataclasses.field(default=Reactive(False))
    hubble_slideshow_finished: Reactive[bool] = dataclasses.field(
        default=Reactive(False)
    )
    hubble_slideshow_state: HubbleSlideshowState = dataclasses.field(
        default_factory=HubbleSlideshowState
    )

    def setup(self):
        pass
    
    @computed_property
    def tre_dat2_gate(self):
        return LOCAL_STATE.question_completed("tre-dat-mc1")
    
    @computed_property
    def rel_vel1_gate(self):
        return LOCAL_STATE.question_completed("tre-dat-mc3")
    
    @computed_property
    def hub_exp1_gate(self):
        return LOCAL_STATE.question_completed("galaxy-trend")

    @computed_property
    def tre_lin1_gate(self):
        return (
            bool(self.hubble_slideshow_finished.value)
        )
