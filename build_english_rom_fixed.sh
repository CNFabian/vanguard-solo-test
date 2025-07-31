#!/bin/bash
# CF VANGUARD ENGLISH ROM BUILDER - FIXED VERSION
# Phase 5.3 - Building first English CF Vanguard ROM

set -e  # Exit on error

echo "🎮 CF VANGUARD ENGLISH ROM BUILDER"
echo "=================================="
echo "Phase 5.3 - Creating first English CF Vanguard ROM"
echo ""

# Configuration
ORIGINAL_ROM="cf_vanguard.3ds"
OUTPUT_ROM="cf_vanguard_english_v1.3ds"
BUILD_DIR="build_english"
ROMFS_ENG_DIR="romfs_english_precision"
RSF_FILE="cf_vanguard_complete.rsf"

# Check prerequisites
echo "🔍 CHECKING PREREQUISITES..."
if [ ! -f "$ORIGINAL_ROM" ]; then
    echo "❌ Original ROM not found: $ORIGINAL_ROM"
    exit 1
fi

if [ ! -f "makerom" ]; then
    echo "❌ makerom not found in current directory"
    echo "Looking for makerom in system..."
    if command -v makerom &> /dev/null; then
        echo "✅ Found system makerom"
        MAKEROM_CMD="makerom"
    else
        echo "❌ makerom not found. Please install it."
        exit 1
    fi
else
    echo "✅ Found local makerom"
    MAKEROM_CMD="./makerom"
fi

# Create build directory
echo ""
echo "📁 SETTING UP BUILD ENVIRONMENT..."
mkdir -p "$BUILD_DIR"

# Extract original ROM components if not already done
if [ ! -f "$BUILD_DIR/code.bin" ] || [ ! -f "$BUILD_DIR/exheader.bin" ]; then
    echo "📦 Extracting original ROM components..."
    
    # Use ctrtool if available, otherwise use makerom to extract
    if command -v ctrtool &> /dev/null; then
        echo "Using ctrtool..."
        ctrtool --exheader="$BUILD_DIR/exheader.bin" --exefsdir="$BUILD_DIR/exefs" --romfsdir="$BUILD_DIR/romfs_original" "$ORIGINAL_ROM"
        cp "$BUILD_DIR/exefs/code.bin" "$BUILD_DIR/code.bin" 2>/dev/null || cp "$BUILD_DIR/exefs/.code" "$BUILD_DIR/code.bin"
    else
        echo "Using makerom to extract..."
        # This is a fallback - makerom can't extract, so we need the files from previous extraction
        if [ ! -f "files/code.bin" ] || [ ! -f "files/exheader.bin" ]; then
            echo "❌ Need code.bin and exheader.bin from original ROM extraction"
            echo "Please extract them using ctrtool or 3dstool first"
            exit 1
        fi
        cp "files/code.bin" "$BUILD_DIR/code.bin"
        cp "files/exheader.bin" "$BUILD_DIR/exheader.bin"
    fi
fi

# Create complete RSF file
echo "📝 Creating complete RSF configuration..."
cat > "$BUILD_DIR/$RSF_FILE" << 'EOF'
BasicInfo:
  Title                   : "CF!! Vanguard G"
  ProductCode             : CTR-P-BVGJ
  Logo                    : Nintendo

RomFs:
  RootPath                : romfs

TitleInfo:
  Category                : Application
  UniqueId                : 0x001658

Option:
  UseOnSD                 : true
  FreeProductCode         : true
  MediaFootPadding        : false
  EnableCrypt             : false
  EnableCompress          : false
  
AccessControlInfo:
  CoreVersion                   : 2
  DescVersion                   : 2
  ReleaseKernelMajor            : "02"
  ReleaseKernelMinor            : "33" 
  UseExtSaveData                : false
  FileSystemAccess:
   - CategorySystemApplication
   - CategoryHardwareCheck
   - CategoryFileSystemTool
   - Debug
   - TwlCardBackup
   - TwlNandData
   - Boss
   - DirectSdmc
   - Core
   - CtrNandRo
   - CtrNandRw
   - CtrNandRoWrite
   - CategorySystemSettings
   - CardBoard
   - ExportImportIvs
   - DirectSdmcWrite
   - SwitchCleanup
   - SaveDataMove
   - Shop
   - Shell
   - CategoryHomeMenu

  MemoryType                    : Application
  SystemMode                    : 64MB
  IdealProcessor                : 0
  AffinityMask                  : 1
  Priority                      : 16
  MaxCpu                        : 0x9E
  HandleTableSize               : 0x200
  DisableDebug                  : false
  EnableForceDebug              : false
  CanWriteSharedPage            : true
  CanUsePrivilegedPriority      : false
  CanUseNonAlphabetAndNumber    : true
  PermitMainFunctionArgument    : true
  CanShareDeviceMemory          : true
  RunnableOnSleep               : false
  SpecialMemoryArrange          : true
  SystemModeExt                 : 124MB
  CpuSpeed                      : 804MHz
  EnableL2Cache                 : true
  CanAccessCore2                : true 

  IORegisterMapping:
   - 1ff00000-1ff7ffff
  MemoryMapping: 
   - 1f000000-1f5fffff:r

  SystemCallAccess: 
    ArbitrateAddress: 34
    Backdoor: 123
    Break: 60
    CancelTimer: 28
    ClearEvent: 25
    ClearTimer: 29
    CloseHandle: 35
    ConnectToPort: 45
    ControlMemory: 1
    CreateAddressArbiter: 33
    CreateEvent: 23
    CreateMemoryBlock: 30
    CreateMutex: 19
    CreateSemaphore: 21
    CreateThread: 8
    CreateTimer: 26
    DuplicateHandle: 39
    ExitProcess: 3
    ExitThread: 9
    GetCurrentProcessorNumber: 17
    GetHandleInfo: 41
    GetProcessId: 53
    GetProcessIdOfThread: 54
    GetProcessIdealProcessor: 6
    GetProcessInfo: 43
    GetResourceLimit: 56
    GetResourceLimitCurrentValues: 58
    GetResourceLimitLimitValues: 57
    GetSystemInfo: 42
    GetSystemTick: 40
    GetThreadContext: 59
    GetThreadId: 55
    GetThreadIdealProcessor: 15
    GetThreadInfo: 44
    GetThreadPriority: 11
    MapMemoryBlock: 31
    OutputDebugString: 61
    QueryMemory: 2
    ReleaseMutex: 20
    ReleaseSemaphore: 22
    SendSyncRequest1: 46
    SendSyncRequest2: 47
    SendSyncRequest3: 48
    SendSyncRequest4: 49
    SendSyncRequest: 50
    SetThreadPriority: 12
    SetTimer: 27
    SignalEvent: 24
    SleepThread: 10
    UnmapMemoryBlock: 32
    WaitSynchronization1: 36
    WaitSynchronizationN: 37

  ServiceAccessControl:
   - cfg:u
   - fs:USER
   - gsp::Gpu
   - hid:USER
   - ndm:u
   - pxi:dev
   - APT:U
   - ac:u
   - act:u
   - am:net
   - boss:U
   - cam:u
   - cecd:u
   - csnd:SND
   - frd:u
   - http:C
   - ir:USER
   - ir:u
   - ir:rst
   - ldr:ro
   - mic:u
   - news:u
   - nfc:u
   - nim:aoc
   - nwm::UDS
   - ptm:u
   - qtm:u
   - soc:U
   - ssl:C
   - y2r:u

SystemControlInfo:
  SaveDataSize: 512K
  RemasterVersion: 0
  StackSize: 0x40000
  Dependency: 
    ac: 0x0004013000002402
    act: 0x0004013000003802
    am: 0x0004013000001502
    boss: 0x0004013000003402
    camera: 0x0004013000001602
    cecd: 0x0004013000002602
    cfg: 0x0004013000001702
    codec: 0x0004013000001802
    csnd: 0x0004013000002702
    dlp: 0x0004013000002802
    dsp: 0x0004013000001a02
    friends: 0x0004013000003202
    gpio: 0x0004013000001b02
    gsp: 0x0004013000001c02
    hid: 0x0004013000001d02
    http: 0x0004013000002902
    i2c: 0x0004013000001e02
    ir: 0x0004013000003302
    mcu: 0x0004013000001f02
    mic: 0x0004013000002002
    ndm: 0x0004013000002b02
    news: 0x0004013000003502
    nfc: 0x0004013000004002
    nim: 0x0004013000002c02
    nwm: 0x0004013000002d02
    pdn: 0x0004013000002102
    ps: 0x0004013000003102
    ptm: 0x0004013000002202
    qtm: 0x0004013020004202
    ro: 0x0004013000003702
    socket: 0x0004013000002e02
    spi: 0x0004013000002302
    ssl: 0x0004013000002f02
EOF

echo "✅ RSF configuration created"

# Prepare RomFS with English translations
echo ""
echo "📋 Preparing English RomFS..."
if [ -d "$ROMFS_ENG_DIR" ]; then
    echo "✅ Using precision-injected RTZ files from $ROMFS_ENG_DIR"
    cp -r "$ROMFS_ENG_DIR" "$BUILD_DIR/romfs"
else
    echo "❌ English RTZ directory not found: $ROMFS_ENG_DIR"
    exit 1
fi

# Build the ROM
echo ""
echo "🔨 BUILDING ENGLISH ROM..."
echo "ROM Name: $OUTPUT_ROM"
echo "Build Directory: $BUILD_DIR"
echo ""

# Build command
echo "⚙️  Running makerom..."
cd "$BUILD_DIR"

$MAKEROM_CMD -f cci \
    -o "../$OUTPUT_ROM" \
    -rsf "$RSF_FILE" \
    -code code.bin \
    -exheader exheader.bin \
    -romfs romfs \
    -ver 0

cd ..

# Check if build succeeded
if [ -f "$OUTPUT_ROM" ]; then
    echo ""
    echo "✅ ROM BUILD SUCCESSFUL!"
    echo "=================================="
    echo "📦 Output: $OUTPUT_ROM"
    echo "📊 Size: $(ls -lh "$OUTPUT_ROM" | awk '{print $5}')"
    echo ""
    echo "🎮 NEXT STEPS:"
    echo "1. Test in Citra emulator"
    echo "2. Look for English text in tutorials:"
    echo "   - 'Attack on Rear Guard' instead of 'リアガードにアタック'"
    echo "   - 'Card as Damage' instead of 'ダメージとしてカード'"
    echo "   - 'VANGUARD' instead of 'ヴァンガード'"
    echo ""
    echo "🏆 Congratulations! You've created the first English CF Vanguard ROM!"
else
    echo ""
    echo "❌ ROM BUILD FAILED"
    echo "Check the error messages above for details"
fi