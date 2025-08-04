#!/bin/bash
# Quick Zero Test ROM Builder - Fixed Version
# This fixes the makerom path issue

echo "🧪 QUICK ZERO TEST ROM BUILD"
echo "============================"

# Check if we have everything
if [ ! -d "romfs_zero_test" ]; then
    echo "❌ Missing romfs_zero_test directory"
    exit 1
fi

if [ ! -f "files/code.bin" ] || [ ! -f "files/exheader.bin" ]; then
    echo "❌ Missing code.bin or exheader.bin in files/"
    exit 1
fi

if [ ! -f "makerom" ]; then
    echo "❌ Missing makerom in current directory"
    exit 1
fi

echo "✅ All files found, building zero test ROM..."

# Create simple build directory
BUILD_DIR="build_quick_zero"
rm -rf "$BUILD_DIR" 2>/dev/null
mkdir -p "$BUILD_DIR"
mkdir -p logs

# Copy files
cp files/code.bin "$BUILD_DIR/"
cp files/exheader.bin "$BUILD_DIR/"
cp -r romfs_zero_test "$BUILD_DIR/romfs"

# Create minimal RSF
cat > "$BUILD_DIR/zero.rsf" << 'EOF'
BasicInfo:
  Title                   : "CF Vanguard Zero Test"
  ProductCode             : CTR-P-BVGJ
  Logo                    : Nintendo

RomFs:
  RootPath                : romfs

TitleInfo:
  Category                : Application
  UniqueId                : 0x001658

SystemControlInfo:
  SaveDataSize: 1MB
  RemasterVersion: 0
  StackSize: 0x40000
EOF

# Build ROM (staying in main directory)
echo "🔨 Building zero test ROM..."
echo "Command: ./makerom -f cci -o cf_vanguard_zero_test.3ds -code $BUILD_DIR/code.bin -exheader $BUILD_DIR/exheader.bin -romfs $BUILD_DIR/romfs -rsf $BUILD_DIR/zero.rsf"

./makerom -f cci \
    -o "cf_vanguard_zero_test.3ds" \
    -code "$BUILD_DIR/code.bin" \
    -exheader "$BUILD_DIR/exheader.bin" \
    -romfs "$BUILD_DIR/romfs" \
    -rsf "$BUILD_DIR/zero.rsf" \
    2>&1 | tee "logs/quick_zero_build_$(date +%Y%m%d_%H%M%S).log"

# Check result
if [ -f "cf_vanguard_zero_test.3ds" ]; then
    ROM_SIZE=$(ls -lh cf_vanguard_zero_test.3ds | awk '{print $5}')
    echo ""
    echo "🎉 ZERO TEST ROM BUILD SUCCESSFUL!"
    echo "ROM: cf_vanguard_zero_test.3ds ($ROM_SIZE)"
    echo ""
    echo "🧪 ZERO TEST INSTRUCTIONS:"
    echo "1. Load cf_vanguard_zero_test.3ds in Citra"
    echo "2. Navigate to tutorial sections"
    echo "3. Look for '0' characters instead of Japanese text"
    echo ""
    echo "🎯 EXPECTED RESULTS:"
    echo "✅ SUCCESS: See '0' characters → RTZ injection mechanism works!"
    echo "❌ FAILURE: Still Japanese → RTZ files not being read"
else
    echo ""
    echo "❌ BUILD FAILED!"
    echo "Check the log file for details"
fi