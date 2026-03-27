"""Meststof-definities en conversieconstanten."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ActiveIngredient:
    element: str   # e.g. 'Ca', 'N', 'K', 'Fe'
    percentage: float  # 0-1 fraction


@dataclass
class FertilizerDef:
    id: str
    name: str
    tank: str  # 'A', 'B', 'C', 'micro'
    active_ingredients: List[ActiveIngredient] = field(default_factory=list)
    ec_value: float = 1.0
    molar_mass: Optional[float] = None  # For micro element umol calc
    unit: str = 'kg'  # 'kg' or 'liter'
    is_liquid: bool = False
    liquid_density: float = 1.0


# === All fertilizer definitions ===

FERTILIZERS: List[FertilizerDef] = [
    # TANK A
    FertilizerDef('calcium-nitrate', 'Calcium Nitrate', 'A',
        [ActiveIngredient('Ca', 0.19), ActiveIngredient('N', 0.155)], 1.24),
    FertilizerDef('calcium-chloride', 'Calciumchloride', 'A',
        [ActiveIngredient('Ca', 0.39), ActiveIngredient('Cl', 0.45)], 1.41),
    FertilizerDef('potassium-chloride', 'Potassiumchloride', 'A',
        [ActiveIngredient('K', 0.60), ActiveIngredient('Cl', 0.474)], 1.41),
    FertilizerDef('potassium-nitrate-a', 'Potassium Nitrate', 'A',
        [ActiveIngredient('K', 0.46), ActiveIngredient('N', 0.13)], 1.35),
    FertilizerDef('magnesium-nitrate-a', 'Magnesium Nitrate', 'A',
        [ActiveIngredient('Mg', 0.095)], 0.87),
    FertilizerDef('magnesium-nitrate-liquid-a', 'Magnesium Nitrate (vlb)', 'A',
        [ActiveIngredient('Mg', 0.06), ActiveIngredient('N', 0.07)], 0.50,
        unit='liter', is_liquid=True, liquid_density=1.35),
    FertilizerDef('ammonium-nitrate-a', 'Ammonium Nitrate', 'A',
        [ActiveIngredient('N', 0.35)], 1.60),
    FertilizerDef('nitric-acid-a', 'Nitric Acid 68%', 'A',
        [ActiveIngredient('N', 0.14)], 0.68),

    # TANK B
    FertilizerDef('mono-potassium-phosphate', 'Mono Potassium Phosphate', 'B',
        [ActiveIngredient('K', 0.34), ActiveIngredient('P', 0.52)], 0.68),
    FertilizerDef('mono-ammonium-phosphate', 'Mono Ammonium Phosphate', 'B',
        [ActiveIngredient('N', 0.12), ActiveIngredient('P', 0.59)], 0.86),
    FertilizerDef('ammonium-nitrate-b', 'Ammonium Nitrate', 'B',
        [ActiveIngredient('N', 0.35)], 1.60),
    FertilizerDef('ammonium-sulfate', 'Ammonium Sulfate', 'B',
        [ActiveIngredient('N', 0.21), ActiveIngredient('S', 0.242)], 1.90),
    FertilizerDef('magnesium-nitrate-b', 'Magnesium Nitrate', 'B',
        [ActiveIngredient('Mg', 0.095), ActiveIngredient('N', 0.105)], 0.87),
    FertilizerDef('magnesium-nitrate-liquid-b', 'Magnesium Nitrate (vlb)', 'B',
        [ActiveIngredient('Mg', 0.06), ActiveIngredient('N', 0.07)], 0.50,
        unit='liter', is_liquid=True, liquid_density=1.35),
    FertilizerDef('magnesium-sulfate', 'Magnesium Sulfate', 'B',
        [ActiveIngredient('Mg', 0.097), ActiveIngredient('S', 0.13)], 0.94),
    FertilizerDef('potassium-nitrate-b', 'Potassium Nitrate', 'B',
        [ActiveIngredient('K', 0.46), ActiveIngredient('N', 0.13)], 1.35),
    FertilizerDef('potassium-sulfate', 'Potassium Sulfate', 'B',
        [ActiveIngredient('N', 0.13)], 1.54),
    FertilizerDef('nitric-acid-b', 'Nitric Acid 68%', 'B',
        [ActiveIngredient('N', 0.14)], 0.68),

    # TANK C
    FertilizerDef('nitric-acid-c', 'Nitric Acid 68%', 'C',
        [ActiveIngredient('N', 0.14)], 0.68),
    FertilizerDef('mono-potassium-phosphate-c', 'Mono Potassium Phosphate', 'C',
        [ActiveIngredient('K', 0.34), ActiveIngredient('P', 0.52)], 0.68),

    # MICRO
    FertilizerDef('manganese-sulphate', 'Manganese Sulphate', 'micro',
        [ActiveIngredient('Mn', 0.325)], 1.0, molar_mass=169),
    FertilizerDef('zinc-sulphate', 'Zinc Sulphate', 'micro',
        [ActiveIngredient('Zn', 0.227)], 1.0, molar_mass=288),
    FertilizerDef('borax', 'Borax', 'micro',
        [ActiveIngredient('B', 0.113)], 1.0, molar_mass=380),
    FertilizerDef('copper-sulphate', 'Copper Sulphate', 'micro',
        [ActiveIngredient('Cu', 0.254)], 1.0, molar_mass=250),
    FertilizerDef('sodium-molybdate', 'Sodium Molybdate', 'micro',
        [ActiveIngredient('Mo', 0.396)], 1.0, molar_mass=242),
    FertilizerDef('fe-dtpa-11', 'Fe-chelate 11% DTPA', 'micro',
        [ActiveIngredient('Fe', 0.11)], 1.0, molar_mass=468.15),
    FertilizerDef('fe-eddha-6', 'Fe-chelate 6% EDDHA', 'micro',
        [ActiveIngredient('Fe', 0.06)], 1.35, molar_mass=1118),
    FertilizerDef('fe-dtpa-3-liquid', 'Fe-chelate 3% DTPA (vlb)', 'micro',
        [ActiveIngredient('Fe', 0.03)], 1.0, molar_mass=1863,
        unit='liter', is_liquid=True),
]

FERT_BY_ID = {f.id: f for f in FERTILIZERS}

# Recommended umol values
RECOMMENDED_UMOL = {'Mn': 5, 'Zn': 3, 'B': 10, 'Cu': 0.5, 'Mo': 0.5, 'Fe': 15}

# mmol->ppm factors (Na added)
MMOL_TO_PPM = {
    'NO3': 14, 'NH4': 18.038, 'K': 39.102, 'Ca': 40.08,
    'Mg': 24.31, 'H2PO4': 97, 'SO4': 96, 'Cl': 35.453, 'Na': 22.99,
}

# umol->ppm factors
UMOL_TO_PPM = {'Fe': 0.056, 'Mn': 0.055, 'Zn': 0.065, 'B': 0.011, 'Cu': 0.064, 'Mo': 0.096}

# Molar masses for mmol conversion
MOLAR_MASSES = {
    'calcium-nitrate': 216, 'calcium-chloride': 147, 'potassium-chloride': 74.55,
    'potassium-nitrate': 101.1, 'potassium-sulfate': 174.3,
    'mono-potassium-phosphate': 136.1, 'mono-ammonium-phosphate': 115,
    'ammonium-nitrate': 80, 'ammonium-sulfate': 132.1,
    'magnesium-nitrate': 256.3, 'magnesium-nitrate-liquid': 400,
    'magnesium-sulfate': 246.4, 'nitric-acid': 63,
}

# Element split factors per fertilizer (mmol distribution)
ELEMENT_SPLITS = {
    'calcium-nitrate': [('NO3', 2.2), ('NH4', 0.2), ('Ca', 1.0)],
    'calcium-chloride': [('Ca', 1.0), ('Cl', 2.0)],
    'potassium-chloride': [('K', 1.0), ('Cl', 1.0)],
    'potassium-nitrate': [('NO3', 1.0), ('K', 1.0)],
    'potassium-sulfate': [('SO4', 1.0), ('K', 2.0)],
    'mono-potassium-phosphate': [('H2PO4', 1.0), ('K', 1.0)],
    'mono-ammonium-phosphate': [('H2PO4', 1.0), ('NH4', 1.0)],
    'ammonium-nitrate': [('NO3', 1.0), ('NH4', 1.0)],
    'ammonium-sulfate': [('SO4', 1.0), ('NH4', 2.0)],
    'magnesium-nitrate': [('NO3', 2.0), ('Mg', 1.0)],
    'magnesium-nitrate-liquid': [('NO3', 2.0), ('Mg', 1.0)],
    'magnesium-sulfate': [('SO4', 1.0), ('Mg', 1.0)],
    'nitric-acid': [('NO3', 1.0)],
}
