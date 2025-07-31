from tkinter import Toplevel, Text, RIGHT, LEFT, END
from tkinter import ttk
from typing import Callable
class EditCaptionDialog(Toplevel):
    caption: str
    tags: list[str]
    
    def __init__(self, caption: str, onSave: Callable[[str], None], onClose: Callable[[], None], **kwargs):
        Toplevel.__init__(self, height=180, width=200, **kwargs)
        self.title("Edit Image Caption")
        self.resizable(True, True)
        self.grab_set()
        self.caption = caption
        self.onSave = onSave
        self.onClose = onClose
        self.protocol("WM_DELETE_WINDOW", self.close)
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)
        self.text = Text(f)
        self.text.insert("0.0", caption or "")
        self.text.pack(fill="both")
        ttk.Sizegrip(self).pack(side="bottom", anchor="se")
        bf = ttk.Frame(self, padding=10)
        bf.pack(side="bottom", anchor="s")
        self.saveBtn = ttk.Button(bf, text="Save", state="disabled", command=self.saveAndClose)
        self.saveBtn.pack(side=RIGHT, padx=5)
        ttk.Button(bf, text="Close", command=self.close).pack(side=LEFT, padx=5)
        self.text.bind("<Key>", self.onKeyPress)
        self.text.bind("<Control-s>", self.save)
        
        
    def onKeyPress(self, event):
        self.saveBtn.configure(state="normal" if self.caption != self.text.get("0.0", END) else "disabled")
        
    def saveAndClose(self):
        self.caption = self.text.get("0.0", END)
        self.onSave(self.caption)
        self.grab_release()
        self.close()
        
    def save(self):
        self.caption = self.text.get("0.0", END)
        self.saveBtn.configure(state="disabled")
        self.onSave(self.text.get("0.0", END))
        
    def close(self):
        self.onClose()
        self.destroy()
