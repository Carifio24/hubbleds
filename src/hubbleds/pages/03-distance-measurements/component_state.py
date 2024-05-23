from solara import Reactive
import enum
from ...decorators import computed_property
from ...marker_base import MarkerBase
import dataclasses
from ...data_models.student import student_data


ELEMENT_REST = {
    'H-α': 6562.79,
    'Mg-I': 5176.7
}


class Marker(enum.Enum, MarkerBase):
    ang_siz1 = enum.auto()	
    cho_row1 = enum.auto()	
    ang_siz2 = enum.auto()	
    ang_siz2b = enum.auto()	
    ang_siz3 = enum.auto()	
    ang_siz4 = enum.auto()	
    ang_siz5 = enum.auto()	
    est_dis1 = enum.auto()	
    est_dis2 = enum.auto()	
    cho_row2 = enum.auto()	
    est_dis3 = enum.auto()	
    est_dis4 = enum.auto()	
    dot_seq1 = enum.auto()	
    dot_seq2 = enum.auto()	
    dot_seq3 = enum.auto()	
    dot_seq4 = enum.auto()	
    dot_seq4a = enum.auto()	
    ang_siz5a  = enum.auto()	
    # ang_siz6  = enum.auto() We skipped this in the voila version
    dot_seq5  = enum.auto()	
    dot_seq5a = enum.auto()	
    dot_seq5b = enum.auto()	
    dot_seq5c = enum.auto()	
    dot_seq6  = enum.auto()	
    dot_seq7 = enum.auto()	
    rep_rem1 = enum.auto()	
    fil_rem1 = enum.auto()


@dataclasses.dataclass
class ComponentState:
    current_step: Reactive[Marker] = dataclasses.field(
        default=Reactive(Marker.ang_siz1)
    )
    dosdonts_tutorial_opened: Reactive[bool] = dataclasses.field(
        default=Reactive(False)
    )
    selected_galaxy: Reactive[dict] = dataclasses.field(default=Reactive({}))
    selected_example_galaxy: Reactive[dict] = dataclasses.field(default=Reactive({}))

    def setup(self):
        pass

    def is_current_step(self, step: Marker):
        return self.current_step.value == step

    def can_transition(self, step: Marker=None, next=False, prev=False):
        if next:
            if self.current_step.value is Marker.last():
                return False  # FIX once we sort out transitions between stages
            step = Marker.next(self.current_step.value)
        elif prev:
            if self.current_step.value is Marker.first():
                return False  # FIX once we sort out transitions between stages
            step = Marker.previous(self.current_step.value)

        if hasattr(self, f"{step.name}_gate"):
            return getattr(
                self,
                f"{step.name}_gate",
            )().value

        print(f"No gate exists for step {step.name}, allowing anyway.")
        return True

    def transition_to(self, step: Marker, force=False):
        if self.can_transition(step) or force:
            self.current_step.set(step)
        else:
            print(
                f"Conditions not met to transition from "
                f"{self.current_step.value.name} to {step.name}."
            )

    def transition_next(self):
        next_marker = Marker.next(self.current_step.value)
        self.transition_to(next_marker)

    def transition_previous(self):
        previous_marker = Marker.previous(self.current_step.value)
        self.transition_to(previous_marker, force=True)

    @computed_property
    def dot_seq5_gate(self):
        return (
            bool(self.dosdonts_tutorial_opened.value)
        )
