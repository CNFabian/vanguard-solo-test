#!/bin/bash

echo "🔧 FIXING MINIMAL TEST ROM BUILD"
echo "================================"

# Check for existing romfs.bin files
echo "Looking for existing romfs.bin..."

if [ -f "romfs.bin" ]; then
    echo "✅ Found romfs.bin in current directory"
    ROMFS_PATH="romfs.bin"
elif [ -f "build_temp/romfs.bin" ]; then
    echo "✅ Found romfs.bin in build_temp/"
    ROMFS_PATH="build_temp/romfs.bin"
else
    echo "❌ No romfs.bin found, extracting from original ROM..."
    ./tools/ctrtool --romfs=romfs.bin cf_vanguard.3ds
    if [ -f "romfs.bin" ]; then
        echo "✅ Extracted romfs.bin"
        ROMFS_PATH="romfs.bin"
    else
        echo "❌ Failed to extract romfs.bin"
        exit 1
    fi
fi

# Verify we have the required files
echo ""
echo "Checking required files..."

for file in "files/full_patched_minimal.bin" "files/exheader_patched.bin" "files/cf_vanguard.rsf"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing $file"
        exit 1
    fi
done

# Extract banner and icon if needed
if [ ! -f "banner.bin" ] || [ ! -f "icon.bin" ]; then
    echo ""
    echo "Extracting banner and icon..."
    ./tools/ctrtool --exefsdir=. cf_vanguard.3ds
fi

# Build the minimal test ROM
echo ""
echo "Building minimal test ROM..."
./tools/makerom -f cci \
    -o cf_vanguard_minimal_test.3ds \
    -rsf files/cf_vanguard.rsf \
    -code files/full_patched_minimal.bin \
    -exheader files/exheader_patched.bin \
    -banner banner.bin \
    -icon icon.bin \
    -romfs "$ROMFS_PATH"

if [ -f "cf_vanguard_minimal_test.3ds" ]; then
    ROM_SIZE=$(stat -f%z "cf_vanguard_minimal_test.3ds" 2>/dev/null || stat -c%s "cf_vanguard_minimal_test.3ds")
    echo ""
    echo "🎉 MINIMAL TEST ROM COMPLETED!"
    echo "=============================="
    echo "📁 Output: cf_vanguard_minimal_test.3ds"
    echo "📊 Size: ${ROM_SIZE} bytes"
    echo "📈 Contains exactly ONE English translation"
    echo ""
    echo "🎯 MISSION: Find this exact text in the game:"
    echo "   'You can change your character's appearance, name, and nickname'"
    echo ""
    echo "🔍 SEARCH AREAS (most likely first):"
    echo "1. Main Menu → Options/Settings (環境設定)"
    echo "2. Character Profile/Info screens"
    echo "3. Help/Tutorial menus"
    echo "4. Communication Settings"
    echo "5. New Game character creation"
    echo ""
    echo "💡 TIP: Since this is the ONLY English text in the ROM,"
    echo "   it should be easy to spot among all the Japanese text!"
else
    echo "❌ ROM build failed again"
    echo ""
    echo "🔍 Let's try a different approach..."
    
    # Alternative: Use the existing successful ROM but test systematically
    if [ -f "cf_vanguard_test_translation.3ds" ]; then
        echo ""
        echo "✅ We still have the working ROM: cf_vanguard_test_translation.3ds"
        echo "🎯 TESTING STRATEGY:"
        echo "Load cf_vanguard_test_translation.3ds and systematically check:"
        echo ""
        echo "1. MAIN MENU - scan every text element"
        echo "2. OPTIONS/SETTINGS - check all submenus"
        echo "3. PROFILE/CHARACTER - any character-related screens"
        echo "4. HELP/TUTORIAL - instruction screens"
        echo "5. NEW GAME - character creation process"
        echo ""
        echo "👀 Look for ANY English text - even one word means success!"
    fi
fi