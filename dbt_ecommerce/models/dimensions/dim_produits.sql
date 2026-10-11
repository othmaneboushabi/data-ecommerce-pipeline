{{ config(materialized='table') }}

SELECT
    id_produit,
    nom_produit,
    categorie,
    prix AS prix_unitaire_catalogue,
    cout_achat
FROM {{ source('silver', 'silver_produits') }}
WHERE id_produit IS NOT NULL