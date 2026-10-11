{{ config(materialized='table') }}

SELECT
    id_client,
    ville,
    pays,
    date_inscription
FROM {{ source('silver', 'silver_clients') }}
WHERE id_client IS NOT NULL