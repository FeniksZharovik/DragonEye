import os
import pandas as pd

def convert_csv_to_excel():
    base_dir = r"E:\DragonEye\dataset"

    csv_files = [
        ("features.csv", "features.xlsx"),
        ("graded_features.csv", "graded_features.xlsx")
    ]

    print("=== Konversi CSV ke Excel Dimulai ===")

    for csv_name, excel_name in csv_files:
        csv_path = os.path.join(base_dir, csv_name)
        excel_path = os.path.join(base_dir, excel_name)

        if not os.path.exists(csv_path):
            print(f"[SKIP] File CSV tidak ditemukan: {csv_path}")
            continue

        print(f"Memuat file: {csv_name}")

        # Baca CSV
        df = pd.read_csv(csv_path)

        # Tulis Excel dengan writer xlsxwriter
        with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]

            # --- Format Header ---
            header_fmt = workbook.add_format({
                "bold": True,
                "bg_color": "#D9E1F2",
                "border": 1
            })

            # Terapkan format header
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)

            # --- Format isi tabel ---
            cell_fmt = workbook.add_format({"border": 1})

            # Hitung auto width
            for i, col in enumerate(df.columns):
                # Cari panjang maksimum (header vs isi)
                column_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2  # padding
                worksheet.set_column(i, i, column_len, cell_fmt)

        print(f"Berhasil menulis file Excel rapi: {excel_path}")

    print("=== Konversi Selesai ===")


if __name__ == "__main__":
    convert_csv_to_excel()
