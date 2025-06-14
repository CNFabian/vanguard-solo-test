# export_section_sizes.py
import idautils
import idaapi
import idc
import ida_kernwin

def export_section_sizes():
    sections = []
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        name = idc.get_segm_name(seg_ea)
        start = seg.start_ea
        end   = seg.end_ea
        size  = end - start
        sections.append((name, start, end, size))

    # Demande de chemin
    out_path = ida_kernwin.ask_file(1, "*.csv", "Enregistrer la taille des sections sous…")
    if not out_path:
        print("Export annulé.")
        return

    # Écriture CSV
    with open(out_path, 'w', newline='') as f:
        f.write("Section,StartEA,EndEA,SizeBytes\n")
        for name, start, end, size in sections:
            f.write(f"{name},0x{start:08X},0x{end:08X},{size}\n")

    print(f"✅ Exporté {len(sections)} sections dans : {out_path}")

if __name__ == "__main__":
    export_section_sizes()
