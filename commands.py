import argparse

from scripts import create_vectordb, download_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear base de datos vectorial")
    parser.add_argument(
        "--create", action="store_true", help="Crear la base de datos vectorial"
    )
    parser.add_argument(
        "--download", action="store_true", help="Descargar datos desde Google Drive"
    )

    args = parser.parse_args()

    if args.create:
        vectordb = create_vectordb.create_vectordb()
        print("Base de datos vectorial creada exitosamente.")
    elif args.download:
        download_data.download_data()
        print("Datos descargados exitosamente.")
    else:
        print(
            "Por favor, usa --create para crear la base de datos vectorial o --download para descargar datos."
        )
