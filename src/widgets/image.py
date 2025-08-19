from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk, font
from tktooltip import ToolTip
from typing import Callable
from enum import Enum
import PIL.Image

import os
import subprocess
import platform

from ..utils import Resolution, Orientation
from .caption import EditCaptionDialog

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
    
    def updateControlsState(self, state=None):
        pass
    
    def toggleControls(self, disabled):
        pass

class ImageList(ttk.Frame):
    
    _files: list[ImageEntry] = []
    _widgets: list[ttk.Widget] = []
    
    def __init__(self, master = None, app = None, title: str = "", **kwargs):
        ttk.Frame.__init__(self, master, **kwargs)
        self._app = app
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
        self.frame.bind("<Configure>", self.onFrameConfig)
        f2 = ttk.Frame(self)
        f2.pack(side=RIGHT, fill=Y, anchor=E)
        
    def _on_mousewheel(self, evt: Event):
        self.canvas.yview_scroll(int(-1*(evt.delta/120)), "units")
    
    def __len__(self):
        return len(self._files)
    
    @property
    def files(self):
        return self._files
    
    def setFiles(self, files: list[ImageEntry]):
        self._files = files
        self.onFrameUpdate()
            
    def loadFromJson(self, entriesJson):        
        self._files = []
        for i in range(0, len(entriesJson)):
            self._files.append(None)            
        for im_json in entriesJson:
            if "index" in im_json:
                im_json["page"] = im_json["index"] + 1
                del im_json["index"]
            self._files[int(im_json["page"])-1] = ImageEntry.fromJson(im_json, self)
        
    def onAddFiles(self, index=None):
        selectedFiles = filedialog.askopenfilenames(parent=self,
            title="Select images to add", 
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;")], 
            multiple=True,
        )
        if selectedFiles:
            for (i, file) in enumerate(selectedFiles):
                self.createEntry(file, )
        
        self.onFrameUpdate()
        self.canvas.yview_moveto(1.0)
                
    def onInsertFiles(self, widget):
        self.onAddFiles(self._widgets.index(widget) // 2)
        
    def onFrameConfig(self, evt: Event):
        self.canvas.itemconfig(self.windows_item, width = evt.width)
        self.onFrameUpdate()
        
    def onFrameUpdate(self):        
        self.canvas.configure(scrollregion=self.frame.bbox())
        self.canvas.update_idletasks()
    
    def clear(self):
        for w in self._files:
            w.grid_forget()
            w.destroy()
            
        self._files = []
        
    def toggleControls(self, disabled):
        for entry in self._files:
            entry.toggleControls(disabled)
            
    def createEntry(self, filePath, index=None):
        image = ImageEntry(self, filePath, scale=self._app.defaultScale.get())
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
        if index == len(self._files) and index > 0:
            self._files[index-1].updateControlsState()
        else:
            for (ix, im) in enumerate(self._files[index:]):
                im.setRow(ix-1)
            
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
        entry.setRow(len(self._files)-1)
                
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
    _layout: IntVar
    _font: tuple = ("Arial", 12)
    _dialog: Toplevel = None
    _sidebarSize: DoubleVar
    _scale: DoubleVar
    resolution: Resolution
    
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
            
        def update(self, state=None):
            if state is not None:
                if state == "normal" and self.tooltip is None:
                    self.tooltip = ToolTip(self.btn, self.msg, delay=0.5)
                elif state == "disabled" and self.tooltip is not None:
                    self.tooltip.destroy()
                    self.tooltip = None
                self.btn.configure(state=state, cursor="hand2" if state=="normal" else None)
            elif self.state_fn():
                if self.tooltip is None:
                    self.tooltip = ToolTip(self.btn, self.msg, delay=0.5)
                self.btn.configure(state = "normal", cursor="hand2")
            else:
                if self.tooltip is not None:
                    self.tooltip.destroy()
                    self.tooltip = None
                self.btn.configure(state="disabled", cursor=None)
                
    def __init__(self, 
            list: ImageList, 
            file: str, 
            layout: PageLayout | str = PageLayout.IMAGE_ONLY, 
            caption = "", 
            scale = 1.0, 
            page = None,
            # normalizeExclude: bool = False, 
            sidebar = 3.0,
            sidebarPosition = None):      
        ttk.Frame.__init__(self, list.frame, padding=5, border=2, relief=SOLID, borderwidth=2)
        self._list = list
        self._file = file
        if isinstance(layout, str):
            layout = PageLayout[layout]
        self._layout = IntVar(value=layout.value)   
        self._sidebarSize = DoubleVar(value=sidebar)
        if not caption:
            info = IPTCInfo(self._file)
            try:
                self._caption = info['caption/abstract'].decode("utf-8")
            except:
                self._caption = ""
        else:
            self._caption = caption
        self.resolution = Resolution.fromFilePath(file)
        self._scale = DoubleVar(value = scale)
                
        f = ttk.Frame(self)
        f.pack(side=LEFT, fill=BOTH, expand=True)
        f.grid_columnconfigure((1, 2, 3, 4), weight=1)
        f.grid_columnconfigure(0, weight=0, minsize=5)
        f.grid_columnconfigure(1, pad=5)  
        f.grid_rowconfigure(1, weight=0)
        f.grid_rowconfigure(3, weight=1)

        defaultfont = ("Arial", 10)
        hoverfont = ("Arial", 10, "underline")
        self.page = IntVar(value = page if page is not None else len(self._list)+1)
        ttk.Label(f, textvariable=self.page, width=5, anchor=CENTER, relief="sunken").grid(row=0, column=0, sticky=(W))
        label = ttk.Label(f, text=os.path.basename(self._file), font=defaultfont, justify="left")
        ToolTip(label, msg="Double-click to open file", delay=1.5)
        label.grid(row=0, column=1, columnspan=4, sticky=(W, E))
        label.bind("<Enter>", lambda evt : evt.widget.configure(font=hoverfont, cursor="hand2"), add="+")
        label.bind("<Leave>", lambda evt : evt.widget.configure(font=defaultfont, cursor=None), add="+")
        label.bind("<Double-Button-1>", self.onFileDblClick)
        self._index = page - 1 if page is not None else len(self._list)
        
        
        
        self.sf = ttk.Frame(f)
        self.sf.grid_columnconfigure(3, weight=0, minsize=10)
        ttk.Label(self.sf, text="Sidebar Size: ").grid(row=0, column=0, sticky=(W))
        self.sidebarInput = ttk.Entry(self.sf, textvariable=self._sidebarSize, width=5)
        self.sidebarInput.grid(row=0, column=1, sticky=(E, W))
        ttk.Label(self.sf, text="in").grid(row=0, column=2, sticky=(W))
        ttk.Label(self.sf, text="Sidebar Position").grid(row=0, column=4)
        if sidebarPosition is None:
            if self.resolution.getOrientation() == Orientation.LANDSCAPE:
                sidebarPosition = RIGHT
            else:
                sidebarPosition = BOTTOM
                
        self.sidebarPosition = StringVar(value = sidebarPosition)
        ttk.OptionMenu(self.sf, self.sidebarPosition, sidebarPosition, BOTTOM, RIGHT).grid(row=0, column=5)

        ttk.Label(f, text="Image Scale").grid(row=3, column=0, columnspan=2, sticky=(W))
        ttk.Entry(f, textvariable=self._scale, width=5).grid(row=3, column=2, sticky=(W, E))
        layoutFrm = ttk.Frame(f)
        ttk.Radiobutton(layoutFrm, variable=self._layout, text="Image Only", value=PageLayout.IMAGE_ONLY.value, command=self.onLayoutChange).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(layoutFrm, variable=self._layout, text="Caption Sidebar", value=PageLayout.CAPTION_SIDEBAR.value, command=self.onLayoutChange).grid(row=0, column=1, padx=5) 
        layoutFrm.grid(row=1, column=0, columnspan=5, sticky=(W))
        
        f2 = ttk.Frame(f)
        self.delBtn = ttk.Button(f2, text='\u2715', cursor="hand2", width=3, command = self.onRemove, style="Delete.TButton")
        self.delBtn.pack(side=LEFT, padx=2)
        ToolTip(self.delBtn, msg="Remove image", delay=0.5)
        self.expBtn = ttk.Button(f2, text='\U0001F5C0', cursor="hand2", width=3, command=self.openSourceFolder)
        self.expBtn.pack(side=LEFT)
        ToolTip(self.expBtn, msg="View in File Explorer", delay=0.5)
        
        self.captionBtn = ttk.Button(f2, text="Edit Caption", command=self.editCaption, state="disabled")
        self.captionBtn.pack(side=LEFT, padx=10)
        ttk.Label(f2, text="(%.2fin x %.2fin)" % self.resolution.toTuple()).pack(side=RIGHT)
        
        f2.grid(row=5, column=0, columnspan=6, sticky=(W, S))
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
        
        if self.layout == PageLayout.CAPTION_SIDEBAR:
            self.sf.grid(row=3, column=3, columnspan=2, sticky=(W))
            self.captionBtn.configure(state="normal")
            
        self.grid(row=self._index, column=0, **IMAGE_SETTINGS)
        self.updateControlsState()
    
    @staticmethod
    def fromJson(json: dict, list: ImageList) -> ImageEntry:
        return ImageEntry(list, **json)
        
    def toJson(self):
        return {
            "file": self._file,
            "scale": self._scale.get(),
            "layout": self.layout.name,
            "caption": self._caption,
            "page": self.page.get(),
            "sidebar": self._sidebarSize.get(),
            "sidebarPosition": self.sidebarPosition.get()
        }
    
    def setScale(self, scale): 
        self._scale.set(scale)
    
    def setSidebarSize(self, size):
        self._sidebarSize.set(size)
        
    def onLayoutChange(self):
        layout = PageLayout(self._layout.get())
        if layout == PageLayout.CAPTION_SIDEBAR:
            self.captionBtn.configure(state="normal", cursor="hand2")
            self.sf.grid(row=3, column=3, columnspan=2, sticky=(W))
        else:
            self.captionBtn.configure(state="disabled", cursor=None)
            self.sf.grid_forget()
    
    def onRemove(self):
        if messagebox.askyesno("Remove Image?", "Are you sure you want to remove this image?"):
            self._list.removeEntry(self)
            
    def editCaption(self):
        EditCaptionDialog(self._caption, onSave = self.setCaption, onClose=self.onEditDialogClose)
        self._list.toggleControls(True)
    
    def getResolution(self) -> Resolution:
        return self.resolution.scale(self._scale.get())
    @property
    def layout(self) -> PageLayout:
        return PageLayout(self._layout.get())
    
    @property
    def sidebarSize(self) -> float:
        return self._sidebarSize.get()
    
    @property
    def filePath(self) -> str:
        return self._file
    
    def getImageScale(self) -> float:
        return self._scale.get()
    
    def getCaption(self) -> str:
        return self._caption
    
    def setCaption(self, caption: str):
        self._caption = caption
    
    def onEditDialogClose(self):
        self.captionBtn.configure(state="normal")
        self._list._app.root.focus_force()
        self._list.toggleControls(False)
    
    def toggleControls(self, disabled):
        if not disabled:
            if self.layout == PageLayout.CAPTION_SIDEBAR:
                self.captionBtn.configure(state="normal", cursor="hand2")
            else:
                self.captionBtn.configure(state="disabled", cursor=None)
        else:
            self.captionBtn.configure(state="disabled", cursor=None)
        
        state = "normal" if not disabled else "disabled"
        cursor = "hand2" if not disabled else None
        self.delBtn.configure(state=state, cursor=cursor)
        self.expBtn.configure(state=state, cursor=cursor)
        self.updateControlsState(state)
        
    def setRow(self, index):
        self._index = index
        self.grid(row=index, column=0, **IMAGE_SETTINGS)
        self.page.set(index+1)
        self.updateControlsState()
        
    def updateControlsState(self, state=None):
        for ctrl in self.moveControls:
            ctrl.update(state)
        
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
    
        
    
   
    