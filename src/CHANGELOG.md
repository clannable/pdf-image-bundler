## 0.4.1
Added
- Base image resolutions now saved in bundles
  - Speeds up bundle loading times by not having to load image files to get the resolution
Modified
- Removed custom font settings from LaTeX template file (for now)
- Changed package used to remove first page to *pagesel*

## 0.4.0
Added
- "Force remove first page" option in Options menu
  - To be used in cases where the first page of the bundle can sometimes get wrapped by LaTeX, creating an extra blank page at the start of the PDF

## 0.3.2
Fixed
- Error retrieving caption when image is missing the metadata field

## 0.3.1
Added
- Keyboard shortcuts for saving (CTRL+S), opening (CTRL+O) bundles  
- Keyboard shortcut for saving caption while editing (CTRL+S)
  - Using CTRL+S to save will not close the edit caption window
  
## 0.3.0
Added
- Caption sidebar layout
  - Adds additional space to the page for a text area to display the image's caption (below for portait images, to the right for landscape)
  - Caption can be edited by clicking the "Edit Caption" button while the "Caption Sidebar" layout is selected
    - When an image is added, caption is loaded from IPTC metadata (if available)
    - Captions can be styled using LaTeX syntax
  - Space to add can be customized using the "Sidebar Size" input field on each image
    - Field is only visible when "Caption Sidebar" layout is selected
- Paragraph spacing option
  - Specifies space between paragraphs in caption when rendered to PDF
    - Paragraphs are denoted by newlines (Enter key)
- Default scale option
  - Specifies Image Scale value to initially apply for newly added images (does not overwrite scale values for images already listed)
- Save/Load bundles
  - Image bundles can now be saved and loaded to maintain progress, especially useful when customizing captions
    - Bundles are saved as JSON files
  - The following settings are saved in bundles:
    - Paragraph spacing
    - Default image scale
    - Output directory
    - "Output to image source folder" check value
    - Output file name
    - Selected files:
      - File path
      - Image scale
      - Layout
      - Caption
      - Page number/list position
      - Sidebar size

Fixed
- File list scrollbar not adjusting after adding file(s) 
  
## 0.2.0
Added
- Custom widgets for listing image files
  - Replaces basic list widget
  - Allows for more individual controls, settings for each image

## 0.1.0
Added
- Initial bundler app