# PDF Image Bundler

This tool is designed to let users create PDF files consisting of full-page images, with each page sized to each image's print resolution (image size / DPI).

I set out to make this because I wanted to "print" a bunch of images to a single PDF file as full-page images, but found using *Print to PDF* was too cumbersome when I was often dealing with images that didn't fit existing paper sizes.

This tool uses LaTeX to generate a PDF file where each page is the exact print size of the image on it. The "Image Scale" field will scale all input image files, so if your images are bigger than the rough page size desired, they can be shrunk down.

**Planned Features (so far)**
- Additional page layout options
    - Include image caption on page
    - Multiple images per page (i.e. two-column)
- Per-image scale settings
- Better look and feel

![UI window](./docs/window2.jpg)


## Requirements

- pdflatex (included in [standard LaTeX distributions](https://www.latex-project.org/get/))
- Python >= 3.11

## Setup

1. Set up virtual environment

```sh
python -m venv venv
```

2. Activate virutal environment
```sh
# for cmd
venv\Scripts\activate.bat
# for powershell
venv\Scripts\Activate.ps1
# for linux/mac
source venv/bin/activate
```

3. Install requirements
```sh
pip install -r requirements.txt
```

4. Execute main python script

```sh
python main.py
```
