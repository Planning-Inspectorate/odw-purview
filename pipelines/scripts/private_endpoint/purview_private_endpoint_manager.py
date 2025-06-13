from pipelines.scripts.private_endpoint.private_endpoint_manager import PrivateEndpointManager


class PurviewPrivateEndpointManager(PrivateEndpointManager):
    def get_resource_type(self):
        return "Microsoft.Purview/accounts"
