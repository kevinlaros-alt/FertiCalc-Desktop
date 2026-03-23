"""Excel I/O — lees/schrijf recepten en meststoffen naar/van .xlsx."""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openpyxl import Workbook, load_workbook
from ..engine.fertilizers import FERTILIZERS, FertilizerDef
from ..engine.calculations import TankConfig, WaterAnalysis


DATA_FILE = 'FertiCalc_data.xlsx'
SHEET_FERTS = 'Meststoffen'
SHEET_RECIPES = 'Recepten'
SHEET_RECIPE_FERTS = 'ReceptMeststoffen'
SHEET_WATER = 'Wateranalyses'
SHEET_HISTORY = 'Historie'


def _get_path() -> str:
    """Get path to data file next to executable or cwd."""
    # Try next to the script/exe first
    for base in [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
        p = os.path.join(base, DATA_FILE)
        if os.path.exists(p):
            return p
    # Default: create in cwd
    return os.path.join(os.getcwd(), DATA_FILE)


def ensure_database() -> str:
    """Create database Excel if it doesn't exist. Returns path."""
    path = _get_path()
    if os.path.exists(path):
        return path

    wb = Workbook()

    # Meststoffen sheet
    ws = wb.active
    ws.title = SHEET_FERTS
    ws.append(['ID', 'Naam', 'Tank', 'Element1', 'Pct1', 'Element2', 'Pct2', 'EC Waarde', 'Molaire Massa', 'Eenheid', 'Vloeibaar', 'Dichtheid'])
    for f in FERTILIZERS:
        ai1 = f.active_ingredients[0] if len(f.active_ingredients) > 0 else None
        ai2 = f.active_ingredients[1] if len(f.active_ingredients) > 1 else None
        ws.append([
            f.id, f.name, f.tank,
            ai1.element if ai1 else '', ai1.percentage if ai1 else 0,
            ai2.element if ai2 else '', ai2.percentage if ai2 else 0,
            f.ec_value, f.molar_mass or '', f.unit,
            f.is_liquid, f.liquid_density if f.is_liquid else '',
        ])

    # Recepten sheet
    ws2 = wb.create_sheet(SHEET_RECIPES)
    ws2.append(['ID', 'Naam', 'Gewas', 'Aangemaakt', 'Gewijzigd',
                'Tank A L', 'Tank A Verd', 'Tank B L', 'Tank B Verd',
                'Tank C L', 'Tank C Verd', 'Dosering', 'Gewenste EC'])

    # ReceptMeststoffen sheet
    ws3 = wb.create_sheet(SHEET_RECIPE_FERTS)
    ws3.append(['Recept ID', 'Meststof ID', 'Hoeveelheid'])

    # Wateranalyses sheet
    ws4 = wb.create_sheet(SHEET_WATER)
    ws4.append(['Recept ID', 'EC', 'NO3', 'K', 'Mg', 'Ca', 'P2O5', 'S', 'Cl',
                'Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo'])

    # Historie sheet
    ws5 = wb.create_sheet(SHEET_HISTORY)
    ws5.append(['Recept ID', 'Datum', 'Snapshot'])

    wb.save(path)
    return path


def _next_recipe_id(ws) -> int:
    """Get next recipe ID."""
    max_id = 0
    for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
        if row[0] and isinstance(row[0], (int, float)):
            max_id = max(max_id, int(row[0]))
    return max_id + 1


def list_recipes() -> List[Dict]:
    """Return list of {id, name, crop, modified}."""
    path = ensure_database()
    wb = load_workbook(path, read_only=True)
    ws = wb[SHEET_RECIPES]
    recipes = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        recipes.append({
            'id': int(row[0]),
            'name': row[1] or '',
            'crop': row[2] or '',
            'modified': str(row[4] or row[3] or ''),
        })
    wb.close()
    return recipes


def load_recipe(recipe_id: int) -> Optional[Dict]:
    """Load a full recipe: tanks, ferts, water."""
    path = ensure_database()
    wb = load_workbook(path, read_only=True)

    # Find recipe row
    ws = wb[SHEET_RECIPES]
    recipe = None
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] and int(row[0]) == recipe_id:
            recipe = {
                'id': int(row[0]), 'name': row[1] or '', 'crop': row[2] or '',
                'tank_a': TankConfig(capacity=row[5] or 1000, dilution=row[6] or 100, dose=row[11] or 10),
                'tank_b': TankConfig(capacity=row[7] or 1000, dilution=row[8] or 100, dose=row[11] or 10),
                'tank_c': TankConfig(capacity=row[9] or 1000, dilution=row[10] or 100, dose=row[11] or 10),
                'micro': TankConfig(capacity=row[7] or 1000, dilution=row[8] or 100, dose=row[11] or 10),
                'desired_ec': row[12] or 0,
            }
            break

    if not recipe:
        wb.close()
        return None

    # Load fertilizer entries
    ws2 = wb[SHEET_RECIPE_FERTS]
    for row in ws2.iter_rows(min_row=2, values_only=True):
        if row[0] and int(row[0]) == recipe_id:
            fid = row[1]
            qty = row[2] or 0
            # Determine which tank this fert belongs to
            from ..engine.fertilizers import FERT_BY_ID
            fdef = FERT_BY_ID.get(fid)
            if fdef:
                tank_key = {'A': 'tank_a', 'B': 'tank_b', 'C': 'tank_c', 'micro': 'micro'}.get(fdef.tank)
                if tank_key:
                    recipe[tank_key].entries[fid] = float(qty)

    # Load water analysis
    ws3 = wb[SHEET_WATER]
    water = WaterAnalysis()
    for row in ws3.iter_rows(min_row=2, values_only=True):
        if row[0] and int(row[0]) == recipe_id:
            fields = ['ec', 'no3', 'k', 'mg', 'ca', 'p2o5', 's', 'cl', 'fe', 'mn', 'zn', 'b', 'cu', 'mo']
            for i, f in enumerate(fields):
                setattr(water, f, float(row[i + 1] or 0))
            break
    recipe['water'] = water

    wb.close()
    return recipe


def save_recipe(
    recipe_id: Optional[int],
    name: str,
    crop: str,
    tank_a: TankConfig,
    tank_b: TankConfig,
    tank_c: TankConfig,
    micro: TankConfig,
    desired_ec: float,
    water: WaterAnalysis,
) -> int:
    """Save recipe. Returns recipe ID (new or existing)."""
    path = ensure_database()
    wb = load_workbook(path)

    ws = wb[SHEET_RECIPES]
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    if recipe_id is None:
        recipe_id = _next_recipe_id(ws)
        ws.append([
            recipe_id, name, crop, now, now,
            tank_a.capacity, tank_a.dilution,
            tank_b.capacity, tank_b.dilution,
            tank_c.capacity, tank_c.dilution,
            tank_a.dose, desired_ec,
        ])
    else:
        for row in ws.iter_rows(min_row=2):
            if row[0].value and int(row[0].value) == recipe_id:
                row[1].value = name
                row[2].value = crop
                row[4].value = now
                row[5].value = tank_a.capacity
                row[6].value = tank_a.dilution
                row[7].value = tank_b.capacity
                row[8].value = tank_b.dilution
                row[9].value = tank_c.capacity
                row[10].value = tank_c.dilution
                row[11].value = tank_a.dose
                row[12].value = desired_ec
                break

    # Clear old fertilizer entries for this recipe
    ws2 = wb[SHEET_RECIPE_FERTS]
    rows_to_delete = []
    for i, row in enumerate(ws2.iter_rows(min_row=2), start=2):
        if row[0].value and int(row[0].value) == recipe_id:
            rows_to_delete.append(i)
    for i in reversed(rows_to_delete):
        ws2.delete_rows(i)

    # Write new entries
    for tank_key, tank in [('tank_a', tank_a), ('tank_b', tank_b), ('tank_c', tank_c), ('micro', micro)]:
        for fid, qty in tank.entries.items():
            if qty > 0:
                ws2.append([recipe_id, fid, qty])

    # Update water analysis
    ws3 = wb[SHEET_WATER]
    found_water = False
    for row in ws3.iter_rows(min_row=2):
        if row[0].value and int(row[0].value) == recipe_id:
            for i, f in enumerate(['ec', 'no3', 'k', 'mg', 'ca', 'p2o5', 's', 'cl', 'fe', 'mn', 'zn', 'b', 'cu', 'mo']):
                row[i + 1].value = getattr(water, f)
            found_water = True
            break
    if not found_water:
        ws3.append([recipe_id, water.ec, water.no3, water.k, water.mg, water.ca,
                     water.p2o5, water.s, water.cl, water.fe, water.mn, water.zn,
                     water.b, water.cu, water.mo])

    wb.save(path)
    wb.close()
    return recipe_id


def delete_recipe(recipe_id: int):
    """Delete a recipe and its related data."""
    path = ensure_database()
    wb = load_workbook(path)

    for sheet_name in [SHEET_RECIPES, SHEET_RECIPE_FERTS, SHEET_WATER, SHEET_HISTORY]:
        ws = wb[sheet_name]
        rows = []
        for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
            if row[0].value and int(row[0].value) == recipe_id:
                rows.append(i)
        for i in reversed(rows):
            ws.delete_rows(i)

    wb.save(path)
    wb.close()
