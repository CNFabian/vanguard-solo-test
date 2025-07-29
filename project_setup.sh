#!/bin/bash

echo "=== CF VANGUARD ROM EXTRACTION (FIXED) ==="
echo ""

# Create extraction directories
mkdir -p extract/exefs extract/romfs

# The main content file is the largest .app file (00_0004000000170500.app)
CONTENT_FILE="00_0004000000170500.app"

if [ ! -f "$CONTENT_FILE" ]; then
    echo "❌ Main content file $CONTENT_FILE not found!"
    echo "Available files:"
    ls -la *.app 2>/dev/null || echo "No .app files found"
    exit 1
fi

echo "✓ Using main content file: $CONTENT_FILE ($(stat -f%z "$CONTENT_FILE" 2>/dev/null || stat -c%s "$CONTENT_FILE") bytes)"

echo ""
echo "Step 1: Extract ExeFS and RomFS from main content..."
./tools/ctrtool --romfs=extract/romfs.bin --exefs=extract/exefs.bin "$CONTENT_FILE"

echo ""
echo "Step 2: Extract ExeFS directory (with code.bin)..."
./tools/ctrtool --exefsdir=extract/exefs --decompresscode "$CONTENT_FILE"

echo ""
echo "Step 3: Extract RomFS directory (with game assets)..."
./tools/ctrtool --romfsdir=extract/romfs "$CONTENT_FILE"

echo ""
echo "✓ ROM extraction completed!"
echo ""

# Check results
if [ -f "extract/exefs/code.bin" ]; then
    CODE_SIZE=$(stat -f%z "extract/exefs/code.bin" 2>/dev/null || stat -c%s "extract/exefs/code.bin")
    echo "✓ code.bin found (${CODE_SIZE} bytes)"
    
    # Copy to project root
    cp extract/exefs/code.bin ./code.bin
    echo "✓ code.bin copied to project root"
else
    echo "❌ code.bin not found"
fi

if [ -d "extract/romfs" ]; then
    echo "✓ RomFS extracted successfully"
    echo "RomFS directories:"
    ls -1 extract/romfs/ | head -10
else
    echo "❌ RomFS not extracted"
fi

echo ""
echo "=== EXTRACTION SUMMARY ==="
echo "Files extracted:"
if [ -f "extract/exefs.bin" ]; then echo "- extract/exefs.bin"; fi
if [ -f "extract/romfs.bin" ]; then echo "- extract/romfs.bin"; fi
if [ -d "extract/exefs" ]; then echo "- extract/exefs/ (directory)"; fi
if [ -d "extract/romfs" ]; then echo "- extract/romfs/ (directory)"; fi
if [ -f "code.bin" ]; then echo "- code.bin (copied to root)"; fi

echo ""
echo "Ready for character selection analysis!"