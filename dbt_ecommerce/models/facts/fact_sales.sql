{{ config(materialized='table') }}

SELECT
    d.id_detail,
    c.id_commande,
    c.id_client,
    d.id_produit,
    c.date_commande,
    c.statut,
    d.prix_unitaire AS montant_vente
FROM {{ source('silver', 'silver_details_commandes') }} d
JOIN {{ source('silver', 'silver_commandes') }} c
    ON d.id_commande = c.id_commande