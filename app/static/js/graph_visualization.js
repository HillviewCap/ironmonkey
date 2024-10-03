document.addEventListener('DOMContentLoaded', () => {
    const viewSelector = document.getElementById('graph-view-selector');
    
    function fetchAndRenderGraph(view) {
        fetch(`/api/v1/graph?view=${encodeURIComponent(view)}`)
            .then(response => response.json())
            .then(data => {
                if (window.cy) {
                    window.cy.destroy();
                }
                
                window.cy = cytoscape({
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
                    layout: { 
                        name: 'cose',
                        idealEdgeLength: 100,
                        nodeOverlap: 20,
                        refresh: 20,
                        fit: true,
                        padding: 30,
                        randomize: false,
                        componentSpacing: 100,
                        nodeRepulsion: 400000,
                        edgeElasticity: 100,
                        nestingFactor: 5,
                        gravity: 80,
                        numIter: 1000,
                        initialTemp: 200,
                        coolingFactor: 0.95,
                        minTemp: 1.0
                    }
                });

                // Optional: Add event listeners for interactivity
                cy.on('tap', 'node', function(evt){
                    var node = evt.target;
                    // Implement drill-down functionality
                    alert('Node clicked: ' + node.data('name'));
                });
            });
    }

    // Initial graph render
    fetchAndRenderGraph(viewSelector.value);

    // Update graph when view changes
    viewSelector.addEventListener('change', function() {
        fetchAndRenderGraph(this.value);
    });
});
