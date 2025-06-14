#!/usr/bin/env python3
import csv
import struct
import re
import json
import requests
import logging
from pathlib import Path

# --- Config logs ---
logging.basicConfig(
    level=logging.INFO,
    format="📝 [%(levelname)s] %(message)s"
)

INPUT_BIN          = 'code.bin'
OUTPUT_BIN         = 'code_patched.bin'
POINTERS_CSV       = 'sorted_pointers_list.csv'
ARGOS_ENDPOINT     = 'http://localhost:5001/translate'

SEPARATOR_PATTERN      = re.compile(rb'(?:\x00\x00|\xff\xff)+')
KANJI_KANA_TAG_PATTERN = re.compile(r"<\|(.+?)\|.+?\|>")
BALISE_PATTERN         = re.compile(r"\{\$[0-9A-Fa-f]{1,6}\}|\{\$\}")  
JAPANESE_CHAR_PATTERN  = re.compile(r'[\u3000-\u30FF\u4E00-\u9FFF]+')
# On remplace désormais les placeholders de la forme @AB (2 chars, A–Z0–9)
PLACEHOLDER_PATTERN    = re.compile(r"@([A-Z0-9]{2})")


def read_pointers(csv_file):
    pointers = []
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            # on retire le segment de bank si nécessaire
            source = int(row['cible'], 16) - 0x00100000
            size   = int(row['taille'])
            pointers.append((source, size))
    logging.info(f"🔎 Loaded {len(pointers)} pointers from CSV.")
    return pointers


def extract_string(data, offset):
    end = offset
    while end < len(data) - 1:
        if SEPARATOR_PATTERN.match(data[end:end+4]):
            break
        end += 2
    return data[offset:end], end


def decode_utf16le(data):
    return data.decode('utf-16le', errors='ignore')


def encode_utf16le(text):
    return text.encode('utf-16le')


def translate_text(text):
    original_text = text
    text = text.replace('\n', ' ')

    # Sauvegarde des placeholders @AB → __AT_AB__
    at_placeholders = PLACEHOLDER_PATTERN.findall(text)
    at_map = {f"__AT_{code}__": f"@{code}" for code in at_placeholders}
    for placeholder, original in at_map.items():
        text = text.replace(original, placeholder)

    # Balises <|kanji|kana|> → kanji
    text = KANJI_KANA_TAG_PATTERN.sub(r"\1", text)

    # Suppression des balises {$123456} et {$}
    text = BALISE_PATTERN.sub('', text)

    # Skip si pas de japonais
    if not JAPANESE_CHAR_PATTERN.search(text):
        logging.info("⏭️  No Japanese detected. Skipping translation.")
        return original_text

    try:
        response = requests.post(ARGOS_ENDPOINT, json={
            "q": text,
            "source": "ja",
            "target": "en",
            "format": "text"})
        response.raise_for_status()
        translated = response.json().get("translatedText", text)
        logging.info(f"🌐 Translated: {original_text.strip()} => {translated.strip()}")
    except Exception as e:
        logging.error(f"❌ Translation failed: {e}")
        return original_text

    # Remise en place des placeholders __AT_AB__ → @AB
    for placeholder, original in at_map.items():
        translated = translated.replace(placeholder, original)

    return translated


def patch_binary(input_file, output_file, pointers):
    with open(input_file, 'rb') as f:
        data = bytearray(f.read())

    total = len(pointers)
    for idx, (offset, size) in enumerate(pointers, 1):
        logging.info(f"\n[{idx}/{total}] 🔧 Processing string at offset {hex(offset)}")

        original_bytes, end = extract_string(data, offset)
        original_text = decode_utf16le(original_bytes)
        logging.info(f"📜 Original: {original_text.strip()}")

        translated_text = translate_text(original_text)
        translated_bytes = encode_utf16le(translated_text)

        sep_match = SEPARATOR_PATTERN.match(data[end:])
        sep_bytes = sep_match.group(0) if sep_match else b''

        # Ajuster à la taille d'origine
        if len(translated_bytes) > len(original_bytes):
            translated_bytes = translated_bytes[:len(original_bytes)]
            logging.warning("⚠️  Translation truncated to fit original size.")
        elif len(translated_bytes) < len(original_bytes):
            pad_units = (len(original_bytes) - len(translated_bytes)) // 2
            translated_bytes += b'\x20\x00' * pad_units
            logging.info("🧵 Padded translation to match original size.")

        # Écrire traduction + séparation
        data[offset:offset+len(original_bytes)] = translated_bytes
        if sep_bytes:
            data[offset+len(original_bytes):offset+len(original_bytes)+len(sep_bytes)] = sep_bytes

        # Indice de progression détaillé
        logging.info(f"✅ Completed [{idx}/{total}]")

    with open(output_file, 'wb') as f:
        f.write(data)
    logging.info(f"\n🎯 Patch completed! Output written to {output_file}")


if __name__ == '__main__':
    logging.info("🚀 Starting binary patcher with full translation...")
    pointers = read_pointers(POINTERS_CSV)
    patch_binary(INPUT_BIN, OUTPUT_BIN, pointers)
