import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import indicators
import threading

plt.style.use('seaborn-v0_8-darkgrid')


class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("EcoVol Dashboard")
        self.geometry = root.geometry("1200x800")

        #Global status bar
        self.master_status  = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.master_status.pack(side=tk.BOTTOM, fill=tk.X)

        #Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        #Add all indicator tabs
        self.vixspread_tab = VixSpread(self.notebook)
        self.notebook.add(self.vixspread_tab, text="VIX Spread")

        self.volspread_tab = VolSpread(self.notebook)
        self.notebook.add(self.volspread_tab, text="Volatility Spread")

        self.autocorr_tab = VixAutocorr(self.notebook)
        self.notebook.add(self.autocorr_tab, text="Autocorrelation")


        self.composite_tab = Composite(self.notebook, [self.vixspread_tab.indicator, 
                                                       self.volspread_tab.indicator, 
                                                       self.autocorr_tab.indicator])
        self.notebook.add(self.composite_tab, text="Composite")

        

        #Start the global sequence after window is drawn
        self.indicator_tabs = [self.vixspread_tab, self.volspread_tab, self.autocorr_tab,self.composite_tab] #Add other tabs as needed
        self.root.after(500, self.start_global_load)

    def start_global_load(self):
        #Runs the sequential loading in a background thread
        threading.Thread(target=self.global_load_worker, daemon=True).start()
    
    def global_load_worker(self):
        for i, tab in enumerate(self.indicator_tabs):
            self.master_status.config(text=f"Loading {i+1}/{len(self.indicator_tabs)} indicators...")
            tab.run_update_thread(is_initial_load=True)
        
        self.master_status.config(text="System Ready - All Data Loaded")



class IndicatorModule(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.upper_input = tk.StringVar(value=self.indicator.upper)
        self.lower_input = tk.StringVar(value=self.indicator.lower)
        self.from_date_input = tk.StringVar(value=self.indicator.from_date)


        # --- Reserved for Data Display ---
        self.data_sidebar = tk.Frame(self, width=400, bg='darkgrey', padx=10, pady=10)
        self.data_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.data_sidebar.pack_propagate(False)
        tk.Label(self.data_sidebar, text="DATADISPLAY", font=('Arial', 10, 'bold'), bg='darkgrey').pack(pady=10)

        # --- Chart & Settings Container --
        self.main_container = tk.Frame(self)
        self.main_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Settings Box (Bottom) ---
        #self.settings_box = tk.Frame(self.main_container, height=300, bg='lightgrey', padx=10, pady=10)
        #self.settings_box.pack(side=tk.BOTTOM, fill=tk.X)
        #self.settings_box.pack_propagate(False)

        # --- Plot Area (Top) ---
        self.plot_area = tk.Frame(self.main_container, bg='white')
        self.plot_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 2. THE INNER GRID FRAME (The "Content Holder")
        # We pack this inside the settings_box
        self.grid_frame = tk.Frame(self.data_sidebar, bg='lightgrey')
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        # 3. CONFIGURE GRID ON THE INNER FRAME
        self.grid_frame.columnconfigure(0, weight=0)
        self.grid_frame.columnconfigure(1, weight=0)
        self.grid_frame.columnconfigure(2, weight=0)
        self.grid_frame.columnconfigure(3, weight=0)
        self.grid_frame.columnconfigure(4, weight=1)

        # --- Now use self.grid_frame for all your grid() calls ---
        tk.Label(self.grid_frame, text="INDICATOR PARAMETERS", 
                 font=('Arial', 10, 'bold'), bg='lightgrey')\
                 .grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 15))

        tk.Label(self.grid_frame, text="Upper Threshold:", bg='lightgrey')\
                 .grid(row=1, column=0, sticky='e', pady=5)
        
        self.upper_entry = tk.Entry(self.grid_frame, width=8, textvariable=self.upper_input)
        self.upper_entry.grid(row=1, column=1, sticky='w', padx=10)

        #Lower entry
        tk.Label(self.grid_frame, text="Lower Threshold:", bg='lightgrey')\
                 .grid(row=2, column=0, sticky='e', pady=5)
        self.lower_entry = tk.Entry(self.grid_frame, width=8, textvariable=self.lower_input)
        self.lower_entry.grid(row=2, column=1, sticky='w', padx=10)

        tk.Label(self.grid_frame, text="From Date:", bg='lightgrey')\
                 .grid(row=1, column=2, sticky='e', pady=5)
        self.from_date_entry = tk.Entry(self.grid_frame, width=15, textvariable=self.from_date_input)
        self.from_date_entry.grid(row=1, column=3, sticky='w', padx=10)

        #-- Updated Button --
        self.update_button = tk.Button(self.grid_frame, text="UPDATE", command=self.run_update_thread)
        self.update_button.grid(row=4, column=0, columnspan=2, pady=15, sticky='e')


        #Progress bar and loading logic
        self.status_var = tk.StringVar(value="Status: Ready")
        self.status_label = tk.Label(self.grid_frame, textvariable=self.status_var)
        self.status_label.grid(row=10, column=0, columnspan=5, pady=10)

    def run_update_thread(self, is_initial_load=False):
        self.status_var.set("Status: Loading...")
        self.update_button.config(state='disabled')
        thread = threading.Thread(target = self.process_data_backend)
        thread.start()

    def process_data_backend(self):
        #Implemented in the child class
        pass


class VixSpread(IndicatorModule):
    def __init__(self, parent):
        self.indicator = indicators.VixSpread()
        self.avg_window_input = tk.StringVar(value=self.indicator.avg_window)
        super().__init__(parent)

        # Placeholders for Plot
        self.fig = Figure(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)        
        

        tk.Label(self.grid_frame, text="Avg. Window:", bg='lightgrey')\
                 .grid(row=3, column=0, sticky='e', pady=5)
        self.avg_window_entry = tk.Entry(self.grid_frame, width=8, textvariable=self.avg_window_input)
        self.avg_window_entry.grid(row=3, column=1, sticky='w', padx=10)


        # Override the button command to use our new threader
        self.update_button.config(command=self.run_update_thread)

    def process_data_backend(self):
        """HEAVY MATH - Runs in background thread"""
        try:
            # Sync inputs to indicator object
            self.indicator.upper = float(self.upper_input.get())
            self.indicator.lower = float(self.lower_input.get())
            self.indicator.avg_window = int(self.avg_window_input.get())
            
            # RUN THE CALCULATIONS
            self.indicator.indicator() 
            self.fig = self.indicator.plot_indicator(from_date=self.from_date_input.get())

            # Tell Main Thread to update UI
            self.after(0, self.update_ui_finished)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

    def update_ui_finished(self):
        """UI UPDATE - Runs in main thread"""
        for widget in self.plot_area.winfo_children():
            widget.destroy() # Clear old canvas/toolbar

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.status_var.set("Status: Updated")
        self.update_button.config(state='normal')

class VixAutocorr(IndicatorModule):
    def __init__(self, parent):
        self.indicator = indicators.AutoCorrVol()
        super().__init__(parent)

        # Placeholders for Plot
        self.fig = Figure(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)        
        


        # Override the button command to use our new threader
        self.update_button.config(command=self.run_update_thread)

    def process_data_backend(self):
        """HEAVY MATH - Runs in background thread"""
        try:
            # Sync inputs to indicator object
            self.indicator.upper = float(self.upper_input.get())
            self.indicator.lower = float(self.lower_input.get())
            
            # RUN THE CALCULATIONS
            data = dashboard.volspread_tab.indicator.indicator_data['actual_vol']
            self.indicator.indicator(data) 
            self.fig = self.indicator.plot_indicator(from_date=self.from_date_input.get())

            # Tell Main Thread to update UI
            self.after(0, self.update_ui_finished)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

    def update_ui_finished(self):
        """UI UPDATE - Runs in main thread"""
        for widget in self.plot_area.winfo_children():
            widget.destroy() # Clear old canvas/toolbar

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.status_var.set("Status: Updated")
        self.update_button.config(state='normal')


class VolSpread(IndicatorModule):
    def __init__(self, parent):
        self.indicator = indicators.VolSpread()
        self.avg_window_input = tk.StringVar(value=self.indicator.avg_window)
        super().__init__(parent)

        # Placeholders for Plot
        self.fig = Figure(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)        
        

        tk.Label(self.grid_frame, text="Avg. Window:", bg='lightgrey')\
                 .grid(row=3, column=0, sticky='e', pady=5)
        self.avg_window_entry = tk.Entry(self.grid_frame, width=8, textvariable=self.avg_window_input)
        self.avg_window_entry.grid(row=3, column=1, sticky='w', padx=10)

        # Override the button command to use our new threader
        self.update_button.config(command=self.run_update_thread)

    def process_data_backend(self):
        """HEAVY MATH - Runs in background thread"""
        try:
            # Sync inputs to indicator object
            self.indicator.upper = float(self.upper_input.get())
            self.indicator.lower = float(self.lower_input.get())
            self.indicator.avg_window = int(self.avg_window_input.get())
            
            # RUN THE CALCULATIONS
            self.indicator.indicator() 
            self.fig = self.indicator.plot_indicator(from_date=self.from_date_input.get())

            # Tell Main Thread to update UI
            self.after(0, self.update_ui_finished)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

    def update_ui_finished(self):
        """UI UPDATE - Runs in main thread"""
        for widget in self.plot_area.winfo_children():
            widget.destroy() # Clear old canvas/toolbar

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.status_var.set("Status: Updated")
        self.update_button.config(state='normal')
  
class Composite(IndicatorModule):
    def __init__(self, parent, indicators_list):
        self.indicator = indicators.Composite(indicators_list)
        super().__init__(parent)

        # Placeholders for Plot
        self.fig = Figure(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)        

        # Override the button command to use our new threader
        self.update_button.config(command=self.run_update_thread)

    def process_data_backend(self):
        """HEAVY MATH - Runs in background thread"""
        try:
            # Sync inputs to indicator object
            self.indicator.upper = float(self.upper_input.get())
            self.indicator.lower = float(self.lower_input.get())
            
            # RUN THE CALCULATIONS
            self.indicator.indicator() 
            self.fig = self.indicator.plot_indicator(from_date=self.from_date_input.get())

            # Tell Main Thread to update UI
            self.after(0, self.update_ui_finished)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

    def update_ui_finished(self):
        """UI UPDATE - Runs in main thread"""
        for widget in self.plot_area.winfo_children():
            widget.destroy() # Clear old canvas/toolbar

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.status_var.set("Status: Updated")
        self.update_button.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    dashboard = Dashboard(root)
    root.mainloop()