def test_graph_connection_initialization():
    from app.utils.graph_connection_manager import GraphConnectionManager
    app = create_app()
    with app.app_context():
        GraphConnectionManager.initialize(app)
        client = GraphConnectionManager.get_client()
        assert client is not None
