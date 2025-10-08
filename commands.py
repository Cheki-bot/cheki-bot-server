import argparse

from scripts import create_vectordb, download_data, fill_database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear base de datos vectorial")
    parser.add_argument("--create", action="store_true", help="Crear la base de datos vectorial")
    parser.add_argument("--download", action="store_true", help="Descargar datos desde Google Drive")
    parser.add_argument("--fill", action="store_true", help="Rellenar la base de datos con datos")

    args = parser.parse_args()

    if args.create:
        vectordb = create_vectordb.create_vectordb()
        print("Base de datos vectorial creada exitosamente.")
    elif args.download:
        download_data.download_data()
        print("Datos descargados exitosamente.")
    elif args.fill:
        fill_database.fill_database()
        print("Base de datos rellena exitosamente.")
    else:
        print("Por favor, usa --create para crear la base de datos vectorial, --download para descargar datos o --fill para rellenar la base de datos.")
