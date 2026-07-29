import argparse
import json
import os
from typing import Any

import requests
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv(verbose=True, override=True)

"""
ODW raw data can come in many different formats for the same entity, which results in "duplicate" entities in Purview which represent each format.
The raw data itself will have roughly the same schema between the Purview entities, and will also contain the ODW entity name within their `displayText`

This script gathers the columns of the "duplicate" Purview entities and synchronises their classification tags, so that the classifications across all of
the "duplicates" are the same

# Example usage
## Running without applying (i.e. this just prints the changes that will be made)
python3 scripts/sync_column_classifications.py -en "TABLE_NAME_HERE" -cn "CONTAINER_NAME_HERE"

### Running and applying (i.e. this will modify the entries in Purview)
python3 scripts/sync_column_classifications.py -en "TABLE_NAME_HERE" -cn "CONTAINER_NAME_HERE" -a

### Running against different entity types
Note by default this runs against ADLSG2 and Azure Blob entities - if you want to run against others (such as MSSQL, you will need to specify them here)
python3 scripts/sync_column_classifications.py -en "TABLE_NAME_HERE" -cn "CONTAINER_NAME_HERE" --tf "Some Entity Type, Another Entity Type"

"""

CREDENTIAL = AzureCliCredential()
REQUEST_HEADERS = {
    "Authorization": f"Bearer {CREDENTIAL.get_token('https://purview.azure.net/.default').token}",
    "Content-Type": "application/json",
}
PURVIEW_NAME = os.environ.get("PURVIEW_NAME")
PURVIEW_ENTITY_CACHE = {}


def get_entities_by_guids(guids: list[str]):
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
            print(resp.text)
            raise
        all_results.extend(result)
    # Cache the entities in a lookup dictionary
    for entity in all_results:
        PURVIEW_ENTITY_CACHE[entity["guid"]] = entity
    return all_results


def get_related_table_entities(
    table_name: str, container_name: str, entity_types: list[str]
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
        x["id"]
        for x in entity_summaries
        if container_name in x["qualifiedName"] and entity_name in x["qualifiedName"]
    ]
    entities = get_entities_by_guids(relevant_entity_guids)
    print(f"Found {len(relevant_entity_guids)} table entities")
    entity_qualified_names = [x["attributes"]["qualifiedName"] for x in entities]
    print("The following table entity qualified names will be considered:")
    print(json.dumps(entity_qualified_names, indent=4))
    return entities


def extract_columns_of_table_entities(entities: list[dict[str, Any]]):
    """
    Deeply extract the child entities of the given entity list. Return a dictionary with the form <entity_guid: child_entity_guid>
    """

    def get_child_entities(entity: dict[str, Any]):
        return (
            [
                x["guid"]
                for x in entity["relationshipAttributes"].get("attachedSchema", [])
            ]
            + [x["guid"] for x in entity["relationshipAttributes"].get("items", [])]
            + [
                x["guid"]
                for x in entity["relationshipAttributes"].get("properties", [])
            ]
            + [x["guid"] for x in entity["relationshipAttributes"].get("columns", [])]
        )

    def recursively_extract_child_entities(entity: dict[str, Any]):
        guids_to_expand = get_child_entities(entity)
        new_child_entities = get_entities_by_guids(guids_to_expand)
        new_children = [
            grandchild
            for child in new_child_entities
            for grandchild in recursively_extract_child_entities(child)
        ]
        return new_child_entities + new_children

    return {
        entity["guid"]: recursively_extract_child_entities(entity)
        for entity in entities
    }


def group_similar_classification_tags_for_table_entities(
    table_entities: list[dict[str, Any]],
):
    """
    Return a dictionary of <column_entity_guid: common_classifications> with classifications that are common to all column
    entities with the same name

    i.e. If you have two column entities for colA, then their classification tags will be synced in the result dictionary

    This prints a comparison of before/after so you can trace what is happening
    """
    table_entity_column_map = extract_columns_of_table_entities(table_entities)
    # Generate a map of the classification tags for columns with the same names
    column_name_classifications = {}
    column_guid_name_map = {}
    original_column_entity_classifications = {}
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
                column_name_classifications[column_name] = list(
                    set(
                        column_name_classifications[column_name]
                        + new_classification_names
                    )
                )
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
    print("The below classifications were found for the columns")
    print(json.dumps(column_name_classifications, indent=4))
    if modified_column_entity_classifications:
        relevant_column_name_map = {
            column_guid: column_guid_name_map[column_guid]
            for column_guid in modified_column_entity_classifications
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
    entity_classification_dict: dict[str, list[str]], apply=False
):
    """
    Take in a dictionary of <entity_guid: [classification_names]> and bulk upload to Purview
    """

    def generate_request_json(entity_guid, entity_classifications: list[str]):
        entity_json = PURVIEW_ENTITY_CACHE[entity_guid]
        existing_classifications = {
            x["typeName"] for x in entity_json.get("classifications", [])
        }
        # The REST API
        return [
            {"typeName": classification_name, "entityGuid": entity_guid}
            for classification_name in entity_classifications
            if classification_name not in existing_classifications
        ]

    request_bodies = {
        entity_guid: generate_request_json(entity_guid, classification_list)
        for entity_guid, classification_list in entity_classification_dict.items()
    }
    if apply:
        for (
            guid,
            body,
        ) in request_bodies.items():
            print(f"Applying classifications to entity with guid '{guid}'")
            url = f"https://{PURVIEW_NAME}.purview.azure.com/datamap/api/atlas/v2/entity/guid/{guid}/classifications"
            resp = requests.post(url, json=body, headers=REQUEST_HEADERS)
            print(f"    {resp}")
            print(resp.text)


def sync_purview_column_classifications(
    table_name: str,
    container_name: str,
    entity_type_filter: list[str],
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
    type_filter_string: str = args.type_filter
    apply = args.apply
    type_filter = [x.lstrip().rstrip() for x in type_filter_string.split(",")]

    sync_purview_column_classifications(
        entity_name, container_name, type_filter, bool(apply)
    )
