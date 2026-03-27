"""Berekeningsengine — volledig gelijk aan web versie (recirculatie, Na, auto-dilution, targets)."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .fertilizers import (
    FERT_BY_ID, MOLAR_MASSES, ELEMENT_SPLITS,
    MMOL_TO_PPM, UMOL_TO_PPM, FertilizerDef,
)

FE_IDS = {'fe-dtpa-11', 'fe-eddha-6', 'fe-dtpa-3-liquid'}


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
    entries: Dict[str, float] = field(default_factory=dict)  # fert_id -> qty


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
    na: float = 0.0
    fe: float = 0.0
    mn: float = 0.0
    zn: float = 0.0
    b: float = 0.0
    cu: float = 0.0
    mo: float = 0.0


@dataclass
class DrainAnalysis:
    ec: float = 0.0
    nh4: float = 0.0
    no3: float = 0.0
    k: float = 0.0
    mg: float = 0.0
    ca: float = 0.0
    p2o5: float = 0.0
    so4: float = 0.0
    cl: float = 0.0
    na: float = 0.0
    fe: float = 0.0
    mn: float = 0.0
    zn: float = 0.0
    b: float = 0.0
    cu: float = 0.0
    mo: float = 0.0


@dataclass
class TargetValues:
    ec: float = 0.0
    nh4: float = 0.0
    no3: float = 0.0
    k: float = 0.0
    ca: float = 0.0
    mg: float = 0.0
    h2po4: float = 0.0
    so4: float = 0.0
    cl: float = 0.0
    na: float = 0.0
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
    na: float = 0.0


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
    mmol_drain: MmolResult = field(default_factory=MmolResult)
    mmol_ab: MmolResult = field(default_factory=MmolResult)
    umol_raw: UmolResult = field(default_factory=UmolResult)
    umol_scaled: UmolResult = field(default_factory=UmolResult)
    umol_drain: UmolResult = field(default_factory=UmolResult)
    umol_ab: UmolResult = field(default_factory=UmolResult)
    ppm: Dict[str, float] = field(default_factory=dict)
    ratio_nk: float = 0.0
    ratio_kca: float = 0.0
    ratio_mgca: float = 0.0
    # Recirculation fields
    ec_drain: float = 0.0
    ec_ab: float = 0.0
    ab_percentage: float = 1.0
    auto_dilution: float = 0.0
    auto_dose: float = 0.0


def _base_key(fert_id: str) -> str:
    return re.sub(r'-[abc]$', '', fert_id)


def calc_fert_ec(fert_id: str, qty: float, tank: TankConfig, is_micro: bool = False) -> FertResult:
    fdef = FERT_BY_ID.get(fert_id)
    if not fdef or qty == 0 or tank.capacity == 0:
        return FertResult(fert_id)

    dose = tank.dose
    factor = 1 if is_micro else 1000
    ec_per_liter = qty * fdef.ec_value * factor / tank.capacity
    calc_ec = ec_per_liter * dose / 1000
    gr_per_l = calc_ec / fdef.ec_value if fdef.ec_value else 0

    if fdef.is_liquid and fdef.liquid_density:
        gr_per_l *= fdef.liquid_density

    return FertResult(fert_id, ec_per_liter, calc_ec, gr_per_l)


def calc_tank(tank: TankConfig, is_micro: bool = False) -> List[FertResult]:
    return [calc_fert_ec(fid, qty, tank, is_micro) for fid, qty in tank.entries.items()]


def calc_micro(micro_entries: Dict[str, float], tank_a: TankConfig, tank_b: TankConfig) -> List[FertResult]:
    results = []
    for fid, qty in micro_entries.items():
        if fid in FE_IDS:
            tank = TankConfig(capacity=tank_a.capacity, dilution=tank_a.dilution,
                              dose=1000 / tank_a.dilution if tank_a.dilution else 10)
        else:
            tank = TankConfig(capacity=tank_b.capacity, dilution=tank_b.dilution,
                              dose=1000 / tank_b.dilution if tank_b.dilution else 10)
        results.append(calc_fert_ec(fid, qty, tank, is_micro=True))
    return results


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
        return MmolResult(**raw.__dict__)
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
        na=water.na or 0,  # Na komt alleen uit water, nooit uit kunstmest
    )


def scale_umol(raw: UmolResult, calc_ec: float, desired_ec: float, water: WaterAnalysis) -> UmolResult:
    if calc_ec == 0 or desired_ec == 0:
        return UmolResult(**raw.__dict__)
    r = desired_ec / calc_ec
    return UmolResult(
        fe=r * raw.fe + water.fe,
        mn=r * raw.mn + water.mn,
        zn=r * raw.zn + water.zn,
        b=r * raw.b + water.b,
        cu=r * raw.cu + water.cu,
        mo=r * raw.mo + water.mo,
    )


def _add_mmol(a: MmolResult, b: MmolResult) -> MmolResult:
    return MmolResult(
        no3=a.no3 + b.no3, h2po4=a.h2po4 + b.h2po4, so4=a.so4 + b.so4,
        nh4=a.nh4 + b.nh4, k=a.k + b.k, ca=a.ca + b.ca, mg=a.mg + b.mg,
        cl=a.cl + b.cl, na=a.na + b.na,
    )


def _add_umol(a: UmolResult, b: UmolResult) -> UmolResult:
    return UmolResult(
        fe=a.fe + b.fe, mn=a.mn + b.mn, zn=a.zn + b.zn,
        b=a.b + b.b, cu=a.cu + b.cu, mo=a.mo + b.mo,
    )


def _drain_mmol(drain: DrainAnalysis, drain_pct: float) -> MmolResult:
    return MmolResult(
        no3=drain.no3 * drain_pct, h2po4=drain.p2o5 * drain_pct,
        so4=drain.so4 * drain_pct, nh4=drain.nh4 * drain_pct,
        k=drain.k * drain_pct, ca=drain.ca * drain_pct,
        mg=drain.mg * drain_pct, cl=drain.cl * drain_pct,
        na=drain.na * drain_pct,
    )


def _drain_umol(drain: DrainAnalysis, drain_pct: float) -> UmolResult:
    return UmolResult(
        fe=drain.fe * drain_pct, mn=drain.mn * drain_pct,
        zn=drain.zn * drain_pct, b=drain.b * drain_pct,
        cu=drain.cu * drain_pct, mo=drain.mo * drain_pct,
    )


def _build_ppm(mmol: MmolResult, umol: UmolResult) -> Dict[str, float]:
    ppm = {}
    for k, v in MMOL_TO_PPM.items():
        ppm[k] = getattr(mmol, k.lower(), 0) * v
    for k, v in UMOL_TO_PPM.items():
        ppm[k] = getattr(umol, k.lower(), 0) * v
    return ppm


def _build_ratios(mmol: MmolResult):
    total_n = mmol.no3 + mmol.nh4
    return (
        total_n / mmol.k if mmol.k else 0,
        mmol.k / mmol.ca if mmol.ca else 0,
        mmol.mg / mmol.ca if mmol.ca else 0,
    )


def calculate(
    tank_a: TankConfig,
    tank_b: TankConfig,
    tank_c: TankConfig,
    micro: TankConfig,
    desired_ec: float,
    water: WaterAnalysis,
    mode: str = 'standard',
    drain_percentage: float = 0.0,
    drain_analysis: Optional[DrainAnalysis] = None,
) -> CalcResults:
    # EC per liter totals (before dilution)
    res_a_orig = calc_tank(tank_a)
    res_b_orig = calc_tank(tank_b)
    ec_per_liter_a = sum(r.ec_per_liter for r in res_a_orig)
    ec_per_liter_b = sum(r.ec_per_liter for r in res_b_orig)
    res_m_orig = calc_micro(micro.entries, tank_a, tank_b)
    fe_ec_per_liter = sum(r.ec_per_liter for r in res_m_orig if r.fert_id in FE_IDS)

    if mode == 'recirculation' and drain_analysis:
        drain_pct = drain_percentage  # 0-1
        drain_ec = drain_pct * drain_analysis.ec
        ec_ab = max(0, desired_ec - drain_ec)

        # Auto-dilution based on Tank A + B only (NOT Tank C)
        total_ec_per_liter_ab = ec_per_liter_a + fe_ec_per_liter + ec_per_liter_b
        auto_dilution = total_ec_per_liter_ab / ec_ab if ec_ab > 0 else 0
        auto_dose = 1000 / auto_dilution if auto_dilution > 0 else 0

        # Recalculate A+B at auto-dilution, Tank C keeps original
        auto_a = TankConfig(tank_a.capacity, auto_dilution, auto_dose, tank_a.entries)
        auto_b = TankConfig(tank_b.capacity, auto_dilution, auto_dose, tank_b.entries)
        res_a = calc_tank(auto_a)
        res_b = calc_tank(auto_b)
        res_c = calc_tank(tank_c)
        res_m = calc_micro(micro.entries, auto_a, auto_b)

        mmol_ab = calc_mmol(res_a + res_b + res_c)
        umol_ab = calc_umol(res_m)
        mmol_drain = _drain_mmol(drain_analysis, drain_pct)
        umol_drain = _drain_umol(drain_analysis, drain_pct)
        mmol_scaled = _add_mmol(mmol_drain, mmol_ab)
        umol_scaled = _add_umol(umol_drain, umol_ab)

        fe_ec = sum(r.calc_ec for r in res_m if r.fert_id in FE_IDS)
        ec_a = sum(r.calc_ec for r in res_a) + fe_ec
        ec_b = sum(r.calc_ec for r in res_b)
        ec_c = sum(r.calc_ec for r in res_c)

        nk, kca, mgca = _build_ratios(mmol_scaled)
        return CalcResults(
            tank_results={'A': res_a, 'B': res_b, 'C': res_c, 'micro': res_m},
            total_ec_a=ec_a, total_ec_b=ec_b, total_ec_c=ec_c, total_ec=ec_a + ec_b + ec_c,
            mmol_raw=mmol_ab, mmol_scaled=mmol_scaled, mmol_drain=mmol_drain, mmol_ab=mmol_ab,
            umol_raw=umol_ab, umol_scaled=umol_scaled, umol_drain=umol_drain, umol_ab=umol_ab,
            ppm=_build_ppm(mmol_scaled, umol_scaled),
            ratio_nk=nk, ratio_kca=kca, ratio_mgca=mgca,
            ec_drain=drain_ec, ec_ab=ec_ab, ab_percentage=1 - drain_pct,
            auto_dilution=auto_dilution, auto_dose=auto_dose,
        )

    # === Standard mode ===
    total_ec_per_liter_ab = ec_per_liter_a + fe_ec_per_liter + ec_per_liter_b
    auto_dilution = total_ec_per_liter_ab / desired_ec if desired_ec > 0 else 0
    auto_dose = 1000 / auto_dilution if auto_dilution > 0 else 0

    auto_a = TankConfig(tank_a.capacity, auto_dilution, auto_dose, tank_a.entries)
    auto_b = TankConfig(tank_b.capacity, auto_dilution, auto_dose, tank_b.entries)
    res_a = calc_tank(auto_a)
    res_b = calc_tank(auto_b)
    res_c = calc_tank(tank_c)
    res_m = calc_micro(micro.entries, auto_a, auto_b)

    fe_ec = sum(r.calc_ec for r in res_m if r.fert_id in FE_IDS)
    ec_a = sum(r.calc_ec for r in res_a) + fe_ec
    ec_b = sum(r.calc_ec for r in res_b)
    ec_c = sum(r.calc_ec for r in res_c)
    ec_total = ec_a + ec_b + ec_c

    mmol_raw = calc_mmol(res_a + res_b + res_c)
    umol_raw = calc_umol(res_m)
    mmol_s = scale_mmol(mmol_raw, ec_total, desired_ec, water)
    umol_s = scale_umol(umol_raw, ec_total, desired_ec, water)

    nk, kca, mgca = _build_ratios(mmol_s)
    return CalcResults(
        tank_results={'A': res_a, 'B': res_b, 'C': res_c, 'micro': res_m},
        total_ec_a=ec_a, total_ec_b=ec_b, total_ec_c=ec_c, total_ec=ec_total,
        mmol_raw=mmol_raw, mmol_scaled=mmol_s,
        mmol_drain=MmolResult(), mmol_ab=MmolResult(),
        umol_raw=umol_raw, umol_scaled=umol_s,
        umol_drain=UmolResult(), umol_ab=UmolResult(),
        ppm=_build_ppm(mmol_s, umol_s),
        ratio_nk=nk, ratio_kca=kca, ratio_mgca=mgca,
        ec_drain=0, ec_ab=0, ab_percentage=1,
        auto_dilution=auto_dilution, auto_dose=auto_dose,
    )
