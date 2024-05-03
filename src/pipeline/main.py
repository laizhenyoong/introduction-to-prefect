#!/usr/bin/env python3

import httpx
from prefect import flow, get_run_logger, task
import psycopg2

@task 
def retrieve_from_api(
    base_url,
    path,
    secure
):
    logger = get_run_logger()
    if secure:
        url = f"https://{base_url}{path}"
    else: 
        url = f"http://{base_url}{path}"
    response = httpx.get(url)
    response.raise_for_status()
    inventory_stats = response.json()
    logger.info(inventory_stats)
    return inventory_stats

@task 
def clean_state_data(inventory_stats):
    return {
        "sold": inventory_stats.get("sold", 0) + inventory_stats.get("Sold", 0),
        "available": inventory_stats.get("available", 0) + inventory_stats.get("Available", 0),
        "unavailable": inventory_stats.get("unavailable", 0) + inventory_stats.get("Unavailable", 0),
        "pending": inventory_stats.get("pending", 0) + inventory_stats.get("Pending", 0)
    }

@flow 
def collect_petstore_inventory(
    base_url: str="petstore.swagger.io",
    path: str="/v2/store/inventory",
    secure: bool=True,
    db_host: str="localhost",
    db_user: str="root",
    db_pass: str="root",
    db_name: str="petstore"
):
    inventory_stats = retrieve_from_api(base_url, path, secure)
    inventory_stats = clean_state_data(inventory_stats)
    insert_to_db(inventory_stats, db_host, db_user, db_pass, db_name)

@task 
def insert_to_db(
    inventory_stats: dict,
    db_host: str,
    db_user: str,
    db_pass: str,
    db_name: str
):
    with psycopg2.connect(
        user=db_user, password=db_pass, dbname=db_name, host=db_host
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
               """ insert into inventory_history (
                        fetch_timestamp, 
                        sold, 
                        pending, 
                        available,
                        unavailable
                     ) values (
                        now(), 
                        %(sold)s, 
                        %(pending)s, 
                        %(available)s,
                        %(unavailable)s
                     )""", inventory_stats) 

def main():
    collect_petstore_inventory.serve("petstore-collection-deployment")


if __name__ == "__main__":
    main()
