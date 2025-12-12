from tkinter import Tk
from src.app import App

if __name__ == "__main__":
    root = Tk()
    root.iconbitmap("bundler.ico")
    app = App(root)
    root.mainloop()