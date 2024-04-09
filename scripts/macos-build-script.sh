# Define directories
DATA_DIR='data'
LIBS_DIR='data/libs'
MODELS_DIR='data/models'
MANGA_OCR_BASE_DIR='data/models/manga-ocr-base'
PKUSEG_DIR='data/models/pkuseg'
POSTAG_DIR='data/models/pkuseg/postag'
SPACY_ONTONOTES_DIR='data/models/pkuseg/spacy_ontonotes'

# Create and activate Python virtual environment
echo "STEP 2: Create and activate Python virtual environment"
python_version=$(python3 -V 2>&1 | cut -d" " -f2 | cut -d"." -f1-2)

if ! which python3 >/dev/null 2>&1; then
    echo "ERROR: ❌ The 'python3' command not found."
    echo "ERROR: Please check the Python environment configuration."
    exit 1
else
    echo "INFO: The 'python3' command found." 
    if [ "$python_version" == "3.11" ]; then
        echo "INFO: ✅ The current Python version is 3.11"
        python3 -m venv venv
        echo "INFO: ✅ Python virtual enviroment created."
        source venv/bin/activate
        echo "INFO: ✅ Python virtual enviroment activated."
    else
        echo "ERROR: ❌ The current Python version is $python_version but 3.11 is required."
        echo "ERROR: Please switch to Python 3.11 before running this script."
        exit 1
    fi
fi

# OpenCV installation check
echo "STEP 3: Check installation of OpenCV."
echo "INFO: Install OpenCV Python package in virtual environment."
pip3 install opencv-python
echo "INFO: Checking OpenCV installation..."
python3 -c "import cv2" 2>/dev/null
if [ $? -eq 0 ]; then
    opencv_version=$(python3 -c "import cv2; print(cv2.__version__)")
    echo "INFO: ✅ OpenCV is installed. Version: $opencv_version"
else
    echo "ERROR: ❌ OpenCV is not installed."
    echo "ERROR: Please install OpenCV before running this script."
    echo "INFO: Recommand install via Homebrew with command 'brew install opencv'."
    exit 1
fi

# Checklist of extra data files
check_list="
data/alphabet-all-v5.txt
$LIBS_DIR/libopencv_world.4.4.0.dylib
$LIBS_DIR/libpatchmatch_inpaint.dylib
$MODELS_DIR/aot_inpainter.ckpt
$MODELS_DIR/comictextdetector.pt
$MODELS_DIR/comictextdetector.pt.onnx
$MODELS_DIR/lama_mpe.ckpt
$MANGA_OCR_BASE_DIR/README.md
$MANGA_OCR_BASE_DIR/config.json
$MANGA_OCR_BASE_DIR/preprocessor_config.json
$MANGA_OCR_BASE_DIR/pytorch_model.bin
$MANGA_OCR_BASE_DIR/special_tokens_map.json
$MANGA_OCR_BASE_DIR/tokenizer_config.json
$MANGA_OCR_BASE_DIR/vocab.txt
$MODELS_DIR/mit32px_ocr.ckpt
$MODELS_DIR/mit48pxctc_ocr.ckpt
$POSTAG_DIR/features.pkl
$POSTAG_DIR/weights.npz
$SPACY_ONTONOTES_DIR
$SPACY_ONTONOTES_DIR/features.msgpack
$SPACY_ONTONOTES_DIR/weights.npz
data/pkusegscores.json
"

# Validate extra data files exist
echo "STEP 5: Validate data files exist."
fail=false
for item in $check_list; do
    if [ ! -e "$item" ]; then
        echo "ERROR: ❌ $item not found"
        fail=true
    fi
done
 
if [ "$fail" = true ]; then
    echo "ERROR: ❌ Data files check failed. Exiting."
    exit 1
else
    echo "INFO: ✅ Data files all exist."
fi

# Install Python dependencies
echo "STEP 6: Install Python dependencies."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Delete .DS_Store files 
echo "STEP 7: Delete .DS_Store files."
echo "INFO: Permission required to delete .DS_Store files."
sudo find ./ -name '.DS_Store'
sudo find ./ -name '.DS_Store' -delete
echo "INFO: ✅ .DS_Store files all deleted."

# Create packaged app
echo "STEP 8: Create packaged app."
echo "INFO: Use the pyinstaller spec file to bundle the app."
sudo pyinstaller launch.spec

# Check if app exists
app_path="dist/BallonsTranslator.app"
if [ -e "$app_path" ]; then
    # Copy app to Downloads folder
    echo "INFO: Copying app to Downloads folder..."
    ditto "$app_path" "$HOME/Downloads/BallonsTranslator.app"
    echo "INFO: ✅ The app is now in your Downloads folder."
    echo "INFO: Drag and drop the app icon into Applications folder to install it."
    open $HOME/Downloads
else
    echo "ERROR: ❌ App not found. Please build the app first."
fi
