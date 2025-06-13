import subprocess
from typing import List, Dict, Any
import json
import os
import logging


class Util:
    """
        Class that has useful utility functions
    """
    @classmethod
    def run_az_cli_command(cls, args: List[str]):
        """
            Run an az cli command. Raises a `RuntimeException` if something goes wrong
        """
        logging.info(f"Running command {' '.join(args)}")
        try:
            return subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            exception = e
        raise RuntimeError(f"Exception raised when running the above command: {exception.output.decode('utf-8')}")

    @classmethod
    def get_current_subscription_details(cls) -> Dict[str, Any]:
        """
            Return the output of `az account show`
        """
        cmd = "az account show"
        exception = None
        try:
            return json.loads(os.popen(cmd).read())
        except json.JSONDecodeError as e:
            exception = e
        raise RuntimeError(f"Failed to decode output from `{cmd}` - please check you are signed in. Raised exception: {exception}")

    @classmethod
    def get_current_user(cls) -> str:
        """
            Return the name of the current user
        """
        return cls.get_current_subscription_details()["user"]["name"]

    @classmethod
    def get_subscription_id(cls, subscription_name: str) -> str:
        """
            Return the id of the current subscription
        """
        subscriptions = json.loads(cls.run_az_cli_command(["az", "account", "subscription", "list", "--output", "json"]))
        for subscription in subscriptions:
            if subscription["displayName"] == subscription_name:
                return subscription["id"].replace("/subscriptions/", "")
        raise ValueError(f"Could not find a subscription with name '{subscription_name}'")

    @classmethod
    def get_purview_managed_storage_accounts(cls) -> Dict[str, Any]:
        """
            Return the details of all Purview managed storage accounts
        """
        resource_group = f"pins-rg-datamgmt-purview-managed"
        command = f"az storage account list -g {resource_group}"
        return json.loads(cls.run_az_cli_command(command.split(" ")))

    @classmethod
    def get_purview_managed_storage_account_names(cls) -> List[str]:
        return [
            storage_account["name"]
            for storage_account in cls.get_purview_managed_storage_accounts()
        ]
    
    @classmethod
    def get_purview_managed_event_hub_namespaces(cls):
        """
            Return the details of all Purview managed event hubs
        """
        resource_group = f"pins-rg-datamgmt-purview-managed"
        command = f"az eventhubs namespace list -g {resource_group}"
        return json.loads(cls.run_az_cli_command(command.split(" ")))

    @classmethod
    def get_purview_managed_event_hub_namespace_names(cls) -> List[str]:
        return [
            event_hub["name"]
            for event_hub in cls.get_purview_managed_event_hub_namespaces()
        ]
