# export_pointers_v3.py — export de la table de pointeurs vers CSV pour IDA 9+
import idautils
import idaapi
import ida_segment
import idc
import ida_kernwin

# === CONFIGURATION ===
START = 0x00949720
END   = 0x00B51CE0

# 1) Collecte toutes les occurrences DWORD LE pointant dans [START..END)
pointers = []
for seg_start in idautils.Segments():
    seg_obj = idaapi.getseg(seg_start)
    # si tu veux ignorer les segments code, décommente la ligne suivante :
    # if seg_obj and (seg_obj.type & ida_segment.SEG_CODE): continue
    seg_end = idc.get_segm_end(seg_start)
    ea = seg_start
    while ea < seg_end:
        val = idaapi.get_wide_dword(ea)
        if START <= val < END:
            pointers.append((ea, val))
        ea += 4

count = len(pointers)
print(f"🔍 {count} pointeur(s) trouvé(s) dans la plage 0x{START:08X}–0x{END:08X}")

# 2) Tri par valeur de cible
pointers_sorted = sorted(pointers, key=lambda x: x[1])

# 3) Préparation des tailles
unique_targets = sorted({tgt for _, tgt in pointers_sorted})
target_index   = {tgt: i for i, tgt in enumerate(unique_targets)}

table = []
for ptr_ea, tgt in pointers_sorted:
    idx      = target_index[tgt]
    next_tgt = unique_targets[idx + 1] if idx + 1 < len(unique_targets) else END
    size     = next_tgt - tgt
    table.append((ptr_ea, tgt, size))

# 4) Boîte de dialogue de sauvegarde
out_path = ida_kernwin.ask_file(1, "*.csv", "Enregistrer la table de pointeurs sous…")
if not out_path:
    print("❌ Export annulé par l'utilisateur.")
else:
    try:
        with open(out_path, 'w', newline='') as f:
            f.write("offset;cible;taille\n")
            for ptr_ea, tgt, size in table:
                f.write(f"{ptr_ea:08X};{tgt:08X};{size}\n")
        print(f"✅ Export réussi : {count} pointeur(s) écrits dans\n    {out_path}")
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture du fichier : {e}")

print("=== Script terminé ===")
