#!/usr/bin/env python3

import httpx
from prefect import flow, get_run_logger

@flow 
def collect_petstore_inventory():
    logger = get_run_logger()
    url = "https://petstore.swagger.io/v2/store/inventory"
    response = httpx.get(url)
    response.raise_for_status()
    inventory_stats = response.json()
    logger.info(inventory_stats)

def main():
    collect_petstore_inventory.serve("petstore-collection-deployment")


if __name__ == "__main__":
    main()
