from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tktooltip import ToolTip
from typing import Callable
from enum import Enum
import os
import subprocess
import platform
import PIL.Image
from iptcinfo3 import IPTCInfo
# LAYOUT_ICONS = {
#     "caption_sidebar": PhotoImage(file=os.path.join(os.getcwd(), "src", "assets", "sidebar.png")),
#     "full_page": PhotoImage(file=os.path.join(os.getcwd(), "src", "assets", "fullpage.png"))
# }

IMAGE_SETTINGS = {
    "sticky": (N, S, E, W),
    "pady": 3,
    "padx": 3
}
class PageLayout(Enum):
    IMAGE_ONLY = 0 # only display image on page
    CAPTION_SIDEBAR = 1 # display image caption in narrow sidebar to the right of image
    CAPTION_TWO_COLUMN = 2 # double page width, insert caption in right-hand column 

class ImageEntry(ttk.Frame):
    
    def __init__(self, filePath):
        pass
    
    def setRow(self, index):
        pass
    
    def updateControlsState(self):
        pass

class ImageList(ttk.Frame):
    _files: list[ImageEntry] = []
    _widgets: list[ttk.Widget] = []
    
    def __init__(self, master: Misc | None = None, title: str = "", **kwargs):
        ttk.Frame.__init__(self, master, **kwargs)
        f0 = ttk.Frame(self, padding=10)
        f0.pack(side=TOP, fill=X, anchor=NW)
        ttk.Label(f0, text=title, font=("Arial", 12, "bold")).pack(side=LEFT, fill=X)
        ttk.Button(f0, text="Add Files", command=self.onAddFiles).pack(side=RIGHT, padx=10)
                
        f1 = ttk.Frame(self, borderwidth=2, relief=SUNKEN)
        f1.pack(side=LEFT, fill=BOTH, expand=True, anchor=W)
        self.canvas = Canvas(f1, borderwidth=0, highlightthickness=0, bg="#ffffff", background="#ffffff")
        self.frame = ttk.Frame(self.canvas, style="FileList.TFrame")
        self.frame.grid_columnconfigure(0, weight=1)
        vsb = Scrollbar(f1, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        
        vsb.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.windows_item = self.canvas.create_window(0, 0, window=self.frame, anchor=NW)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self.onFrameConfig)
        
        f2 = ttk.Frame(self)
        f2.pack(side=RIGHT, fill=Y, anchor=E)
        
    def _on_mousewheel(self, evt: Event):
        self.canvas.yview_scroll(int(-1*(evt.delta/120)), "units")
    
    def __len__(self):
        return len(self._files)
    
    @property
    def files(self):
        return [x.file for x in self._files]
    
    def onAddFiles(self, index=None):
        selectedFiles = filedialog.askopenfilenames(parent=self,
            title="Select images to add", 
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.jfif")], 
            multiple=True,
        )
        if selectedFiles:
            for (i, file) in enumerate(selectedFiles):
                self.createEntry(file, )
        
        self.onFrameUpdate()
        
    # index - 
    # def insertAddButton(self, index):
    #     btn = ttk.Button(self.frame, text="+", style="AddFile.TButton", command=lambda : self.onInsertFiles(btn))
    #     if index is not None:
    #         self._widgets.
                
    def onInsertFiles(self, widget):
        self.onAddFiles(self._widgets.index(widget) // 2)
        
    def onFrameConfig(self, evt: Event):
        self.canvas.itemconfig(self.windows_item, width = evt.width)
        self.onFrameUpdate()
        
    def onFrameUpdate(self):        
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.frame.bbox())
    
    def clear(self):
        for w in self._widgets:
            w.grid_forget()
            w.destroy()
            
        self._files = []
        self._widgets = []
        
    def createEntry(self, filePath, index=None):
        image = ImageEntry(self, filePath)
        self._files.append(image)
        if len(self._files) == 2:
            self._files[0].updateControlsState()
        elif len(self._files) > 2:
            self._files[-2].updateControlsState()
            
    def removeEntry(self, entry: ImageEntry):
        index = self._files.index(entry)
        self._files.pop(index)
        entry.grid_forget()
        entry.destroy()
        if index == len(self._files) and index != 0:
            self._files[-1].updateControlsState()
        else:
            for (ix, im) in enumerate(self._files[index:]):
                im.setRow(ix*2)
            
    def moveEntryUp(self, entry: ImageEntry):
        index = self._files.index(entry)
        self._files.pop(index)
        y = self._files[index-1]
        self._files.insert(index-1, entry)
        
        # entry.grid_forget()
        y.setRow(index)
        entry.setRow(index-1)        
        
    def moveEntryDown(self, entry: ImageEntry):
        index = self._files.index(entry)
        y = self._files[index+1]
        self._files.pop(index)
        self._files.insert(index+1, entry)
        
        # entry.grid_forget()
        y.setRow(index)
        entry.setRow(index+1)
        
    def floorEntry(self, entry: ImageEntry):
        index = self._files.index(entry)
        self._files.pop(index)
        # entry.grid_forget()
        for i in range(index, len(self._files)-1, 1):
            im = self._files[i]
            im.setRow(i-1)
        self._files.append(entry)
        im.setRow(len(self._files)-1)
                
    def ceilEntry(self, entry: ImageEntry):
        index = self._files.index(entry)
        self._files.pop(index)
        # entry.grid_forget()
        for i in range(index-1, 0, -1):
            im = self._files[i]
            im.setRow(i+1)
        
        self._files.insert(0, entry)
        entry.setRow(0)        

class ImageEntry(ttk.Frame):
    _file: str
    _index: int = 0
    _list: ImageList
    _widget: Widget
    _caption: str
    _layout: PageLayout
    
    class MoveControl(object):
        tooltip: ToolTip = None
        msg: str
        btn: ttk.Button
        state_fn: Callable[[], bool]
        
        def __init__(self, btn, msg: str, state_fn):
            self.btn = btn
            self.msg = msg
            self.state_fn = state_fn
            self.update()
            
        def update(self):
            if self.state_fn():
                if self.tooltip is None:
                    self.tooltip = ToolTip(self.btn, self.msg, delay=0.5)
                self.btn.configure(state = "normal", cursor="hand2")
            else:
                if self.tooltip is not None:
                    self.tooltip.destroy()
                    self.tooltip = None
                self.btn.configure(state="disabled", cursor=None)
                
    def __init__(self, list: ImageList, file_path: str, layout: PageLayout = PageLayout.IMAGE_ONLY, index=None):      
        ttk.Frame.__init__(self, list.frame, padding=5, border=2, relief=SOLID, borderwidth=2)
        self._list = list
        self._file = file_path
        self._layout = IntVar(value=layout)   
        
        info = IPTCInfo(self._file)
        self._caption = info['caption/abstract']
        # with PIL.Image.open(self._file) as imFile:
            # for tag in [, ExifTags.Base.XPComment]:
            # meta = (imFile)
            # print(meta)
            # try:
            #     descr = exif[ExifTags.Base.ImageDescription]
            #     self._caption = descr
            #     print()
            # except KeyError:
            #     try:
            #         self._caption = exif[ExifTags.Base.XPComment]
            #         print(self._caption)
            #     except KeyError:
            #         self._caption = None
                
        f = ttk.Frame(self)
        f.pack(side=LEFT, fill=BOTH, expand=True)
        f.grid_columnconfigure((2, 3, 4), weight=1)
        f.grid_columnconfigure((0, 1), weight=0, minsize=5)
        f.grid_columnconfigure(1, pad=5)  
        f.grid_rowconfigure(1, weight=1)

        defaultfont = ("Arial", 10)
        hoverfont = ("Arial", 10, "underline")
        label = ttk.Label(f, text=os.path.basename(self._file), font=defaultfont, justify="left")
        ToolTip(label, msg="Double-click to open file", delay=1.5)
        label.grid(row=0, column=0, columnspan=5, sticky=(W, E))
        label.bind("<Enter>", lambda evt : evt.widget.configure(font=hoverfont, cursor="hand2"), add="+")
        label.bind("<Leave>", lambda evt : evt.widget.configure(font=defaultfont, cursor=None), add="+")
        label.bind("<Double-Button-1>", self.onFileDblClick)
        self._index = index if index is not None else len(self._list)
        
        delBtn = ttk.Button(f, text='\u2715', cursor="hand2", width=3, command = lambda : self._list.removeEntry(self), style="Delete.TButton")
        delBtn.grid(row=2, column=0)
        ToolTip(delBtn, msg="Remove image", delay=0.5)
        expBtn = ttk.Button(f, text='\U0001F5C0', cursor="hand2", width=3, command=self.openSourceFolder)
        expBtn.grid(row=2, column=1)
        ToolTip(expBtn, msg="View in File Explorer", delay=0.5)

        layoutFrm = ttk.Frame(f)
        ttk.Radiobutton(layoutFrm, variable=self._layout, text="Image Only", value=PageLayout.IMAGE_ONLY).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(layoutFrm, variable=self._layout, text="Caption Sidebar", value=PageLayout.CAPTION_SIDEBAR).grid(row=0, column=1, padx=5) 
        layoutFrm.grid(row=1, column=0, columnspan=5, sticky=(W))
        
        listControls = ttk.Frame(self)
        listControls.pack(side=RIGHT, anchor=NE, fill=Y, expand=True)
        

        ceilBtn = ttk.Button(listControls, text='\u2191\u2191', width=2, command=lambda : self._list.ceilEntry(self))
        ceilBtn.grid(row=0, column=0)   
        moveUpBtn = ttk.Button(listControls, text='\u2191', width=2, command=lambda : self._list.moveEntryUp(self))
        moveUpBtn.grid(row=1, column=0)
        moveDownBtn = ttk.Button(listControls, text='\u2193',  width=2, command=lambda : self._list.moveEntryDown(self))
        moveDownBtn.grid(row=2, column=0)
        floorBtn = ttk.Button(listControls, text='\u2193\u2193', width=2, command=lambda : self._list.floorEntry(self))
        floorBtn.grid(row=3, column=0)
        
        self.moveControls = [
            self.MoveControl(ceilBtn, "Move to top", lambda : self._index > 0),
            self.MoveControl(moveUpBtn, "Shift up", lambda : self._index > 0),
            self.MoveControl(moveDownBtn, "Shift down", lambda : self._index < len(self._list)-1),
            self.MoveControl(floorBtn, "Move to bottom", lambda : self._index < len(self._list)-1)
        ]      
        
        self.grid(row=self._index, column=0, **IMAGE_SETTINGS)
        self.updateControlsState()
    
    @property
    def layout(self):
        return self._layout.get()
    
    def onLayoutChange(self):
        pass
    
    def setRow(self, index):
        self._index = index
        self.grid(row=index, column=0, **IMAGE_SETTINGS)
        self.updateControlsState()
        
    def updateControlsState(self):
        for ctrl in self.moveControls:
            ctrl.update()
        
    def openSourceFolder(self):
        
        path = os.path.dirname(self._file).replace("/", "\\")
        system = platform.system()
        if system == "Windows":
            subprocess.Popen('explorer /select,"%s"' % self._file.replace('/', '\\'))
        elif system == "Darwin":
            subprocess.Popen(['open', path])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", path])
            
    def setLayout(self, layout: PageLayout):
        self._layout = layout
        
    def onFileDblClick(self, evt):
        os.startfile(self._file)
        
    @property
    def file(self):
        return self._file
    
        
    
   
    