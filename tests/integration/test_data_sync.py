def test_data_sync():
    from app.services.data_sync import sync_data_to_graph
    sync_data_to_graph()
    # Verify that data exists in the graph database
    client = GraphConnectionManager.get_client()
    result = client.submit("g.V().count()").all().result()
    assert result[0] > 0
