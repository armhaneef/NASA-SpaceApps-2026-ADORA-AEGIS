"""Numeric MVP validation rules; these are not clinical alert thresholds."""

from datetime import timezone
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field
from pydantic import StrictBool, StringConstraints, model_validator

from app.schemas.astronaut import Identifier

# Accepted labels are preserved, not silently converted. Extend with team agreement.
MEASUREMENTS = {
    "heart_rate": ({"beats/min", "bpm"}, 0, None),
    "spo2": ({"%"}, 0, 100),
    "temperature": ({"degC"}, None, None),
    "skin_temperature": ({"degC"}, None, None),
    "respiration_rate": ({"breaths/min"}, 0, None),
    "co2": ({"ppm"}, 0, None),
    "humidity": ({"%"}, 0, 100),
    "sleep_duration": ({"h", "min"}, 0, None),
    "activity_steps": ({"steps"}, 0, None),
    "radiation_dose": ({"mSv", "uSv"}, 0, None),
}
Timestamp = Annotated[AwareDatetime, AfterValidator(lambda value: value.astimezone(timezone.utc))]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Source = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    astronaut_id: Identifier
    timestamp: Timestamp
    sensor_type: Label
    is_simulated: StrictBool
    quality: Label | None = None


class SensorCreate(Provenance):
    measurement_type: Label
    value: Number
    unit: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    source: Source

    @model_validator(mode="after")
    def validate_measurement(self):
        if self.measurement_type not in MEASUREMENTS:
            raise ValueError(f"Unsupported measurement_type: {self.measurement_type}")
        units, minimum, maximum = MEASUREMENTS[self.measurement_type]
        if self.unit not in units:
            raise ValueError(f"Unit for {self.measurement_type} must be one of {sorted(units)}")
        if minimum is not None and self.value < minimum:
            raise ValueError("Value is below the measurement's numeric domain")
        if maximum is not None and self.value > maximum:
            raise ValueError("Value is above the measurement's numeric domain")
        return self


class Measurement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Number
    unit: str


class GroupedReading(Provenance):
    """Shared grouped fields, enriched with explicit provenance metadata."""

    data_source: Source
    heart_rate: Measurement | None = None
    spo2: Measurement | None = None
    temperature: Measurement | None = None
    skin_temperature: Measurement | None = None
    respiration_rate: Measurement | None = None
    co2: Measurement | None = None

    @model_validator(mode="after")
    def validate_readings(self):
        if any(key in self.model_fields_set and getattr(self, key) is None
               for key in self.measurement_fields()):
            raise ValueError("Omit absent measurements rather than submitting null")
        if not any(getattr(self, key) is not None for key in self.measurement_fields()):
            raise ValueError("Provide at least one measurement")
        self.to_readings()
        return self

    @staticmethod
    def measurement_fields():
        return (
            "heart_rate", "spo2", "temperature", "skin_temperature",
            "respiration_rate", "co2",
        )

    def to_readings(self) -> list[SensorCreate]:
        common = self.model_dump(include=set(Provenance.model_fields))
        return [
            SensorCreate(**common, source=self.data_source, measurement_type=key,
                         **getattr(self, key).model_dump())
            for key in self.measurement_fields() if getattr(self, key) is not None
        ]


class SensorRead(SensorCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
