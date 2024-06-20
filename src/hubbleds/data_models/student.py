from pydantic import BaseModel
from typing import Optional, List


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


class ClassMeasurement(StudentMeasurement):
    student_id: int


class ClassData(StudentData):
    measurements: Optional[List[ClassMeasurement]]

    def clear(self):
        if self.measurements:
            self.measurements.clear()

    def update_measurements(self, measurements: List[ClassMeasurement]):
        self.clear()
        self.measurements = measurements


student_data = StudentData(measurements=[])
example_data = StudentData(measurements=[])
class_data = ClassData(measurements=[])
