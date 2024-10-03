document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/v1/graph')
        .then(response => response.json())
        .then(data => {
            const cy = cytoscape({
                container: document.getElementById('graph-container'),
                elements: [
                    ...data.nodes.map(node => ({
                        data: { id: node.id, label: node.label, name: node.name }
                    })),
                    ...data.edges.map(edge => ({
                        data: {
                            id: edge.id,
                            source: edge.outV,
                            target: edge.inV,
                            label: edge.label
                        }
                    }))
                ],
                style: [
                    {
                        selector: 'node',
                        style: {
                            'label': 'data(name)',
                            'background-color': '#0074D9',
                            'color': '#fff',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'width': '50',
                            'height': '50',
                            'shape': 'ellipse'
                        }
                    },
                    {
                        selector: 'node[label="Tool"]',
                        style: {
                            'shape': 'diamond',
                            'background-color': '#FF4136'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'label': 'data(label)',
                            'line-color': '#AAAAAA',
                            'target-arrow-color': '#AAAAAA',
                            'target-arrow-shape': 'triangle'
                        }
                    }
                ],
                layout: { name: 'cose' }
            });

            // Optional: Add event listeners for interactivity
            cy.on('tap', 'node', function(evt){
                var node = evt.target;
                // Implement drill-down functionality
                alert('Node clicked: ' + node.data('name'));
            });
        });
});
