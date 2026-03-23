"""FertiCalc hoofdvenster."""

import customtkinter as ctk
from tkinter import messagebox
from ..engine.calculations import calculate, TankConfig, WaterAnalysis
from ..data.excel_io import ensure_database, list_recipes, load_recipe, save_recipe, delete_recipe
from .tank_frame import TankFrame
from .water_frame import WaterFrame
from .results_frame import ResultsFrame


class FertiCalcApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FertiCalc - Bemestingscalculator")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        ensure_database()
        self.current_recipe_id = None
        self._updating = False

        self._build_toolbar()
        self._build_main()
        self._recalculate()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color=("#166534", "#14532d"))
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text="FertiCalc", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").pack(side="left", padx=15)

        # Recipe selector
        recipe_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        recipe_frame.pack(side="left", padx=20)

        ctk.CTkLabel(recipe_frame, text="Recept:", text_color="white",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.recipe_var = ctk.StringVar(value="-- Nieuw --")
        self.recipe_menu = ctk.CTkOptionMenu(
            recipe_frame, variable=self.recipe_var, values=["-- Nieuw --"],
            command=self._on_recipe_select, width=200
        )
        self.recipe_menu.pack(side="left")
        self._refresh_recipe_list()

        # Name + Crop
        ctk.CTkLabel(recipe_frame, text="Naam:", text_color="white").pack(side="left", padx=(15, 5))
        self.var_name = ctk.StringVar(value="")
        ctk.CTkEntry(recipe_frame, textvariable=self.var_name, width=150, placeholder_text="Receptnaam").pack(side="left")

        ctk.CTkLabel(recipe_frame, text="Gewas:", text_color="white").pack(side="left", padx=(10, 5))
        self.var_crop = ctk.StringVar(value="")
        ctk.CTkEntry(recipe_frame, textvariable=self.var_crop, width=120, placeholder_text="Gewas").pack(side="left")

        ctk.CTkLabel(recipe_frame, text="Gewenste EC:", text_color="white").pack(side="left", padx=(10, 5))
        self.var_desired_ec = ctk.StringVar(value="")
        ec_entry = ctk.CTkEntry(recipe_frame, textvariable=self.var_desired_ec, width=70,
                                fg_color=("#e8f0fe", "#1e3a5f"), justify="right")
        ec_entry.pack(side="left")
        self.var_desired_ec.trace_add('write', lambda *_: self._recalculate())

        # Buttons
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right", padx=15)

        ctk.CTkButton(btn_frame, text="Opslaan", width=80, command=self._save,
                      fg_color="#22c55e", hover_color="#16a34a").pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="Verwijder", width=80, command=self._delete,
                      fg_color="#dc2626", hover_color="#b91c1c").pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="Print", width=70, command=self._print,
                      fg_color="#3b82f6", hover_color="#2563eb").pack(side="left", padx=3)

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=5, pady=5)

        # Left: tabs + water
        left = ctk.CTkFrame(main, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        # Tabs
        self.tabview = ctk.CTkTabview(left, height=400)
        self.tabview.pack(fill="both", expand=True, padx=5)

        self.tank_frames = {}
        for key, label in [('A', 'Tank A'), ('B', 'Tank B'), ('C', 'Tank C'), ('micro', 'Micro')]:
            tab = self.tabview.add(label)
            frame = TankFrame(tab, key, on_change=self._recalculate)
            frame.pack(fill="both", expand=True)
            self.tank_frames[key] = frame

        # Right: water analysis + results
        right = ctk.CTkScrollableFrame(main, width=310)
        right.pack(side="right", fill="y", padx=(0, 5))

        self.water_frame = WaterFrame(right, on_change=self._recalculate)
        self.water_frame.pack(fill="x", pady=(0, 5))

        self.results_frame = ResultsFrame(right)
        self.results_frame.pack(fill="x")

    def _recalculate(self):
        if self._updating:
            return

        tank_a = self.tank_frames['A'].get_config()
        tank_b = self.tank_frames['B'].get_config()
        tank_c = self.tank_frames['C'].get_config()
        micro = self.tank_frames['micro'].get_config()
        water = self.water_frame.get_analysis()

        try:
            desired_ec = float(self.var_desired_ec.get())
        except (ValueError, TypeError):
            desired_ec = 0

        results = calculate(tank_a, tank_b, tank_c, micro, desired_ec, water)

        # Update tank result displays
        for key in ['A', 'B', 'C', 'micro']:
            self.tank_frames[key].update_results(results.tank_results.get(key, []))

        self.results_frame.update(results)

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
        self._updating = False
        self._recalculate()

    def _new_recipe(self):
        self._updating = True
        self.current_recipe_id = None
        self.var_name.set("")
        self.var_crop.set("")
        self.var_desired_ec.set("")
        for frame in self.tank_frames.values():
            frame.set_config(TankConfig())
        self.water_frame.set_analysis(WaterAnalysis())
        self._updating = False
        self._recalculate()

    def _save(self):
        name = self.var_name.get().strip()
        if not name:
            messagebox.showwarning("Naam vereist", "Vul een receptnaam in.")
            return

        try:
            desired_ec = float(self.var_desired_ec.get())
        except (ValueError, TypeError):
            desired_ec = 0

        rid = save_recipe(
            recipe_id=self.current_recipe_id,
            name=name,
            crop=self.var_crop.get().strip(),
            tank_a=self.tank_frames['A'].get_config(),
            tank_b=self.tank_frames['B'].get_config(),
            tank_c=self.tank_frames['C'].get_config(),
            micro=self.tank_frames['micro'].get_config(),
            desired_ec=desired_ec,
            water=self.water_frame.get_analysis(),
        )
        self.current_recipe_id = rid
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

    def _print(self):
        """Simple print: open a text summary window."""
        try:
            desired_ec = float(self.var_desired_ec.get())
        except (ValueError, TypeError):
            desired_ec = 0

        results = calculate(
            self.tank_frames['A'].get_config(),
            self.tank_frames['B'].get_config(),
            self.tank_frames['C'].get_config(),
            self.tank_frames['micro'].get_config(),
            desired_ec,
            self.water_frame.get_analysis(),
        )

        lines = []
        lines.append(f"FertiCalc - {self.var_name.get() or 'Naamloos'}")
        lines.append(f"Gewas: {self.var_crop.get() or '-'}")
        lines.append(f"Gewenste EC: {desired_ec}")
        lines.append("=" * 50)
        lines.append(f"EC: Tank A={results.total_ec_a:.3f}  B={results.total_ec_b:.3f}  C={results.total_ec_c:.3f}  Totaal={results.total_ec:.3f}")
        lines.append("")
        lines.append("mmol/l:")
        m = results.mmol_scaled
        for elem in ['NO3', 'NH4', 'K', 'Ca', 'Mg', 'H2PO4', 'SO4', 'Cl']:
            val = getattr(m, elem.lower(), 0)
            ppm = results.ppm_mmol.get(elem, 0)
            lines.append(f"  {elem:8s}  {val:8.2f} mmol  {ppm:8.0f} ppm")
        lines.append("")
        lines.append("umol/l:")
        u = results.umol_scaled
        for elem in ['Fe', 'Mn', 'Zn', 'B', 'Cu', 'Mo']:
            val = getattr(u, elem.lower(), 0)
            ppm = results.ppm_umol.get(elem, 0)
            lines.append(f"  {elem:8s}  {val:8.1f} umol  {ppm:8.3f} ppm")
        lines.append("")
        lines.append(f"N:K = {results.ratio_nk:.2f}   K:Ca = {results.ratio_kca:.2f}   Mg:Ca = {results.ratio_mgca:.2f}")

        # Show in new window
        win = ctk.CTkToplevel(self)
        win.title("Print Preview")
        win.geometry("500x600")
        txt = ctk.CTkTextbox(win, font=ctk.CTkFont(family="Courier", size=12))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", "\n".join(lines))
        txt.configure(state="disabled")
