import requests
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
import json
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import argparse


load_dotenv(verbose=True, override=True)


CREDENTIAL = AzureCliCredential()
REQUEST_HEADERS = {
    "Authorization": f"Bearer {CREDENTIAL.get_token('https://purview.azure.net/.default').token}",
    "Content-Type": "application/json",
}
PURVIEW_NAME = os.environ.get("PURVIEW_NAME")


def get_entities_by_guids(guids: List[str]):
    """
    Fetch a list of Purview entities by a list of entity guids
    """
    chunk_size = 50
    query_chunks = [guids[i : i + chunk_size] for i in range(0, len(guids), chunk_size)]
    all_results = []
    for chunk in query_chunks:
        guid_string = "&guid=".join(chunk)
        url = f"https://{PURVIEW_NAME}.purview.azure.com/datamap/api/atlas/v2/entity/bulk?guid={guid_string}"
        resp = requests.get(url, headers=REQUEST_HEADERS)
        try:
            result = resp.json()["entities"]
        except json.JSONDecodeError:
            print(resp)
            raise
        all_results.extend(result)
    return all_results


def get_related_table_entities(
    table_name: str, container_name: str, entity_types: List[str]
):
    """
    Search Purview to find tables that match the given table_name and entity_types, and filter down the result to 
    only include entities that represent data in the specified container
    """
    search_endpoint = f"https://{PURVIEW_NAME}.purview.azure.com/catalog/api/search/query?api-version=2023-02-01-preview&includeTermHierarchy=false"
    entity_type_filter = (
        [{"or": [{"assetType": entity_type} for entity_type in entity_types]}]
        if entity_types
        else []
    )
    search_payload = {
        "keywords": table_name,
        "filter": {
            "and": entity_type_filter
            + [
                {
                    "not": {
                        "or": [
                            {
                                "attributeName": "size",
                                "operator": "eq",
                                "attributeValue": 0,
                            },
                            {
                                "attributeName": "fileSize",
                                "operator": "eq",
                                "attributeValue": 0,
                            },
                        ]
                    }
                },
                {"not": {"classification": "MICROSOFT.SYSTEM.TEMP_FILE"}},
                {"not": {"glossaryType": "AtlasGlossary"}},
            ]
        },
        "limit": 25,
        "offset": 0,
        "facets": [
            {"facet": "assetType", "count": 0, "sort": {"count": "desc"}},
            {"facet": "collectionId", "count": 10, "sort": {"count": "desc"}},
            {"facet": "classification", "count": 11, "sort": {"count": "desc"}},
            {"facet": "sensitiveInfoType", "count": 10, "sort": {"count": "desc"}},
            {"facet": "contactId", "count": 10, "sort": {"count": "desc"}},
            {"facet": "termGuid", "count": 10, "sort": {"count": "desc"}},
            {"facet": "tag", "count": 0, "sort": {"count": "desc"}},
            {"facet": "sensitivityLabelId", "count": 10, "sort": {"count": "desc"}},
        ],
        "taxonomySetting": {
            "assetTypes": entity_types,
            "facet": {"count": 10, "sort": {"count": "desc"}},
        },
        "enableRankingFunction": False,
    }
    resp = requests.post(search_endpoint, json=search_payload, headers=REQUEST_HEADERS)
    entity_summaries = resp.json().get("value", [])
    relevant_entity_guids = [
        x["id"] for x in entity_summaries if container_name in x["qualifiedName"]
    ]
    entities = get_entities_by_guids(relevant_entity_guids)
    print(f"Found {len(relevant_entity_guids)} table entities")
    entity_qualified_names = [x["attributes"]["qualifiedName"] for x in entities]
    print("The following table entity qualified names will be considered:")
    print(json.dumps(entity_qualified_names, indent=4))
    return entities


def get_entity_column_map(entities: List[Dict[str, Any]]):
    """
    Return a dictionary of the form <table_entity_guid: table_entity_column_entity_list>
    """
    # A map of table_guid: table_attached_schema_guid
    table_attached_schema_guid_map = {
        entity["guid"]: entity["relationshipAttributes"]["attachedSchema"][0]["guid"]
        for entity in entities
        if entity["relationshipAttributes"].get("attachedSchema", None)
    }
    # A map of table_attached_schema_guid: table_attached_schema
    attached_schema_entities = {
        x["guid"]: x
        for x in get_entities_by_guids(list(table_attached_schema_guid_map.values()))
    }
    # A map of table_guid: attached schema column guids
    attached_schema_map = {
        table_guid: [
            x["guid"]
            for x in attached_schema_entities[attached_schema_guid][
                "relationshipAttributes"
            ].get("columns", [])
        ]
        for table_guid, attached_schema_guid in table_attached_schema_guid_map.items()
    }
    # A list of column guids to extract from Purview
    column_entities_to_extract = [
        entity for group in attached_schema_map.values() for entity in group
    ]
    # A map of column_guid: column
    column_entities_map = {
        x["guid"]: x for x in get_entities_by_guids(column_entities_to_extract)
    }
    # A map of table_guid: column_guids
    return {
        table_guid: [
            column_entities_map[column_guid]
            for column_guid in attached_schema_column_guids
        ]
        for table_guid, attached_schema_column_guids in attached_schema_map.items()
    }


def group_similar_classification_tags_for_table_entities(
    table_entities: List[Dict[str, Any]],
):
    """
    Return a dictionary of <column_entity_guid: common_classifications> with classifications that are common to all column
    entities with the same name

    i.e. If you have two column entities for colA, then their classification tags will be synced in the result dictionary

    This prints a comparison of before/after so you can trace what is happening
    """
    table_entity_column_map = get_entity_column_map(table_entities)
    # Generate a map of the classification tags for columns with the same names
    column_name_classifications = dict()
    column_guid_name_map = dict()
    original_column_entity_classifications = dict()
    for column_entities in table_entity_column_map.values():
        for column_entity in column_entities:
            column_guid = column_entity["guid"]
            column_name = column_entity["displayText"]
            column_guid_name_map[column_guid] = column_name
            new_classification_names = [
                x["typeName"] for x in column_entity.get("classifications", [])
            ]
            original_column_entity_classifications[column_guid] = (
                new_classification_names
            )
            if column_name not in column_name_classifications:
                column_name_classifications[column_name] = new_classification_names
            else:
                column_name_classifications[column_name] += new_classification_names
    # Apply classification tags
    new_column_entity_classifications = {
        column_guid: list(set(column_name_classifications[column_name]))
        for column_guid, column_name in column_guid_name_map.items()
    }
    # Only return the columns that need to be updated
    modified_column_entity_classifications = {
        k: v
        for k, v in new_column_entity_classifications.items()
        if set(original_column_entity_classifications[k]) != set(v)
    }
    if modified_column_entity_classifications:
        relevant_column_name_map = {
            column_guid: column_guid_name_map[column_guid]
            for column_guid in modified_column_entity_classifications.keys()
        }
        print(
            "The following column entities have modified classifications, which are below"
        )
        print(json.dumps(relevant_column_name_map, indent=4))
        print("The following classification modifications will be applied")
        print(json.dumps(modified_column_entity_classifications, indent=4))
    else:
        print("No classification modifications detected")
        print("Below are the column entities that have been analysed, and their name")
        print(json.dumps(column_guid_name_map, indent=4))
        print("Below are the original classifications applied to each column")
        print(json.dumps(original_column_entity_classifications, indent=4))
    return modified_column_entity_classifications


def bulk_assign_classifications(
    entity_classification_dict: Dict[str, List[str]], apply=False
):
    """
    Take in a dictionary of <entity_guid: [classification_names]> and bulk upload to Purview
    """

    def generate_request_json(entity_guid, entity_classifications: List[str]):
        return [
            {"typeName": classification_name, "entityGuid": entity_guid}
            for classification_name in entity_classifications
        ]

    request_bodies = {
        entity_guid: generate_request_json(entity_guid, classification_list)
        for entity_guid, classification_list in entity_classification_dict.items()
    }
    if apply:
        for guid in request_bodies.keys():
            print(f"Applying classifications to entity with guid '{guid}'")
            url = f"https://{PURVIEW_NAME}.purview.azure.com/datamap/api/atlas/v2/entity/guid/{guid}/classifications"
            resp = requests.post(
                url, json=request_bodies[guid], headers=REQUEST_HEADERS
            )
            print(f"    {resp}")


def sync_purview_column_classifications(
    table_name: str,
    container_name: str,
    entity_type_filter: List[str],
    apply: bool = False,
):
    """
    Synchronise the column classifications across all Purview entities that represent the same table

    :param table_name str: The table to apply to
    :param container_name str: The container the table must belong to. Use this to narrow down to only a specific ODW layer
    :param entity_type_filter List[str]: A lisr of Purview entity types that the target table must be a type of
    :param apply bool: Whether or not to apply the change in the catalogue. It is recommended to run with `apply=False` before applying
    """
    # appeal-has
    table_entities = get_related_table_entities(
        table_name, container_name, entity_type_filter
    )
    # print(json.dumps(resp, indent=4))
    # print(json.dumps(resp.json(), indent=4))

    classification_map = group_similar_classification_tags_for_table_entities(
        table_entities
    )

    bulk_assign_classifications(classification_map, apply)


VALID_TYPES = ["Azure Data Lake Storage Gen2", "Azure Storage Account"]
# appeal-has

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-en", "--entity_name", help="The entity to synchronise", required=True
    )
    parser.add_argument(
        "-cn",
        "--container_name",
        help="The storage container the entity must belong to",
        required=True,
    )
    parser.add_argument(
        "-tf",
        "--type_filter",
        help="Comma-separated purview type filters. Defaults to ADLSG2",
        default="Azure Data Lake Storage Gen2",
    )
    parser.add_argument(
        "-a",
        "--apply",
        help="If changes should be applied. Defaults to false",
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()
    entity_name = args.entity_name
    container_name = args.container_name
    type_filter_string = args.type_filter
    apply = args.apply

    sync_purview_column_classifications(
        entity_name, container_name, ["Azure Data Lake Storage Gen2"], bool(apply)
    )
