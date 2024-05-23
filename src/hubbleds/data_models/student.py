from pydantic import BaseModel
from typing import Optional, List


class SpectrumData(BaseModel):
    name: str
    wave: list[float]
    flux: list[float]
    ivar: list[float]


class StudentMeasurement(BaseModel):
    id: Optional[str]
    name: Optional[str]
    ra: Optional[float]
    decl: Optional[float]
    z: Optional[float]
    type: Optional[str]
    element: Optional[str]
    rest_wave: Optional[float] = 0.0
    measured_wave: Optional[float] = 0.0
    velocity: Optional[float] = 0.0
    spectrum: Optional[SpectrumData] = None
    angular_size: Optional[float] = 0.0
    distance: Optional[float] = 0.0
    measurement_number: Optional[int] = 0


class StudentData(BaseModel):
    measurements: Optional[List[StudentMeasurement]]

    def update(self, id_: str, data: dict):
        idx = next(i for i, x in enumerate(self.measurements) if x.id == id_)

        if idx is None:
            print(f"No data with id {id_} found.")

        self.measurements[idx] = StudentMeasurement(**{**self.measurements[idx].dict(), **data})


student_data = StudentData(measurements=[])
example_data = StudentData(measurements=[])
