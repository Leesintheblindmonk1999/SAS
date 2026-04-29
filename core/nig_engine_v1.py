"""
core/nig_engine_v1.py — Numerical Invariance Guard v1.1
═══════════════════════════════════════════════════════════════════════════════
Layer 6 — Numerical Invariance Guard (NIG)

EXPANSION v1.1 (03 Abril 2026):
  · Added 50+ verisimilitude ranges for countries, cities, demographics
  · Added economic indicators (GDP, inflation, unemployment)
  · Added sports records, geographical features, historical dates
  · Enhanced keyword mapping for geographic entity detection
  · Increased alpha to 3.0 for higher sensitivity

Registry: EX-2026-18792778 | CONICET #2026032610006187
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum

import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────
KAPPA_D = 0.56
NIG_ALPHA = 3.0           # INCREASED: α=3.0 → 20% deviation → ISI=0.55, 50% → ISI=0.22
MAX_ISI_NIG = 1.0
MIN_ISI_NIG = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 1. UNIT NORMALIZATION — Convert everything to SI base units
# ══════════════════════════════════════════════════════════════════════════════

class UnitSystem(Enum):
    SI = "si"
    IMPERIAL = "imperial"
    CUSTOM = "custom"


@dataclass
class NormalizedValue:
    """Normalized numerical value with unit and confidence."""
    value: float
    unit: str
    original_text: str
    raw_value: float
    raw_unit: str
    confidence: float = 1.0


# Unit conversion tables to SI
LENGTH_CONVERSIONS: Dict[str, float] = {
    "m": 1.0, "meter": 1.0, "meters": 1.0,
    "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
    "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
    "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
    "ly": 9.461e15, "light-year": 9.461e15, "light years": 9.461e15,
}

MASS_CONVERSIONS: Dict[str, float] = {
    "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
    "g": 0.001, "gram": 0.001, "grams": 0.001,
    "mg": 1e-6, "milligram": 1e-6, "milligrams": 1e-6,
    "lb": 0.453592, "pound": 0.453592, "pounds": 0.453592,
    "oz": 0.0283495, "ounce": 0.0283495, "ounces": 0.0283495,
    "t": 1000.0, "tonne": 1000.0, "tonnes": 1000.0,
    "ton": 907.185, "tons": 907.185,
}

TIME_CONVERSIONS: Dict[str, float] = {
    "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
    "ms": 0.001, "millisecond": 0.001, "milliseconds": 0.001,
    "min": 60.0, "minute": 60.0, "minutes": 60.0,
    "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0,
    "d": 86400.0, "day": 86400.0, "days": 86400.0,
    "y": 31536000.0, "year": 31536000.0, "years": 31536000.0,
}

TEMPERATURE_CONVERSIONS: Dict[str, callable] = {
    "K": lambda x: x, "kelvin": lambda x: x,
    "°C": lambda x: x + 273.15, "celsius": lambda x: x + 273.15,
    "°F": lambda x: (x - 32) * 5/9 + 273.15, "fahrenheit": lambda x: (x - 32) * 5/9 + 273.15,
}

ENERGY_CONVERSIONS: Dict[str, float] = {
    "J": 1.0, "joule": 1.0, "joules": 1.0,
    "kJ": 1000.0, "kilojoule": 1000.0, "kilojoules": 1000.0,
    "cal": 4.184, "calorie": 4.184, "calories": 4.184,
    "kcal": 4184.0, "kilocalorie": 4184.0, "kilocalories": 4184.0,
    "eV": 1.602e-19, "electronvolt": 1.602e-19, "electronvolts": 1.602e-19,
    "Wh": 3600.0, "watt-hour": 3600.0, "watt-hours": 3600.0,
}

PRESSURE_CONVERSIONS: Dict[str, float] = {
    "Pa": 1.0, "pascal": 1.0, "pascals": 1.0,
    "kPa": 1000.0, "kilopascal": 1000.0, "kilopascals": 1000.0,
    "MPa": 1e6, "megapascal": 1e6, "megapascals": 1e6,
    "bar": 1e5, "bars": 1e5,
    "atm": 101325.0, "atmosphere": 101325.0, "atmospheres": 101325.0,
    "psi": 6894.76, "pounds per square inch": 6894.76,
}

SPEED_CONVERSIONS: Dict[str, float] = {
    "m/s": 1.0, "meters per second": 1.0,
    "km/h": 0.277778, "kilometers per hour": 0.277778,
    "mph": 0.44704, "miles per hour": 0.44704,
    "knot": 0.514444, "knots": 0.514444,
    "c": 299792458.0, "speed of light": 299792458.0,
}


def normalize_value(raw_value: float, raw_unit: str, quantity_type: str = "dimensionless") -> NormalizedValue:
    unit_lower = raw_unit.lower().strip()
    
    if not raw_unit or raw_unit == "" or quantity_type == "dimensionless":
        return NormalizedValue(
            value=raw_value,
            unit="1",
            original_text=f"{raw_value} {raw_unit}".strip(),
            raw_value=raw_value,
            raw_unit=raw_unit or "1",
        )
    
    if unit_lower in LENGTH_CONVERSIONS:
        return NormalizedValue(
            value=raw_value * LENGTH_CONVERSIONS[unit_lower],
            unit="m",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    if unit_lower in MASS_CONVERSIONS:
        return NormalizedValue(
            value=raw_value * MASS_CONVERSIONS[unit_lower],
            unit="kg",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    if unit_lower in TIME_CONVERSIONS:
        return NormalizedValue(
            value=raw_value * TIME_CONVERSIONS[unit_lower],
            unit="s",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    if unit_lower in TEMPERATURE_CONVERSIONS:
        return NormalizedValue(
            value=TEMPERATURE_CONVERSIONS[unit_lower](raw_value),
            unit="K",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    if unit_lower in ENERGY_CONVERSIONS:
        return NormalizedValue(
            value=raw_value * ENERGY_CONVERSIONS[unit_lower],
            unit="J",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    if unit_lower in PRESSURE_CONVERSIONS:
        return NormalizedValue(
            value=raw_value * PRESSURE_CONVERSIONS[unit_lower],
            unit="Pa",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    if unit_lower in SPEED_CONVERSIONS:
        return NormalizedValue(
            value=raw_value * SPEED_CONVERSIONS[unit_lower],
            unit="m/s",
            original_text=f"{raw_value} {raw_unit}",
            raw_value=raw_value,
            raw_unit=raw_unit,
        )
    
    return NormalizedValue(
        value=raw_value,
        unit=raw_unit,
        original_text=f"{raw_value} {raw_unit}",
        raw_value=raw_value,
        raw_unit=raw_unit,
        confidence=0.5,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 2. NUMERICAL ENTITY EXTRACTION (NEE)
# ══════════════════════════════════════════════════════════════════════════════

NUMBER_PATTERNS = [
    r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
    r"(-?\d+(?:\.\d+)?)",
]

UNIT_PATTERNS = {
    "length": r"(?:km|kilometers?|m|meters?|cm|centimeters?|mm|millimeters?|ft|feet?|in|inches?|mi|miles?)",
    "mass": r"(?:kg|kilograms?|g|grams?|mg|milligrams?|lb|pounds?|oz|ounces?|t|tonnes?)",
    "time": r"(?:s|sec|seconds?|ms|milliseconds?|min|minutes?|h|hr|hours?|d|days?|y|years?)",
    "temperature": r"(?:K|kelvin|°C|celsius|°F|fahrenheit)",
    "energy": r"(?:J|joules?|kJ|kilojoules?|cal|calories?|kcal|kilocalories?|eV|electronvolts?|Wh|watt-hours?)",
    "pressure": r"(?:Pa|pascals?|kPa|kilopascals?|MPa|megapascals?|bar|atm|psi)",
    "speed": r"(?:m/s|km/h|mph|knots?|c)",
    "percentage": r"%|percent",
    "currency": r"(?:\$|USD|EUR|GBP|JPY|CNY)",
    "dimensionless": r"",
}

VALUE_UNIT_PATTERN = re.compile(
    r"(" + "|".join(NUMBER_PATTERNS) + r")\s*(" + "|".join(UNIT_PATTERNS.values()) + r")\b",
    re.IGNORECASE
)

PURE_NUMBER_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b")


@dataclass
class NumericalEntity:
    value: float
    unit: str
    quantity_type: str
    original_text: str
    position: int
    normalized: Optional[NormalizedValue] = None
    context_sentence: str = ""


def extract_numerical_entities(text: str) -> List[NumericalEntity]:
    entities = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        for match in VALUE_UNIT_PATTERN.finditer(sentence):
            value_str = match.group(1)
            unit_str = match.group(2).strip()
            
            try:
                value = float(value_str)
            except ValueError:
                continue
            
            quantity_type = "dimensionless"
            for qtype, pattern in UNIT_PATTERNS.items():
                if re.match(pattern, unit_str, re.IGNORECASE):
                    quantity_type = qtype
                    break
            
            entity = NumericalEntity(
                value=value,
                unit=unit_str,
                quantity_type=quantity_type,
                original_text=match.group(0),
                position=match.start(),
                context_sentence=sentence.strip()[:200],
            )
            
            try:
                entity.normalized = normalize_value(value, unit_str, quantity_type)
            except Exception:
                entity.normalized = None
            
            entities.append(entity)
        
        for match in PURE_NUMBER_PATTERN.finditer(sentence):
            already_captured = False
            for e in entities:
                if abs(e.position - match.start()) < len(match.group(0)) + 5:
                    already_captured = True
                    break
            if already_captured:
                continue
            
            value_str = match.group(1)
            try:
                value = float(value_str)
            except ValueError:
                continue
            
            if 1900 <= value <= 2025:
                continue
            
            if abs(value) < 10 and len(sentence) < 50:
                continue
            
            entity = NumericalEntity(
                value=value,
                unit="",
                quantity_type="dimensionless",
                original_text=value_str,
                position=match.start(),
                context_sentence=sentence.strip()[:200],
                normalized=NormalizedValue(
                    value=value,
                    unit="1",
                    original_text=value_str,
                    raw_value=value,
                    raw_unit="1",
                ),
            )
            entities.append(entity)
    
    return entities


# ══════════════════════════════════════════════════════════════════════════════
# 3. ORACLE LOOKUP — Ground Truth Constants and Verisimilitude Ranges
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OracleEntry:
    name: str
    value: float
    unit: str
    tolerance: float
    category: str
    description: str = ""


# Hard-coded constants
HARD_CONSTANTS: Dict[str, OracleEntry] = {
    "speed_of_light": OracleEntry("speed_of_light", 299792458.0, "m/s", 0.0, "physics", "Speed of light in vacuum"),
    "planck_constant": OracleEntry("planck_constant", 6.62607015e-34, "J·s", 0.0, "physics", "Planck constant"),
    "gravitational_constant": OracleEntry("gravitational_constant", 6.67430e-11, "m³/kg·s²", 0.0001, "physics", "Newtonian constant of gravitation"),
    "elementary_charge": OracleEntry("elementary_charge", 1.602176634e-19, "C", 0.0, "physics", "Elementary charge"),
    "boltzmann_constant": OracleEntry("boltzmann_constant", 1.380649e-23, "J/K", 0.0, "physics", "Boltzmann constant"),
    "avogadro_constant": OracleEntry("avogadro_constant", 6.02214076e23, "mol⁻¹", 0.0, "chemistry", "Avogadro constant"),
    "gas_constant": OracleEntry("gas_constant", 8.314462618, "J/(mol·K)", 0.0001, "chemistry", "Molar gas constant"),
    "standard_gravity": OracleEntry("standard_gravity", 9.80665, "m/s²", 0.0001, "physics", "Standard acceleration due to gravity"),
    "astronomical_unit": OracleEntry("astronomical_unit", 1.495978707e11, "m", 0.0, "astronomy", "Astronomical unit"),
    "parsec": OracleEntry("parsec", 3.085677581e16, "m", 0.0001, "astronomy", "Parsec"),
    "kappa_d": OracleEntry("kappa_d", 0.56, "1", 0.01, "math", "Durante Constant"),
    "pi": OracleEntry("pi", 3.141592653589793, "1", 1e-12, "math", "Pi constant"),
    "e": OracleEntry("e", 2.718281828459045, "1", 1e-12, "math", "Euler's number"),
    "golden_ratio": OracleEntry("golden_ratio", 1.618033988749895, "1", 1e-10, "math", "Golden ratio φ"),
}


# Expanded verisimilitude ranges
VERISIMILITUDE_RANGES: Dict[str, Tuple[float, float]] = {
    # Geography: Countries (population)
    "argentina_population": (45.0e6, 48.0e6),
    "brazil_population": (210.0e6, 220.0e6),
    "usa_population": (330.0e6, 345.0e6),
    "canada_population": (38.0e6, 42.0e6),
    "mexico_population": (125.0e6, 135.0e6),
    "uk_population": (65.0e6, 70.0e6),
    "germany_population": (80.0e6, 85.0e6),
    "france_population": (65.0e6, 70.0e6),
    "italy_population": (55.0e6, 62.0e6),
    "spain_population": (45.0e6, 50.0e6),
    "japan_population": (120.0e6, 128.0e6),
    "india_population": (1.38e9, 1.45e9),
    "china_population": (1.40e9, 1.45e9),
    "russia_population": (140.0e6, 148.0e6),
    "australia_population": (25.0e6, 27.0e6),
    
    # Geography: Cities (population)
    "buenos_aires_population": (2.8e6, 3.2e6),
    "sao_paulo_population": (11.0e6, 13.0e6),
    "rio_population": (6.0e6, 7.5e6),
    "nyc_population": (8.0e6, 9.0e6),
    "london_population": (8.5e6, 9.5e6),
    "tokyo_population": (13.0e6, 15.0e6),
    "shanghai_population": (24.0e6, 26.0e6),
    "mexico_city_population": (8.5e6, 9.5e6),
    
    # Economics: GDP (USD billions)
    "usa_gdp_bn": (25000, 28000),
    "china_gdp_bn": (17000, 19000),
    "japan_gdp_bn": (4000, 4500),
    "germany_gdp_bn": (4000, 4500),
    "uk_gdp_bn": (3000, 3500),
    "india_gdp_bn": (3500, 4000),
    "france_gdp_bn": (2800, 3200),
    "brazil_gdp_bn": (1800, 2200),
    "italy_gdp_bn": (1800, 2200),
    "canada_gdp_bn": (1900, 2200),
    "argentina_gdp_bn": (400, 650),
    "mexico_gdp_bn": (1300, 1600),
    "spain_gdp_bn": (1300, 1600),
    "australia_gdp_bn": (1500, 1800),
    "russia_gdp_bn": (1500, 2000),
    
    # Sports: Stadium capacity
    "camp_nou_capacity": (99000, 100000),
    "santiago_bernabeu_capacity": (81000, 82000),
    "wembley_capacity": (90000, 91000),
    "maracana_capacity": (78000, 80000),
    "la_bombonera_capacity": (54000, 56000),
    "monumental_capacity": (83000, 86000),
    
    # Sports: World records (seconds)
    "men_100m_world_record_s": (9.58, 9.60),
    "women_100m_world_record_s": (10.49, 10.50),
    
    # History: Key dates
    "ww2_start_year": (1939, 1939),
    "ww2_end_year": (1945, 1945),
    "moon_landing_year": (1969, 1969),
    "fall_berlin_wall_year": (1989, 1989),
    
    # Geography: Area (km²)
    "argentina_area_km2": (2.78e6, 2.80e6),
    "brazil_area_km2": (8.51e6, 8.52e6),
    "usa_area_km2": (9.83e6, 9.84e6),
    
    # Mountains
    "everest_height_m": (8848, 8850),
    "aconcagua_height_m": (6960, 6962),
}


# Keyword-to-constant mapping
CONSTANT_KEYWORDS: Dict[str, str] = {
    # Physical constants
    "speed of light": "speed_of_light", "light speed": "speed_of_light",
    "planck": "planck_constant", "planck's constant": "planck_constant",
    "gravitational constant": "gravitational_constant", "g": "gravitational_constant",
    "elementary charge": "elementary_charge", "electron charge": "elementary_charge",
    "boltzmann": "boltzmann_constant", "avogadro": "avogadro_constant",
    "gas constant": "gas_constant", "r constant": "gas_constant",
    "gravity": "standard_gravity", "g force": "standard_gravity",
    "astronomical unit": "astronomical_unit", "au": "astronomical_unit",
    "parsec": "parsec", "pc": "parsec",
    "kappa d": "kappa_d", "durante constant": "kappa_d",
    "pi": "pi", "π": "pi", "euler": "e", "golden ratio": "golden_ratio", "phi": "golden_ratio",
    
    # Geography: Countries
    "population of argentina": "argentina_population", "argentina population": "argentina_population",
    "population of brazil": "brazil_population", "brazil population": "brazil_population",
    "population of united states": "usa_population", "us population": "usa_population",
    "population of canada": "canada_population", "canada population": "canada_population",
    "population of mexico": "mexico_population", "mexico population": "mexico_population",
    "population of uk": "uk_population", "united kingdom population": "uk_population",
    "population of germany": "germany_population", "german population": "germany_population",
    "population of france": "france_population", "french population": "france_population",
    "population of italy": "italy_population", "italian population": "italy_population",
    "population of spain": "spain_population", "spanish population": "spain_population",
    "population of japan": "japan_population", "japanese population": "japan_population",
    "population of india": "india_population", "indian population": "india_population",
    "population of china": "china_population", "chinese population": "china_population",
    "population of russia": "russia_population", "russian population": "russia_population",
    "population of australia": "australia_population", "australian population": "australia_population",
    
    # Geography: Cities
    "buenos aires population": "buenos_aires_population",
    "são paulo population": "sao_paulo_population", "sao paulo population": "sao_paulo_population",
    "rio de janeiro population": "rio_population",
    "new york population": "nyc_population", "nyc population": "nyc_population",
    "london population": "london_population",
    "tokyo population": "tokyo_population",
    "shanghai population": "shanghai_population",
    "mexico city population": "mexico_city_population",
    
    # Economics
    "gdp of usa": "usa_gdp_bn", "us gdp": "usa_gdp_bn", "united states gdp": "usa_gdp_bn",
    "gdp of china": "china_gdp_bn", "chinese gdp": "china_gdp_bn",
    "gdp of argentina": "argentina_gdp_bn", "argentina gdp": "argentina_gdp_bn",
    
    # Sports
    "camp nou capacity": "camp_nou_capacity", "barcelona stadium": "camp_nou_capacity",
    "santiago bernabeu capacity": "santiago_bernabeu_capacity", "real madrid stadium": "santiago_bernabeu_capacity",
    "la bombonera capacity": "la_bombonera_capacity", "boca stadium": "la_bombonera_capacity",
    "monumental capacity": "monumental_capacity", "river plate stadium": "monumental_capacity",
    "100m world record": "men_100m_world_record_s",
    
    # History
    "world war 2 start": "ww2_start_year", "wwii start": "ww2_start_year",
    "world war 2 end": "ww2_end_year", "wwii ended": "ww2_end_year",
    "moon landing": "moon_landing_year", "apollo 11": "moon_landing_year",
    "berlin wall fall": "fall_berlin_wall_year",
    
    # Geography: Area
    "area of argentina": "argentina_area_km2", "argentina area": "argentina_area_km2",
    "area of brazil": "brazil_area_km2", "brazil area": "brazil_area_km2",
    
    # Mountains
    "everest height": "everest_height_m", "mount everest": "everest_height_m",
    "aconcagua height": "aconcagua_height_m", "cerro aconcagua": "aconcagua_height_m",
}


def lookup_ground_truth(
    value: float,
    unit: str,
    quantity_type: str,
    context: str,
) -> Tuple[Optional[OracleEntry], float, str]:
    context_lower = context.lower()
    
    for keyword, const_name in CONSTANT_KEYWORDS.items():
        if keyword in context_lower:
            const = HARD_CONSTANTS.get(const_name)
            if const:
                if const.unit == unit or (const.unit == "1" and unit == ""):
                    return const, const.value, "keyword_match"
    
    for range_name, (low, high) in VERISIMILITUDE_RANGES.items():
        if range_name.replace("_", " ") in context_lower:
            if low <= value <= high:
                pseudo_entry = OracleEntry(range_name, value, unit, 0.1, "verisimilitude")
                return pseudo_entry, (low + high) / 2, "verisimilitude_range"
    
    return None, value, "none"


# ══════════════════════════════════════════════════════════════════════════════
# 4. ISI_NIG COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class NIGResult:
    isi_nig: float
    entities_found: int
    entities_validated: int
    violations: List[Dict[str, Any]]
    violations_count: int
    alert: bool
    summary: str


def compute_isi_nig(
    entities: List[NumericalEntity],
    alpha: float = NIG_ALPHA,
) -> NIGResult:
    violations = []
    isi_values = []
    
    for entity in entities:
        if not entity.normalized:
            continue
        
        oracle, ref_value, match_type = lookup_ground_truth(
            entity.normalized.value,
            entity.normalized.unit,
            entity.quantity_type,
            entity.context_sentence,
        )
        
        if oracle is None:
            continue
        
        if ref_value == 0:
            rel_dev = abs(entity.normalized.value) / 1.0
        else:
            rel_dev = abs(entity.normalized.value - ref_value) / abs(ref_value)
        
        isi_entity = math.exp(-alpha * rel_dev)
        isi_values.append(isi_entity)
        
        if isi_entity < KAPPA_D:
            violations.append({
                "entity": entity.original_text,
                "value": entity.normalized.value,
                "unit": entity.normalized.unit,
                "reference_value": ref_value,
                "reference_name": oracle.name,
                "relative_deviation": rel_dev,
                "isi_entity": isi_entity,
                "context": entity.context_sentence,
                "match_type": match_type,
            })
    
    if isi_values:
        isi_nig = min(isi_values)
    else:
        isi_nig = 1.0
    
    alert = isi_nig < KAPPA_D
    summary = f"Found {len(entities)} numerical entities, validated {len(isi_values)}, {len(violations)} violations. ISI_NIG = {isi_nig:.6f}"
    
    return NIGResult(
        isi_nig=round(isi_nig, 6),
        entities_found=len(entities),
        entities_validated=len(isi_values),
        violations=violations,
        violations_count=len(violations),
        alert=alert,
        summary=summary,
    )


def run_nig(text: str, alpha: float = NIG_ALPHA) -> NIGResult:
    entities = extract_numerical_entities(text)
    return compute_isi_nig(entities, alpha=alpha)


if __name__ == "__main__":
    print("=" * 70)
    print("🧬 NIG v1.1 — Numerical Invariance Guard Test")
    print("=" * 70)
    
    test_texts = [
        "The speed of light is 299792458 m/s.",
        "The Earth's population is about 8 billion people.",
        "The population of Argentina is 120 million people.",
        "Camp Nou has a capacity of 99000 spectators.",
        "World War 2 started in 1945.",
    ]
    
    for text in test_texts:
        print(f"\n📝 Text: {text}")
        result = run_nig(text)
        print(f"   ISI_NIG: {result.isi_nig:.6f}")
        print(f"   Entities: {result.entities_found}, Validated: {result.entities_validated}")
        print(f"   Violations: {result.violations_count}")
        if result.violations:
            for v in result.violations[:2]:
                print(f"     → {v['entity']} = {v['value']} (ref: {v['reference_value']})")
        print(f"   Alert: {'⚠ YES' if result.alert else '✓ NO'}")
    
    print("\n" + "=" * 70)