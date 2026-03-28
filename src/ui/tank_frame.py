"""Tank kolom — compact design matching web portal."""

import customtkinter as ctk
from typing import Callable, Dict, List
from ..engine.fertilizers import FERTILIZERS, FertilizerDef, FERT_BY_ID

# Tank header colors matching web
TANK_COLORS = {
    'A': {'bg': '#15803d', 'label': 'Tank A - Macro (Calcium groep)'},
    'B': {'bg': '#16a34a', 'label': 'Tank B - Macro (Fosfaat/Sulfaat)'},
    'C': {'bg': '#d97706', 'label': 'Tank C - Zuurcorrectie'},
    'micro': {'bg': '#ea580c', 'label': 'Micro-elementen'},
}


def _bind_select_on_focus(entry):
    """Select all text when entry receives focus (overwrite-friendly)."""
    def _on_focus(e):
        e.widget.after(10, lambda: e.widget.select_range(0, 'end'))
    entry.bind('<FocusIn>', _on_focus)


def _bind_enter_next(entry):
    """Move to next input on Enter key."""
    def _on_enter(e):
        e.widget.tk_focusNext().focus()
        return 'break'
    entry.bind('<Return>', _on_enter)


class TankColumn(ctk.CTkFrame):
    """Single tank column matching web layout."""

    def __init__(self, parent, tank_type: str, on_change: Callable, **kwargs):
        super().__init__(parent, fg_color="white", corner_radius=8, border_width=1,
                         border_color="#e5e7eb", **kwargs)
        self.tank_type = tank_type
        self.on_change = on_change
        self.qty_vars: Dict[str, ctk.StringVar] = {}
        self.qty_entries: list = []  # track entry widgets for focus navigation
        self.ferts = [f for f in FERTILIZERS if f.tank == tank_type]
        self._orig_dilution = 100.0  # original user-set dilution (for save/Tank C)
        self._orig_dose = 10.0

        colors = TANK_COLORS.get(tank_type, {'bg': '#166534', 'label': tank_type})

        # Header bar with tank name + EC
        header = ctk.CTkFrame(self, fg_color=colors['bg'], corner_radius=6, height=36)
        header.pack(fill="x", padx=4, pady=(4, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=colors['label'], text_color="white",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=10)
        self.lbl_ec = ctk.CTkLabel(header, text="EC: 0.000", text_color="white",
                                    font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_ec.pack(side="right", padx=10)

        # Settings row — compact single line
        settings = ctk.CTkFrame(self, fg_color="#f9fafb")
        settings.pack(fill="x", padx=4, pady=(4, 2))

        self.var_capacity = ctk.StringVar(value="1000")
        self.var_capacity.trace_add('write', lambda *_: self.on_change())

        ctk.CTkLabel(settings, text="Inhoud:", font=ctk.CTkFont(size=10),
                     text_color="#6b7280").pack(side="left", padx=(6, 0))
        cap_entry = ctk.CTkEntry(settings, textvariable=self.var_capacity, width=50, height=24,
                     font=ctk.CTkFont(size=10), justify="right",
                     border_width=1, border_color="#d1d5db")
        cap_entry.pack(side="left", padx=2)
        _bind_select_on_focus(cap_entry)
        _bind_enter_next(cap_entry)
        ctk.CTkLabel(settings, text="L", font=ctk.CTkFont(size=10),
                     text_color="#9ca3af").pack(side="left")

        ctk.CTkLabel(settings, text="Verd 1:", font=ctk.CTkFont(size=10),
                     text_color="#6b7280").pack(side="left", padx=(8, 0))
        self.lbl_dilution = ctk.CTkLabel(settings, text="100", width=40,
                     font=ctk.CTkFont(size=10, weight="bold"), text_color="#374151",
                     anchor="e")
        self.lbl_dilution.pack(side="left", padx=2)

        ctk.CTkLabel(settings, text="Dos:", font=ctk.CTkFont(size=10),
                     text_color="#6b7280").pack(side="left", padx=(8, 0))
        self.lbl_dose = ctk.CTkLabel(settings, text="10.0", width=35,
                     font=ctk.CTkFont(size=10, weight="bold"), text_color="#374151",
                     anchor="e")
        self.lbl_dose.pack(side="left", padx=2)
        ctk.CTkLabel(settings, text="L/m³", font=ctk.CTkFont(size=10),
                     text_color="#9ca3af").pack(side="left")

        # Separator
        ctk.CTkFrame(self, fg_color="#e5e7eb", height=1).pack(fill="x", padx=8)

        # Column headers
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(2, 0))
        ctk.CTkLabel(hdr, text="Meststof", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#374151", anchor="w").pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(hdr, text="QTY", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#374151", anchor="e", width=55).pack(side="right", padx=(0, 5))

        # Fertilizer rows — no scrollframe, use direct packing for maximum space
        unit = 'gr' if tank_type == 'micro' else 'Kg'
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                         scrollbar_button_color="#d1d5db")
        scroll.pack(fill="both", expand=True, padx=4)

        for fdef in self.ferts:
            row = ctk.CTkFrame(scroll, fg_color="transparent", height=26)
            row.pack(fill="x", pady=0)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=fdef.name, font=ctk.CTkFont(size=11),
                         text_color="#1f2937", anchor="w").pack(side="left", fill="x", expand=True)

            var = ctk.StringVar(value="0")
            var.trace_add('write', lambda *_: self.on_change())
            self.qty_vars[fdef.id] = var

            entry = ctk.CTkEntry(row, textvariable=var, width=55, height=24,
                         fg_color="#dbeafe", border_color="#93c5fd", border_width=1,
                         font=ctk.CTkFont(size=11), justify="right")
            entry.pack(side="right", padx=(4, 0))
            _bind_select_on_focus(entry)
            _bind_enter_next(entry)
            self.qty_entries.append(entry)
            ctk.CTkLabel(row, text=unit, font=ctk.CTkFont(size=10),
                         text_color="#9ca3af", width=22).pack(side="right")

        # Totaal row
        ctk.CTkFrame(self, fg_color="#e5e7eb", height=1).pack(fill="x", padx=8)
        total_row = ctk.CTkFrame(self, fg_color="transparent")
        total_row.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(total_row, text="Totaal", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#1f2937").pack(side="left")
        self.lbl_total = ctk.CTkLabel(total_row, text="0.0", font=ctk.CTkFont(size=11, weight="bold"),
                                       text_color="#1f2937")
        self.lbl_total.pack(side="right", padx=(0, 5))
        ctk.CTkLabel(total_row, text=unit, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af").pack(side="right")

    def get_config(self):
        from ..engine.calculations import TankConfig
        entries = {}
        for fid, var in self.qty_vars.items():
            try:
                v = float(var.get().replace(',', '.'))
            except (ValueError, TypeError):
                v = 0.0
            if v > 0:
                entries[fid] = v
        try:
            cap = float(self.var_capacity.get().replace(',', '.'))
        except ValueError:
            cap = 1000
        return TankConfig(capacity=cap, dilution=self._orig_dilution,
                          dose=self._orig_dose, entries=entries)

    def set_config(self, config):
        self.var_capacity.set(str(config.capacity))
        self._orig_dilution = config.dilution
        self._orig_dose = config.dose
        self.lbl_dilution.configure(text=f"{config.dilution:.0f}")
        self.lbl_dose.configure(text=f"{config.dose:.1f}")
        for fid, var in self.qty_vars.items():
            qty = config.entries.get(fid, 0)
            var.set(str(qty) if qty > 0 else "0")

    def update_auto_dilution(self, auto_dilution: float, auto_dose: float):
        """Update read-only verdunning/dosering display with auto-calculated values."""
        if auto_dilution > 0:
            self.lbl_dilution.configure(text=f"{auto_dilution:.0f}")
            self.lbl_dose.configure(text=f"{auto_dose:.1f}")
        else:
            self.lbl_dilution.configure(text="–")
            self.lbl_dose.configure(text="–")

    def update_results(self, results: list):
        total_ec = sum(r.calc_ec for r in results)
        total_qty = 0
        for r in results:
            var = self.qty_vars.get(r.fert_id)
            if var:
                try:
                    total_qty += float(var.get().replace(',', '.'))
                except ValueError:
                    pass
        self.lbl_ec.configure(text=f"EC: {total_ec:.3f}")
        self.lbl_total.configure(text=f"{total_qty:.1f}")
