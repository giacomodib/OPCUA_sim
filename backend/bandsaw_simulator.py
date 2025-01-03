from enum import Enum
import random
from datetime import datetime

# Enum per gli stati della macchina
class MachineState(Enum):
    INACTIVE = "inattiva"
    RUNNING = "in funzione"
    ERROR = "errore"
    ALARM = "allarme"
    PAUSED = "in pausa"
    EMERGENCY_STOP = "arresto emergenza"

# Enum per i tipi di allarmi
class AlarmType(Enum):
    NONE = "nessun allarme"
    HIGH_TEMPERATURE = "temperatura elevata"
    SAFETY_BARRIER = "barriera di sicurezza"
    BLADE_BREAK = "rottura lama"
    COMMUNICATION_ERROR = "errore comunicazione"
    LOW_COOLANT = "livello refrigerante basso"
    MOTOR_OVERLOAD = "sovraccarico motore"

# Dati dei materiali
materials_data = {
    "Acciai al carbonio St 37/42": {
        "tensile_strength": 400,
        "cutting_speeds": {
            "<100mm": (70, 90),
            "100-400mm": (60, 80)
        },
        "feed_rates": {
            "<100mm": (0.4, 0.6),
            "100-400mm": (0.3, 0.5)
        }
    },
    "Acciai da cementazione C10/C15": {
        "tensile_strength": 450,
        "cutting_speeds": {
            "<100mm": (60, 80),
            "100-400mm": (50, 65)
        },
        "feed_rates": {
            "<100mm": (0.35, 0.55),
            "100-400mm": (0.25, 0.45)
        }
    },
    "Ghisa GG30": {
        "tensile_strength": 300,
        "cutting_speeds": {
            "<100mm": (31, 41),
            "100-400mm": (26, 36)
        },
        "feed_rates": {
            "<100mm": (0.3, 0.5),
            "100-400mm": (0.2, 0.4)
        }
    },
    "Alluminio 6003": {
        "tensile_strength": 240,
        "cutting_speeds": {
            "<100mm": (95, 115),
            "100-400mm": (100, 120)
        },
        "feed_rates": {
            "<100mm": (0.6, 0.8),
            "100-400mm": (0.5, 0.7)
        }
    },
    "Leghe al nichel NiCr 19 NbMc": {
        "tensile_strength": 950,
        "cutting_speeds": {
            "<100mm": (10, 13),
            "100-400mm": (9, 12)
        },
        "feed_rates": {
            "<100mm": (0.2, 0.3),
            "100-400mm": (0.15, 0.25)
        }
    }
}

# Funzioni di calcolo

def calculate_cutting_speed(material, section):
    if material in materials_data and section in materials_data[material]["cutting_speeds"]:
        min_speed, max_speed = materials_data[material]["cutting_speeds"][section]
        return (min_speed + max_speed) / 2
    return 0

def calculate_feed_rate(material, section):
    if material in materials_data and section in materials_data[material]["feed_rates"]:
        min_rate, max_rate = materials_data[material]["feed_rates"][section]
        return (min_rate + max_rate) / 2
    return 0.0

def calculate_power(material, cutting_speed, feed_rate):
    BLADE_THICKNESS = 0.9
    TEETH_PER_MM = 0.157
    MECHANICAL_EFFICIENCY = 0.85
    CUTTING_EFFICIENCY = 0.70
    MOTOR_EFFICIENCY = 0.90

    tensile_strength = materials_data[material]["tensile_strength"]
    feed_per_tooth = feed_rate * 60 / (TEETH_PER_MM * cutting_speed)
    theoretical_power = (tensile_strength * BLADE_THICKNESS * feed_per_tooth * cutting_speed) / 60000
    total_efficiency = MECHANICAL_EFFICIENCY * CUTTING_EFFICIENCY * MOTOR_EFFICIENCY
    actual_power = theoretical_power / total_efficiency
    actual_power *= random.uniform(0.95, 1.05)

    return actual_power * 1000

# Simulatore della sega a nastro
class BandSawSimulator:
    def __init__(self):
        self.alarm = AlarmType.NONE
        self.state = MachineState.INACTIVE
        self.pieces = 0
        self.next_pause_at = 15
        self.consumption = 0  # consumo energia
        self.MAX_POWER = 2200.0  # potenza massima motore
        self.error_probability = 0.001
        self.material = "Acciai al carbonio St 37/42"
        self.section = "<100mm"
        self.temperature = 20.0
        self.last_state_change = datetime.now()
        self.cutting_speed = calculate_cutting_speed(self.material, self.section)
        self.feed_rate = calculate_feed_rate(self.material, self.section)

        self.TEMP_NORMAL_MIN = 100
        self.TEMP_NORMAL_MAX = 250
        self.TEMP_WARNING = 350
        self.TEMP_CRITICAL = 600

    def update_temperature(self):
        if self.state == MachineState.RUNNING:
            power_factor = min(1.0, self.consumption / self.MAX_POWER)
            temp_increase = random.uniform(0.3, 0.6) * power_factor

            if self.temperature < self.TEMP_NORMAL_MIN:
                temp_increase *= 2
            elif self.temperature > self.TEMP_NORMAL_MAX:
                temp_increase *= 0.5

            # limite superiore alla temp = 700° C
            self.temperature = min(700, self.temperature + temp_increase)

        else:
            cooling_rate = 0.4 if self.temperature > self.TEMP_WARNING else 0.2
            self.temperature = max(20.0, self.temperature - random.uniform(0.2, cooling_rate))

    def update_consumption(self):
        if self.state == MachineState.RUNNING:
            self.consumption = calculate_power(self.material, self.cutting_speed, self.feed_rate)

            if self.temperature > self.TEMP_WARNING:
                temp_factor = 1 + ((self.temperature - self.TEMP_WARNING) / 250)
                self.consumption *= temp_factor
        else:
            base_consumption = {
                MachineState.INACTIVE: (700, 800),
                MachineState.ERROR: (1900, 2200),
                MachineState.ALARM: (600, 700),
                MachineState.PAUSED: (700, 800)
            }
            range_values = base_consumption[self.state]
            self.consumption = random.uniform(*range_values)

    def update_state(self):
        current_time = datetime.now()
        time_in_state = (current_time - self.last_state_change).total_seconds()

        if self.state == MachineState.PAUSED and time_in_state >= 5:
            self.state = MachineState.RUNNING
            self.last_state_change = current_time
            return

        if self.state == MachineState.RUNNING and self.pieces == self.next_pause_at:
            self.state = MachineState.PAUSED
            self.next_pause_at += 15
            self.last_state_change = current_time
            return

        if self.state == MachineState.RUNNING:
            self.pieces += 1

        self.update_temperature()
        self.update_consumption()

    def high_temperature_alarm(self):
        return self.temperature > self.TEMP_CRITICAL

    def low_coolant_alarm(self):
        return self.temperature < self.TEMP_NORMAL_MIN

    def communication_error_alarm(self):
        return random.random() < self.error_probability

    def blade_break_error(self):
        return random.random() < 0.005

    def motor_overload(self):
        return self.consumption > self.MAX_POWER
