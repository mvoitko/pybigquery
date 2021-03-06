import pytest
from sqlalchemy.engine.url import make_url
from google.cloud.bigquery import QueryJobConfig
from google.cloud.bigquery.table import EncryptionConfiguration, TableReference
from google.cloud.bigquery.dataset import DatasetReference

from pybigquery.parse_url import parse_url


@pytest.fixture(scope='session')
def url_with_everything():
    # create_disposition
    # CREATE_IF_NEEDED
    # CREATE_NEVER

    # write_disposition
    # WRITE_APPEND
    # WRITE_TRUNCATE
    # WRITE_EMPTY

    # priority
    # INTERACTIVE
    # BATCH

    # schema_update_option
    # ALLOW_FIELD_ADDITION
    # ALLOW_FIELD_RELAXATION

    return make_url(
        'bigquery://some-project/some-dataset'
        '?credentials_path=/some/path/to.json'
        '&location=some-location'
        '&arraysize=1000'
        '&clustering_fields=a,b,c'
        '&create_disposition=CREATE_IF_NEEDED'
        '&destination=different-project.different-dataset.table'
        '&destination_encryption_configuration=some-configuration'
        '&dry_run=true'
        '&labels=a:b,c:d'
        '&maximum_bytes_billed=1000'
        '&priority=INTERACTIVE'
        '&schema_update_options=ALLOW_FIELD_ADDITION,ALLOW_FIELD_RELAXATION'
        '&use_query_cache=true'
        '&write_disposition=WRITE_APPEND'
    )


def test_basic(url_with_everything):
    project_id, location, dataset_id, arraysize, credentials_path, job_config = parse_url(url_with_everything)

    assert project_id == 'some-project'
    assert location == 'some-location'
    assert dataset_id == 'some-dataset'
    assert arraysize == 1000
    assert credentials_path == '/some/path/to.json'
    assert isinstance(job_config, QueryJobConfig)

@pytest.mark.parametrize('param, value', [
    ('clustering_fields', ['a', 'b', 'c']),
    ('create_disposition', 'CREATE_IF_NEEDED'),
    ('destination', TableReference(DatasetReference('different-project', 'different-dataset'), 'table')),
    ('destination_encryption_configuration', lambda enc: enc.kms_key_name == EncryptionConfiguration('some-configuration').kms_key_name),
    ('dry_run', True),
    ('labels', { 'a': 'b', 'c': 'd' }),
    ('maximum_bytes_billed', 1000),
    ('priority', 'INTERACTIVE'),
    ('schema_update_options', ['ALLOW_FIELD_ADDITION', 'ALLOW_FIELD_RELAXATION']),
    ('use_query_cache', True),
    ('write_disposition', 'WRITE_APPEND'),
])
def test_all_values(url_with_everything, param, value):
    job_config = parse_url(url_with_everything)[5]

    config_value = getattr(job_config, param)
    if callable(value):
        assert value(config_value)
    else:
        assert config_value == value

# def test_malformed():
#     location, dataset_id, arraysize, credentials_path, job_config = parse_url(make_url('bigquery:///?credentials_path=a'))

#     print(credentials_path)
#     assert False

@pytest.mark.parametrize("param, value", [
    ('arraysize', 'not-int'),
    ('create_disposition', 'not-attribute'),
    ('destination', 'not.fully-qualified'),
    ('dry_run', 'not-bool'),
    ('labels', 'not-key-value'),
    ('maximum_bytes_billed', 'not-int'),
    ('priority', 'not-attribute'),
    ('schema_update_options', 'not-attribute'),
    ('use_query_cache', 'not-bool'),
    ('write_disposition', 'not-attribute'),
])
def test_bad_values(param, value):
    url = make_url('bigquery:///?' + param + '=' + value)
    with pytest.raises(ValueError):
        parse_url(url)

def test_empty_url():
    for value in parse_url(make_url('bigquery://')):
        assert value is None

    for value in parse_url(make_url('bigquery:///')):
        assert value is None

def test_empty_with_non_config():
    url = parse_url(make_url('bigquery:///?location=some-location&arraysize=1000&credentials_path=/some/path/to.json'))
    project_id, location, dataset_id, arraysize, credentials_path, job_config = url

    assert project_id is None
    assert location == 'some-location'
    assert dataset_id is None
    assert arraysize == 1000
    assert credentials_path == '/some/path/to.json'
    assert job_config is None

def test_only_dataset():
    url = parse_url(make_url('bigquery:///some-dataset'))
    project_id, location, dataset_id, arraysize, credentials_path, job_config = url

    assert project_id is None
    assert location is None
    assert dataset_id == 'some-dataset'
    assert arraysize is None
    assert credentials_path is None
    assert isinstance(job_config, QueryJobConfig)
    # we can't actually test that the dataset is on the job_config,
    # since we take care of that afterwards, when we have a client to fill in the project

@pytest.mark.parametrize('disallowed_arg', [
    'use_legacy_sql',
    'allow_large_results',
    'flatten_results',
    'maximum_billing_tier',
    'default_dataset',
    'dataset_id',
    'project_id',
])
def test_disallowed(disallowed_arg):
    url = make_url('bigquery://some-project/some-dataset/?' + disallowed_arg + '=' + 'whatever')
    with pytest.raises(ValueError):
        parse_url(url)

@pytest.mark.parametrize('not_implemented_arg', [
    'query_parameters',
    'table_definitions',
    'time_partitioning',
    'udf_resources',
])
def test_not_implemented(not_implemented_arg):
    url = make_url('bigquery://some-project/some-dataset/?' + not_implemented_arg + '=' + 'whatever')
    with pytest.raises(NotImplementedError):
        parse_url(url)
