"""Wateranalyse + Drainwater invoerframe."""

import customtkinter as ctk
from typing import Callable
from ..engine.calculations import WaterAnalysis, DrainAnalysis


MACRO_FIELDS = [
    ('ec', 'EC', ''),
    ('no3', 'NO3', 'mmol'),
    ('k', 'K', 'mmol'),
    ('mg', 'Mg', 'mmol'),
    ('ca', 'Ca', 'mmol'),
    ('p2o5', 'P2O5', 'mmol'),
    ('s', 'S', 'mmol'),
    ('cl', 'Cl', 'mmol'),
    ('na', 'Na', 'mmol'),
]

MICRO_FIELDS = [
    ('fe', 'Fe', 'umol'),
    ('mn', 'Mn', 'umol'),
    ('zn', 'Zn', 'umol'),
    ('b', 'B', 'umol'),
    ('cu', 'Cu', 'umol'),
    ('mo', 'Mo', 'umol'),
]

DRAIN_MACRO_FIELDS = [
    ('ec', 'EC', ''),
    ('nh4', 'NH4', 'mmol'),
    ('no3', 'NO3', 'mmol'),
    ('k', 'K', 'mmol'),
    ('mg', 'Mg', 'mmol'),
    ('ca', 'Ca', 'mmol'),
    ('p2o5', 'P2O5', 'mmol'),
    ('so4', 'SO4', 'mmol'),
    ('cl', 'Cl', 'mmol'),
    ('na', 'Na', 'mmol'),
]

DRAIN_MICRO_FIELDS = [
    ('fe', 'Fe', 'umol'),
    ('mn', 'Mn', 'umol'),
    ('zn', 'Zn', 'umol'),
    ('b', 'B', 'umol'),
    ('cu', 'Cu', 'umol'),
    ('mo', 'Mo', 'umol'),
]


class WaterFrame(ctk.CTkFrame):
    def __init__(self, parent, on_change: Callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_change = on_change
        self.vars = {}

        ctk.CTkLabel(self, text="Wateranalyse", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))

        ctk.CTkLabel(self, text="Macro (mmol)", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray50").pack(anchor="w", padx=10)

        for key, label, unit in MACRO_FIELDS:
            self._add_field(key, label, unit)

        ctk.CTkLabel(self, text="Micro (umol)", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray50").pack(anchor="w", padx=10, pady=(10, 0))

        for key, label, unit in MICRO_FIELDS:
            self._add_field(key, label, unit)

    def _add_field(self, key, label, unit):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=1)

        text = f"{label} ({unit})" if unit else label
        ctk.CTkLabel(row, text=text, width=100, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")

        var = ctk.StringVar(value="")
        var.trace_add('write', lambda *_: self.on_change())
        self.vars[key] = var

        ctk.CTkEntry(row, textvariable=var, width=70, justify="right",
                     fg_color=("#e8f0fe", "#1e3a5f"),
                     font=ctk.CTkFont(size=12)).pack(side="right")

    def get_analysis(self) -> WaterAnalysis:
        wa = WaterAnalysis()
        for key, var in self.vars.items():
            try:
                setattr(wa, key, float(var.get()))
            except (ValueError, TypeError):
                pass
        return wa

    def set_analysis(self, wa: WaterAnalysis):
        for key, var in self.vars.items():
            val = getattr(wa, key, 0)
            var.set(str(val) if val else "")


class DrainFrame(ctk.CTkFrame):
    """Drainwater analyse invoer (voor recirculatie modus)."""

    def __init__(self, parent, on_change: Callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_change = on_change
        self.vars = {}

        ctk.CTkLabel(self, text="Drainwater Analyse", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#1d4ed8").pack(pady=(10, 5))

        ctk.CTkLabel(self, text="Macro (mmol)", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3b82f6").pack(anchor="w", padx=10)

        for key, label, unit in DRAIN_MACRO_FIELDS:
            self._add_field(key, label, unit)

        ctk.CTkLabel(self, text="Micro (umol)", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3b82f6").pack(anchor="w", padx=10, pady=(10, 0))

        for key, label, unit in DRAIN_MICRO_FIELDS:
            self._add_field(key, label, unit)

    def _add_field(self, key, label, unit):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=1)

        text = f"{label} ({unit})" if unit else label
        ctk.CTkLabel(row, text=text, width=100, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")

        var = ctk.StringVar(value="")
        var.trace_add('write', lambda *_: self.on_change())
        self.vars[key] = var

        ctk.CTkEntry(row, textvariable=var, width=70, justify="right",
                     fg_color=("#dbeafe", "#1e3a5f"),
                     font=ctk.CTkFont(size=12)).pack(side="right")

    def get_analysis(self) -> DrainAnalysis:
        da = DrainAnalysis()
        for key, var in self.vars.items():
            try:
                setattr(da, key, float(var.get()))
            except (ValueError, TypeError):
                pass
        return da

    def set_analysis(self, da: DrainAnalysis):
        for key, var in self.vars.items():
            val = getattr(da, key, 0)
            var.set(str(val) if val else "")
