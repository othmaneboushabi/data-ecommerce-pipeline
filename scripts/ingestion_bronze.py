import os
from datetime import datetime
from minio import Minio
from minio.error import S3Error

# ==========================================
# 1. CONFIGURATION DU CLIENT MINIO
# ==========================================
# On se connecte à notre conteneur Docker MinIO local
client = Minio(
    "localhost:9000",          # L'adresse de l'API MinIO définie dans le docker-compose
    access_key="admin",        # Le nom d'utilisateur (MINIO_ROOT_USER)
    secret_key="password123",  # Le mot de passe (MINIO_ROOT_PASSWORD)
    secure=False               # False car on est en local (HTTP et non HTTPS)
)

bucket_name = "bronze"         # Le nom de notre couche de données brutes

def main():
    try:
        # ==========================================
        # 2. CRÉATION DU BUCKET (S'IL N'EXISTE PAS)
        # ==========================================
        # On vérifie si le bucket "bronze" existe déjà
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' créé avec succès.")
        else:
            print(f"ℹ️ Le bucket '{bucket_name}' existe déjà.")

        # ==========================================
        # 3. PRÉPARATION DE L'UPLOAD
        # ==========================================
        # Liste des fichiers à charger depuis le dossier local "data"
        fichiers_a_charger = [
            "users.csv", 
            "products.csv", 
            "inventory_items.csv", 
            "orders.csv", 
            "order_items.csv"
        ]
        
        # On génère la date du jour (ex: 2026-10-10) pour la traçabilité
        # En Data Engineering, on partitionne souvent les données par date de chargement
        date_chargement = datetime.now().strftime("%Y-%m-%d")

        # ==========================================
        # 4. BOUCLE D'INGESTION DES FICHIERS
        # ==========================================
        for fichier in fichiers_a_charger:
            chemin_local = f"../data/{fichier}" # Chemin vers le fichier sur votre PC
            
            # On vérifie que le fichier CSV est bien présent dans le dossier data
            if os.path.exists(chemin_local):
                
                # On définit le nom et l'emplacement du fichier dans MinIO
                # Ex: ecommerce/2026-10-10/users.csv
                chemin_minio = f"ecommerce/{date_chargement}/{fichier}"
                
                # La commande fput_object envoie le fichier vers MinIO
                client.fput_object(
                    bucket_name, 
                    chemin_minio, 
                    chemin_local
                )
                print(f"🚀 Succès : {fichier} a été chargé dans {chemin_minio}")
            else:
                print(f"❌ Erreur : Le fichier {chemin_local} est introuvable.")

    except S3Error as err:
        print(f"Erreur MinIO: {err}")
    except Exception as e:
        print(f"Erreur inattendue: {e}")

# Point d'entrée standard en Python
if __name__ == "__main__":
    # Pour exécuter ce script depuis VS Code, assurez-vous d'être 
    # dans le dossier racine du projet ou dans le dossier scripts.
    main()