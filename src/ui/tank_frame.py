"""Herbruikbaar tank-invoerframe voor Tank A/B/C/Micro."""

import customtkinter as ctk
from typing import Callable, Dict, List
from ..engine.fertilizers import FERTILIZERS, FertilizerDef, FERT_BY_ID


class TankFrame(ctk.CTkFrame):
    def __init__(self, parent, tank_type: str, on_change: Callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.tank_type = tank_type  # 'A', 'B', 'C', 'micro'
        self.on_change = on_change
        self.qty_vars: Dict[str, ctk.StringVar] = {}
        self.result_labels: Dict[str, Dict[str, ctk.CTkLabel]] = {}

        self.ferts = [f for f in FERTILIZERS if f.tank == tank_type]

        self._build_settings()
        self._build_table()

    def _build_settings(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=(10, 5))

        self.var_capacity = ctk.StringVar(value="1000")
        self.var_dilution = ctk.StringVar(value="100")
        self.var_dose = ctk.StringVar(value="10")

        for var in [self.var_capacity, self.var_dilution, self.var_dose]:
            var.trace_add('write', lambda *_: self.on_change())

        ctk.CTkLabel(frame, text="Inhoud:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(frame, textvariable=self.var_capacity, width=80).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(frame, text="lts").pack(side="left", padx=(0, 15))
        ctk.CTkLabel(frame, text="Verdunning 1:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(frame, textvariable=self.var_dilution, width=80).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(frame, text="Dosering:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(frame, textvariable=self.var_dose, width=80).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(frame, text="liter A/B per m3").pack(side="left")

    def _build_table(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        header.pack(fill="x", padx=10, pady=(5, 0))

        cols = [("Meststof", 200), ("QTY", 80), ("AI%", 100), ("EC", 60), ("EC/l", 70), ("Calc EC", 80), ("gr/l", 80)]
        for text, w in cols:
            ctk.CTkLabel(header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="w" if text == "Meststof" else "e").pack(side="left", padx=2, pady=3)

        # Scrollable rows
        scroll = ctk.CTkScrollableFrame(self, height=300)
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for fdef in self.ferts:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)

            # Name
            ctk.CTkLabel(row, text=fdef.name, width=200, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=2)

            # QTY input (blue-ish)
            var = ctk.StringVar(value="")
            var.trace_add('write', lambda *_: self.on_change())
            self.qty_vars[fdef.id] = var
            entry = ctk.CTkEntry(row, textvariable=var, width=80, fg_color=("#e8f0fe", "#1e3a5f"),
                                 justify="right", font=ctk.CTkFont(size=12))
            entry.pack(side="left", padx=2)

            # AI%
            ai_text = ", ".join(f"{ai.element} {ai.percentage*100:.1f}%" for ai in fdef.active_ingredients)
            ctk.CTkLabel(row, text=ai_text, width=100, font=ctk.CTkFont(size=11),
                         text_color="gray50", anchor="w").pack(side="left", padx=2)

            # EC value (fixed)
            ctk.CTkLabel(row, text=f"{fdef.ec_value:.2f}", width=60, anchor="e",
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=2)

            # Result columns (updated dynamically)
            labels = {}
            for key, w in [("ec_l", 70), ("calc_ec", 80), ("gr_l", 80)]:
                lbl = ctk.CTkLabel(row, text="0.000", width=w, anchor="e",
                                   font=ctk.CTkFont(size=12, family="Courier"))
                lbl.pack(side="left", padx=2)
                labels[key] = lbl
            self.result_labels[fdef.id] = labels

        # Totals row
        self.totals_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        self.totals_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(self.totals_frame, text="Totaal", width=200, anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=2)
        self.lbl_total_qty = ctk.CTkLabel(self.totals_frame, text="0.0", width=80, anchor="e",
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_total_qty.pack(side="left", padx=2)
        ctk.CTkLabel(self.totals_frame, text="", width=100).pack(side="left", padx=2)
        ctk.CTkLabel(self.totals_frame, text="", width=60).pack(side="left", padx=2)
        ctk.CTkLabel(self.totals_frame, text="", width=70).pack(side="left", padx=2)
        self.lbl_total_ec = ctk.CTkLabel(self.totals_frame, text="0.000", width=80, anchor="e",
                                         font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_total_ec.pack(side="left", padx=2)
        self.lbl_total_grl = ctk.CTkLabel(self.totals_frame, text="0.000", width=80, anchor="e",
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_total_grl.pack(side="left", padx=2)

    def get_config(self):
        """Return TankConfig from current UI state."""
        from ..engine.calculations import TankConfig
        entries = {}
        for fid, var in self.qty_vars.items():
            try:
                v = float(var.get())
            except (ValueError, TypeError):
                v = 0.0
            if v > 0:
                entries[fid] = v

        try:
            cap = float(self.var_capacity.get())
        except ValueError:
            cap = 1000
        try:
            dil = float(self.var_dilution.get())
        except ValueError:
            dil = 100
        try:
            dose = float(self.var_dose.get())
        except ValueError:
            dose = 10

        return TankConfig(capacity=cap, dilution=dil, dose=dose, entries=entries)

    def set_config(self, config):
        """Set UI from TankConfig."""
        self.var_capacity.set(str(config.capacity))
        self.var_dilution.set(str(config.dilution))
        self.var_dose.set(str(config.dose))
        for fid, var in self.qty_vars.items():
            qty = config.entries.get(fid, 0)
            var.set(str(qty) if qty > 0 else "")

    def update_results(self, results: list):
        """Update the result labels from calc results."""
        total_ec = 0
        total_grl = 0
        total_qty = 0
        for r in results:
            labels = self.result_labels.get(r.fert_id, {})
            if labels:
                labels["ec_l"].configure(text=f"{r.ec_per_liter:.2f}")
                labels["calc_ec"].configure(text=f"{r.calc_ec:.3f}")
                labels["gr_l"].configure(text=f"{r.gr_per_l:.4f}")
            total_ec += r.calc_ec
            total_grl += r.gr_per_l
            # Get qty
            var = self.qty_vars.get(r.fert_id)
            if var:
                try:
                    total_qty += float(var.get())
                except ValueError:
                    pass

        self.lbl_total_qty.configure(text=f"{total_qty:.1f}")
        self.lbl_total_ec.configure(text=f"{total_ec:.3f}")
        self.lbl_total_grl.configure(text=f"{total_grl:.4f}")
