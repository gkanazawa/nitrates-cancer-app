import tkinter as tk
from tkinter import Frame, Label
from PIL import Image, ImageTk

class ProgressBar(Frame):

    def __init__(self, root, initProgress = 0.1):
        # A custom widget for displaying progress bar and status text
        super().__init__(root) # access superclass

        self.backgroundImg = ImageTk.PhotoImage(Image.open("progbarbg.png"))
        self.backdrop = Label(root, image=self.backgroundImg)
        self.backdrop.place(x=0, y=0, relwidth=1, relheight=1)

        # display progress bar frame
        self.frameProgress = Frame(root, bg="#382933", bd=5, relief = tk.RIDGE)
        self.frameProgress.place(relheight=0.2, relwidth=0.5, relx=0.25, rely=0.4)

        # add bar container
        self.barContainer = Frame(self.frameProgress, bg="white", bd=3, relief=tk.RIDGE)
        self.barContainer.place(relheight=0.12, relwidth=0.9, relx=0.05, rely=0.1)

        # add bar and progress label
        self.prog = Label(self.barContainer, bg="#519872")
        self.prog.place(x=0, relheight=1, relwidth= float(initProgress))

        self.lblProg = Label(self.frameProgress, bg="#382933", fg="white", justify="center", text=f"{initProgress}%")
        self.lblProg.place(x=0, rely=0.57, relwidth=1)

        # add status text
        self.lblStatus = Label(self.frameProgress, bg="#382933", fg="white", justify="center")
        self.lblStatus.place(x=0, rely=0.57, relwidth=1)


    def set_prog(self, x):
        # sets progress bar's value. 0<x<1 represents % of progress

        self.prog.place(x=0, relheight=1, relwidth=x)
        self.lblProg["text"] = f'{int(x*100)}%'
        self.frameProgress.update()

    def set_status(self, text):
        # sets status label to display input text
        self.lblStatus["text"] = str(text)
        self.frameProgress.update()

    def close(self):
        # destroys progressbar instance
        self.frameProgress.destroy()
        self.backdrop.destroy()
        self.destroy()