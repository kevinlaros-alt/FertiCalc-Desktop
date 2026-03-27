"""Berekende waarden balk — horizontale tabel onder de tanks, matching web portal."""

import customtkinter as ctk
from ..engine.calculations import CalcResults, TargetValues


MACRO_ELEMS = ['EC', 'NH4', 'NO3', 'K', 'Ca', 'Mg', 'H2PO4', 'SO4', 'Cl', 'Na']
MICRO_ELEMS = ['Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo']


class ResultsBar(ctk.CTkFrame):
    """Horizontal results summary bar at the bottom of the calculator."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="white", corner_radius=8,
                         border_width=1, border_color="#e5e7eb", **kwargs)
        self._targets = TargetValues()
        self._is_recirc = False
        self._build()

    def _build(self):
        # Green header bar
        header = ctk.CTkFrame(self, fg_color="#15803d", corner_radius=6, height=32)
        header.pack(fill="x", padx=4, pady=(4, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="Berekende waarden (mmol/umol)",
                     text_color="white", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        self.lbl_total_ec = ctk.CTkLabel(header, text="EC: 0.000",
                                          text_color="white", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_total_ec.pack(side="right", padx=10)

        # Recirculation info bar (hidden by default)
        self.recirc_bar = ctk.CTkFrame(self, fg_color="#dbeafe", corner_radius=4, height=28)
        self.recirc_labels = {}
        recirc_inner = ctk.CTkFrame(self.recirc_bar, fg_color="transparent")
        recirc_inner.pack(fill="x", padx=10)
        for key, label, color in [
            ('drain_ec', 'EC uit Drain:', '#2563eb'),
            ('ab_ec', 'EC uit A/B:', '#16a34a'),
            ('dilution', 'Auto Verdunning:', '#7c3aed'),
        ]:
            ctk.CTkLabel(recirc_inner, text=label, font=ctk.CTkFont(size=11),
                         text_color=color).pack(side="left", padx=(10, 2))
            lbl = ctk.CTkLabel(recirc_inner, text="0.000", font=ctk.CTkFont(size=11, weight="bold"),
                               text_color=color)
            lbl.pack(side="left", padx=(0, 10))
            self.recirc_labels[key] = lbl

        # Column headers
        hdr_frame = ctk.CTkFrame(self, fg_color="#f9fafb")
        hdr_frame.pack(fill="x", padx=4, pady=(4, 0))

        # Label column
        ctk.CTkLabel(hdr_frame, text="", width=65, font=ctk.CTkFont(size=10)).pack(side="left")

        self.col_labels = {}
        for elem in MACRO_ELEMS:
            lbl = ctk.CTkLabel(hdr_frame, text=elem, width=58,
                               font=ctk.CTkFont(size=10, weight="bold"),
                               text_color="#374151", anchor="center")
            lbl.pack(side="left", padx=1)

        # Separator
        ctk.CTkLabel(hdr_frame, text="|", width=10, text_color="#d1d5db",
                     font=ctk.CTkFont(size=10)).pack(side="left")

        for elem in MICRO_ELEMS:
            lbl = ctk.CTkLabel(hdr_frame, text=elem, width=50,
                               font=ctk.CTkFont(size=10, weight="bold"),
                               text_color="#ea580c", anchor="center")
            lbl.pack(side="left", padx=1)

        # Berekend row
        calc_frame = ctk.CTkFrame(self, fg_color="transparent")
        calc_frame.pack(fill="x", padx=4, pady=2)

        ctk.CTkLabel(calc_frame, text="Berekend", width=65,
                     font=ctk.CTkFont(size=11), text_color="#374151",
                     anchor="w").pack(side="left")

        self.calc_labels = {}
        for elem in MACRO_ELEMS:
            lbl = ctk.CTkLabel(calc_frame, text="0", width=58,
                               font=ctk.CTkFont(size=11, weight="bold"),
                               text_color="#1f2937", anchor="center")
            lbl.pack(side="left", padx=1)
            self.calc_labels[elem] = lbl

        ctk.CTkLabel(calc_frame, text="|", width=10, text_color="#d1d5db",
                     font=ctk.CTkFont(size=10)).pack(side="left")

        for elem in MICRO_ELEMS:
            lbl = ctk.CTkLabel(calc_frame, text="0", width=50,
                               font=ctk.CTkFont(size=11, weight="bold"),
                               text_color="#ea580c", anchor="center")
            lbl.pack(side="left", padx=1)
            self.calc_labels[elem] = lbl

        # Target row
        target_frame = ctk.CTkFrame(self, fg_color="transparent")
        target_frame.pack(fill="x", padx=4, pady=(0, 6))

        ctk.CTkLabel(target_frame, text="Target", width=65,
                     font=ctk.CTkFont(size=11), text_color="#d97706",
                     anchor="w").pack(side="left")

        self.target_vars = {}
        for elem in MACRO_ELEMS:
            var = ctk.StringVar(value="")
            entry = ctk.CTkEntry(target_frame, textvariable=var, width=56, height=24,
                                 fg_color="#fef3c7", border_color="#fcd34d", border_width=1,
                                 font=ctk.CTkFont(size=10), justify="center")
            entry.pack(side="left", padx=1)
            self.target_vars[elem] = var

        ctk.CTkLabel(target_frame, text="|", width=10, text_color="#d1d5db",
                     font=ctk.CTkFont(size=10)).pack(side="left")

        for elem in MICRO_ELEMS:
            var = ctk.StringVar(value="")
            entry = ctk.CTkEntry(target_frame, textvariable=var, width=48, height=24,
                                 fg_color="#ffedd5", border_color="#fdba74", border_width=1,
                                 font=ctk.CTkFont(size=10), justify="center")
            entry.pack(side="left", padx=1)
            self.target_vars[elem] = var

    def set_recirculation(self, is_recirc: bool):
        self._is_recirc = is_recirc
        if is_recirc:
            self.recirc_bar.pack(fill="x", padx=4, pady=(2, 0),
                                 after=list(self.children.values())[0])
        else:
            self.recirc_bar.pack_forget()

    def set_targets(self, targets: TargetValues):
        self._targets = targets
        mapping = {
            'EC': 'ec', 'NH4': 'nh4', 'NO3': 'no3', 'K': 'k', 'Ca': 'ca',
            'Mg': 'mg', 'H2PO4': 'h2po4', 'SO4': 'so4', 'Cl': 'cl', 'Na': 'na',
            'Fe': 'fe', 'Mn': 'mn', 'Zn': 'zn', 'B': 'b', 'Cu': 'cu', 'Mo': 'mo',
        }
        for display_name, attr in mapping.items():
            var = self.target_vars.get(display_name)
            if var:
                val = getattr(targets, attr, 0)
                var.set(str(val) if val else "")

    def get_targets(self) -> TargetValues:
        targets = TargetValues()
        mapping = {
            'EC': 'ec', 'NH4': 'nh4', 'NO3': 'no3', 'K': 'k', 'Ca': 'ca',
            'Mg': 'mg', 'H2PO4': 'h2po4', 'SO4': 'so4', 'Cl': 'cl', 'Na': 'na',
            'Fe': 'fe', 'Mn': 'mn', 'Zn': 'zn', 'B': 'b', 'Cu': 'cu', 'Mo': 'mo',
        }
        for display_name, attr in mapping.items():
            var = self.target_vars.get(display_name)
            if var:
                try:
                    setattr(targets, attr, float(var.get().replace(',', '.')))
                except (ValueError, TypeError):
                    pass
        return targets

    def update(self, results: CalcResults):
        self.lbl_total_ec.configure(text=f"EC: {results.total_ec:.3f}")

        mmol = results.mmol_scaled
        umol = results.umol_scaled
        ppm = results.ppm

        # EC column shows desired EC (= total_ec for standard)
        self.calc_labels['EC'].configure(text=f"{results.total_ec:.3f}")

        # Macro mmol values
        for elem in ['NH4', 'NO3', 'K', 'Ca', 'Mg', 'H2PO4', 'SO4', 'Cl', 'Na']:
            val = getattr(mmol, elem.lower(), 0)
            self.calc_labels[elem].configure(text=f"{val:.2f}")

        # Micro umol values
        for elem in ['Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo']:
            val = getattr(umol, elem.lower(), 0)
            self.calc_labels[elem].configure(text=f"{val:.1f}")

        # Recirculation info
        if self._is_recirc:
            self.recirc_labels['drain_ec'].configure(text=f"{results.ec_drain:.3f}")
            self.recirc_labels['ab_ec'].configure(text=f"{results.ec_ab:.3f}")
            dil = f"1:{results.auto_dilution:.1f}" if results.auto_dilution else "0"
            self.recirc_labels['dilution'].configure(text=dil)


class RatioBox(ctk.CTkFrame):
    """Compact ratio display matching web portal."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#f9fafb", corner_radius=6,
                         border_width=1, border_color="#e5e7eb", **kwargs)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=10, pady=6)

        ctk.CTkLabel(inner, text="Verhoudingen", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#374151").pack(side="left", padx=(0, 10))

        self.ratio_labels = {}
        for key, label in [('nk', 'N:K'), ('kca', 'K:Ca'), ('mgca', 'Mg:Ca')]:
            ctk.CTkLabel(inner, text=label, font=ctk.CTkFont(size=11),
                         text_color="#6b7280").pack(side="left", padx=(8, 2))
            lbl = ctk.CTkLabel(inner, text="0.00", font=ctk.CTkFont(size=12, weight="bold"),
                               text_color="#1f2937")
            lbl.pack(side="left")
            self.ratio_labels[key] = lbl

    def update(self, results: CalcResults):
        self.ratio_labels['nk'].configure(text=f"{results.ratio_nk:.2f}")
        self.ratio_labels['kca'].configure(text=f"{results.ratio_kca:.2f}")
        self.ratio_labels['mgca'].configure(text=f"{results.ratio_mgca:.2f}")
