import shutil
from pathlib import Path

with open("jclasses-sorted.txt") as f:
    lines = {l.strip() for l in f.readlines() if l.strip()}  # noqa: E741

for l in lines:  # noqa: E741
    path, file, clz = l.rsplit("/", 2)
    p = Path(path)
    if (p / file / "__init__.pyi").is_file():
        with (p / file / "__init__.pyi").open("a") as f:
            f.writelines(
                [
                    f"class {clz}[**Ts](jep._PyJObject): ...\n",
                    "\n"
                ]
            )
    elif (p.with_suffix(".pyi")).is_file():
        _ = shutil.move(p.with_suffix(".pyi"), p.with_suffix(".tmp"))
        p.mkdir(parents=True, exist_ok=True)
        _ = shutil.move(p.with_suffix(".tmp"), p / "__init__.pyi")
    else:
        p.mkdir(parents=True, exist_ok=True)
        if not (p / f"{file}.pyi").is_file():
            _ = (p / f"{file}.pyi").write_text("# pyright: reportPrivateUsage = none\n\nimport jep\n\n")
        with (p / f"{file}.pyi").open("a") as f:
            f.writelines(
                [
                    f"class {clz}[**Ts](jep._PyJObject): ...\n",
                    "\n"
                ]
            )