
import io
import pandas as pd
from minio import Minio
from sqlalchemy import create_engine, text
from datetime import datetime

# ==========================================
# 1. CONFIGURATION DES CONNEXIONS
# ==========================================

# Connexion à MinIO (Couche Bronze)
minio_client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

bucket_name = "bronze"
date_chargement = datetime.now().strftime("%Y-%m-%d")

# Connexion à PostgreSQL (Couche Silver)
db_url = "postgresql+psycopg2://postgres:postgres@postgres:5432/ecommerce_db"

engine = create_engine(db_url)


# ==========================================
# 2. LECTURE DES CSV DEPUIS MINIO
# ==========================================

def lire_csv_depuis_minio(nom_fichier):
    """Télécharge un CSV depuis MinIO et le charge dans Pandas."""

    chemin_minio = f"ecommerce/{date_chargement}/{nom_fichier}"
    reponse = None

    try:
        reponse = minio_client.get_object(
            bucket_name,
            chemin_minio
        )

        contenu = reponse.read()
        df = pd.read_csv(io.BytesIO(contenu))

        print(
            f"📥 Lecture réussie depuis MinIO : "
            f"{nom_fichier} ({len(df)} lignes)"
        )

        return df

    except Exception as e:
        print(f"❌ Erreur lors de la lecture de {nom_fichier} : {e}")
        return None

    finally:
        if reponse is not None:
            reponse.close()
            reponse.release_conn()


# ==========================================
# 3. FONCTION DE NETTOYAGE DES DATES
# ==========================================

def convertir_date(colonne):
    """
    Convertit les dates, même si les formats varient
    ou si les valeurs contiennent UTC.

    Les dates invalides deviennent NaT.
    Le fuseau horaire est retiré pour PostgreSQL.
    """

    dates = pd.to_datetime(
        colonne,
        format="mixed",
        utc=True,
        errors="coerce"
    )

    return dates.dt.tz_localize(None)


# ==========================================
# 4. TRAITEMENT DE LA COUCHE SILVER
# ==========================================

def main():

    print("🚀 Début du traitement de la Couche Silver...\n")

    # ------------------------------------------
    # A. CLIENTS
    # ------------------------------------------

    df_users = lire_csv_depuis_minio("users.csv")

    if df_users is not None:

        colonnes = [
            "id", "city", "country", "created_at"
        ]

        df_clients = df_users[colonnes].copy()

        df_clients.rename(
            columns={
                "id": "id_client",
                "city": "ville",
                "country": "pays",
                "created_at": "date_inscription"
            },
            inplace=True
        )

        df_clients["date_inscription"] = convertir_date(
            df_clients["date_inscription"]
        )

        nb_dates_invalides = df_clients["date_inscription"].isna().sum()
        print(f"⚠️ Dates d'inscription manquantes/invalides : {nb_dates_invalides}")

        df_clients.to_sql(
            "silver_clients",
            engine,
            if_exists="replace",
            index=False,
            chunksize=10000
        )

        print("✅ Table 'silver_clients' chargée dans PostgreSQL.\n")

    # ------------------------------------------
    # B. PRODUITS
    # ------------------------------------------

    df_products = lire_csv_depuis_minio("products.csv")

    if df_products is not None:

        colonnes = [
            "id", "name", "category", "retail_price", "cost"
        ]

        df_produits = df_products[colonnes].copy()

        df_produits.rename(
            columns={
                "id": "id_produit",
                "name": "nom_produit",
                "category": "categorie",
                "retail_price": "prix",
                "cost": "cout_achat"
            },
            inplace=True
        )

        df_produits.to_sql(
            "silver_produits",
            engine,
            if_exists="replace",
            index=False,
            chunksize=10000
        )

        print("✅ Table 'silver_produits' chargée dans PostgreSQL.\n")

    # ------------------------------------------
    # C. COMMANDES
    # ------------------------------------------

    df_orders = lire_csv_depuis_minio("orders.csv")

    if df_orders is not None:

        colonnes = [
            "order_id", "user_id", "status", "created_at"
        ]

        df_commandes = df_orders[colonnes].copy()

        df_commandes.rename(
            columns={
                "order_id": "id_commande",
                "user_id": "id_client",
                "status": "statut",
                "created_at": "date_commande"
            },
            inplace=True
        )

        # Correction du problème de format des dates
        df_commandes["date_commande"] = convertir_date(
            df_commandes["date_commande"]
        )

        nb_dates_invalides = df_commandes["date_commande"].isna().sum()
        print(f"⚠️ Dates de commande manquantes/invalides : {nb_dates_invalides}")

        # Traduction des statuts en français
        traduction_statuts = {
            "Shipped": "Expédiée",
            "Complete": "Terminée",
            "Processing": "En cours",
            "Cancelled": "Annulée",
            "Returned": "Retournée"
        }

        df_commandes["statut"] = (
            df_commandes["statut"]
            .replace(traduction_statuts)
        )

        df_commandes.to_sql(
            "silver_commandes",
            engine,
            if_exists="replace",
            index=False,
            chunksize=10000
        )

        print("✅ Table 'silver_commandes' chargée dans PostgreSQL.\n")

    # ------------------------------------------
    # D. DÉTAILS DES COMMANDES
    # ------------------------------------------

    df_order_items = lire_csv_depuis_minio("order_items.csv")

    if df_order_items is not None:

        colonnes = [
            "id", "order_id", "product_id", "sale_price"
        ]

        df_details = df_order_items[colonnes].copy()

        df_details.rename(
            columns={
                "id": "id_detail",
                "order_id": "id_commande",
                "product_id": "id_produit",
                "sale_price": "prix_unitaire"
            },
            inplace=True
        )

        df_details.to_sql(
            "silver_details_commandes",
            engine,
            if_exists="replace",
            index=False,
            chunksize=10000
        )

        print(
            "✅ Table 'silver_details_commandes' "
            "chargée dans PostgreSQL.\n"
        )

    # ------------------------------------------
    # E. STOCKS / INVENTAIRE
    # ------------------------------------------

    df_inventory = lire_csv_depuis_minio("inventory_items.csv")

    if df_inventory is not None:

        colonnes = [
            "id", "product_id", "created_at", "sold_at"
        ]

        df_stocks = df_inventory[colonnes].copy()

        df_stocks.rename(
            columns={
                "id": "id_stock",
                "product_id": "id_produit",
                "created_at": "date_ajout",
                "sold_at": "date_vente"
            },
            inplace=True
        )

        # Conversion robuste des deux colonnes de dates
        df_stocks["date_ajout"] = convertir_date(
            df_stocks["date_ajout"]
        )

        df_stocks["date_vente"] = convertir_date(
            df_stocks["date_vente"]
        )

        print(
            "⚠️ Dates d'ajout manquantes/invalides : "
            f"{df_stocks['date_ajout'].isna().sum()}"
        )

        print(
            "⚠️ Dates de vente manquantes/invalides : "
            f"{df_stocks['date_vente'].isna().sum()}"
        )

        df_stocks.to_sql(
            "silver_stocks",
            engine,
            if_exists="replace",
            index=False,
            chunksize=10000
        )

        print("✅ Table 'silver_stocks' chargée dans PostgreSQL.\n")

    # ------------------------------------------
    # 5. VÉRIFICATION DES TABLES
    # ------------------------------------------

    print("🔎 Vérification des tables Silver...\n")

    tables = [
        "silver_clients",
        "silver_produits",
        "silver_commandes",
        "silver_details_commandes",
        "silver_stocks"
    ]

    with engine.connect() as connexion:

        for table in tables:

            resultat = connexion.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            )

            nombre_lignes = resultat.scalar()

            print(f"📊 {table} : {nombre_lignes} lignes")

    print("\n🎉 Traitement de la Couche Silver terminé !")


# ==========================================
# 6. POINT D'ENTRÉE DU SCRIPT
# ==========================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur pendant le traitement Silver : {e}")
        raise
    finally:
        engine.dispose()
