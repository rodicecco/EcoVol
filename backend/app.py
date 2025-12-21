import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

import indicators

plt.style.use('seaborn-v0_8-darkgrid')

class PlotModule(tk.Frame):
    """A reusable frame containing a plot and a setting sidebar"""
    def __init__(self, parent, title , color):
        super().__init__(parent)

        #Define variable to take input

        # --- Layout: Sidebar (Left) and Plot (Right) --
        self.sidebar = tk.Frame(self, width=200, bg='lightgrey', padx=10, pady=10)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.plot_area = tk.Frame(self)
        self.plot_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Sidebar Content ---
        tk.Label(self.sidebar, text=title, font=('Arial', 14, 'bold'), bg='lightgrey').pack(pady=10)


        self.btn_update = tk.Button(self.sidebar, text="Update", command=self.update_plot)
        self.btn_update.pack(fill=tk.X, pady=5)


    def update_plot(self):
            self.ax.clear()
            data = np.random.randn(50).cumsum() # Simulated data
            self.ax.plot(data, color=self.color, lw=2)
            self.ax.grid(self.show_grid.get())
            self.ax.set_title("Live Analysis")
            self.canvas.draw()

class VixSpread(indicators.VixSpread, PlotModule):
    def __init__(self, parent):
        PlotModule.__init__(self, parent, "VIX Spread Settings", "blue")
        super().__init__()

        #Define variable to take input
        self.upper_entry = tk.StringVar(value=self.upper)
        self.lower_entry = tk.StringVar(value=self.lower)
        self.avg_window_entry = tk.StringVar(value=self.avg_window)

        tk.Label(self.sidebar, text="Upper Threshold:", bg='lightgrey').pack(pady=5)
        self.upper_input = tk.Entry(self.sidebar, textvariable=self.upper_entry)
        self.upper_input.pack(fill=tk.X, pady=5)

        tk.Label(self.sidebar, text="Lower Threshold:", bg='lightgrey').pack(pady=5)
        self.lower_input = tk.Entry(self.sidebar, textvariable=self.lower_entry)
        self.lower_input.pack(fill=tk.X, pady=5)

        tk.Label(self.sidebar, text="Avg. Window", bg='lightgrey').pack(pady=5)
        self.avg_input = tk.Entry(self.sidebar, textvariable=tk.StringVar(value=5))
        self.avg_input.pack(fill=tk.X, pady=5)

        self.fig = self.plot_indicator()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Force layout update
        self.plot_area.update_idletasks()
        # Remove the initial update_plot call since we already have the figure
    
    def update_plot(self):
        #get new inputs
        try:
            self.upper = float(self.upper_entry.get())
            self.lower = float(self.lower_entry.get())
            self.avg_window = int(self.avg_window_entry.get())

        except ValueError:
            tk.messagebox.showerror("Invalid Input", "Please enter valid numeric values for thresholds.")
            
        # Remove old canvas and toolbar
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()
        
        # Create new figure and canvas
        self.fig = self.plot_indicator()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar and pack it
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_area)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Force layout update
        self.plot_area.update_idletasks()
        
        self.canvas.draw()


class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Analysis Dashboard")
        self.root.geometry("1000x600")

        # Create Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Volatility Analysis
        self.tab_vol = VixSpread(self.notebook)
        self.notebook.add(self.tab_vol, text="Annualized Vol")

        # Tab 2: GEX Profile
        self.tab_gex = PlotModule(self.notebook, "GEX Settings", "green")
        self.notebook.add(self.tab_gex, text="Spot GEX")

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()