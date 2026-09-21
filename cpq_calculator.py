import tkinter as tk
from tkinter import messagebox, ttk


class SalesforceCalculationEngineUI:

  def __init__(self, root):
    self.root = root
    self.root.title("Salesforce CPQ Calculation Engine & Verification UI")
    self.root.geometry("980x860")
    self.root.minsize(900, 750)

    # State flag to prevent recursive updates between Years and Months
    self.updating_duration = False

    # Styling: Clean, normal, non-fancy standard enterprise look
    self.setup_styles()

    # Main layout container
    self.main_container = ttk.Frame(self.root, padding="15")
    self.main_container.pack(fill=tk.BOTH, expand=True)

    # Build interface components
    self.build_header()
    self.build_inputs()
    self.build_action_bar()
    self.build_results_table()

    # Initial run with sample values from test sheets
    self.recalculate()

  def setup_styles(self):
    self.style = ttk.Style()
    self.style.theme_use("clam")

    # Font definitions
    self.style.configure(
        "Title.TLabel", font=("Arial", 13, "bold"), foreground="#1e293b"
    )
    self.style.configure(
        "Sub.TLabel", font=("Arial", 9), foreground="#475569"
    )
    self.style.configure(
        "Group.TLabelframe.Label",
        font=("Arial", 9, "bold"),
        foreground="#0f172a",
    )
    self.style.configure("TLabel", font=("Arial", 9))
    self.style.configure("TButton", font=("Arial", 9))
    self.style.configure("Treeview.Heading", font=("Arial", 9, "bold"))
    self.style.configure("Treeview", font=("Arial", 9), rowheight=24)

  def build_header(self):
    hdr = ttk.Frame(self.main_container)
    hdr.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(
        hdr,
        text="Salesforce CPQ Price & Margin Calculation Engine",
        style="Title.TLabel",
    ).pack(anchor="w")
    ttk.Label(
        hdr,
        text=(
            "Supports Service, SaaS, and Hardware item types with Salesforce"
            " decimal accuracy comparison."
        ),
        style="Sub.TLabel",
    ).pack(anchor="w")
    ttk.Separator(self.main_container, orient=tk.HORIZONTAL).pack(
        fill=tk.X, pady=(4, 12)
    )

  def build_inputs(self):
    box = ttk.LabelFrame(
        self.main_container,
        text=" Quote Line Inputs ",
        style="Group.TLabelframe",
        padding=10,
    )
    box.pack(fill=tk.X, pady=(0, 10))

    box.columnconfigure(1, weight=1)
    box.columnconfigure(3, weight=1)

    # Row 0: Item Type & Duration Multiplier Behavior
    ttk.Label(box, text="Item Type:").grid(
        row=0, column=0, sticky="w", padx=6, pady=4
    )
    self.var_item_type = tk.StringVar(value="Service")
    cb_type = ttk.Combobox(
        box,
        textvariable=self.var_item_type,
        values=["Service", "SaaS", "Hardware / Software"],
        state="readonly",
        width=20,
    )
    cb_type.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
    cb_type.bind("<<ComboboxSelected>>", self.on_item_type_change)

    self.var_mult_term = tk.BooleanVar(value=True)
    self.chk_mult = ttk.Checkbutton(
        box,
        text="Multiply Unit Cost & Price by Duration (Term Compounding)",
        variable=self.var_mult_term,
        command=self.recalculate,
    )
    self.chk_mult.grid(
        row=0, column=2, columnspan=2, sticky="w", padx=6, pady=4
    )

    # Row 1: List Price & Quantity
    ttk.Label(box, text="Unit List Price ($):").grid(
        row=1, column=0, sticky="w", padx=6, pady=4
    )
    self.ent_lp = ttk.Entry(box)
    self.ent_lp.insert(0, "9.00")
    self.ent_lp.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(box, text="Quantity:").grid(
        row=1, column=2, sticky="w", padx=6, pady=4
    )
    self.ent_qty = ttk.Entry(box)
    self.ent_qty.insert(0, "10")
    self.ent_qty.grid(row=1, column=3, sticky="ew", padx=6, pady=4)

    # Row 2: Duration in Years & Months (Auto-Converting pair)
    self.lbl_years = ttk.Label(box, text="Service Duration (Years):")
    self.lbl_years.grid(row=2, column=0, sticky="w", padx=6, pady=4)
    self.ent_years = ttk.Entry(box)
    self.ent_years.insert(0, "3")
    self.ent_years.grid(row=2, column=1, sticky="ew", padx=6, pady=4)

    self.lbl_months = ttk.Label(box, text="Initial Term (Months):")
    self.lbl_months.grid(row=2, column=2, sticky="w", padx=6, pady=4)
    self.ent_months = ttk.Entry(box)
    self.ent_months.insert(0, "36")
    self.ent_months.grid(row=2, column=3, sticky="ew", padx=6, pady=4)

    # Row 3: VAR Discount % & Customer Discount %
    ttk.Label(box, text="VAR Discount %:").grid(
        row=3, column=0, sticky="w", padx=6, pady=4
    )
    self.ent_var_disc = ttk.Entry(box)
    self.ent_var_disc.insert(0, "45.00")
    self.ent_var_disc.grid(row=3, column=1, sticky="ew", padx=6, pady=4)

    ttk.Label(box, text="Customer Discount %:").grid(
        row=3, column=2, sticky="w", padx=6, pady=4
    )
    self.ent_cust_disc = ttk.Entry(box)
    self.ent_cust_disc.insert(0, "0.00")
    self.ent_cust_disc.grid(row=3, column=3, sticky="ew", padx=6, pady=4)

    # Bind dynamic listener on all entries
    self.ent_years.bind("<KeyRelease>", self.on_years_edit)
    self.ent_months.bind("<KeyRelease>", self.on_months_edit)

    for e in [self.ent_lp, self.ent_qty, self.ent_var_disc, self.ent_cust_disc]:
      e.bind("<KeyRelease>", lambda evt: self.recalculate())

  def on_years_edit(self, event=None):
    if self.updating_duration:
      return
    try:
      self.updating_duration = True
      val = self.ent_years.get().strip()
      if val:
        y = float(val)
        m = y * 12.0
        self.ent_months.delete(0, tk.END)
        self.ent_months.insert(
            0, f"{int(m)}" if m.is_integer() else f"{m:.2f}"
        )
    except ValueError:
      pass
    finally:
      self.updating_duration = False
      self.recalculate()

  def on_months_edit(self, event=None):
    if self.updating_duration:
      return
    try:
      self.updating_duration = True
      val = self.ent_months.get().strip()
      if val:
        m = float(val)
        y = m / 12.0
        self.ent_years.delete(0, tk.END)
        self.ent_years.insert(
            0, f"{int(y)}" if y.is_integer() else f"{y:.4f}"
        )
    except ValueError:
      pass
    finally:
      self.updating_duration = False
      self.recalculate()

  def on_item_type_change(self, event=None):
    itype = self.var_item_type.get()
    if itype == "Service":
      self.ent_years.config(state="normal")
      self.ent_months.config(state="normal")
      self.chk_mult.config(state="normal")
      self.var_mult_term.set(True)
    elif itype == "SaaS":
      self.ent_years.config(state="normal")
      self.ent_months.config(state="normal")
      self.chk_mult.config(state="normal")
      self.var_mult_term.set(True)
    else:  # Hardware / Software
      self.updating_duration = True
      self.ent_years.delete(0, tk.END)
      self.ent_years.insert(0, "1")
      self.ent_months.delete(0, tk.END)
      self.ent_months.insert(0, "12")
      self.updating_duration = False

      self.ent_years.config(state="disabled")
      self.ent_months.config(state="disabled")
      self.chk_mult.config(state="disabled")
      self.var_mult_term.set(False)

    self.recalculate()

  def build_action_bar(self):
    bar = ttk.Frame(self.main_container)
    bar.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(
        bar, text="Recalculate", command=self.recalculate, width=14
    ).pack(side=tk.LEFT, padx=(0, 8))

    ttk.Label(bar, text="Load Sheet Scenario:").pack(side=tk.LEFT, padx=(8, 4))

    ttk.Button(
        bar,
        text="Scenario 1: Service (3 Yrs / 36 Mo)",
        command=lambda: self.load_preset(
            9.0, 10, 3.0, 45.0, 0.0, "Service", True
        ),
    ).pack(side=tk.LEFT, padx=3)

    ttk.Button(
        bar,
        text="Scenario 2: SaaS (Term = 1)",
        command=lambda: self.load_preset(
            74.75, 83, 1 / 12, 39.55, 19.0, "SaaS", False
        ),
    ).pack(side=tk.LEFT, padx=3)

    ttk.Button(
        bar,
        text="Scenario 3: Maint Service (Sheet Baseline)",
        command=lambda: self.load_preset(
            445.34, 1, 3.0, 60.10, 19.0, "Service", True
        ),
    ).pack(side=tk.LEFT, padx=3)

  def load_preset(
      self, lp, qty, years, var_disc, cust_disc, itype, mult_term
  ):
    self.var_item_type.set(itype)
    self.var_mult_term.set(mult_term)
    self.on_item_type_change()

    self.ent_lp.delete(0, tk.END)
    self.ent_lp.insert(0, str(lp))

    self.ent_qty.delete(0, tk.END)
    self.ent_qty.insert(0, str(qty))

    self.updating_duration = True
    self.ent_years.delete(0, tk.END)
    self.ent_years.insert(
        0, f"{int(years)}" if float(years).is_integer() else f"{years:.4f}"
    )

    m = float(years) * 12.0
    self.ent_months.delete(0, tk.END)
    self.ent_months.insert(
        0, f"{int(m)}" if m.is_integer() else f"{m:.2f}"
    )
    self.updating_duration = False

    self.ent_var_disc.delete(0, tk.END)
    self.ent_var_disc.insert(0, str(var_disc))

    self.ent_cust_disc.delete(0, tk.END)
    self.ent_cust_disc.insert(0, str(cust_disc))

    self.recalculate()

  def build_results_table(self):
    res_frame = ttk.LabelFrame(
        self.main_container,
        text=" Salesforce CPQ Pricing & Verification Output ",
        style="Group.TLabelframe",
        padding=10,
    )
    res_frame.pack(fill=tk.BOTH, expand=True)

    # Top KPI Metrics Strip
    self.kpi_bar = ttk.Frame(res_frame)
    self.kpi_bar.pack(fill=tk.X, pady=(0, 10))

    self.lbl_kpi_total_lp = ttk.Label(
        self.kpi_bar,
        text="Extended List: $0.00",
        font=("Arial", 9, "bold"),
        foreground="#0f172a",
    )
    self.lbl_kpi_total_lp.pack(side=tk.LEFT, padx=(4, 15))

    self.lbl_kpi_cost = ttk.Label(
        self.kpi_bar,
        text="VAR Cost: $0.00",
        font=("Arial", 9, "bold"),
        foreground="#b91c1c",
    )
    self.lbl_kpi_cost.pack(side=tk.LEFT, padx=15)

    self.lbl_kpi_cust = ttk.Label(
        self.kpi_bar,
        text="Cust Price: $0.00",
        font=("Arial", 9, "bold"),
        foreground="#15803d",
    )
    self.lbl_kpi_cust.pack(side=tk.LEFT, padx=15)

    self.lbl_kpi_profit = ttk.Label(
        self.kpi_bar,
        text="Profit: $0.00 (0.00%)",
        font=("Arial", 9, "bold"),
        foreground="#0284c7",
    )
    self.lbl_kpi_profit.pack(side=tk.LEFT, padx=15)

    # Treeview Columns
    cols = ("section", "api_name", "label", "sf_value", "raw_value", "formula")
    self.tree = ttk.Treeview(res_frame, columns=cols, show="headings", height=15)

    self.tree.heading("section", text="Section")
    self.tree.heading("api_name", text="Salesforce Field API")
    self.tree.heading("label", text="Field Description")
    self.tree.heading("sf_value", text="Salesforce Currency (2 Dec)")
    self.tree.heading("raw_value", text="Engine Raw Value (Up to 8 Dec)")
    self.tree.heading("formula", text="Engine Formula Reference")

    self.tree.column("section", width=80, anchor="w")
    self.tree.column("api_name", width=170, anchor="w")
    self.tree.column("label", width=170, anchor="w")
    self.tree.column("sf_value", width=150, anchor="e")
    self.tree.column("raw_value", width=170, anchor="e")
    self.tree.column("formula", width=220, anchor="w")

    sb = ttk.Scrollbar(res_frame, orient=tk.VERTICAL, command=self.tree.yview)
    self.tree.configure(yscrollcommand=sb.set)
    self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

  def recalculate(self):
    try:
      lp = float(self.ent_lp.get().strip())
      qty = float(self.ent_qty.get().strip())
      years = float(self.ent_years.get().strip())
      months = float(self.ent_months.get().strip())
      var_disc = float(self.ent_var_disc.get().strip()) / 100.0
      cust_disc = float(self.ent_cust_disc.get().strip()) / 100.0
    except ValueError:
      return

    itype = self.var_item_type.get()
    mult_term = self.var_mult_term.get()

    # Determine duration factor applied
    if itype == "Service":
      # In Service, duration in months is applied directly when term compounding is active
      duration_mult = months if mult_term else 1.0
      total_lp = lp * qty * (months if not mult_term else duration_mult)
    elif itype == "SaaS":
      duration_mult = months if mult_term else 1.0
      total_lp = lp * qty * (months if not mult_term else duration_mult)
    else:
      duration_mult = 1.0
      total_lp = lp * qty

    # 1. VAR Costs
    var_unit_cost = lp * (1.0 - var_disc) * duration_mult
    var_total_cost = var_unit_cost * qty

    # 2. Customer Pricing
    cust_unit_price = lp * (1.0 - cust_disc) * duration_mult
    cust_extended_price = cust_unit_price * qty

    # 3. Margins & Profitability
    margin = cust_unit_price - var_unit_cost
    margin_pct = (
        (margin / cust_unit_price * 100.0) if cust_unit_price != 0 else 0.0
    )
    markup_pct = (margin / var_unit_cost * 100.0) if var_unit_cost != 0 else 0.0
    total_profit = cust_extended_price - var_total_cost

    # Update Top KPI strip
    self.lbl_kpi_total_lp.config(text=f"Extended List: ${total_lp:,.2f}")
    self.lbl_kpi_cost.config(
        text=f"VAR Unit Cost: ${var_unit_cost:,.2f} (Total: ${var_total_cost:,.2f})"
    )
    self.lbl_kpi_cust.config(
        text=f"Cust Unit Price: ${cust_unit_price:,.2f} (Total: ${cust_extended_price:,.2f})"
    )
    self.lbl_kpi_profit.config(
        text=f"Profit: ${total_profit:,.2f} (Margin: {margin_pct:.2f}%)"
    )

    # Refresh output rows
    for itm in self.tree.get_children():
      self.tree.delete(itm)

    display_rows = [
        (
            "Source",
            "List_Price__c",
            "Unit List Price",
            f"${lp:,.2f}",
            f"{lp:.4f}",
            "Input",
        ),
        (
            "Source",
            "Quantity__c",
            "Quantity",
            f"{qty:,.0f}" if qty.is_integer() else f"{qty:,.2f}",
            str(qty),
            "Input",
        ),
        (
            "Source",
            "Service_Duration__c",
            "Service Duration (Years)",
            f"{years:,.2f} Yrs",
            f"{years:.4f}",
            "Input or Months / 12",
        ),
        (
            "Source",
            "Initial_Term__c",
            "Initial Term (Months)",
            f"{months:,.0f} Mo"
            if months.is_integer()
            else f"{months:,.2f} Mo",
            f"{months:.4f}",
            "Years * 12",
        ),
        (
            "Source",
            "Total_List_Price__c",
            "Extended List Price",
            f"${total_lp:,.2f}",
            f"{total_lp:.6f}",
            "List_Price * Qty * Months",
        ),
        (
            "VAR",
            "VAR_Discount_Pct__c",
            "VAR Discount %",
            f"{var_disc*100:.2f}%",
            f"{var_disc:.6f}",
            "Input",
        ),
        (
            "VAR",
            "VAR_Unit_Cost__c",
            "VAR Unit Cost",
            f"${var_unit_cost:,.2f}",
            f"{var_unit_cost:.6f}",
            "List_Price * (1 - VAR_Disc) * Months",
        ),
        (
            "VAR",
            "VAR_Total_Cost__c",
            "VAR Total Cost",
            f"${var_total_cost:,.2f}",
            f"{var_total_cost:.6f}",
            "VAR_Unit_Cost * Quantity",
        ),
        (
            "Customer",
            "Cust_Discount_Pct__c",
            "Customer Discount %",
            f"{cust_disc*100:.2f}%",
            f"{cust_disc:.6f}",
            "Input",
        ),
        (
            "Customer",
            "Cust_Unit_Price__c",
            "Customer Unit Price",
            f"${cust_unit_price:,.2f}",
            f"{cust_unit_price:.6f}",
            "List_Price * (1 - Cust_Disc) * Months",
        ),
        (
            "Customer",
            "Cust_Extended_Price__c",
            "Customer Total Price",
            f"${cust_extended_price:,.2f}",
            f"{cust_extended_price:.6f}",
            "Cust_Unit_Price * Quantity",
        ),
        (
            "Margin",
            "VAR_Margin__c",
            "Unit Margin ($)",
            f"${margin:,.2f}",
            f"{margin:.6f}",
            "Cust_Unit_Price - VAR_Unit_Cost",
        ),
        (
            "Margin",
            "VAR_Margin_Pct__c",
            "VAR Margin %",
            f"{margin_pct:.2f}%",
            f"{margin_pct/100:.6f}",
            "(Cust_Unit - VAR_Cost) / Cust_Unit",
        ),
        (
            "Margin",
            "VAR_Markup_Pct__c",
            "VAR Markup %",
            f"{markup_pct:.2f}%",
            f"{markup_pct/100:.6f}",
            "(Cust_Unit - VAR_Cost) / VAR_Cost",
        ),
        (
            "Margin",
            "VAR_Total_Profit__c",
            "Total Partner Profit",
            f"${total_profit:,.2f}",
            f"{total_profit:.6f}",
            "Cust_Extended - VAR_Total_Cost",
        ),
    ]

    for r in display_rows:
      self.tree.insert("", tk.END, values=r)


if __name__ == "__main__":
  root = tk.Tk()
  app = SalesforceCalculationEngineUI(root)
  root.mainloop()