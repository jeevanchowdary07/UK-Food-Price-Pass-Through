from pathlib import Path
import matplotlib.pyplot as plt


def line_by_category(df, variable: str, title: str, ylabel: str, outpath: Path) -> None:
    plt.figure(figsize=(10, 5.5))
    for category, g in df.groupby("category"):
        plt.plot(g["month"], g[variable], label=category)
    plt.xlabel("Month")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath, dpi=200)
    plt.close()
