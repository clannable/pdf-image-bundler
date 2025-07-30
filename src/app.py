import subprocess
import os
import re
import json
import tempfile
import shutil
import PIL.Image

from tkinter import *
from tkinter import ttk, filedialog, simpledialog, messagebox
import threading

from .utils import *
from .widgets.image import ImageList, ImageEntry, PageLayout

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
        self.bundle = None
        
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        self.fileMenu = Menu(menubar, tearoff=False)
        self.fileMenu.add_command(label="Open Bundle", accelerator="Ctrl+O", command=self.openBundle)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Save Bundle", accelerator="Ctrl+S", command=self.saveBundle)
        self.fileMenu.add_command(label="Save Bundle As...", command=self.saveBundleAs)
        
        self.root.bind_all("<Control-s>", lambda _: self.saveBundle())
        self.root.bind_all("<Control-o>", lambda _: self.openBundle())
        menubar.add_cascade(label="File", menu=self.fileMenu)
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
        
        imMenu = Menu(menubar, tearoff=False)
        imMenu.add_command(label="Set all images scale to...", command=self.scaleAllImages)
        imMenu.add_command(label="Set all sidebar sizes to...", command=self.setSidebarSizes)
        
        menubar.add_cascade(label="Images", menu=imMenu)
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
        inputFrm.grid_rowconfigure((0, 8), weight=1)
        inputFrm.grid_rowconfigure((1, 4), pad=10)
        inputFrm.grid_rowconfigure((6), pad=5)
        inputFrm.grid_columnconfigure((0, 7), weight=1)

        ### Image scale input
        #TODO: Add radio options for different image arrangements (2 per page, full page, landscape 2 per page)      
        # self.imageScale = DoubleVar(value=1)
        # ttk.Label(inputFrm, text="Image Scale", justify="left").grid(row=1, column=1, columnspan=2, sticky=(W))
        # ttk.Entry(inputFrm, width=6, textvariable=self.imageScale).grid(row=1, column=5, sticky=(E))
        
        self.parSpacing = IntVar(value=6)
        ttk.Label(inputFrm, text="Paragraph Spacing").grid(row=1, column=1, columnspan=3, sticky=(W))
        ttk.Entry(inputFrm, textvariable=self.parSpacing, width=4).grid(row=1, column=5, sticky=(W, E))
        ttk.Label(inputFrm, text="pt").grid(row=1, column=6, sticky=(W))
        
        self.defaultScale = DoubleVar(value = 1)
        ttk.Label(inputFrm, text="Default Scale", justify="left").grid(row=2, column=1, columnspan=3, sticky=(W))
        ttk.Entry(inputFrm, textvariable=self.defaultScale).grid(row=2, column=5, sticky=(W, E))
        
        ### Output folder input
        self.outputDir = StringVar()
        ttk.Label(inputFrm, text="Output Folder", justify="left").grid(row=3, column=1, columnspan=2, sticky=(W))
        self.outputBrowseButton = ttk.Button(inputFrm, text="Choose", command=self.selectOutputDir)
        self.outputBrowseButton.grid(row=3, column=4, columnspan=2) 
        self.outputDirEntry = ttk.Entry(inputFrm, textvariable=self.outputDir)
        self.outputDirEntry["state"] = "readonly"
        self.outputDirEntry.grid(row=4, column=1, columnspan=5, sticky=(W,E), pady=5)

        ### "Use Source Folder" checkbox
        self.useSourceDir = BooleanVar()
        ttk.Checkbutton(inputFrm, command=self.toggleSourceDir, text="Output to image source folder", variable=self.useSourceDir).grid(row=5, column=1, columnspan=5, pady=5)
        
        ### Output file name input
        self.outputFileName = StringVar(value="output")
        ttk.Label(inputFrm, text="Output File Name", justify="left").grid(row=6, column=1, columnspan=2, sticky=(W))
        self.outputFileEntry = ttk.Entry(inputFrm, textvariable=self.outputFileName, justify="right")
        self.outputFileEntry.grid(row=7, column=1, columnspan=5, sticky=(W,E))
        ttk.Label(inputFrm, text=".pdf").grid(row=7, column=6, sticky=(W))
    
        self.generateBtn = ttk.Button(f1, text="Generate PDF", command=self.onGeneratePdf, padding=10)
        self.generateBtn.pack(side=BOTTOM, anchor=S, expand=True, padx=10, pady=10)
        
        ## File list group

        # Wrapper frame to pack group to top
        f2 = ttk.Frame(self.frm, padding=5)
        f2.grid(row=0, column=1, sticky=(N,S,E,W))
        self.fileList = ImageList(f2, self, "Selected Files")
        self.fileList.pack(fill=BOTH, expand=True, anchor=NW)

        ### PDF Generation status text holder
        self.status = StringVar()
        self.statusLbl = ttk.Label(self.root, textvariable=self.status)
        self.statusLbl.pack(side=BOTTOM, anchor=SW, fill=X, pady=5, padx=10)
            
    #---------Menubar command callbacks---------
    
    def openBundle(self):
        bundlePath = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if bundlePath:
            with open(bundlePath, "r") as bundle:
                bundlejson = json.load(bundle)
                bundle.close()
                
            spacing = self.parSpacing.get()
            outputDir = self.outputDir.get()
            sourceDir = self.useSourceDir.get()
            outputName = self.outputFileName.get()
            files = self.fileList.files
            
            try:
                
                self.parSpacing.set(bundlejson["parSpacing"])
                self.outputDir.set(bundlejson["outputDir"])
                self.useSourceDir.set(bundlejson["useSourceAsOutput"])
                self.outputFileName.set(bundlejson["outputName"])
                self.fileList.loadFromJson(bundlejson["files"])
                if "normalizeImages" in bundlejson:
                    self.normalizeSize.set(bundlejson["normalizeImages"])
                if "defaultScale" in bundlejson:
                    self.defaultScale.set(bundlejson["defaultScale"])
                
                for oldFile in files:
                    oldFile.destroy()
                
                self.bundle = bundlePath
                self.fileMenu.entryconfig("Save Bundle", state="normal")
                self.root.update_idletasks()
            except Exception as e:
                messagebox.showerror("Error: Failed to load bundle")
                self.parSpacing.set(spacing)
                self.outputDir.set(outputDir)
                self.useSourceDir.set(sourceDir)
                self.outputFileName.set(outputName)
                self.fileList.setFiles(files)
                raise e
                                    

    def saveBundleAs(self):
        exportPath = filedialog.asksaveasfilename(
            defaultextension=".json", 
            filetypes=[("JSON File", "*.json")],
            initialdir=os.path.dirname(self.bundle) if self.bundle else None,
            initialfile=os.path.basename(self.bundle) if self.bundle else "bundle"    
        )
        if exportPath:
            try:
                self.saveBundle(exportPath)
                self.fileMenu.entryconfig("Save Bundle", state="normal")
            except Exception as e:
                raise e
        
    def saveBundle(self, bundle=None):
        if not bundle and not self.bundle:
            self.saveBundleAs()
            return
        elif not bundle and self.bundle:
            bundle = self.bundle
        if bundle:
            try:
                jsonOut = {
                    "parSpacing": self.parSpacing.get(),
                    "outputDir": self.outputDir.get(),
                    "useSourceAsOutput": self.useSourceDir.get(),
                    "outputName": self.outputFileName.get(),
                    "normalizeImages": self.normalizeSize.get(),
                    "defaultScale": self.defaultScale.get(),
                    "files": [im.toJson() for im in self.fileList.files]
                }
                with open(bundle, "w") as exportFile:
                    json.dump(jsonOut, exportFile, indent=4)
                    exportFile.close()
                    self.bundle = bundle
            except Exception as e:
                messagebox.showerror("An Error Occurred", "Error saving bundle")
                raise e
            
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
    
    def scaleAllImages(self):
        scale = simpledialog.askfloat("Set image scale", "Enter in the scale value to use for all images", initialvalue=1, minvalue=0.1)
        if scale:
            for entry in self.fileList.files:
                entry.setScale(scale) 
                
    def setSidebarSizes(self):
        size = simpledialog.askfloat("Set sidebar size", "Enter the value to use as the sidebar size for all images", initialvalue=3.0, minvalue=1.0) 
        if size:
            for entry in self.fileList.files:
                entry.setSidebarSize(size)
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
        spacing = self.parSpacing.get()
        if not spacing or spacing < 0:
            messagebox.showerror(message="Error: Invalid paragraph spacing")
            return
        # scale = self.imageScale.get() or 1
        # if scale <= 0:
        #     messagebox.showerror(message="Error: Invalid image scale")
        #     return
            
        if self.useSourceDir.get():
            outDir = os.path.dirname(files[0].filePath)
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
        
    def generate_pdf(self, files: list[ImageEntry], outDir, outFile):
        tempFiles, tempDir = [], tempfile.mkdtemp()            
        entries: list[tuple[str, ImageEntry]] = []
        minWidth, minHeight = None, None
        texSource = os.path.join(os.getcwd(), "src", "latex", "images-to-pdf-caption.tex")

        # try:
        # scale = self.imageScale.get() or 1
        # if scale != 1:
        self.status.set("Resizing & copying images...")
        # else:
        #     self.status.set("Copying images...")
        self.statusLbl.update()
            
        for i, entry in enumerate(files):
            tempFilePath = os.path.join(tempDir, str(i) + os.path.splitext(entry.filePath)[1])
            
            try:
                # with PIL.Image.open(entry.filePath) as im:
                    # scale = entry.getImageScale()
                    # if scale != 1:
                    #     (width, height) = im.size
                    #     im_rs = im.resize((round(width*scale), round(height*scale)))
                    #     im_rs.save(tempFilePath)
                    #     entry.resolution = Resolution.fromImage(im_rs)
                    #     im_rs.close()
                    # else:
                    #     entry.resolution = Resolution.fromImage(im)
                    # im.save(tempFilePath)
                        
                    # im.close()
                shutil.copyfile(entry.filePath, tempFilePath)
                tempFiles.append(tempFilePath)
                if self.normalizeSize.get():
                    res = entry.getResolution()
                    if res and res.getOrientation() == Orientation.PORTRAIT:
                        minWidth = min(res.width, minWidth) if minWidth is not None else res.width
                    else:
                        minHeight = min(res.height, minHeight) if minHeight is not None else res.height
                    
                entries.append((tempFilePath, entry))
            except Exception as e:
                print(e)
                continue
            
        self.status.set("Normalizing page sizes...")
        self.statusLbl.update()
        texArgs = []
        for i in entries:
            imgSizer = "width=\\pdfpagewidth" 
            entry: ImageEntry = i[1]
            res = entry.getResolution()
            orientation = res.getOrientation()
            layout = entry.layout
            if self.normalizeSize.get():
                (width, height) = res.normalize(minWidth, minHeight).toTuple()
            else:
                (width, height) = res.toTuple()
            if layout == PageLayout.CAPTION_SIDEBAR:
                if orientation == Orientation.PORTRAIT:
                    imgSizer = "width=\\pdfpagewidth"
                    height += entry.sidebarSize
                else:
                    imgSizer = "height=\\pdfpageheight"
                    width += entry.sidebarSize
                    
            args = "\\pdfpagewidth %.2fin \\pdfpageheight %.2fin \n\\noindent \\includegraphics[%s]{%s}\n" % (width, height, imgSizer, i[0].replace("\\", "/"))
            if layout == PageLayout.CAPTION_SIDEBAR:
                if orientation == Orientation.PORTRAIT:
                    bx = 0.25
                    by = height - entry.sidebarSize + 0.25
                    bw = width - 0.5
                else:
                    bx = width - entry.sidebarSize + 0.25
                    by = 0.25
                    bw = entry.sidebarSize - 0.5
                args += "\\begin{flushleft} \\begin{textblock*}{%.2fin}(%.2fin, %.2fin)\n" % (bw, bx, by)
                if entry.getCaption():
                    # print(entry.getCaption())
                    for par in entry.getCaption().split("\n"):
                        if not par:
                            continue
                        args += par.replace("&", "\\&") + "\\par\n"
                args += "\\end{textblock*}\n\\end{flushleft}\n"
            texArgs.append(args)
            
        with open(texSource, "r") as source:
            latexSource = source.read()

            latexSource = latexSource.replace("%PAR_SPACING%", str(self.parSpacing.get()))
            latexSource = latexSource.replace("%ARGS%", "\\newpage\n".join(texArgs))
            source.close()

        self.status.set("Generating LaTeX file...")
        self.statusLbl.update()
        
        with open(os.path.join(tempDir, "output.tex"), 'w', encoding="utf-8") as texOutput:
            texOutput.write(latexSource)
            texOutput.close()

        cmd = "xelatex {0}/output.tex -halt-on-error -output-directory {0}".format(tempDir.replace('\\', '/'))
        try:
            self.status.set("Generating pdf file...")
            self.statusLbl.update()
            result = subprocess.call(cmd)
            if result != 0:
                raise Exception("latex error")
            tempPath = os.path.join(tempDir, "output.pdf")
            if (os.path.exists(tempPath)):
                outputPath = os.path.join(outDir, outFile + ".pdf")
                # Remove existing file to prevent name conflicts
                if os.path.exists(os.path.join(outputPath)):
                    os.remove(outputPath)
                shutil.copyfile(tempPath, outputPath)
                shutil.copyfile(os.path.join(tempDir, "output.tex"), os.path.join(outDir, "output.tex"))
            
            self.status.set("Done")
            self.statusLbl.update()
            openFile = messagebox.askyesno("File generated", "PDF file successfully generated. View it now?")
            if openFile:
                os.startfile(outputPath)
        except Exception as e:
            self.status.set("Error: Failed to generate PDF")
            messagebox.showerror(message=f"Failed to generate PDF: {e}")
        # except Exception as e:
        #     print(e)
        finally:
            shutil.rmtree(tempDir)

