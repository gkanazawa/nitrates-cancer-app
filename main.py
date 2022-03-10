
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog
import tkinter.messagebox as messagebox
from tkinter import ttk
from ProgressBar import ProgressBar
from time import sleep
from PIL import Image, ImageTk
from subprocess import Popen
import AnalysisAndMapping as am

HEIGHT = 850
WIDTH = 1100
FONT = ("Roboto, 14")

root = tk.Tk()
root.title('Groundwater Nitrate Levels and Cancer Rates in Wisconsin')
root.resizable(False, False)

def idwHelp():
    messagebox.showinfo("IDW Interpolation", "Inverse Distance Weighted (IDW) is a type of spatial interpolation which assigns weights to locations based on their distance from the measured point (in this case the well points) and a distance decay coefficient K. The higher the value of K, the more weight is assigned to close areas and the less weight assigned to distant areas. K-values must be greater than 1; values greater than 10 will assign vanishingly small weights to locations away from the sample points and likely do not reflect real-world conditions. For more on IDW in ArcGIS, visit https://pro.arcgis.com/en/pro-app/2.8/tool-reference/spatial-analyst/idw.htm")

def regression():
    messagebox.showinfo("OLS Regression", "Ordinary Least Squares (OLS) is a spatial regression analysis technique which provides a global model of the correlation we are trying to understand - in this case cancer rates and drinking water nitrate levels. In OLS regression, the dependent variable (cancer rates) is set equal to a set of explanatory variables (nitrate levels) with corresponding regression coefficients and residuals. The OLS regression output map symbolizes the standard residuals in terms of whether they over-estimate or under-estimate the model-predicted values. For more on OLS in ArcGIS, visit https://pro.arcgis.com/en/pro-app/2.8/tool-reference/spatial-statistics/ordinary-least-squares.htm")

def about():
    messagebox.showinfo("About", "This application allows for an exploration of the relationship between levels of nitrate in drinking water and cancer rates per census tract in Wisconsin. Choose different values of K for the interpolation from the provided sample points, and view the resulting nitrate interpolation, regression residuals, and spatial autocorrelation report!")

canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
canvas.pack()

BackgroundImg = ImageTk.PhotoImage(Image.open("IntroMap.png"))
imgBackground = tk.Label(canvas, image=BackgroundImg)
imgBackground.pack()

menu = tk.Menu(root)
root.config(menu=menu)

info = tk.Menu(menu)

menu.add_cascade(label="Info", menu=info)

# info.add_command(label="About", command=about)
info.add_command(label="IDW Interpolation", command=idwHelp)
info.add_command(label="OLS Regression", command=regression)

#Results image
img = None

# Moran's I report link
moransReport = None

fontTitle = tkFont.Font(family="Roboto", size=16)
fontParagraph = tkFont.Font(family="Roboto", size=12)
fontSmall = tkFont.Font(family="Roboto", size=10)

def run_analysis(k):

    global moransReport  #enable modifying report inside fcn

    # validate k entry
    try:
        k = float(k)
        if k <= 1:
            raise ValueError

    except ValueError:
        messagebox.showerror("Invalid Entry", f'K = {k}\nError, K must be a value greater than 1.')
        return

    btnRunAnalysis["state"] = "disabled"

    #input data paths
    wells = "data/well_nitrate.shp"
    tracts = "data/cancer_tracts.shp"
    counties = "data/cancer_county.shp"

    # show progress bar
    progbar = ProgressBar(root)

    root.update()

    import arcpy
    arcpy.CheckOutExtension("spatial")

    progbar.set_status('Initializing...')
    am.initialize()
    sleep(1)

    progbar.set_status(f'Interpolating nitrate levels from well points via IDW, K={k}...')
    progbar.set_prog(0.2)
    idwOutput = am.run_idw(wells, counties, k)

    progbar.set_status('Calculating average nitrate per census tract...')
    progbar.set_prog(0.35)
    nitrateVals = am.get_avg_nitrate(tracts, "GEOID10", idwOutput, k)

    progbar.set_status('Updating nitrates field in tracts...')
    progbar.set_prog(0.4)
    am.update_nitrates_field(nitrateVals, tracts)

    progbar.set_status('Running Ordinary Least Squares regression...')
    progbar.set_prog(0.6)
    am.run_ols(tracts, k)

    progbar.set_status("Running Moran's I spatial autocorrelation...")
    progbar.set_prog(0.75)
    moransReport = am.run_moransI(k)

    progbar.set_status("Creating maps...")
    progbar.set_prog(0.9)
    am.generate_maps(k)

    progbar.set_status("Finalizing output...")
    progbar.set_prog(1)
    sleep(1)

    progbar.close()
    btnRunAnalysis["state"] = "active"

    show_frameResults(k)

def show_frameResults(k):

    global img
    global moransReport

    def load_image(k, type):
        fileName = f'reports/{type}_{str(k).replace(".","_")}.png'
        img = Image.open(fileName)
        img = img.resize((430,550))
        imgTk = ImageTk.PhotoImage(img)
        return imgTk

    def change_image(k, type, currentMap):
        # change image in results frame
        imgTk = load_image(k, type)
        currentMap.configure(image = imgTk)
        currentMap.image = imgTk

    def view_ols_report(k):
        import os
        olsFile = f'{os.getcwd()}\\ols_reports\\{k}_ols.pdf'
        Popen(olsFile, shell=True)
        
    def view_moransI_report(path):
        if path:
            Popen(path, shell=True)
        else:
            messagebox.showerror("Error loading Moran's I report", "There was an error in loading the Moran's I report.")

    def save_as_pdf(k, type):
        saveAsPath = filedialog.asksaveasfilename(initialdir="/", filetypes=[("pdf files", "*.pdf")])
        if ".pdf" not in saveAsPath.lower():
            saveAsPath += '.pdf'
        imagePath = f'reports/{type}_{str(k).replace(".","_")}.png'
        img = Image.open(imagePath)
        imgfinal = img.convert('RGB')
        imgfinal.save(saveAsPath, "PDF")
        
    # reset frameResults to clear previous analysis runs
    for child in frameResults.winfo_children():
        child.destroy()

    # show frameResults
    frameResults.place(relheight = 0.75, relwidth=0.4, relx=0.55, rely=0.1)

    # show map image; defaults to IDW
    img = load_image(k, "IDW")
    currentMap = tk.Label(frameResults, image=img)
    currentMap.pack()


    frameButtons = tk.Frame(frameResults, bg="#382933", height=80)
    frameButtons.pack(side='bottom', fill='x')

    btnIDW = ttk.Button(frameButtons, text="Show IDW Results", command=lambda: change_image(k, "IDW", currentMap))
    btnIDW.place(x=5, rely=0.15, relwidth=0.3, relheight=0.3)
    
    btnOLS = ttk.Button(frameButtons, text="Show OLS Results", command=lambda: change_image(k, "OLS", currentMap))
    btnOLS.place(x=5, rely=0.6, relwidth=0.3, relheight=0.3)

    btnViewOLS = ttk.Button(frameButtons, text="View OLS Report", command=lambda: view_ols_report(k))
    btnViewOLS.place(relx=0.35, rely=0.15, relwidth = 0.3, relheight=0.3)

    btnIDWSave = ttk.Button(frameButtons, text="Save IDW Map to PDF...", command=lambda: save_as_pdf(k, "IDW"))
    btnIDWSave.place(relx=0.68, rely=0.15, relwidth=0.3, relheight=0.3)
    
    btnMoransI = ttk.Button(frameButtons, text="View Morans I Report", command=lambda: view_moransI_report(moransReport))
    btnMoransI.place(relx=0.35, rely=0.6, relwidth=0.3, relheight=0.3)

    btnOLSSave = ttk.Button(frameButtons, text="Save OLS Map to PDF...", command=lambda: save_as_pdf(k, "OLS"))
    btnOLSSave.place(relx=0.68, rely=0.6, relwidth=0.3, relheight=0.3)    


frameSetup = tk.Frame(root, bg="#3B5249", bd=5, relief=tk.RIDGE)
frameSetup.place(relheight=0.70, relwidth=0.35, relx=0.05, rely=0.1)

lblTitle = tk.Label(frameSetup, text="Is There a Relationship Between Groundwater Nitrates and Cancer?", fg="white", bg="#382933", justify="center", wraplength="335", pady=0.1, font=fontTitle)
lblTitle.place(x=0, y=0, relwidth=1, relheight=0.1)

lblDesc = tk.Label(frameSetup, anchor="n", text=open('description.txt').read(), fg="white", bg="#382933", pady = 2, justify="center", wraplength="330", font=fontParagraph)
lblDesc.place(x=0, rely=0.12, relwidth=1, relheight=1)

frameKVal = tk.Frame(frameSetup, bg="#382933", bd=5, relief=tk.RIDGE)
frameKVal.place(relx=0.22, rely=0.67, relwidth=0.6, relheight=0.1)

lblKEquals = tk.Label(frameKVal, text="K = ", bg="#382933", fg="white", font=fontSmall)
lblKEquals.pack(side="left")

txtKVal = tk.Entry(frameKVal)
txtKVal.insert(0, "2.0")  # default value
txtKVal.pack(side="left")

btnRunAnalysis = ttk.Button(frameSetup, text="Run Analysis", command=lambda: run_analysis(txtKVal.get()))
btnRunAnalysis.place(rely=0.8, relx=0.39)

frameResults = tk.Frame(root, bg="#382933", bd=5, relief=tk.RIDGE)

root.mainloop()