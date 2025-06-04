#!/usr/bin/env python3
"""
HCL Graph Builder - Creates and visualizes graph of HCL relationships
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Tuple, Any
import seaborn as sns
from collections import Counter
import json

class HCLGraphBuilder:
    def __init__(self):
        """Initialize the graph builder"""
        self.graph = nx.DiGraph()  # Directed graph for HCL relationships
        self.metadata_df = None
        self.relationships_df = None
        
        # Color mapping for relationship types
        self.relationship_colors = {
            'modifică': '#FF6B6B',    # Red
            'abrogă': '#4ECDC4',      # Teal  
            'completează': '#45B7D1',  # Blue
            'referă': '#96CEB4',       # Green
            'înlocuiește': '#FECA57',  # Yellow
            'suspendă': '#A8A8A8'      # Gray
        }
        
    def load_data(self, metadata_file: str = 'hcl_metadata.csv', 
                  relationships_file: str = 'hcl_relationships.csv'):
        """Load metadata and relationships data"""
        try:
            self.metadata_df = pd.read_csv(metadata_file, encoding='utf-8')
            print(f"Loaded {len(self.metadata_df)} metadata records")
            
            if pd.io.common.file_exists(relationships_file):
                self.relationships_df = pd.read_csv(relationships_file, encoding='utf-8')
                print(f"Loaded {len(self.relationships_df)} relationship records")
            else:
                print(f"Relationships file {relationships_file} not found. Creating empty relationships.")
                self.relationships_df = pd.DataFrame(columns=[
                    'source', 'target', 'relationship_type', 'reference_text', 'year'
                ])
                
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
        return True
    
    def build_graph(self):
        """Build the NetworkX graph from the data"""
        
        # Add nodes (HCL items)
        for index, row in self.metadata_df.iterrows():
            hcl_nr = row['hcl_nr']
            
            # Node attributes
            node_attrs = {
                'subject_matter': row.get('subject_matter', ''),
                'data_adoptarii': row.get('data_adoptarii', ''),
                'data_publicarii': row.get('data_publicarii', ''),
                'relationship_type': row.get('relationship_type', 'referă'),
                'entities_count': len(eval(row.get('entities_involved', '[]')) if 
                                     isinstance(row.get('entities_involved'), str) else 
                                     row.get('entities_involved', [])),
                'references_count': len(eval(row.get('hcl_references', '[]')) if 
                                       isinstance(row.get('hcl_references'), str) else 
                                       row.get('hcl_references', []))
            }
            
            self.graph.add_node(hcl_nr, **node_attrs)
        
        # Add edges (relationships)
        for index, row in self.relationships_df.iterrows():
            source = row['source']
            target = row['target']
            relationship_type = row['relationship_type']
            reference_text = row.get('reference_text', '')
            year = row.get('year', '')
            
            # Only add edge if both nodes exist
            if source in self.graph.nodes and target in self.graph.nodes:
                self.graph.add_edge(source, target, 
                                  relationship_type=relationship_type,
                                  reference_text=reference_text,
                                  year=year,
                                  weight=1.0)
        
        print(f"Graph built with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")
        
    def analyze_graph_metrics(self) -> Dict[str, Any]:
        """Calculate various graph metrics"""
        
        metrics = {}
        
        # Basic metrics
        metrics['num_nodes'] = len(self.graph.nodes)
        metrics['num_edges'] = len(self.graph.edges)
        metrics['density'] = nx.density(self.graph)
        
        # Centrality measures
        if len(self.graph.nodes) > 0:
            metrics['degree_centrality'] = nx.degree_centrality(self.graph)
            metrics['in_degree_centrality'] = nx.in_degree_centrality(self.graph)
            metrics['out_degree_centrality'] = nx.out_degree_centrality(self.graph)
            
            if nx.is_weakly_connected(self.graph):
                metrics['betweenness_centrality'] = nx.betweenness_centrality(self.graph)
                metrics['closeness_centrality'] = nx.closeness_centrality(self.graph)
        
        # Connected components
        metrics['num_weakly_connected_components'] = nx.number_weakly_connected_components(self.graph)
        metrics['num_strongly_connected_components'] = nx.number_strongly_connected_components(self.graph)
        
        # Relationship type distribution
        edge_types = [self.graph[u][v]['relationship_type'] for u, v in self.graph.edges()]
        metrics['relationship_type_counts'] = Counter(edge_types)
        
        return metrics
    
    def create_matplotlib_visualization(self, figsize: Tuple[int, int] = (15, 12)):
        """Create a matplotlib visualization of the graph"""
        
        plt.figure(figsize=figsize)
        
        # Calculate layout
        if len(self.graph.nodes) > 0:
            # Use spring layout for better visualization
            pos = nx.spring_layout(self.graph, k=3, iterations=50)
            
            # Draw nodes
            node_sizes = [300 + self.graph.nodes[node].get('references_count', 0) * 100 
                         for node in self.graph.nodes()]
            
            nx.draw_networkx_nodes(self.graph, pos, 
                                 node_size=node_sizes,
                                 node_color='lightblue',
                                 alpha=0.7)
            
            # Draw edges by relationship type
            for rel_type, color in self.relationship_colors.items():
                edges_of_type = [(u, v) for u, v in self.graph.edges() 
                               if self.graph[u][v]['relationship_type'] == rel_type]
                
                if edges_of_type:
                    nx.draw_networkx_edges(self.graph, pos,
                                         edgelist=edges_of_type,
                                         edge_color=color,
                                         arrows=True,
                                         arrowsize=20,
                                         alpha=0.7,
                                         label=rel_type)
            
            # Draw labels
            nx.draw_networkx_labels(self.graph, pos, font_size=8)
            
            plt.title("HCL Relationship Graph", fontsize=16, fontweight='bold')
            plt.legend()
            plt.axis('off')
            plt.tight_layout()
            
        else:
            plt.text(0.5, 0.5, 'No graph data to display', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=plt.gca().transAxes, fontsize=14)
        
        plt.savefig('hcl_graph_matplotlib.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_plotly_visualization(self):
        """Create an interactive Plotly visualization"""
        
        if len(self.graph.nodes) == 0:
            print("No nodes to visualize")
            return
        
        # Calculate layout
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # Prepare edge traces
        edge_traces = []
        
        for rel_type, color in self.relationship_colors.items():
            edge_x = []
            edge_y = []
            edge_info = []
            
            for edge in self.graph.edges():
                if self.graph[edge[0]][edge[1]]['relationship_type'] == rel_type:
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_info.append(f"{edge[0]} → {edge[1]} ({rel_type})")
            
            if edge_x:
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=2, color=color),
                    hoverinfo='none',
                    mode='lines',
                    name=rel_type,
                    showlegend=True
                )
                edge_traces.append(edge_trace)
        
        # Prepare node trace
        node_x = []
        node_y = []
        node_info = []
        node_sizes = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node info for hover
            node_attrs = self.graph.nodes[node]
            info = f"HCL: {node}<br>"
            info += f"Subject: {node_attrs.get('subject_matter', 'N/A')[:50]}...<br>"
            info += f"Date: {node_attrs.get('data_adoptarii', 'N/A')}<br>"
            info += f"References: {node_attrs.get('references_count', 0)}"
            node_info.append(info)
            
            # Node size based on references count
            size = 20 + node_attrs.get('references_count', 0) * 10
            node_sizes.append(min(size, 100))  # Cap at 100
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node for node in self.graph.nodes()],
            textposition="middle center",
            hovertext=node_info,
            marker=dict(
                size=node_sizes,
                color='lightblue',
                line=dict(width=2, color='darkblue')
            ),
            name='HCL Documents',
            showlegend=True
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace],
                       layout=go.Layout(
                           title='Interactive HCL Relationship Graph',
                           titlefont_size=16,
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Hover over nodes and edges for details",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002 ) ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                      )
        
        fig.write_html("hcl_graph_interactive.html")
        fig.show()
        print("Interactive graph saved as 'hcl_graph_interactive.html'")
    
    def create_dashboard(self):
        """Create a comprehensive dashboard with multiple visualizations"""
        
        metrics = self.analyze_graph_metrics()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Relationship Types Distribution', 'Node Degree Distribution',
                          'Centrality Measures', 'Graph Statistics'),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # Relationship types distribution
        if 'relationship_type_counts' in metrics:
            rel_types = list(metrics['relationship_type_counts'].keys())
            rel_counts = list(metrics['relationship_type_counts'].values())
            
            fig.add_trace(
                go.Bar(x=rel_types, y=rel_counts, 
                      marker_color=[self.relationship_colors.get(rt, '#CCCCCC') for rt in rel_types],
                      name='Relationship Types'),
                row=1, col=1
            )
        
        # Node degree distribution
        if len(self.graph.nodes) > 0:
            degrees = [self.graph.degree(node) for node in self.graph.nodes()]
            fig.add_trace(
                go.Histogram(x=degrees, nbinsx=10, name='Degree Distribution'),
                row=1, col=2
            )
        
        # Centrality measures (top 5 nodes)
        if 'degree_centrality' in metrics:
            top_nodes = sorted(metrics['degree_centrality'].items(), 
                             key=lambda x: x[1], reverse=True)[:5]
            nodes, centralities = zip(*top_nodes) if top_nodes else ([], [])
            
            fig.add_trace(
                go.Bar(x=list(nodes), y=list(centralities), name='Top Degree Centrality'),
                row=2, col=1
            )
        
        # Graph statistics table
        stats_data = [
            ['Metric', 'Value'],
            ['Number of Nodes', metrics.get('num_nodes', 0)],
            ['Number of Edges', metrics.get('num_edges', 0)],
            ['Graph Density', f"{metrics.get('density', 0):.4f}"],
            ['Weakly Connected Components', metrics.get('num_weakly_connected_components', 0)],
            ['Strongly Connected Components', metrics.get('num_strongly_connected_components', 0)]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=stats_data[0]),
                cells=dict(values=list(zip(*stats_data[1:])))
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False, 
                         title_text="HCL Graph Analysis Dashboard")
        
        fig.write_html("hcl_dashboard.html")
        fig.show()
        print("Dashboard saved as 'hcl_dashboard.html'")
    
    def export_graph_data(self, format_type: str = 'gexf'):
        """Export graph data in various formats"""
        
        if format_type.lower() == 'gexf':
            nx.write_gexf(self.graph, "hcl_graph.gexf")
            print("Graph exported as 'hcl_graph.gexf' (Gephi format)")
        
        elif format_type.lower() == 'graphml':
            nx.write_graphml(self.graph, "hcl_graph.graphml")
            print("Graph exported as 'hcl_graph.graphml'")
        
        elif format_type.lower() == 'json':
            graph_data = nx.node_link_data(self.graph)
            with open('hcl_graph.json', 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            print("Graph exported as 'hcl_graph.json'")
    
    def find_important_nodes(self, top_n: int = 5) -> Dict[str, List[Tuple[str, float]]]:
        """Find most important nodes based on various centrality measures"""
        
        if len(self.graph.nodes) == 0:
            return {}
        
        important_nodes = {}
        
        # Degree centrality
        degree_cent = nx.degree_centrality(self.graph)
        important_nodes['degree_centrality'] = sorted(
            degree_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # In-degree centrality (most referenced)
        in_degree_cent = nx.in_degree_centrality(self.graph)
        important_nodes['in_degree_centrality'] = sorted(
            in_degree_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Out-degree centrality (most referencing)
        out_degree_cent = nx.out_degree_centrality(self.graph)
        important_nodes['out_degree_centrality'] = sorted(
            out_degree_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return important_nodes

def main():
    """Main function to build and visualize the HCL graph"""
    
    print("Starting HCL Graph Building...")
    
    # Initialize graph builder
    builder = HCLGraphBuilder()
    
    # Load data
    if not builder.load_data():
        print("Failed to load data!")
        return
    
    # Build graph
    builder.build_graph()
    
    # Analyze metrics
    metrics = builder.analyze_graph_metrics()
    print(f"\nGraph Metrics:")
    print(f"- Nodes: {metrics['num_nodes']}")
    print(f"- Edges: {metrics['num_edges']}")
    print(f"- Density: {metrics['density']:.4f}")
    print(f"- Weakly Connected Components: {metrics['num_weakly_connected_components']}")
    
    # Find important nodes
    important_nodes = builder.find_important_nodes()
    print(f"\nMost Important Nodes:")
    
    for measure, nodes in important_nodes.items():
        print(f"\n{measure.replace('_', ' ').title()}:")
        for node, score in nodes:
            print(f"  {node}: {score:.4f}")
    
    # Create visualizations
    print(f"\nCreating visualizations...")
    
    # Static visualization
    builder.create_matplotlib_visualization()
    
    # Interactive visualization
    builder.create_plotly_visualization()
    
    # Dashboard
    builder.create_dashboard()
    
    # Export graph data
    builder.export_graph_data('gexf')
    builder.export_graph_data('json')
    
    print(f"\nGraph analysis complete!")
    print(f"Generated files:")
    print(f"- hcl_graph_matplotlib.png (static graph)")
    print(f"- hcl_graph_interactive.html (interactive graph)")
    print(f"- hcl_dashboard.html (analysis dashboard)")
    print(f"- hcl_graph.gexf (Gephi format)")
    print(f"- hcl_graph.json (JSON format)")

if __name__ == "__main__":
    main() 