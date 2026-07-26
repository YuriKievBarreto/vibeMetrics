from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, inspect
from sqlmodel import SQLModel
import asyncio
import os
from dotenv import load_dotenv
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL


def get_db_structure(sync_conn):
    """Executa a inspeção do DB de forma SÍNCRONA."""

    inspector = inspect(sync_conn)

    table_names = inspector.get_table_names()
    db_structure = {}

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]

    return db_structure


async_engine = create_async_engine(DATABASE_URL)


async def init_db():

    import app.models.all_models

    try:
        async with async_engine.begin() as conn:
            print("iniciando tentativa de conexao com o banco de dados")
            print("verificando e criando tabelas...")
            await conn.run_sync(SQLModel.metadata.create_all)
            print("conexao bem sucedida")

            db_structure = await conn.run_sync(get_db_structure)

            print("\n--- ESTRUTURA ATUAL DO BANCO DE DADOS ---")

            table_count = 0
            for table_name, column_names in db_structure.items():
                print(f"[{table_name.upper()}] ({len(column_names)} colunas):")
                print(f"  -> Colunas: {', '.join(column_names)}")
                table_count += 1

            print("-----------------------------------------")
            print(f"✅ Conexao bem sucedida e {table_count} tabelas verificadas.")

            print("Conexao bem sucedida e tabelas verificadas/criadas.")

    except Exception as e:
        print("erro de conexao: ", e)
        raise e


def get_session() -> AsyncSession:
    return AsyncSession(async_engine)
