from pydantic import BaseModel
from typing import Optional, List, Iterable


class SpectrumData(BaseModel):
    name: str
    wave: list[float]
    flux: list[float]
    ivar: list[float]


class GalaxyData(BaseModel):
    id: Optional[str]
    name: Optional[str]
    ra: Optional[float]
    decl: Optional[float]
    z: Optional[float]
    type: Optional[str]
    element: Optional[str]
    spectrum: Optional[SpectrumData] = None
    angular_size: Optional[int] = None
    distance: Optional[float] = None
    measurement_number: Optional[int] = 1


class StudentMeasurement(BaseModel):
    student_id: Optional[int] = 0
    class_id: Optional[int] = 0
    ang_size: Optional[float] = 0
    est_dist: Optional[float] = 0
    rest_wave: Optional[float] = 0.0
    obs_wave: Optional[float] = 0.0
    velocity: Optional[float] = 0.0
    galaxy: Optional[GalaxyData] = None


class StudentData(BaseModel):
    measurements: Optional[List[StudentMeasurement]]

    def update(self, id_: str, data: dict):
        idx = next(
            iter(i for i, x in enumerate(self.measurements) if x.galaxy.id == id_),
            None,
        )

        if idx is None:
            # print(f"No data with id {id_} found.")
            return

        self.measurements[idx] = StudentMeasurement(
            **{**self.measurements[idx].dict(), **data}
        )

    def get_by_galaxy_id(self, id_: str | int, exclude=None):
        idx = next(
            iter(i for i, x in enumerate(self.measurements) if x.galaxy.id == id_),
            None,
        )

        if idx is None:
            # print(f"No data with id {id_} found.")
            return {}

        print(f"Found spectral data with id {id_} at index {idx}.")

        return self.measurements[idx].dict(exclude=exclude)

    def get_spectrum_by_galaxy_id(self, id_: str):
        measurement = self.get_by_galaxy_id(id_)

        return measurement['galaxy']['spectrum']


class MeasurementsData(StudentData):
    measurements: Optional[List[StudentMeasurement]]

    def clear(self):
        if self.measurements:
            self.measurements.clear()

    def update_measurements(self, measurements: List[StudentMeasurement]):
        self.clear()
        self.measurements = measurements

    def get_by_id_and_galaxy(self, student_id: int, galaxy_id: int, exclude=None):
        idx = next(
            iter(i for i, x in enumerate(self.measurements) if x.galaxy.id == galaxy_id and x.student_id == student_id),
            None
        )

        if idx is None:
            return {}

        return self.measurements[idx].dict(exclude=exclude)

    def get_by_student_ids(self, student_ids: Iterable[int]) -> List[StudentMeasurement]:
        if not self.measurements:
            return []
        return [m for m in self.measurements if m.student_id is not None and m.student_id in student_ids]


class Summary(BaseModel):
    id: int
    fit_value: float
    fit_unit: str
    age_value: float
    age_unit: str


class SummaryData(BaseModel):
    summaries: Optional[List[Summary]]


student_data = StudentData(measurements=[])
example_data = StudentData(measurements=[])
class_data = MeasurementsData(measurements=[])
all_data = MeasurementsData(measurements=[])
student_summaries = SummaryData(summaries=[])
class_summaries = SummaryData(summaries=[])
