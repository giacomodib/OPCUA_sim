from enum import Enum
from dataclasses import dataclass
import random
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional


class MachineState(Enum):
    INACTIVE = "inattiva"
    RUNNING = "in funzione"
    ERROR = "errore"
    ALARM = "allarme"
    PAUSED = "in pausa"
    EMERGENCY_STOP = "arresto emergenza"
    BREAK_IN = "rodaggio lama"


class AlarmType(Enum):
    NONE = "nessun allarme"
    HIGH_TEMPERATURE = "temperatura elevata"
    HIGH_POWER = "consumo elevato"
    SAFETY_BARRIER = "barriera di sicurezza"
    CONNECTION_ERROR = "errore connessione"
    BLADE_WEAR = "usura lama"
    COOLANT_LOW = "livello refrigerante basso"
    MATERIAL_JAM = "inceppamento materiale"


class SectionType(Enum):
    ROUND = "tondo"
    SQUARE = "quadrato"
    RECTANGULAR = "rettangolare"


@dataclass
class MaterialProperties:
    tensile_strength: float
    hardness: float  # Brinell hardness
    thermal_conductivity: float  # W/(m·K)
    cutting_speeds: Dict[str, Tuple[float, float]]
    feed_rates: Dict[str, Tuple[float, float]]


materials_data = {
    "Acciai al carbonio St 37/42": MaterialProperties(
        tensile_strength=400,
        hardness=120,
        thermal_conductivity=50,
        cutting_speeds={
            "<100mm": (70, 90),
            "100-400mm": (60, 80)
        },
        feed_rates={
            "<100mm": (0.4, 0.6),
            "100-400mm": (0.3, 0.5)
        }
    ),
    "Acciai da cementazione C10/C15": MaterialProperties(
        tensile_strength=450,
        hardness=150,
        thermal_conductivity=45,
        cutting_speeds={
            "<100mm": (60, 80),
            "100-400mm": (50, 65)
        },
        feed_rates={
            "<100mm": (0.35, 0.55),
            "100-400mm": (0.25, 0.45)
        }
    ),
    "Ghisa GG30": MaterialProperties(
        tensile_strength=300,
        hardness=200,
        thermal_conductivity=40,
        cutting_speeds={
            "<100mm": (31, 41),
            "100-400mm": (26, 36)
        },
        feed_rates={
            "<100mm": (0.3, 0.5),
            "100-400mm": (0.2, 0.4)
        }
    ),
    "Alluminio 6003": MaterialProperties(
        tensile_strength=240,
        hardness=80,
        thermal_conductivity=180,
        cutting_speeds={
            "<100mm": (95, 115),
            "100-400mm": (100, 120)
        },
        feed_rates={
            "<100mm": (0.6, 0.8),
            "100-400mm": (0.5, 0.7)
        }
    ),
    "Leghe al nichel NiCr 19 NbMc": MaterialProperties(
        tensile_strength=950,
        hardness=250,
        thermal_conductivity=15,
        cutting_speeds={
            "<100mm": (10, 13),
            "100-400mm": (9, 12)
        },
        feed_rates={
            "<100mm": (0.2, 0.3),
            "100-400mm": (0.15, 0.25)
        }
    )
}


class BandSawSimulator:
    def __init__(self):
        # Machine state
        self.state = MachineState.INACTIVE
        self.alarm = AlarmType.NONE
        self.last_state_change = datetime.now()
        self.last_maintenance = datetime.now()

        # Production metrics
        self.pieces = 0
        self.scrap_pieces = 0
        self.total_pieces_attempted = 0
        self.pieces_per_hour = 0
        self.last_piece_time = None
        self.next_pause_at = 15

        # Machine parameters
        self.material = "Acciai al carbonio St 37/42"
        self.section = "<100mm"
        self.section_type = SectionType.ROUND
        self.cutting_angle = 0
        self.cutting_speed = 0.0
        self.feed_rate = 0.0
        self.recommended_cutting_speed = 0.0
        self.recommended_feed_rate = 0.0

        # Machine health
        self.temperature = 20.0
        self.consumption = 0
        self.blade_wear = 0.0
        self.coolant_level = 100.0
        self.break_in_pieces = 0

        # Constants
        self.MAX_POWER = 3000
        self.TEMP_NORMAL_MIN = 100
        self.TEMP_NORMAL_MAX = 250
        self.TEMP_WARNING = 350
        self.TEMP_CRITICAL = 600

        # Performance tracking
        self.start_time = datetime.now()
        self.downtime = timedelta()

        self.update_recommended_parameters()

    def update_recommended_parameters(self):
        """Calculate recommended cutting parameters based on current settings"""
        material_props = materials_data[self.material]
        base_speed_range = material_props.cutting_speeds[self.section]
        base_feed_range = material_props.feed_rates[self.section]

        # Section type adjustments
        section_factors = {
            SectionType.ROUND: 1.0,
            SectionType.SQUARE: 0.9,
            SectionType.RECTANGULAR: 0.85
        }

        angle_factor = max(0.7, 1.0 - (self.cutting_angle / 90) * 0.3)

        final_factor = section_factors[self.section_type] * angle_factor
        self.recommended_cutting_speed = ((base_speed_range[0] + base_speed_range[1]) / 2) * final_factor
        self.recommended_feed_rate = ((base_feed_range[0] + base_feed_range[1]) / 2) * final_factor

    def calculate_power_consumption(self) -> float:
        """Calculate power consumption based on current parameters"""
        material_props = materials_data[self.material]

        base_power = (material_props.tensile_strength * self.cutting_speed * self.feed_rate) / 1000

        # Adjustments based on conditions
        temp_factor = 1.0 + max(0, (self.temperature - self.TEMP_NORMAL_MAX) / self.TEMP_NORMAL_MAX) * 0.3
        wear_factor = 1.0 + (self.blade_wear / 100) * 0.2
        angle_factor = 1.0 + (self.cutting_angle / 45) * 0.15

        # Random variation (±5%)
        variation = random.uniform(0.95, 1.05)

        return base_power * temp_factor * wear_factor * angle_factor * variation

    def update_temperature(self):
        """Update machine temperature based on operating conditions"""
        if self.state == MachineState.RUNNING:
            # Calculate temperature increase based on multiple factors
            power_factor = min(1.0, self.consumption / self.MAX_POWER)
            material_cooling = materials_data[self.material].thermal_conductivity / 100
            coolant_efficiency = self.coolant_level / 100

            base_increase = random.uniform(0.3, 0.6) * power_factor
            cooling_effect = material_cooling * coolant_efficiency

            net_change = base_increase - cooling_effect

            # Apply temperature change with limits
            self.temperature = min(700, max(20, self.temperature + net_change))
        else:
            # Cooling when not running
            cooling_rate = 0.4 if self.temperature > self.TEMP_WARNING else 0.2
            self.temperature = max(20.0, self.temperature - random.uniform(0.2, cooling_rate))

    def process_piece(self):
        """Process a single piece and determine quality outcome"""
        self.total_pieces_attempted += 1

        # Base error probability
        error_prob = 0.05

        # Parameter deviation effects
        speed_dev = abs(self.cutting_speed - self.recommended_cutting_speed) / self.recommended_cutting_speed
        feed_dev = abs(self.feed_rate - self.recommended_feed_rate) / self.recommended_feed_rate
        param_error = (speed_dev + feed_dev) * 0.2

        # Machine condition effects
        condition_error = (
                (self.blade_wear / 100) * 0.3 +
                (1 - self.coolant_level / 100) * 0.2 +
                max(0, (self.temperature - self.TEMP_NORMAL_MAX) / self.TEMP_CRITICAL) * 0.3
        )

        # Material and angle effects
        material_difficulty = materials_data[self.material].hardness / 250  # Normalize to ~1
        angle_difficulty = self.cutting_angle / 90

        total_error_prob = min(0.95, error_prob + param_error + condition_error +
                               (material_difficulty * 0.1) + (angle_difficulty * 0.1))

        # Determine piece outcome
        if random.random() < total_error_prob:
            self.scrap_pieces += 1
        else:
            self.pieces += 1

        # Update production rate metrics
        current_time = datetime.now()
        if self.last_piece_time:
            time_diff = (current_time - self.last_piece_time).total_seconds() / 3600
            self.pieces_per_hour = 1 / time_diff if time_diff > 0 else 0
        self.last_piece_time = current_time

    def update_state(self):
        """Main update function for machine state and parameters"""
        current_time = datetime.now()
        time_in_state = (current_time - self.last_state_change).total_seconds()

        if self.check_alarms():
            return

        # Handle different machine states
        if self.state == MachineState.RUNNING:
            self.update_wear()
            self.process_piece()
            if self.pieces == self.next_pause_at:
                self.state = MachineState.PAUSED
                self.next_pause_at += 15
                self.last_state_change = current_time

        elif self.state == MachineState.PAUSED and time_in_state >= 5:
            self.state = MachineState.RUNNING
            self.last_state_change = current_time

        elif self.state == MachineState.BREAK_IN:
            self.handle_break_in()

        self.update_temperature()
        self.consumption = self.calculate_power_consumption()

    def update_wear(self):
        """Update wear-related parameters during operation"""
        wear_factor = (
                              abs(self.cutting_speed - self.recommended_cutting_speed) / self.recommended_cutting_speed +
                              abs(self.feed_rate - self.recommended_feed_rate) / self.recommended_feed_rate
                      ) / 2
        base_wear = random.uniform(0.01, 0.03)
        material_wear = materials_data[self.material].hardness / 1000
        self.blade_wear = min(100, self.blade_wear + (base_wear * (1 + wear_factor) * (1 + material_wear)))

        coolant_use = random.uniform(0.02, 0.05) * (self.temperature / self.TEMP_NORMAL_MAX)
        self.coolant_level = max(0, self.coolant_level - coolant_use)

    def check_alarms(self) -> bool:
        """Check for alarm conditions"""
        if self.state != MachineState.ALARM:
            if self.temperature > self.TEMP_CRITICAL:
                self.set_alarm(AlarmType.HIGH_TEMPERATURE)
                return True
            elif self.consumption > self.MAX_POWER * 1.1:
                self.set_alarm(AlarmType.HIGH_POWER)
                return True
            elif self.blade_wear >= 90:
                self.set_alarm(AlarmType.BLADE_WEAR)
                return True
            elif self.coolant_level <= 10:
                self.set_alarm(AlarmType.COOLANT_LOW)
                return True
            elif random.random() < 0.001:  # Random material jam
                self.set_alarm(AlarmType.MATERIAL_JAM)
                return True
        return False

    def handle_break_in(self):
        """Handle blade break-in process"""
        if self.break_in_pieces < 5:
            self.cutting_speed = self.recommended_cutting_speed * 0.7
            self.feed_rate = self.recommended_feed_rate * 0.6
            self.process_piece()
            self.break_in_pieces += 1
        else:
            self.state = MachineState.INACTIVE
            self.break_in_pieces = 0
            self.blade_wear = 0.0

    def calculate_oee(self) -> Dict[str, float]:
        """Calculate Overall Equipment Effectiveness metrics"""
        current_time = datetime.now()
        total_time = (current_time - self.start_time).total_seconds() / 3600

        # Availability
        planned_production_time = total_time - (self.downtime.total_seconds() / 3600)
        availability = (planned_production_time / total_time) if total_time > 0 else 0

        # Performance
        ideal_cycle_time = 60 / self.recommended_feed_rate if self.recommended_feed_rate > 0 else 0
        theoretical_output = (planned_production_time * 3600) / ideal_cycle_time if ideal_cycle_time > 0 else 0
        performance = (self.pieces / theoretical_output) if theoretical_output > 0 else 0

        # Quality
        quality = ((self.pieces - self.scrap_pieces) / self.total_pieces_attempted
                   if self.total_pieces_attempted > 0 else 1)

        return {
            "availability": availability * 100,
            "performance": performance * 100,
            "quality": quality * 100,
            "oee": (availability * performance * quality) * 100
        }

    def set_alarm(self, alarm_type: AlarmType):
        """Set alarm state"""
        self.alarm = alarm_type
        self.state = MachineState.ALARM
        self.last_state_change = datetime.now()

    def reset_alarm(self):
            """Reset alarm state and return to inactive state"""
            self.alarm = AlarmType.NONE
            self.state = MachineState.INACTIVE
            self.last_state_change = datetime.now()

    def perform_maintenance(self):
            """Perform maintenance tasks and reset wear indicators"""
            self.blade_wear = 0.0
            self.coolant_level = 100.0
            self.last_maintenance = datetime.now()
            self.temperature = 20.0
            self.reset_alarm()
            return True

    def set_cutting_parameters(self, cutting_speed: Optional[float] = None,
                                   feed_rate: Optional[float] = None,
                                   cutting_angle: Optional[float] = None):
            """Set custom cutting parameters with validation"""
            if cutting_speed is not None:
                # Allow ±20% from recommended speed
                min_speed = self.recommended_cutting_speed * 0.8
                max_speed = self.recommended_cutting_speed * 1.2
                self.cutting_speed = max(min_speed, min(max_speed, cutting_speed))

            if feed_rate is not None:
                # Allow ±20% from recommended feed rate
                min_feed = self.recommended_feed_rate * 0.8
                max_feed = self.recommended_feed_rate * 1.2
                self.feed_rate = max(min_feed, min(max_feed, feed_rate))

            if cutting_angle is not None:
                # Validate angle (0°, 45°, 60°)
                valid_angles = [0, 45, 60]
                self.cutting_angle = min(valid_angles, key=lambda x: abs(x - cutting_angle))

            # Update recommended parameters after changes
            self.update_recommended_parameters()
            return True

    def set_material_parameters(self, material: Optional[str] = None,
                                    section: Optional[str] = None,
                                    section_type: Optional[SectionType] = None):
            """Set material and section parameters"""
            if material and material in materials_data:
                self.material = material

            if section and section in ["<100mm", "100-400mm"]:
                self.section = section

            if section_type and isinstance(section_type, SectionType):
                self.section_type = section_type

            self.update_recommended_parameters()
            return True

    def start_break_in(self):
            """Start blade break-in procedure"""
            if self.state == MachineState.INACTIVE and self.alarm == AlarmType.NONE:
                self.state = MachineState.BREAK_IN
                self.break_in_pieces = 0
                self.blade_wear = 0.0
                self.last_state_change = datetime.now()
                return True
            return False

    def get_machine_status(self) -> Dict:
            """Get comprehensive machine status report"""
            return {
                "operational_status": {
                    "state": self.state.value,
                    "alarm_type": self.alarm.value,
                    "running_since": self.last_state_change.isoformat(),
                    "last_maintenance": self.last_maintenance.isoformat()
                },
                "production_metrics": {
                    "total_pieces": self.pieces,
                    "scrap_pieces": self.scrap_pieces,
                    "quality_rate": ((self.pieces - self.scrap_pieces) / self.total_pieces_attempted * 100)
                    if self.total_pieces_attempted > 0 else 100,
                    "pieces_per_hour": self.pieces_per_hour
                },
                "machine_health": {
                    "temperature": round(self.temperature, 1),
                    "blade_wear_percentage": round(self.blade_wear, 1),
                    "coolant_level_percentage": round(self.coolant_level, 1),
                    "power_consumption": round(self.consumption, 2)
                },
                "cutting_parameters": {
                    "material": self.material,
                    "section": self.section,
                    "section_type": self.section_type.value,
                    "cutting_angle": self.cutting_angle,
                    "current_speed": round(self.cutting_speed, 1),
                    "recommended_speed": round(self.recommended_cutting_speed, 1),
                    "current_feed_rate": round(self.feed_rate, 2),
                    "recommended_feed_rate": round(self.recommended_feed_rate, 2)
                },
                "performance_metrics": self.calculate_oee()
            }

    def get_material_recommendations(self) -> Dict:
            """Get recommended parameters for current material setup"""
            material_props = materials_data[self.material]
            return {
                "material_properties": {
                    "tensile_strength": material_props.tensile_strength,
                    "hardness": material_props.hardness,
                    "thermal_conductivity": material_props.thermal_conductivity
                },
                "recommended_parameters": {
                    "cutting_speed": round(self.recommended_cutting_speed, 1),
                    "feed_rate": round(self.recommended_feed_rate, 2),
                    "speed_range": material_props.cutting_speeds[self.section],
                    "feed_range": material_props.feed_rates[self.section]
                },
                "current_deviations": {
                    "speed_deviation_percent": round(((self.cutting_speed - self.recommended_cutting_speed) /
                                                      self.recommended_cutting_speed * 100), 1),
                    "feed_deviation_percent": round(((self.feed_rate - self.recommended_feed_rate) /
                                                     self.recommended_feed_rate * 100), 1)
                }
            }

