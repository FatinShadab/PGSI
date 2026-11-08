# Replication supplement

Material moved out of the manuscript for space (approved PAGE BUDGET items 11, 13, 14 and 15). The paper points readers to "the replication package", so this folder must be added to the GitHub repository at `replication_supplement/`.

| File | Content | Note |
|---|---|---|
| `algorithms_1_2.tex` | Pseudocode for GreenScore computation and the bootstrap/Friedman procedure | Moved unchanged. **Fix before publishing:** "algorithm" means execution method here but workload in the paper, `G[j]` sums over workloads rather than the E, C and T components of Eq. 2, and "resample algorithm columns" contradicts resampling workloads. Needs `\usepackage{algorithm2e}` |
| `table_windows_fallback.tex` | Windows fallback GreenScore table | Moved unchanged |
| `figures_4_5_float_source.tex` | LaTeX floats for the two moved figures | Moved unchanged |
| `fig04_greenscore_components.pdf` | Component figure | **Linux bars are clipped.** Regenerate before publishing |
| `fig05_methodology_flow.pdf` | Measurement pipeline figure | Contains a visible `x86\_64` artifact. States "Wall time + TDP lookup" for the Windows path |
