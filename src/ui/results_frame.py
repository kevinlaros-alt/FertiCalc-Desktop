"""Resultaten panel — mmol, ppm, EC, verhoudingen."""

import customtkinter as ctk
from ..engine.calculations import CalcResults
from ..engine.fertilizers import RECOMMENDED_UMOL


class ResultsFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self):
        # EC section
        ec_frame = ctk.CTkFrame(self)
        ec_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(ec_frame, text="EC Overzicht", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        ec_grid = ctk.CTkFrame(ec_frame, fg_color="transparent")
        ec_grid.pack(fill="x", padx=10, pady=5)

        self.ec_labels = {}
        for i, (key, label) in enumerate([('a', 'Tank A'), ('b', 'Tank B'), ('c', 'Tank C'), ('total', 'Totaal')]):
            col = ctk.CTkFrame(ec_grid, fg_color=("gray90", "gray20"), corner_radius=8)
            col.pack(side="left", expand=True, fill="x", padx=3)
            ctk.CTkLabel(col, text=label, font=ctk.CTkFont(size=10), text_color="gray50").pack()
            lbl = ctk.CTkLabel(col, text="0.000", font=ctk.CTkFont(size=16, weight="bold"))
            lbl.pack(pady=(0, 5))
            self.ec_labels[key] = lbl

        # mmol table
        mmol_frame = ctk.CTkFrame(self)
        mmol_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(mmol_frame, text="mmol/l bij gewenste EC", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=5)

        header = ctk.CTkFrame(mmol_frame, fg_color=("gray85", "gray25"))
        header.pack(fill="x", padx=5)
        for text, w in [("Element", 80), ("mmol", 80), ("ppm", 80)]:
            ctk.CTkLabel(header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="e" if text != "Element" else "w").pack(side="left", padx=3, pady=2)

        self.mmol_labels = {}
        for elem in ['NO3', 'NH4', 'K', 'Ca', 'Mg', 'H2PO4', 'SO4', 'Cl']:
            row = ctk.CTkFrame(mmol_frame, fg_color="transparent")
            row.pack(fill="x", padx=5)
            ctk.CTkLabel(row, text=elem, width=80, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            lbl_mmol = ctk.CTkLabel(row, text="0.00", width=80, anchor="e", font=ctk.CTkFont(size=12, family="Courier"))
            lbl_mmol.pack(side="left", padx=3)
            lbl_ppm = ctk.CTkLabel(row, text="0", width=80, anchor="e", font=ctk.CTkFont(size=12, family="Courier"), text_color="gray50")
            lbl_ppm.pack(side="left", padx=3)
            self.mmol_labels[elem] = (lbl_mmol, lbl_ppm)

        # µmol table
        umol_frame = ctk.CTkFrame(self)
        umol_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(umol_frame, text="umol/l Micro-elementen", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=5)

        header2 = ctk.CTkFrame(umol_frame, fg_color=("gray85", "gray25"))
        header2.pack(fill="x", padx=5)
        for text, w in [("Element", 70), ("umol", 70), ("ppm", 70), ("Advies", 60)]:
            ctk.CTkLabel(header2, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="e" if text != "Element" else "w").pack(side="left", padx=3, pady=2)

        self.umol_labels = {}
        for elem in ['Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo']:
            row = ctk.CTkFrame(umol_frame, fg_color="transparent")
            row.pack(fill="x", padx=5)
            ctk.CTkLabel(row, text=elem, width=70, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            lbl_umol = ctk.CTkLabel(row, text="0.0", width=70, anchor="e", font=ctk.CTkFont(size=12, family="Courier"))
            lbl_umol.pack(side="left", padx=3)
            lbl_ppm = ctk.CTkLabel(row, text="0.000", width=70, anchor="e", font=ctk.CTkFont(size=12, family="Courier"), text_color="gray50")
            lbl_ppm.pack(side="left", padx=3)
            rec = RECOMMENDED_UMOL.get(elem, '')
            ctk.CTkLabel(row, text=str(rec), width=60, anchor="e", font=ctk.CTkFont(size=11), text_color="gray40").pack(side="left", padx=3)
            self.umol_labels[elem] = (lbl_umol, lbl_ppm)

        # Ratios
        ratio_frame = ctk.CTkFrame(self)
        ratio_frame.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(ratio_frame, text="Verhoudingen", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=5)
        rg = ctk.CTkFrame(ratio_frame, fg_color="transparent")
        rg.pack(fill="x", padx=10, pady=5)

        self.ratio_labels = {}
        for key, label in [('nk', 'N:K'), ('kca', 'K:Ca'), ('mgca', 'Mg:Ca')]:
            col = ctk.CTkFrame(rg, fg_color=("gray90", "gray20"), corner_radius=8)
            col.pack(side="left", expand=True, fill="x", padx=3)
            ctk.CTkLabel(col, text=label, font=ctk.CTkFont(size=10), text_color="gray50").pack()
            lbl = ctk.CTkLabel(col, text="0.00", font=ctk.CTkFont(size=14, weight="bold"))
            lbl.pack(pady=(0, 5))
            self.ratio_labels[key] = lbl

    def update(self, results: CalcResults):
        self.ec_labels['a'].configure(text=f"{results.total_ec_a:.3f}")
        self.ec_labels['b'].configure(text=f"{results.total_ec_b:.3f}")
        self.ec_labels['c'].configure(text=f"{results.total_ec_c:.3f}")
        self.ec_labels['total'].configure(text=f"{results.total_ec:.3f}")

        mmol = results.mmol_scaled
        ppm_m = results.ppm_mmol
        for elem, (lbl_m, lbl_p) in self.mmol_labels.items():
            attr = elem.lower()
            val = getattr(mmol, attr, 0)
            ppm_val = ppm_m.get(elem, 0)
            lbl_m.configure(text=f"{val:.2f}")
            lbl_p.configure(text=f"{ppm_val:.0f}")

        umol = results.umol_scaled
        ppm_u = results.ppm_umol
        for elem, (lbl_u, lbl_p) in self.umol_labels.items():
            attr = elem.lower()
            val = getattr(umol, attr, 0)
            ppm_val = ppm_u.get(elem, 0)
            lbl_u.configure(text=f"{val:.1f}")
            lbl_p.configure(text=f"{ppm_val:.3f}")

        self.ratio_labels['nk'].configure(text=f"{results.ratio_nk:.2f}")
        self.ratio_labels['kca'].configure(text=f"{results.ratio_kca:.2f}")
        self.ratio_labels['mgca'].configure(text=f"{results.ratio_mgca:.2f}")
