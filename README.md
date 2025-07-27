# PDF Image Bundler

This tool is designed to let users create PDF files consisting of full-page images, with each page sized to each image's print resolution (image size / DPI).

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
