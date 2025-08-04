import argparse

from scripts import create_vectordb

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear base de datos vectorial")
    parser.add_argument(
        "--create", action="store_true", help="Crear la base de datos vectorial"
    )

    args = parser.parse_args()

    if args.create:
        vectordb = create_vectordb.create_vectordb()
        print("Base de datos vectorial creada exitosamente.")
    else:
        print("Por favor, usa --create para crear la base de datos vectorial.")
