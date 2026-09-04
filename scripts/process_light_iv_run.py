from pathlib import Path

from toposcript.processing.light_iv_postprocess import process_light_iv_run


# === CONFIG ===
input_folder = r"C:\Users\aacha097\source\repos\AyaAchaby\TopoScript\data\light_iv\raw\20260619_150342_C5776-X20Y10"
cell_area_cm2 = 0.054

run_name = Path(input_folder).name



processed_folder = (
    Path("data")
    / "light_iv"
    / "processed"
    / run_name
)

output_csv = processed_folder / "light_iv_summary.csv"


process_light_iv_run(
    input_folder=input_folder,
    output_csv=output_csv,
    cell_area_cm2=cell_area_cm2,
    make_plots=True,
    processed_folder=output_csv.parent,
)