import subprocess
import os
import re
import tempfile
import shutil
import PIL.Image

from tkinter import *
from tkinter import ttk, filedialog, simpledialog, messagebox
import threading

from .utils import *
from .widgets import ImageList

class App:
    def __init__(self, root: Tk):
        style = ttk.Style()
        style.configure("FileList.TFrame", background="#ffffff")
        style.configure("Delete.TButton", foreground="red")
        style.configure("AddFile.TButton", font=("Arial", 8))
        self.lastOpened: str = None
        
        self.root: Tk = root
        self.root.title("Image PDF Bundler")
        self.root.geometry("800x500")
                
        # Menubar options
        
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        optsMenu = Menu(menubar, tearoff=False)
        
        self.normalizeSize = BooleanVar()
        optsMenu.add_checkbutton(label="Normalize image sizes", variable=self.normalizeSize, onvalue=True, offvalue=False)

        # Reset config sub-menu
        resetMenu = Menu(optsMenu, tearoff=False)
        resetMenu.add_command(label="Selected files", command=self.resetFiles)
        resetMenu.add_command(label="Output settings", command=self.resetOutputs)
        resetMenu.add_separator()
        resetMenu.add_command(label="Reset All Settings", command=self.resetAll)
        optsMenu.add_cascade(label="Reset", menu=resetMenu)

        menubar.add_cascade(label="Options", menu=optsMenu)
        
        # Main app window
        ttk.Label(self.root, padding=3, font=("Arial", 16), text="Image Set PDF Bundler").pack()
        
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.pack(fill=BOTH, expand=True)
        self.frm.grid_columnconfigure(0, weight=1)
        self.frm.grid_columnconfigure(1, weight=2)
        self.frm.grid_rowconfigure(0, weight=1)

        
        ## Form field inputs group
        
        # Wrapper frame to pack form fields to window bottom 
        f1 = ttk.Frame(self.frm, padding=5)
        f1.grid(row=0, column=0, sticky=(N,S,E,W))
        
        inputFrm = ttk.Frame(f1)
        inputFrm.pack(side=TOP, fill=BOTH, expand=True)
        inputFrm.grid_rowconfigure((0, 7), weight=1)
        inputFrm.grid_rowconfigure((1, 4), pad=10)
        inputFrm.grid_rowconfigure((6), pad=5)
        inputFrm.grid_columnconfigure((0, 6), weight=1)

        ### Image scale input
        #TODO: Add radio options for different image arrangements (2 per page, full page, landscape 2 per page)      
        self.imageScale = DoubleVar(value=1)
        ttk.Label(inputFrm, text="Image Scale", justify="left").grid(row=1, column=1, columnspan=2, sticky=(W))
        ttk.Entry(inputFrm, width=6, textvariable=self.imageScale).grid(row=1, column=5, sticky=(E))
        
        ### Output folder input
        self.outputDir = StringVar()
        ttk.Label(inputFrm, text="Output Folder", justify="left").grid(row=2, column=1, columnspan=2, sticky=(W))
        self.outputBrowseButton = ttk.Button(inputFrm, text="Choose", command=self.selectOutputDir)
        self.outputBrowseButton.grid(row=2, column=4, columnspan=2) 
        self.outputDirEntry = ttk.Entry(inputFrm, textvariable=self.outputDir)
        self.outputDirEntry["state"] = "readonly"
        self.outputDirEntry.grid(row=3, column=1, columnspan=5, sticky=(W,E), pady=5)

        ### "Use Source Folder" checkbox
        self.useSourceDir = BooleanVar()
        ttk.Checkbutton(inputFrm, command=self.toggleSourceDir, text="Output to image source folder", variable=self.useSourceDir).grid(row=4, column=1, columnspan=5, pady=5)
        
        ### Output file name input
        self.outputFileName = StringVar(value="output")
        ttk.Label(inputFrm, text="Output File Name", justify="left").grid(row=5, column=1, columnspan=2, sticky=(W))
        self.outputFileEntry = ttk.Entry(inputFrm, textvariable=self.outputFileName, justify="right")
        self.outputFileEntry.grid(row=6, column=1, columnspan=5, sticky=(W,E))
        ttk.Label(inputFrm, text=".pdf").grid(row=6, column=6, sticky=(W))
    
        self.generateBtn = ttk.Button(f1, text="Generate PDF", command=self.onGeneratePdf, padding=10)
        self.generateBtn.pack(side=BOTTOM, anchor=S, expand=True, padx=10, pady=10)
        
        ## File list group

        # Wrapper frame to pack group to top
        f2 = ttk.Frame(self.frm, padding=5)
        f2.grid(row=0, column=1, sticky=(N,S,E,W))
        self.fileList = ImageList(f2, "Selected Files")
        self.fileList.pack(fill=BOTH, expand=True, anchor=NW)

        ### PDF Generation status text holder
        self.status = StringVar()
        self.statusLbl = ttk.Label(self.root, textvariable=self.status)
        self.statusLbl.pack(side=BOTTOM, anchor=SW, fill=X, pady=5, padx=10)
            
    #---------Menubar command callbacks---------
    
    def resetOutputs(self):
        if messagebox.askyesno("Reset Output Settings", "Reset all output settings?"):
            self.outputDir.set("")
            self.outputFileName.set("")
            self.useSourceDir.set(False)
            self.outputFileName.set("output")
            
    def resetFiles(self):
        if messagebox.askyesno("Reset Files List", "Remove all selected files?"):
            self.files = []
            self.fileList.delete(0, END)
            
    def resetAll(self):
        if messagebox.askyesno("Reset All Settings", "Reset all settings and clear selected files?"):
            self.fileList.clear()
            self.outputDir.set("")
            self.outputFileName.set("")
            self.useSourceDir.set(False)
            self.outputFileName.set("output")
                
    #---------Button command callbacks---------
    
    def toggleSourceDir(self):
        toggle = self.useSourceDir.get()
        self.outputBrowseButton["state"] = "disabled" if toggle else "normal"
        self.outputDirEntry["state"] = "disabled" if toggle else "readonly"
                
    def moveFileToInput(self):
        index = simpledialog.askinteger("Enter list position", 
            f"""Enter the new position in the list for the selected item.
            Value should be between 0 and {len(self.files)-1}""", minvalue=1, maxvalue=len(self.files)-1)
        if index is not None:
            self.moveSelectedFile(index)
    
    def selectOutputDir(self):
        outputdir = filedialog.askdirectory(parent=self.root, title="Select output folder", mustexist=True, initialdir=self.lastOpened)
        self.outputDir.set(outputdir)
        
    # def importFolder(self):
    #     importdir = filedialog.askdirectory(parent=self.root, initialdir=self.lastOpened, mustexist=True, title="Import All Images From Folder")
    #     if importdir:
    #         for file in next(os.walk(importdir))[2]:
    #             if re.match(r"\.(png|jpeg|jpg|jfif)", os.path.splitext(file)[1]):
    #                 self.files.append(os.path.join(importdir, file))
    #                 self.fileList.insert(END, os.path.basename(file))

    def onGeneratePdf(self):
        files = self.fileList.files
        
        if not len(files):
            messagebox.showerror(message="Error: No files selected")
            return
        if not self.useSourceDir.get() and not self.outputDir.get():
            messagebox.showerror(message="Error: Invalid output folder")
            return
        if not self.outputFileName.get():
            messagebox.showerror(message="Error: Invalid output file name")
            return
        scale = self.imageScale.get() or 1
        if scale <= 0:
            messagebox.showerror(message="Error: Invalid image scale")
            return
            
        if self.useSourceDir.get():
            outDir = os.path.dirname(files[0])
        else:
            outDir = self.outputDir.get()
        outFile = self.outputFileName.get()
        if os.path.exists(os.path.join(outDir, outFile+".pdf")):
            overwrite = messagebox.askyesnocancel("Overwrite Existing File?", f"A file named '{outFile}.pdf' already exists at this location. Overwrite this file?")
            
            if overwrite == False:
                copyNum = 1
                while os.path.exists(os.path.join(outDir, outFile+".pdf")):
                    outFile = f"{self.outputFileName.get()} ({copyNum})"
                    copyNum += 1
                
            elif overwrite is None:
                return
        thread = threading.Thread(target=self.generate_pdf, args=(
            files, outDir, outFile
        ))
        thread.run()
        
    def generate_pdf(self, files, outDir, outFile):
        tempFiles, tempDir = [], tempfile.mkdtemp()            
        imgSizes: list[tuple[str, Resolution]] = []
        minWidth, minHeight = None, None
        texSource = os.path.join(os.getcwd(), "src", "latex", "images-to-pdf.tex")

        try:
            scale = self.imageScale.get() or 1
            if scale != 1:
                self.status.set("Resizing & copying images...")
            else:
                self.status.set("Copying images...")
            self.statusLbl.update()
                
            for i, file in enumerate(files):
                res: Resolution
                tempFilePath = os.path.join(tempDir, str(i) + os.path.splitext(file)[1])
                
                try:
                    with PIL.Image.open(file) as im:
                        if scale != 1:
                            (width, height) = im.size
                            im_rs = im.resize((round(width*scale), round(height*scale)))
                            im_rs.save(tempFilePath)
                            res = Resolution.fromImage(im_rs)
                            im_rs.close()
                        else:
                            res = Resolution.fromImage(im)
                            tempFilePath = os.path.join(tempDir, str(i) + os.path.splitext(file)[1])
                            im.save(tempFilePath)
                            
                        im.close()
                            
                    tempFiles.append(tempFilePath)
                    if self.normalizeSize.get():
                        if res and res.getOrientation() == Orientation.PORTRAIT:
                            minWidth = min(res.width, minWidth) if minWidth is not None else res.width
                        else:
                            minHeight = min(res.height, minHeight) if minHeight is not None else res.height
                        
                    imgSizes.append((tempFilePath, res))
                except Exception as e:
                    print(e)
                    continue
                
            self.status.set("Normalizing page sizes...")
            self.statusLbl.update()
            texArgs = []

            for i in imgSizes:
                size: Resolution = i[1]
                if self.normalizeSize.get():
                    res = size.normalize(minWidth, minHeight).toTuple()
                else:
                    res = size.toTuple()
                texArgs.append("\\pdfpagewidth %.2fin \\pdfpageheight %.2fin \\noindent \\includegraphics[width=\\pdfpagewidth]{%s} " % (res[0], res[1], i[0].replace("\\", "/")))
            with open(texSource, "r") as source:
                latexSource = source.read()
                latexSource = latexSource.replace("%ARGS%", "\\newpage\n".join(texArgs))
                source.close()

            self.status.set("Generating LaTeX file...")
            self.statusLbl.update()
            
            with open(os.path.join(tempDir, "output.tex"), 'w') as texOutput:
                texOutput.write(latexSource)
                texOutput.close()

            cmd = "pdflatex {0}/output.tex -output-directory {0}".format(tempDir.replace('\\', '/'))
            try:
                self.status.set("Generating pdf file...")
                self.statusLbl.update()
                subprocess.call(cmd)
                tempPath = os.path.join(tempDir, "output.pdf")
                if (os.path.exists(tempPath)):
                    outputPath = os.path.join(outDir, outFile + ".pdf")
                    # Remove existing file to prevent name conflicts
                    if os.path.exists(os.path.join(outputPath)):
                        os.remove(outputPath)
                    shutil.copyfile(tempPath, outputPath)
                
                self.status.set("Done")
                self.statusLbl.update()
                openFile = messagebox.askyesno("File generated", "PDF file successfully generated. View it now?")
                if openFile:
                    os.startfile(outputPath)
            except Exception as e:
                self.status.set("Error: Failed to generate PDF")
                messagebox.showerror(message=f"Failed to generate PDF: {e}")
        except Exception as e:
            print(e)
        finally:
            shutil.rmtree(tempDir)
