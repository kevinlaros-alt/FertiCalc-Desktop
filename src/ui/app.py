"""FertiCalc hoofdvenster — matching web portal layout."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from ..engine.calculations import calculate, TankConfig, WaterAnalysis, DrainAnalysis, TargetValues
from ..data.excel_io import ensure_database, list_recipes, load_recipe, save_recipe, delete_recipe
from .tank_frame import TankColumn
from .water_frame import WaterFrame, DrainFrame
from .results_frame import ResultsBar, RatioBox


class FertiCalcApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FertiCalc - Bemestingscalculator")
        self.geometry("1400x850")
        self.minsize(1200, 700)
        self.configure(fg_color="#f3f4f6")

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        ensure_database()
        self.current_recipe_id = None
        self._updating = False
        self._mode = 'standard'

        self._build_navbar()
        self._build_sub_header()
        self._build_main()

    # === NAVBAR (dark green) ===

    def _build_navbar(self):
        nav = ctk.CTkFrame(self, height=48, fg_color="#166534", corner_radius=0)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text="  FertiCalc", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").pack(side="left", padx=10)

        # Right side: Save + Save As + Print
        btn_frame = ctk.CTkFrame(nav, fg_color="transparent")
        btn_frame.pack(side="right", padx=15)

        ctk.CTkButton(btn_frame, text="Print", width=50, height=32,
                      command=self._print, fg_color="transparent",
                      border_width=1, border_color="#86efac",
                      text_color="white", hover_color="#14532d",
                      font=ctk.CTkFont(size=12)).pack(side="right", padx=3)
        ctk.CTkButton(btn_frame, text="Opslaan als...", width=100, height=32,
                      command=self._save_as, fg_color="transparent",
                      border_width=1, border_color="#86efac",
                      text_color="white", hover_color="#14532d",
                      font=ctk.CTkFont(size=12)).pack(side="right", padx=3)
        ctk.CTkButton(btn_frame, text="Opslaan", width=80, height=32,
                      command=self._save, fg_color="#dc2626",
                      hover_color="#b91c1c", text_color="white",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=3)
        ctk.CTkButton(btn_frame, text="Verwijder", width=70, height=32,
                      command=self._delete, fg_color="transparent",
                      border_width=1, border_color="#fca5a5",
                      text_color="#fca5a5", hover_color="#14532d",
                      font=ctk.CTkFont(size=11)).pack(side="right", padx=3)

    # === SUB-HEADER (recipe info + mode tabs) ===

    def _build_sub_header(self):
        sub = ctk.CTkFrame(self, fg_color="white", height=90, corner_radius=0,
                           border_width=0)
        sub.pack(fill="x")

        # Row 1: Recipe info
        row1 = ctk.CTkFrame(sub, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(8, 4))

        # Recipe selector
        self.recipe_var = ctk.StringVar(value="-- Nieuw --")
        self.recipe_menu = ctk.CTkOptionMenu(
            row1, variable=self.recipe_var, values=["-- Nieuw --"],
            command=self._on_recipe_select, width=180, height=30,
            font=ctk.CTkFont(size=12)
        )
        self.recipe_menu.pack(side="left")
        self._refresh_recipe_list()

        # Name — with visible label
        ctk.CTkLabel(row1, text="Naam:", font=ctk.CTkFont(size=12),
                     text_color="#6b7280").pack(side="left", padx=(10, 2))
        self.var_name = ctk.StringVar(value="")
        name_entry = ctk.CTkEntry(row1, textvariable=self.var_name, width=160, height=30,
                     placeholder_text="Receptnaam",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     border_width=1, border_color="#d1d5db", fg_color="#f9fafb")
        name_entry.pack(side="left")

        # Crop — with visible label
        ctk.CTkLabel(row1, text="Gewas:", font=ctk.CTkFont(size=12),
                     text_color="#6b7280").pack(side="left", padx=(10, 2))
        self.var_crop = ctk.StringVar(value="")
        crop_entry = ctk.CTkEntry(row1, textvariable=self.var_crop, width=100, height=30,
                     placeholder_text="Gewas",
                     font=ctk.CTkFont(size=12),
                     border_width=1, border_color="#d1d5db", fg_color="#f9fafb")
        crop_entry.pack(side="left")

        # Desired EC
        ec_frame = ctk.CTkFrame(row1, fg_color="transparent")
        ec_frame.pack(side="left", padx=20)
        ctk.CTkLabel(ec_frame, text="Gewenste EC:", font=ctk.CTkFont(size=12),
                     text_color="#374151").pack(side="left", padx=(0, 5))
        self.var_desired_ec = ctk.StringVar(value="")
        self.var_desired_ec.trace_add('write', lambda *_: self._recalculate())
        ctk.CTkEntry(ec_frame, textvariable=self.var_desired_ec, width=60, height=30,
                     font=ctk.CTkFont(size=13, weight="bold"), justify="center",
                     border_width=1, border_color="#d1d5db").pack(side="left")

        # Drain % (for recirculation)
        self.drain_pct_frame = ctk.CTkFrame(row1, fg_color="transparent")
        ctk.CTkLabel(self.drain_pct_frame, text="Drain%:", font=ctk.CTkFont(size=12),
                     text_color="#2563eb").pack(side="left", padx=(0, 5))
        self.var_drain_pct = ctk.StringVar(value="0")
        self.var_drain_pct.trace_add('write', lambda *_: self._recalculate())
        ctk.CTkEntry(self.drain_pct_frame, textvariable=self.var_drain_pct, width=50, height=30,
                     font=ctk.CTkFont(size=12), justify="center",
                     fg_color="#dbeafe", border_color="#93c5fd", border_width=1).pack(side="left")

        # Row 2: Mode + Page tabs
        row2 = ctk.CTkFrame(sub, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 6))

        self.mode_var = ctk.StringVar(value="Zonder recirculatie")
        mode_seg = ctk.CTkSegmentedButton(
            row2, values=["Zonder recirculatie", "Met recirculatie"],
            variable=self.mode_var, command=self._on_mode_change,
            font=ctk.CTkFont(size=11), height=30,
        )
        mode_seg.pack(side="left")

        # Spacer
        ctk.CTkLabel(row2, text="", width=20).pack(side="left")

        self.page_var = ctk.StringVar(value="Bakken")
        page_seg = ctk.CTkSegmentedButton(
            row2, values=["Bakken", "Micro & Water"],
            variable=self.page_var, command=self._on_page_change,
            font=ctk.CTkFont(size=11), height=30,
        )
        page_seg.pack(side="left")

    # === MAIN CONTENT ===

    def _build_main(self):
        # Page container
        self.page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.page_container.pack(fill="both", expand=True, padx=10, pady=(5, 0))

        # === PAGE 1: BAKKEN (3 columns) ===
        self.page_bakken = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.page_bakken.pack(fill="both", expand=True)

        tanks_row = ctk.CTkFrame(self.page_bakken, fg_color="transparent")
        tanks_row.pack(fill="both", expand=True)

        self.tank_frames = {}
        for key in ['A', 'B', 'C']:
            col = TankColumn(tanks_row, key, on_change=self._recalculate)
            col.pack(side="left", fill="both", expand=True, padx=3)
            self.tank_frames[key] = col

        # Ratio box below Tank C area
        ratio_row = ctk.CTkFrame(self.page_bakken, fg_color="transparent")
        ratio_row.pack(fill="x", pady=(4, 0))
        # Push to the right (under Tank C)
        ctk.CTkFrame(ratio_row, fg_color="transparent").pack(side="left", expand=True, fill="x")
        self.ratio_box = RatioBox(ratio_row)
        self.ratio_box.pack(side="right", padx=3)

        # === PAGE 2: MICRO & WATER (hidden) ===
        self.page_micro = ctk.CTkFrame(self.page_container, fg_color="transparent")

        micro_content = ctk.CTkFrame(self.page_micro, fg_color="transparent")
        micro_content.pack(fill="both", expand=True)

        # Left: Micro tank
        micro_col = ctk.CTkFrame(micro_content, fg_color="transparent")
        micro_col.pack(side="left", fill="both", expand=True, padx=3)
        self.tank_frames['micro'] = TankColumn(micro_col, 'micro', on_change=self._recalculate)
        self.tank_frames['micro'].pack(fill="both", expand=True)

        # Middle: Water analysis (hidden in recirculation mode)
        self.water_col = ctk.CTkScrollableFrame(micro_content, fg_color="white",
                                            corner_radius=8, border_color="#e5e7eb",
                                            width=280)
        self.water_col.pack(side="left", fill="y", padx=3)
        self.water_frame = WaterFrame(self.water_col, on_change=self._recalculate)
        self.water_frame.pack(fill="x")

        # Right: Drain analysis (for recirculation)
        self.drain_col = ctk.CTkScrollableFrame(micro_content, fg_color="white",
                                                 corner_radius=8, border_color="#93c5fd",
                                                 width=280)
        self.drain_frame = DrainFrame(self.drain_col, on_change=self._recalculate)
        self.drain_frame.pack(fill="x")

        # === RESULTS BAR (always visible at bottom) ===
        self.results_bar = ResultsBar(self)
        self.results_bar.pack(fill="x", padx=10, pady=(5, 8))

        self._recalculate()

    # === PAGE + MODE SWITCHING ===

    def _on_page_change(self, page):
        if page == "Bakken":
            self.page_micro.pack_forget()
            self.page_bakken.pack(fill="both", expand=True)
        else:
            self.page_bakken.pack_forget()
            self.page_micro.pack(fill="both", expand=True)

    def _on_mode_change(self, mode_label):
        self._mode = 'recirculation' if mode_label == "Met recirculatie" else 'standard'
        if self._mode == 'recirculation':
            self.drain_pct_frame.pack(side="left", padx=20)
            # Hide water analysis, show drain analysis (matching web)
            self.water_col.pack_forget()
            self.drain_col.pack(side="left", fill="y", padx=3)
            self.results_bar.set_recirculation(True)
        else:
            self.drain_pct_frame.pack_forget()
            self.drain_col.pack_forget()
            # Show water analysis again
            self.water_col.pack(side="left", fill="y", padx=3)
            self.results_bar.set_recirculation(False)
        self._recalculate()

    # === CALCULATION ===

    def _recalculate(self):
        if self._updating:
            return

        tank_a = self.tank_frames['A'].get_config()
        tank_b = self.tank_frames['B'].get_config()
        tank_c = self.tank_frames['C'].get_config()
        micro = self.tank_frames['micro'].get_config()
        water = self.water_frame.get_analysis()

        try:
            desired_ec = float(self.var_desired_ec.get().replace(',', '.'))
        except (ValueError, TypeError):
            desired_ec = 0

        drain_pct = 0
        drain = None
        if self._mode == 'recirculation':
            try:
                drain_pct = float(self.var_drain_pct.get().replace(',', '.')) / 100
            except (ValueError, TypeError):
                drain_pct = 0
            drain = self.drain_frame.get_analysis()

        results = calculate(
            tank_a, tank_b, tank_c, micro, desired_ec, water,
            mode=self._mode,
            drain_percentage=drain_pct,
            drain_analysis=drain,
        )

        for key in ['A', 'B', 'C', 'micro']:
            self.tank_frames[key].update_results(results.tank_results.get(key, []))

        # Update auto-calculated verdunning/dosering on Tank A, B (and micro uses same)
        auto_dil = results.auto_dilution
        auto_dose = results.auto_dose
        self.tank_frames['A'].update_auto_dilution(auto_dil, auto_dose)
        self.tank_frames['B'].update_auto_dilution(auto_dil, auto_dose)
        self.tank_frames['micro'].update_auto_dilution(auto_dil, auto_dose)
        # Tank C keeps its original dilution (not auto-calculated)
        c_config = self.tank_frames['C'].get_config()
        self.tank_frames['C'].update_auto_dilution(c_config.dilution, c_config.dose)

        self.results_bar.update(results, desired_ec)
        self.ratio_box.update(results)

    # === RECIPES ===

    def _refresh_recipe_list(self):
        recipes = list_recipes()
        self._recipes = {r['name']: r['id'] for r in recipes}
        values = ["-- Nieuw --"] + [r['name'] for r in recipes]
        self.recipe_menu.configure(values=values)

    def _on_recipe_select(self, choice):
        if choice == "-- Nieuw --":
            self._new_recipe()
            return

        recipe_id = self._recipes.get(choice)
        if not recipe_id:
            return

        data = load_recipe(recipe_id)
        if not data:
            messagebox.showerror("Fout", "Recept niet gevonden")
            return

        self._updating = True
        self.current_recipe_id = data['id']
        self.var_name.set(data['name'])
        self.var_crop.set(data['crop'])
        self.var_desired_ec.set(str(data['desired_ec']) if data['desired_ec'] else "")

        self.tank_frames['A'].set_config(data['tank_a'])
        self.tank_frames['B'].set_config(data['tank_b'])
        self.tank_frames['C'].set_config(data['tank_c'])
        self.tank_frames['micro'].set_config(data['micro'])
        self.water_frame.set_analysis(data['water'])

        mode = data.get('mode', 'standard')
        self._mode = mode
        self.mode_var.set("Met recirculatie" if mode == 'recirculation' else "Zonder recirculatie")
        self._on_mode_change(self.mode_var.get())

        # Always set drain data (even if zero/default)
        drain_pct_val = data.get('drain_percentage', 0) or 0
        self.var_drain_pct.set(str(drain_pct_val * 100))
        drain_da = data.get('drain_analysis')
        if drain_da:
            self.drain_frame.set_analysis(drain_da)

        if data.get('target_values'):
            self.results_bar.set_targets(data['target_values'])

        self._updating = False
        self._recalculate()

    def _new_recipe(self):
        self._updating = True
        self.current_recipe_id = None
        self.var_name.set("")
        self.var_crop.set("")
        self.var_desired_ec.set("")
        self._mode = 'standard'
        self.mode_var.set("Zonder recirculatie")
        self.var_drain_pct.set("0")

        for frame in self.tank_frames.values():
            frame.set_config(TankConfig())
        self.water_frame.set_analysis(WaterAnalysis())
        self.drain_frame.set_analysis(DrainAnalysis())
        self.results_bar.set_targets(TargetValues())

        self._on_mode_change("Zonder recirculatie")
        self._updating = False
        self._recalculate()

    def _save(self):
        name = self.var_name.get().strip()
        if not name:
            messagebox.showwarning("Naam vereist", "Vul een receptnaam in.")
            return
        self._do_save(name, self.current_recipe_id)

    def _save_as(self):
        name = ctk.CTkInputDialog(text="Nieuwe receptnaam:", title="Opslaan als...").get_input()
        if not name or not name.strip():
            return
        self._do_save(name.strip(), None)

    def _do_save(self, name, recipe_id):
        try:
            desired_ec = float(self.var_desired_ec.get().replace(',', '.'))
        except (ValueError, TypeError):
            desired_ec = 0
        try:
            drain_pct = float(self.var_drain_pct.get().replace(',', '.')) / 100
        except (ValueError, TypeError):
            drain_pct = 0

        rid = save_recipe(
            recipe_id=recipe_id,
            name=name,
            crop=self.var_crop.get().strip(),
            tank_a=self.tank_frames['A'].get_config(),
            tank_b=self.tank_frames['B'].get_config(),
            tank_c=self.tank_frames['C'].get_config(),
            micro=self.tank_frames['micro'].get_config(),
            desired_ec=desired_ec,
            water=self.water_frame.get_analysis(),
            mode=self._mode,
            drain_percentage=drain_pct,
            drain_analysis=self.drain_frame.get_analysis(),
            target_values=self.results_bar.get_targets(),
        )
        self.current_recipe_id = rid
        self.var_name.set(name)
        self._refresh_recipe_list()
        self.recipe_var.set(name)
        messagebox.showinfo("Opgeslagen", f"Recept '{name}' opgeslagen.")

    def _delete(self):
        if self.current_recipe_id is None:
            return
        name = self.var_name.get()
        if not messagebox.askyesno("Verwijderen", f"Weet je zeker dat je '{name}' wilt verwijderen?"):
            return
        delete_recipe(self.current_recipe_id)
        self._refresh_recipe_list()
        self._new_recipe()
        self.recipe_var.set("-- Nieuw --")

    # === PRINT ===

    def _print(self):
        try:
            desired_ec = float(self.var_desired_ec.get().replace(',', '.'))
        except (ValueError, TypeError):
            desired_ec = 0

        drain_pct = 0
        drain = None
        if self._mode == 'recirculation':
            try:
                drain_pct = float(self.var_drain_pct.get().replace(',', '.')) / 100
            except (ValueError, TypeError):
                drain_pct = 0
            drain = self.drain_frame.get_analysis()

        results = calculate(
            self.tank_frames['A'].get_config(),
            self.tank_frames['B'].get_config(),
            self.tank_frames['C'].get_config(),
            self.tank_frames['micro'].get_config(),
            desired_ec,
            self.water_frame.get_analysis(),
            mode=self._mode,
            drain_percentage=drain_pct,
            drain_analysis=drain,
        )

        recipe_name = self.var_name.get() or 'Naamloos'
        crop = self.var_crop.get() or '-'
        date_str = datetime.now().strftime('%d %B %Y')

        # Build print window
        win = ctk.CTkToplevel(self)
        win.title(f"Print - {recipe_name}")
        win.geometry("1100x700")
        win.configure(fg_color="white")

        # Header
        hdr = ctk.CTkFrame(win, fg_color="white")
        hdr.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(hdr, text=recipe_name, font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#1f2937").pack(side="left")
        ctk.CTkLabel(hdr, text=date_str, font=ctk.CTkFont(size=12),
                     text_color="#6b7280").pack(side="right")

        info = ctk.CTkFrame(win, fg_color="white")
        info.pack(fill="x", padx=20)
        ctk.CTkLabel(info, text=f"Gewas: {crop}", font=ctk.CTkFont(size=12),
                     text_color="#6b7280").pack(side="left")
        ctk.CTkLabel(info, text=f"Gewenste EC: {desired_ec}",
                     font=ctk.CTkFont(size=12), text_color="#6b7280").pack(side="left", padx=20)

        if self._mode == 'recirculation':
            ctk.CTkLabel(info, text=f"Drain: {drain_pct*100:.0f}%  |  EC uit A/B: {results.ec_ab:.3f}  |  EC uit drain: {results.ec_drain:.3f}",
                         font=ctk.CTkFont(size=12), text_color="#2563eb").pack(side="left", padx=20)

        ctk.CTkFrame(win, fg_color="#e5e7eb", height=1).pack(fill="x", padx=20, pady=5)

        # Tank summary
        tanks_frame = ctk.CTkFrame(win, fg_color="white")
        tanks_frame.pack(fill="x", padx=20, pady=5)

        for key, label, color, ec_val in [
            ('A', 'Tank A', '#15803d', results.total_ec_a),
            ('B', 'Tank B', '#16a34a', results.total_ec_b),
            ('C', 'Tank C', '#d97706', results.total_ec_c),
        ]:
            col = ctk.CTkFrame(tanks_frame, fg_color="white")
            col.pack(side="left", fill="both", expand=True, padx=5)

            hdr_bar = ctk.CTkFrame(col, fg_color=color, corner_radius=4, height=28)
            hdr_bar.pack(fill="x")
            hdr_bar.pack_propagate(False)
            ctk.CTkLabel(hdr_bar, text=label, text_color="white",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)
            ctk.CTkLabel(hdr_bar, text=f"EC: {ec_val:.3f}", text_color="white",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=8)

            tank_config = self.tank_frames[key].get_config()
            for fid, qty in tank_config.entries.items():
                if qty > 0:
                    from ..engine.fertilizers import FERT_BY_ID
                    fdef = FERT_BY_ID.get(fid)
                    fname = fdef.name if fdef else fid
                    row = ctk.CTkFrame(col, fg_color="white")
                    row.pack(fill="x")
                    ctk.CTkLabel(row, text=fname, font=ctk.CTkFont(size=10),
                                 text_color="#374151").pack(side="left", padx=8)
                    unit = 'gr' if key == 'micro' else 'Kg'
                    ctk.CTkLabel(row, text=f"{qty:.1f} {unit}", font=ctk.CTkFont(size=10),
                                 text_color="#1f2937").pack(side="right", padx=8)

        ctk.CTkFrame(win, fg_color="#e5e7eb", height=1).pack(fill="x", padx=20, pady=5)

        # Berekende waarden
        calc_frame = ctk.CTkFrame(win, fg_color="white")
        calc_frame.pack(fill="x", padx=20, pady=5)

        # Header row
        ctk.CTkLabel(calc_frame, text="", width=70, font=ctk.CTkFont(size=10)).grid(row=0, column=0)
        all_elems = ['EC', 'NH4', 'NO3', 'K', 'Ca', 'Mg', 'H2PO4', 'SO4', 'Cl', 'Na',
                     'Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo']
        for i, elem in enumerate(all_elems):
            color = "#ea580c" if elem in ['Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo'] else "#374151"
            ctk.CTkLabel(calc_frame, text=elem, width=55, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=color, anchor="center").grid(row=0, column=i+1, padx=1)

        # Values row
        ctk.CTkLabel(calc_frame, text="Berekend", width=70, font=ctk.CTkFont(size=10),
                     text_color="#374151", anchor="w").grid(row=1, column=0)

        mmol = results.mmol_scaled
        umol = results.umol_scaled
        values = [
            f"{results.total_ec:.3f}",
            f"{mmol.nh4:.2f}", f"{mmol.no3:.2f}", f"{mmol.k:.2f}", f"{mmol.ca:.2f}",
            f"{mmol.mg:.2f}", f"{mmol.h2po4:.2f}", f"{mmol.so4:.2f}", f"{mmol.cl:.2f}", f"{mmol.na:.2f}",
            f"{umol.fe:.1f}", f"{umol.mn:.1f}", f"{umol.zn:.1f}", f"{umol.b:.1f}",
            f"{umol.cu:.1f}", f"{umol.mo:.1f}",
        ]
        for i, val in enumerate(values):
            color = "#ea580c" if i >= 10 else "#1f2937"
            ctk.CTkLabel(calc_frame, text=val, width=55, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=color, anchor="center").grid(row=1, column=i+1, padx=1)

        # Ratios
        ctk.CTkFrame(win, fg_color="#e5e7eb", height=1).pack(fill="x", padx=20, pady=5)
        ratio_row = ctk.CTkFrame(win, fg_color="white")
        ratio_row.pack(fill="x", padx=20)
        ctk.CTkLabel(ratio_row, text=f"Verhoudingen:   N:K {results.ratio_nk:.2f}   K:Ca {results.ratio_kca:.2f}   Mg:Ca {results.ratio_mgca:.2f}",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(side="left")
