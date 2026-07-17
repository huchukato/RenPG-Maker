import argparse
import os
import sys
from .generator import RenpyProjectGenerator


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Converte un progetto RPG Maker MV/MZ in un visual novel Ren'Py."
    )
    parser.add_argument("input", help="Cartella www/data del gioco RPG Maker")
    parser.add_argument("output", help="Cartella di output per il progetto Ren'Py")
    parser.add_argument("--template-dir", default=None, help="Progetto Ren'Py vuoto da cui copiare screens.rpy, gui.rpy e asset GUI")
    parser.add_argument("--start-map", type=int, default=None, help="ID mappa iniziale (ignora System.json)")
    parser.add_argument("--include-events", nargs="+", type=int, default=None, help="Solo determinati eventi (per test)")
    parser.add_argument("--no-dialogue-prefix", action="store_true", help="Non tentare di estrarre speaker dal prefisso nelle variabili")
    args = parser.parse_args(argv)

    data_dir = args.input
    if not os.path.isdir(data_dir):
        print(f"Errore: cartella dati non trovata: {data_dir}", file=sys.stderr)
        return 1

    options = {
        "convert_dialogue_prefix": not args.no_dialogue_prefix,
        "start_map": args.start_map,
        "include_events": args.include_events,
    }

    generator = RenpyProjectGenerator(data_dir, args.output, options, template_dir=args.template_dir)
    generator.generate()
    print(f"Progetto Ren'Py generato in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
