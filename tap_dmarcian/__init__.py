#!/usr/bin/env python3
import os
import json
import re
import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
import boto3


REQUIRED_CONFIG_KEYS = ["bucket"]
LOGGER = singer.get_logger()
FILE_REGEX = "^dmarcian_.*([0-9]{4}-[0-9]{2}-[0-9]{2})\\.json$"


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        mdata = metadata.get_standard_metadata(
            schema=schema.to_dict(),
            key_properties=["report_id", "row_id"],
            valid_replication_keys=["report_date"],
            replication_method="INCREMENTAL",
        )

        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=["report_id", "row_id"],
                metadata=mdata,
                replication_key=["report_date"],
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )
    return Catalog(streams)


def sync(config, state, catalog):
    """ Sync data from tap source """
    # Loop over selected streams in catalog
    s3 = boto3.client('s3')

    bucket = config['bucket']
    prefix = config.get('prefix')

    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        date = singer.get_bookmark(state, stream.tap_stream_id, 'latest_email_date') or config.get('start_date')

        paginator = s3.get_paginator('list_objects_v2')
        pages = 0
        args = { 'Bucket': bucket, 'MaxKeys': 1000 }
        if prefix and date:
            args['StartAfter'] = f"{prefix}/{date}"
        elif date:
            args['StartAfter'] = date
        LOGGER.debug("Getting list of files in bucket %s starting from %s", bucket, args.get('StartAfter'))
        for page in paginator.paginate(**args):
            pages += 1
            LOGGER.debug("On page %s", pages)
            for s3_object_listing in page['Contents']:
                key = s3_object_listing['Key']
                m = re.match(FILE_REGEX, key.split('/')[-1])
                if m == None:
                    continue

                LOGGER.debug("Reading report %s", key)
                parts = key[len(prefix)+1 if prefix else 0:].split('/')
                date = parts[0]
                report_id = parts[1]

                s3_object = s3.get_object(Bucket=bucket, Key=key)
                data = json.loads(s3_object['Body'].read())
                rows = []
                for i, row in enumerate(data):
                    row['report_id'] = report_id
                    row['report_date'] = m[1]
                    row['row_id'] = i
                    rows.append(row)

                singer.write_records(stream.tap_stream_id, rows)
                state = singer.write_bookmark(state, stream.tap_stream_id, 'latest_email_date', date)
                singer.write_state(state)
                LOGGER.info('Wrote %s records for stream "%s"', len(rows), stream.tap_stream_id)


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()
        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
