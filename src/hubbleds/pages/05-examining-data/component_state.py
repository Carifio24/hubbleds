import dataclasses
from hubbleds.decorators import computed_property
from solara import Reactive
import enum

__all__ = ["Marker", "ComponentState"]

class Marker(enum.Enum):
    ran_var1 = enum.auto()
    fin_cla1 = enum.auto()
    cla_res1 = enum.auto()
    rel_age1 = enum.auto()
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
    two_his2 = enum.auto()
    two_his3 = enum.auto()
    two_his3a = enum.auto()
    two_his5 = enum.auto()
    mor_dat1 = enum.auto()

    @staticmethod
    def next(step):
        return Marker(step.value + 1)
    
    @staticmethod
    def previous(step):
        return Marker(step.value - 1)


@dataclasses.dataclass
class UncertaintyState:
    step: Reactive[int] = dataclasses.field(default=Reactive(0))
    length: Reactive[int] = dataclasses.field(default=Reactive(10))
    titles: Reactive[list] = dataclasses.field(
        default=Reactive(
            [
                'What is the true age of the universe?',
                "Shortcomings in our measurements",
                "Shortcomings in our measurements",
                "Messiness in our distance measurements",
                "Uncertainty",            
                "Random Uncertainty (Noise)",
                "Systematic Uncertainty (Bias)",
                "Causes of Systematic Uncertainty",
                "Systematic Uncertainty",
                "Finished Uncertainty Tutorial",
            ]
        )
    )


@dataclasses.dataclass
class MMMState:
    step: Reactive[int] = dataclasses.field(default=Reactive(0))
    length: Reactive[int] = dataclasses.field(default=Reactive(3))
    titles: Reactive[list] = dataclasses.field(
        default=Reactive(
            [
                "Mean",
                "Median",
                "Mode",
            ]
        )
    )


@dataclasses.dataclass
class AgeCalcState:
    hint1_dialog: Reactive[bool] = dataclasses.field(default=Reactive(False))
    hint2_dialog: Reactive[bool] = dataclasses.field(default=Reactive(False))
    hint3_dialog: Reactive[bool] = dataclasses.field(default=Reactive(False))
    best_guess: Reactive[str] = dataclasses.field(default=Reactive(""))
    low_guess: Reactive[str] = dataclasses.field(default=Reactive(""))
    high_guess: Reactive[str] = dataclasses.field(default=Reactive(""))
    short_one: Reactive[str] = dataclasses.field(default=Reactive(""))
    short_two: Reactive[str] = dataclasses.field(default=Reactive(""))
    short_other: Reactive[str] = dataclasses.field(default=Reactive(""))


@dataclasses.dataclass
class ComponentState:
    current_step: Reactive[Marker] = dataclasses.field(default=Reactive(Marker.ran_var1))

    def is_current_step(self, step: Marker):
        print(step, self.current_step.value == step)
        return self.current_step.value == step

    def can_transition(self, step: Marker=None, next=False, prev=False):
        if next:
            step = Marker.next(self.current_step.value)
        elif prev:
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
    def ran_var1_gate(self):
        return True

    @computed_property
    def fin_cla1_gate(self):
        return True
    
