{{ config(materialized='table') }}

SELECT
    id_stock,
    id_produit,
    date_ajout,
    date_vente,
    -- Création d'une règle métier (Logique Gold)
    CASE 
        WHEN date_vente IS NULL THEN 'Disponible'
        ELSE 'Vendu'
    END AS statut_stock
FROM {{ source('silver', 'silver_stocks') }}