from pipelines.scripts.private_endpoint.purview_private_endpoint_manager import PurviewPrivateEndpointManager
from pipelines.scripts.private_endpoint.storage_private_endpoint_manager import StoragePrivateEndpointManager
from pipelines.scripts.private_endpoint.event_hub_private_endpoint_manager import EventHubPrivateEndpointManager
from pipelines.scripts.util import Util
import argparse
import logging


logging.basicConfig(level=logging.INFO)


ENDPOINTS_TO_EXCLUDE = {}


def approve_private_endpoints():
    """
        Approve all Purview private endpoints
    """
    purview_private_endpoint_manager = PurviewPrivateEndpointManager()
    purview_private_endpoint_manager.approve_all(
        "pins-rg-datamgmt",
        "pins-pview",
        ENDPOINTS_TO_EXCLUDE
    )
    storage_private_endpoint_manager = StoragePrivateEndpointManager()
    storage_accounts = Util.get_purview_managed_storage_account_names()
    for storage_account in storage_accounts:
        storage_private_endpoint_manager.approve_all(
            "pins-rg-datamgmt-purview-managed",
            storage_account,
            ENDPOINTS_TO_EXCLUDE
        )
    event_hub_private_endpoint_manager = EventHubPrivateEndpointManager()
    event_hubs = Util.get_purview_managed_event_hub_namespace_names()
    for event_hub in event_hubs:
        event_hub_private_endpoint_manager.approve_all(
            "pins-rg-datamgmt-purview-managed",
            event_hub,
            ENDPOINTS_TO_EXCLUDE
        )


if __name__ == "__main__":
    # Load command line arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args = parser.parse_args()
    approve_private_endpoints()
