import unittest
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session
from tgc_apt.update_databases import (
    fetch_json,
    calculate_hash,
    update_alltools,
    update_allgroups,
    update_databases
)
from models.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from models.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames

class TestUpdateDatabases(unittest.TestCase):

    @patch('tgc_apt.update_databases.requests.get')
    def test_fetch_json(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response

        result = fetch_json('https://example.com/api')
        self.assertEqual(result, {'key': 'value'})
        mock_get.assert_called_once_with('https://example.com/api')

    def test_calculate_hash(self):
        data = {'key': 'value'}
        result = calculate_hash(data)
        self.assertEqual(result, '8c7dd922ad47494fc02c388e12c00eac')

    @patch('tgc_apt.update_databases.Session')
    def test_update_alltools(self, mock_session):
        mock_session = Mock(spec=Session)
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value.first.return_value = None

        data = [{
            'uuid': '123',
            'name': 'Test Tool',
            'values': [{'uuid': '456', 'tool': 'Test Value', 'names': ['Test Name']}]
        }]

        update_alltools(mock_session, data)

        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch('tgc_apt.update_databases.Session')
    def test_update_allgroups(self, mock_session):
        mock_session = Mock(spec=Session)
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value.first.return_value = None

        data = [{
            'uuid': '789',
            'name': 'Test Group',
            'values': [{'uuid': '012', 'actor': 'Test Actor', 'names': [{'name': 'Test Name'}]}]
        }]

        update_allgroups(mock_session, data)

        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch('tgc_apt.update_databases.fetch_json')
    @patch('tgc_apt.update_databases.calculate_hash')
    @patch('tgc_apt.update_databases.update_alltools')
    @patch('tgc_apt.update_databases.update_allgroups')
    @patch('tgc_apt.update_databases.create_engine')
    @patch('tgc_apt.update_databases.sessionmaker')
    def test_update_databases(self, mock_sessionmaker, mock_create_engine, mock_update_allgroups, mock_update_alltools, mock_calculate_hash, mock_fetch_json):
        mock_fetch_json.side_effect = [{'tools': 'data'}, {'groups': 'data'}]
        mock_calculate_hash.side_effect = ['hash1', 'hash2']
        mock_session = Mock()
        mock_sessionmaker.return_value.return_value = mock_session

        update_databases()

        mock_fetch_json.assert_any_call("https://apt.etda.or.th/cgi-bin/getcard.cgi?t=all&o=j")
        mock_fetch_json.assert_any_call("https://apt.etda.or.th/cgi-bin/getcard.cgi?g=all&o=j")
        mock_update_alltools.assert_called_once_with(mock_session, {'tools': 'data'})
        mock_update_allgroups.assert_called_once_with(mock_session, {'groups': 'data'})
        mock_session.commit.assert_called()
        mock_session.close.assert_called()

if __name__ == '__main__':
    unittest.main()
