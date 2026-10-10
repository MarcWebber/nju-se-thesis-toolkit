"""Create vector fixtures with contrasting aspect ratios, not research results."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def main():
    destination = Path(__file__).with_name("assets")
    destination.mkdir(exist_ok=True)
    plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})
    for name, size in (("wide", (6, 1.8)), ("tall", (1.8, 5))):
        if any((destination / (name + "." + ext)).exists() for ext in ("svg", "pdf")):
            raise ValueError("Fixture exists: " + name)
        fig, ax = plt.subplots(figsize=size)
        ax.set(xlim=(0, 1), ylim=(0, 1))
        ax.axis("off")
        ax.add_patch(Rectangle((0.04, 0.04), 0.92, 0.92, fill=False, linewidth=1.5))
        ax.text(0.5, 0.5, name.title() + " sample", ha="center", va="center", fontsize=11)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        for extension in ("svg", "pdf"):
            fig.savefig(destination / (name + "." + extension))
        plt.close(fig)


if __name__ == "__main__":
    main()
