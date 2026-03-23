"""Berekeningsengine — vertaling van de Excel/TypeScript logica."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .fertilizers import (
    FERT_BY_ID, MOLAR_MASSES, ELEMENT_SPLITS,
    MMOL_TO_PPM, UMOL_TO_PPM, FertilizerDef,
)


@dataclass
class FertResult:
    fert_id: str
    ec_per_liter: float = 0.0
    calc_ec: float = 0.0
    gr_per_l: float = 0.0


@dataclass
class TankConfig:
    capacity: float = 1000.0
    dilution: float = 100.0
    dose: float = 10.0
    entries: Dict[str, float] = field(default_factory=dict)  # fert_id → qty


@dataclass
class WaterAnalysis:
    ec: float = 0.0
    no3: float = 0.0
    k: float = 0.0
    mg: float = 0.0
    ca: float = 0.0
    p2o5: float = 0.0
    s: float = 0.0
    cl: float = 0.0
    fe: float = 0.0
    mn: float = 0.0
    zn: float = 0.0
    b: float = 0.0
    cu: float = 0.0
    mo: float = 0.0


@dataclass
class MmolResult:
    no3: float = 0.0
    h2po4: float = 0.0
    so4: float = 0.0
    nh4: float = 0.0
    k: float = 0.0
    ca: float = 0.0
    mg: float = 0.0
    cl: float = 0.0


@dataclass
class UmolResult:
    fe: float = 0.0
    mn: float = 0.0
    zn: float = 0.0
    b: float = 0.0
    cu: float = 0.0
    mo: float = 0.0


@dataclass
class CalcResults:
    tank_results: Dict[str, List[FertResult]] = field(default_factory=dict)
    total_ec_a: float = 0.0
    total_ec_b: float = 0.0
    total_ec_c: float = 0.0
    total_ec: float = 0.0
    mmol_raw: MmolResult = field(default_factory=MmolResult)
    mmol_scaled: MmolResult = field(default_factory=MmolResult)
    umol_raw: UmolResult = field(default_factory=UmolResult)
    umol_scaled: UmolResult = field(default_factory=UmolResult)
    ppm_mmol: Dict[str, float] = field(default_factory=dict)
    ppm_umol: Dict[str, float] = field(default_factory=dict)
    ratio_nk: float = 0.0
    ratio_kca: float = 0.0
    ratio_mgca: float = 0.0


def _base_key(fert_id: str) -> str:
    """Strip tank suffix: 'potassium-nitrate-a' → 'potassium-nitrate'."""
    return re.sub(r'-[abc]$', '', fert_id)


def calc_fert_ec(fert_id: str, qty: float, tank: TankConfig) -> FertResult:
    """Calculate EC values for a single fertilizer entry."""
    fdef = FERT_BY_ID.get(fert_id)
    if not fdef or qty == 0 or tank.capacity == 0:
        return FertResult(fert_id)

    dose = tank.dose
    ec_per_liter = qty * fdef.ec_value * 1000 / tank.capacity
    calc_ec = ec_per_liter * dose / 1000
    gr_per_l = calc_ec / fdef.ec_value if fdef.ec_value else 0

    if fdef.is_liquid and fdef.liquid_density:
        gr_per_l *= fdef.liquid_density

    return FertResult(fert_id, ec_per_liter, calc_ec, gr_per_l)


def calc_tank(tank: TankConfig) -> List[FertResult]:
    return [calc_fert_ec(fid, qty, tank) for fid, qty in tank.entries.items()]


def calc_mmol(all_results: List[FertResult]) -> MmolResult:
    mmol = MmolResult()
    for r in all_results:
        base = _base_key(r.fert_id)
        molar = MOLAR_MASSES.get(base)
        splits = ELEMENT_SPLITS.get(base)
        if not molar or not splits or r.gr_per_l == 0:
            continue

        if base == 'nitric-acid':
            base_mmol = r.gr_per_l * 0.68 / molar * 1000
        else:
            base_mmol = r.gr_per_l / molar * 1000

        for elem, factor in splits:
            attr = elem.lower()
            if hasattr(mmol, attr):
                setattr(mmol, attr, getattr(mmol, attr) + base_mmol * factor)
    return mmol


def calc_umol(micro_results: List[FertResult]) -> UmolResult:
    umol = UmolResult()
    for r in micro_results:
        fdef = FERT_BY_ID.get(r.fert_id)
        if not fdef or not fdef.molar_mass or r.gr_per_l == 0:
            continue
        val = (r.gr_per_l / fdef.molar_mass) * 1_000_000
        if fdef.id == 'borax':
            val *= 4
        elem = fdef.active_ingredients[0].element.lower() if fdef.active_ingredients else None
        if elem and hasattr(umol, elem):
            setattr(umol, elem, getattr(umol, elem) + val)
    return umol


def scale_mmol(raw: MmolResult, calc_ec: float, desired_ec: float, water: WaterAnalysis) -> MmolResult:
    if calc_ec == 0 or desired_ec == 0:
        return MmolResult(**{k: v for k, v in raw.__dict__.items()})
    r = desired_ec / calc_ec
    return MmolResult(
        no3=r * raw.no3 + water.no3,
        h2po4=r * raw.h2po4 + water.p2o5,
        so4=r * raw.so4 + water.s,
        nh4=r * raw.nh4,
        k=r * raw.k + water.k,
        ca=r * raw.ca + water.ca,
        mg=r * raw.mg + water.mg,
        cl=r * raw.cl + water.cl,
    )


def scale_umol(raw: UmolResult, calc_ec: float, desired_ec: float, water: WaterAnalysis) -> UmolResult:
    if calc_ec == 0 or desired_ec == 0:
        return UmolResult(**{k: v for k, v in raw.__dict__.items()})
    r = desired_ec / calc_ec
    return UmolResult(
        fe=r * raw.fe + water.fe,
        mn=r * raw.mn + water.mn,
        zn=r * raw.zn + water.zn,
        b=r * raw.b + water.b,
        cu=r * raw.cu + water.cu,
        mo=r * raw.mo + water.mo,
    )


def calculate(
    tank_a: TankConfig,
    tank_b: TankConfig,
    tank_c: TankConfig,
    micro: TankConfig,
    desired_ec: float,
    water: WaterAnalysis,
) -> CalcResults:
    res_a = calc_tank(tank_a)
    res_b = calc_tank(tank_b)
    res_c = calc_tank(tank_c)
    res_m = calc_tank(micro)

    ec_a = sum(r.calc_ec for r in res_a)
    ec_b = sum(r.calc_ec for r in res_b)
    ec_c = sum(r.calc_ec for r in res_c)
    ec_total = ec_a + ec_b + ec_c

    mmol_raw = calc_mmol(res_a + res_b + res_c)
    umol_raw = calc_umol(res_m)

    mmol_s = scale_mmol(mmol_raw, ec_total, desired_ec, water)
    umol_s = scale_umol(umol_raw, ec_total, desired_ec, water)

    ppm_m = {k: getattr(mmol_s, k.lower()) * v for k, v in MMOL_TO_PPM.items()}
    ppm_u = {k: getattr(umol_s, k.lower()) * v for k, v in UMOL_TO_PPM.items()}

    total_n = mmol_s.no3 + mmol_s.nh4
    return CalcResults(
        tank_results={'A': res_a, 'B': res_b, 'C': res_c, 'micro': res_m},
        total_ec_a=ec_a, total_ec_b=ec_b, total_ec_c=ec_c, total_ec=ec_total,
        mmol_raw=mmol_raw, mmol_scaled=mmol_s,
        umol_raw=umol_raw, umol_scaled=umol_s,
        ppm_mmol=ppm_m, ppm_umol=ppm_u,
        ratio_nk=total_n / mmol_s.k if mmol_s.k else 0,
        ratio_kca=mmol_s.k / mmol_s.ca if mmol_s.ca else 0,
        ratio_mgca=mmol_s.mg / mmol_s.ca if mmol_s.ca else 0,
    )
