import argparse
from label_signals import label_signals


def main():
    parser = argparse.ArgumentParser(
        description="Маркировка сигналов в Nero.csv по strong-фракталам"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="Nero.csv",
        help="Путь к входному CSV (по умолчанию Nero.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="Nero_labeled.csv",
        help="Путь к выходному CSV (по умолчанию Nero_labeled.csv)",
    )

    args = parser.parse_args()

    print(f"Читаю: {args.input}")
    print(f"Сохраняю в: {args.output}")

    label_signals(args.input, args.output)


if __name__ == "__main__":
    main()
