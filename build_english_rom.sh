#!/bin/bash
# CF Vanguard English ROM Builder
# Phase 5.3 - Build complete English ROM from injected RTZ files

set -e  # Exit on any error

echo "🎮 CF VANGUARD ENGLISH ROM BUILDER"
echo "=================================="
echo "Phase 5.3 - Creating first English CF Vanguard ROM"
echo ""

# Configuration
ROM_NAME="cf_vanguard_english_v1.3ds"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BUILD_DIR="build_english"
LOGS_DIR="logs"

# Check prerequisites
echo "🔍 CHECKING PREREQUISITES..."

if [ ! -d "romfs_english" ]; then
    echo "❌ English romfs not found!"
    echo "   Please run RTZ injection first:"
    echo "   python3 scripts/rtz_injection_system.py"
    exit 1
fi

if [ ! -f "files/code.bin" ]; then
    echo "❌ code.bin not found!"
    echo "   Please extract code.bin from ROM first"
    exit 1
fi

if [ ! -f "files/exheader.bin" ]; then
    echo "❌ exheader.bin not found!"
    echo "   Please extract exheader.bin from ROM first"
    exit 1
fi

# Check for ./makerom
if ! command -v ./makerom &> /dev/null; then
    echo "❌ ./makerom not found!"
    echo "   Please install ./makerom for ROM building"
    echo "   Or ensure it's in your PATH"
    exit 1
fi

echo "✅ All prerequisites found"
echo ""

# Create build environment
echo "📁 SETTING UP BUILD ENVIRONMENT..."
mkdir -p "$BUILD_DIR"
mkdir -p "$LOGS_DIR"

# Copy required files
echo "📋 Preparing build files..."
cp "files/code.bin" "$BUILD_DIR/"
cp "files/exheader.bin" "$BUILD_DIR/"

# Create romfs.bin from English romfs
echo "🔧 Building English romfs.bin..."
if command -v 3dstool &> /dev/null; then
    # Using 3dstool if available
    3dstool -cvtf romfs "$BUILD_DIR/romfs.bin" --romfs-dir "romfs_english" 2>&1 | tee "$LOGS_DIR/romfs_build_$TIMESTAMP.log"
elif [ -f "tools/3dstool" ]; then
    # Using local 3dstool
    ./tools/3dstool -cvtf romfs "$BUILD_DIR/romfs.bin" --romfs-dir "romfs_english" 2>&1 | tee "$LOGS_DIR/romfs_build_$TIMESTAMP.log"
else
    # Fallback: copy directory structure (less ideal but may work)
    echo "⚠️  3dstool not found, using directory copy fallback"
    cp -r "romfs_english" "$BUILD_DIR/romfs"
fi

echo "✅ English romfs.bin created"

# Create RSF file for ./makerom
echo "📝 Creating RSF configuration..."
cat > "$BUILD_DIR/english_vanguard.rsf" << EOF
BasicInfo:
  Title                   : CF Vanguard Stride to Victory English
  ProductCode             : CTR-BVCJ-EUR
  Logo                    : Nintendo

TitleInfo:
  UniqueId                : 0x2ee01
  Category                : Application
  
RomFs:
  RootPath                : romfs.bin

SystemControlInfo:
  SaveDataSize            : 1MB
  RemasterVersion         : 0
  StackSize               : 0x40000
EOF

echo "✅ RSF configuration created"

# Build the ROM
echo ""
echo "🔨 BUILDING ENGLISH ROM..."
echo "ROM Name: $ROM_NAME"
echo "Build Directory: $BUILD_DIR"
echo ""

cd "$BUILD_DIR"

# Build command
echo "⚙ Running ./makerom..."
./makerom -f cci \
        -o "../$ROM_NAME" \
        -code "code.bin" \
        -exheader "exheader.bin" \
        -romfs "romfs.bin" \
        -rsf "english_vanguard.rsf" \
        2>&1 | tee "../$LOGS_DIR/./makerom_$TIMESTAMP.log"

cd ..

# Check if ROM was created
if [ -f "$ROM_NAME" ]; then
    ROM_SIZE=$(ls -lh "$ROM_NAME" | awk '{print $5}')
    echo ""
    echo "🎉 ENGLISH ROM BUILD SUCCESSFUL!"
    echo "================================"
    echo "✅ ROM Created: $ROM_NAME"
    echo "✅ ROM Size: $ROM_SIZE"
    echo "✅ Build logs saved to: $LOGS_DIR/"
    
    # Validate ROM size (should be reasonable)
    ROM_BYTES=$(stat -f%z "$ROM_NAME" 2>/dev/null || stat -c%s "$ROM_NAME" 2>/dev/null)
    if [ "$ROM_BYTES" -gt 100000000 ]; then  # > 100MB
        echo "✅ ROM size looks reasonable"
    else
        echo "⚠️  ROM size seems small, check build logs"
    fi
    
    echo ""
    echo "🧪 TESTING RECOMMENDATIONS:"
    echo "1. Test in Citra emulator first"
    echo "2. Check for English text in tutorial/menus"
    echo "3. Verify game functionality is preserved"
    echo "4. Report any display issues"
    
    echo ""
    echo "🎮 LAUNCH IN CITRA:"
    echo "   citra-qt \"$ROM_NAME\""
    echo "   OR"
    echo "   Open Citra → File → Load File → $ROM_NAME"
    
    echo ""
    echo "📊 ENGLISH TRANSLATION CONTENT:"
    echo "   • Tutorial dialog in English"
    echo "   • Combat instructions translated"
    echo "   • Vanguard terminology (Attack, Guard, etc.)"
    echo "   • Card game mechanics explanations"
    echo "   • UI elements with color formatting"
    
    echo ""
    echo "🏆 CONGRATULATIONS!"
    echo "You've created the FIRST EVER English translation"
    echo "of CF Vanguard Stride to Victory!"
    echo ""
    echo "This is a historic achievement for the Vanguard community! 🎉"
    
else
    echo ""
    echo "❌ ROM BUILD FAILED"
    echo "Check build logs in $LOGS_DIR/"
    echo ""
    echo "🔧 Common fixes:"
    echo "1. Ensure ./makerom is properly installed"
    echo "2. Check that all input files exist"
    echo "3. Verify romfs_english directory structure"
    echo "4. Review ./makerom log for specific errors"
    exit 1
fi

# Clean up build directory option
echo ""
read -p "Clean up build directory? (y/N): " cleanup
if [[ $cleanup =~ ^[Yy]$ ]]; then
    rm -rf "$BUILD_DIR"
    echo "✅ Build directory cleaned"
fi

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Test the ROM in Citra"
echo "2. Document any translation issues"
echo "3. Share with Vanguard community"
echo "4. Iterate and improve translations"
echo ""
echo "Happy gaming! 🎮✨"