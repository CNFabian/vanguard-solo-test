#!/bin/bash
# Makerom Installer for macOS
# Sets up makerom for CF Vanguard ROM building

echo "🔧 MAKEROM INSTALLER FOR MACOS"
echo "==============================="
echo ""

# Check if makerom is already installed
if command -v makerom &> /dev/null; then
    echo "✅ makerom is already installed!"
    makerom --version 2>/dev/null || echo "makerom found in PATH"
    exit 0
fi

# Check if we have a local tools directory
TOOLS_DIR="tools"
mkdir -p "$TOOLS_DIR"

echo "📥 Downloading makerom for macOS..."

# Try to download precompiled makerom
MAKEROM_URL="https://github.com/3DSGuy/Project_CTR/releases/download/makerom-v0.18.3/makerom-v0.18.3-macos_x86_64.zip"
MAKEROM_ZIP="$TOOLS_DIR/makerom.zip"

if command -v curl &> /dev/null; then
    echo "⬇️  Downloading with curl..."
    if curl -L -o "$MAKEROM_ZIP" "$MAKEROM_URL" 2>/dev/null; then
        echo "✅ Download successful"
    else
        echo "❌ Download failed with curl"
        DOWNLOAD_FAILED=1
    fi
elif command -v wget &> /dev/null; then
    echo "⬇️  Downloading with wget..."
    if wget -O "$MAKEROM_ZIP" "$MAKEROM_URL" 2>/dev/null; then
        echo "✅ Download successful"
    else
        echo "❌ Download failed with wget"
        DOWNLOAD_FAILED=1
    fi
else
    echo "❌ Neither curl nor wget found"
    DOWNLOAD_FAILED=1
fi

# Extract if download was successful
if [ ! "$DOWNLOAD_FAILED" ] && [ -f "$MAKEROM_ZIP" ]; then
    echo "📂 Extracting makerom..."
    
    if command -v unzip &> /dev/null; then
        cd "$TOOLS_DIR"
        unzip -q makerom.zip
        
        # Find the makerom binary
        MAKEROM_BIN=$(find . -name "makerom" -type f | head -1)
        
        if [ -n "$MAKEROM_BIN" ]; then
            # Make it executable
            chmod +x "$MAKEROM_BIN"
            
            # Move to tools root
            mv "$MAKEROM_BIN" "./makerom"
            
            echo "✅ makerom extracted to tools/makerom"
            
            # Test it
            if ./makerom --version &>/dev/null; then
                echo "✅ makerom is working!"
            else
                echo "⚠️  makerom extracted but may not work on this system"
            fi
        else
            echo "❌ makerom binary not found in archive"
            DOWNLOAD_FAILED=1
        fi
        
        # Clean up
        rm -f makerom.zip
        rm -rf __MACOSX 2>/dev/null
        cd ..
    else
        echo "❌ unzip not found, cannot extract"
        DOWNLOAD_FAILED=1
    fi
fi

# If download failed, try alternative methods
if [ "$DOWNLOAD_FAILED" ]; then
    echo ""
    echo "🔄 ALTERNATIVE INSTALLATION METHODS:"
    echo ""
    
    echo "1. HOMEBREW (Recommended):"
    echo "   If you have Homebrew installed:"
    echo "   brew install --cask makerom"
    echo ""
    
    echo "2. MANUAL DOWNLOAD:"
    echo "   Visit: https://github.com/3DSGuy/Project_CTR/releases"
    echo "   Download makerom for macOS"
    echo "   Extract to tools/ directory"
    echo ""
    
    echo "3. BUILD FROM SOURCE:"
    echo "   git clone https://github.com/3DSGuy/Project_CTR.git"
    echo "   cd Project_CTR/makerom"
    echo "   make"
    echo ""
    
    echo "4. USE EXISTING TOOLS:"
    echo "   If you have 3DS development tools already:"
    echo "   Copy makerom to this project's tools/ directory"
    echo ""
    
    # Check if user has Homebrew
    if command -v brew &> /dev/null; then
        echo "🍺 Homebrew detected!"
        read -p "Install makerom via Homebrew? (y/N): " install_brew
        if [[ $install_brew =~ ^[Yy]$ ]]; then
            echo "⬇️  Installing makerom with Homebrew..."
            if brew install makerom 2>/dev/null; then
                echo "✅ makerom installed via Homebrew!"
            else
                echo "⚠️  Homebrew installation failed, try manual methods above"
            fi
        fi
    fi
    
    exit 1
fi

# Update PATH suggestion
echo ""
echo "🔧 SETUP COMPLETE!"
echo ""
echo "Makerom location: $(pwd)/tools/makerom"
echo ""
echo "💡 To use makerom from anywhere, add to your PATH:"
echo "   export PATH=\"$(pwd)/tools:\$PATH\""
echo ""
echo "🎯 FOR THIS PROJECT:"
echo "   The build script will automatically find makerom in tools/"
echo "   No additional setup needed!"
echo ""
echo "✅ Ready to build CF Vanguard English ROM!"