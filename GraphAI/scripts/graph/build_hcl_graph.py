#!/usr/bin/env python3
"""
HCL Graph Builder - Creates and visualizes graph based on HCL connections
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any
import seaborn as sns
from collections import Counter
import pandas as pd
import os

class HCLGraphBuilder:
    def __init__(self):
        """Initialize the graph builder"""
        self.graph = nx.DiGraph()  
        self.hcl_data = {}
        
        self.relationship_colors = {
            'modifică': '#FF6B6B',    # Red
            'abrogă': '#4ECDC4',      # Teal  
            'completează': '#45B7D1',  # Blue
            'referă': '#96CEB4',       # Green
            'înlocuiește': '#FECA57',  # Yellow
            'revocă': '#A8A8A8'        # Gray
        }
        
    def load_hcl_data(self, file_path: str = 'results/data_exports/hcl_extracted_data.json') -> bool:
        """Load HCL data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.hcl_data = json.load(f)
            print(f"Loaded {len(self.hcl_data)} HCL items from {file_path}")
            return True
        except Exception as e:
            print(f"Error loading HCL data: {e}")
            return False
    
    def build_graph(self):
        """Build the NetworkX graph from HCL data"""
        print("\nBuilding HCL graph...")
        
        # Add nodes for each HCL
        for hcl_key, hcl_info in self.hcl_data.items():
            # Node attributes
            node_attrs = {
                'nume': hcl_info.get('nume', ''),
                'data_adoptarii': hcl_info.get('data_adoptarii', ''),
                'cuvinte_cheie': hcl_info.get('cuvinte_cheie', []),
                'entitati_principale': hcl_info.get('entitati_principale', []),
                'text_length': hcl_info.get('text_length', 0),
                'num_hcl_legaturi': hcl_info.get('num_hcl_legaturi', 0),
                'num_legi_legaturi': hcl_info.get('num_legi_legaturi', 0)
            }
            
            self.graph.add_node(hcl_key, **node_attrs)
        
        # Add edges based on HCL connections
        edges_added = 0
        for source_hcl, hcl_info in self.hcl_data.items():
            hcl_legaturi = hcl_info.get('hcl_legaturi', [])
            
            for connection in hcl_legaturi:
                # Handle both tuple and list formats (JSON converts tuples to lists)
                if len(connection) >= 2:
                    target_hcl = connection[0]
                    relationship_type = connection[1]
                    
                    # Add edge only if target node exists in our graph
                    if target_hcl in self.graph.nodes:
                        self.graph.add_edge(
                            source_hcl, 
                            target_hcl,
                            relationship_type=relationship_type,
                            weight=1.0
                        )
                        edges_added += 1
                    else:
                        # Add the target HCL as a node even if we don't have its full data
                        self.graph.add_node(target_hcl, 
                                          nume=f"HCL {target_hcl}",
                                          data_adoptarii="",
                                          text_length=0,
                                          is_external=True)
                        self.graph.add_edge(
                            source_hcl, 
                            target_hcl,
                            relationship_type=relationship_type,
                            weight=1.0
                        )
                        edges_added += 1
        
        print(f"✓ Graph built with {len(self.graph.nodes)} nodes and {edges_added} edges")
        
    def analyze_graph_metrics(self) -> Dict[str, Any]:
        """Calculate various graph metrics"""
        print("\nAnalyzing graph metrics...")
        
        metrics = {}
        
        # Basic metrics
        metrics['num_nodes'] = len(self.graph.nodes)
        metrics['num_edges'] = len(self.graph.edges)
        metrics['density'] = nx.density(self.graph)
        
        # Centrality measures
        if len(self.graph.nodes) > 0:
            metrics['in_degree_centrality'] = nx.in_degree_centrality(self.graph)
            metrics['out_degree_centrality'] = nx.out_degree_centrality(self.graph)
            metrics['degree_centrality'] = nx.degree_centrality(self.graph)
            
            # Only calculate if graph is connected
            if nx.is_weakly_connected(self.graph):
                metrics['betweenness_centrality'] = nx.betweenness_centrality(self.graph)
                metrics['closeness_centrality'] = nx.closeness_centrality(self.graph)
        
        # Connected components
        metrics['num_weakly_connected_components'] = nx.number_weakly_connected_components(self.graph)
        metrics['num_strongly_connected_components'] = nx.number_strongly_connected_components(self.graph)
        
        # Relationship type distribution
        edge_types = [self.graph[u][v]['relationship_type'] for u, v in self.graph.edges()]
        metrics['relationship_type_counts'] = Counter(edge_types)
        
        # Node statistics
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())
        metrics['avg_in_degree'] = np.mean(list(in_degrees.values()))
        metrics['avg_out_degree'] = np.mean(list(out_degrees.values()))
        metrics['max_in_degree'] = max(in_degrees.values()) if in_degrees else 0
        metrics['max_out_degree'] = max(out_degrees.values()) if out_degrees else 0
        
        return metrics
    
    def create_matplotlib_visualization(self, figsize=(20, 16)):
        """Create a matplotlib visualization of the graph"""
        print("\nCreating matplotlib visualization...")
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('HCL Relationship Graph Analysis', fontsize=18, fontweight='bold')
        
        # Main graph visualization
        ax1 = axes[0, 0]
        if len(self.graph.nodes) > 0:
            # Calculate layout with better separation
            pos = nx.spring_layout(self.graph, k=4, iterations=100, seed=42)
            
            # Node sizes based on number of connections
            node_sizes = []
            for node in self.graph.nodes():
                total_connections = self.graph.in_degree(node) + self.graph.out_degree(node)
                size = 800 + total_connections * 100  # Larger base size
                node_sizes.append(min(size, 2000))  # Cap at 2000
            
            # Draw nodes with better colors
            nx.draw_networkx_nodes(self.graph, pos, ax=ax1,
                                 node_size=node_sizes,
                                 node_color='lightblue',
                                 alpha=0.8,
                                 edgecolors='darkblue',
                                 linewidths=2)
            
            # Draw edges by relationship type
            for rel_type, color in self.relationship_colors.items():
                edges_of_type = [(u, v) for u, v in self.graph.edges() 
                               if self.graph[u][v]['relationship_type'] == rel_type]
                
                if edges_of_type:
                    nx.draw_networkx_edges(self.graph, pos, ax=ax1,
                                         edgelist=edges_of_type,
                                         edge_color=color,
                                         arrows=True,
                                         arrowsize=20,
                                         alpha=0.7,
                                         width=2)
            
            # Draw labels for ALL nodes - show just the HCL number
            node_labels = {}
            for node in self.graph.nodes():
                # Extract just the number before the slash
                if '/' in node:
                    hcl_number = node.split('/')[0]
                else:
                    hcl_number = node
                node_labels[node] = hcl_number
            
            nx.draw_networkx_labels(self.graph, pos, labels=node_labels, 
                                  font_size=10, font_weight='bold', 
                                  font_color='black', ax=ax1)
            
        ax1.set_title("HCL Relationship Network\n(Numbers show HCL IDs)", fontsize=14)
        ax1.axis('off')
        
        # Add legend for relationship types
        legend_elements = [plt.Line2D([0], [0], color=color, lw=3, label=rel_type) 
                          for rel_type, color in self.relationship_colors.items()]
        ax1.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        # Relationship types distribution
        ax2 = axes[0, 1]
        metrics = self.analyze_graph_metrics()
        rel_types = list(metrics['relationship_type_counts'].keys())
        rel_counts = list(metrics['relationship_type_counts'].values())
        colors = [self.relationship_colors.get(rt, '#CCCCCC') for rt in rel_types]
        
        bars = ax2.bar(rel_types, rel_counts, color=colors, alpha=0.8)
        ax2.set_title('Relationship Types Distribution', fontsize=14)
        ax2.set_xlabel('Relationship Type')
        ax2.set_ylabel('Count')
        plt.setp(ax2.get_xticklabels(), rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # Node degree distribution
        ax3 = axes[1, 0]
        degrees = [self.graph.degree(node) for node in self.graph.nodes()]
        ax3.hist(degrees, bins=max(1, len(set(degrees))), alpha=0.8, color='skyblue', edgecolor='navy')
        ax3.set_title('Node Degree Distribution', fontsize=14)
        ax3.set_xlabel('Degree')
        ax3.set_ylabel('Number of Nodes')
        
        # Top nodes by centrality
        ax4 = axes[1, 1]
        if 'in_degree_centrality' in metrics:
            top_nodes = sorted(metrics['in_degree_centrality'].items(), 
                             key=lambda x: x[1], reverse=True)[:8]
            nodes, centralities = zip(*top_nodes) if top_nodes else ([], [])
            
            # Show HCL numbers instead of full names
            short_nodes = []
            for node in nodes:
                if '/' in node:
                    hcl_num = node.split('/')[0]
                    year = node.split('/')[1]
                    short_nodes.append(f"HCL {hcl_num}/{year}")
                else:
                    short_nodes.append(node)
            
            bars = ax4.barh(range(len(short_nodes)), centralities, color='lightcoral', alpha=0.8)
            ax4.set_yticks(range(len(short_nodes)))
            ax4.set_yticklabels(short_nodes)
            ax4.set_title('Top HCLs by In-Degree Centrality', fontsize=14)
            ax4.set_xlabel('Centrality Score')
            
            # Add value labels
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax4.text(width + 0.002, bar.get_y() + bar.get_height()/2,
                        f'{width:.3f}', ha='left', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig('results/visualizations/hcl_graph_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✓ Matplotlib visualization saved as 'results/visualizations/hcl_graph_analysis.png'")
    
    def create_interactive_visualization(self):
        """Create an interactive Plotly visualization"""
        print("\nCreating interactive visualization...")
        
        if len(self.graph.nodes) == 0:
            print("No nodes to visualize")
            return
        
        # Calculate layout
        pos = nx.spring_layout(self.graph, k=3, iterations=50, seed=42)
        
        # Prepare edge traces by relationship type
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
                    name=f'{rel_type} ({len(edge_info)})',
                    showlegend=True
                )
                edge_traces.append(edge_trace)
        
        # Prepare node trace
        node_x = []
        node_y = []
        node_info = []
        node_sizes = []
        node_colors = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node info for hover
            node_attrs = self.graph.nodes[node]
            info = f"<b>HCL: {node}</b><br>"
            info += f"Nume: {node_attrs.get('nume', 'N/A')[:60]}...<br>"
            info += f"Data: {node_attrs.get('data_adoptarii', 'N/A')}<br>"
            info += f"Text length: {node_attrs.get('text_length', 0)} chars<br>"
            info += f"Legături HCL: {node_attrs.get('num_hcl_legaturi', 0)}<br>"
            info += f"Legături legi: {node_attrs.get('num_legi_legaturi', 0)}<br>"
            info += f"In-degree: {self.graph.in_degree(node)}<br>"
            info += f"Out-degree: {self.graph.out_degree(node)}"
            
            node_info.append(info)
            
            # Node size based on total degree
            total_degree = self.graph.degree(node)
            size = 20 + total_degree * 5
            node_sizes.append(min(size, 60))
            
            # Node color based on year
            try:
                if '/' in node:
                    year = int(node.split('/')[1])
                    # Color gradient from blue (old) to red (new)
                    year_norm = (year - 2003) / (2024 - 2003)  # Normalize between 0 and 1
                    node_colors.append(year_norm)
                else:
                    node_colors.append(0.5)
            except:
                node_colors.append(0.5)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node.split('/')[0] for node in self.graph.nodes()],  # Show just HCL number
            textposition="middle center",
            textfont=dict(size=12, color='white', family='Arial Black'),  # Better text formatting
            hovertext=node_info,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                colorscale='RdYlBu_r',
                showscale=True,
                colorbar=dict(
                    title="Anul HCL-ului"
                ),
                line=dict(width=3, color='darkblue')  # Thicker border
            ),
            name='HCL Documents',
            showlegend=False
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace],
                       layout=go.Layout(
                           title=dict(
                               text='Interactive HCL Relationship Graph<br><sub>Node size = degree, Color = year</sub>',
                               x=0.5,
                               font=dict(size=16)
                           ),
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=80),
                           annotations=[ dict(
                               text="Hover over nodes for details. Legend shows relationship types.",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002 ) ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white'
                       ))
        
        fig.write_html("results/visualizations/hcl_graph_interactive.html")
        fig.show()
        print("✓ Interactive graph saved as 'results/visualizations/hcl_graph_interactive.html'")
    
    def export_graph_data(self):
        """Export graph data in various formats"""
        print("\nExporting graph data...")
        
        # Create output directory if it doesn't exist
        os.makedirs('results/data_exports', exist_ok=True)
        
        # Export to GEXF (Gephi format)
        nx.write_gexf(self.graph, "results/data_exports/hcl_graph.gexf")
        print("✓ Graph exported as 'results/data_exports/hcl_graph.gexf' (Gephi format)")
        
        # Export to JSON
        graph_data = nx.node_link_data(self.graph)
        with open('results/data_exports/hcl_graph.json', 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        print("✓ Graph exported as 'results/data_exports/hcl_graph.json'")
        
        # Export adjacency matrix to CSV
        adj_matrix = nx.adjacency_matrix(self.graph, weight='weight')
        nodes_list = list(self.graph.nodes())
        
        df_adj = pd.DataFrame(adj_matrix.toarray(), 
                            index=nodes_list, 
                            columns=nodes_list)
        df_adj.to_csv('results/data_exports/hcl_adjacency_matrix.csv', encoding='utf-8')
        print("✓ Adjacency matrix exported as 'results/data_exports/hcl_adjacency_matrix.csv'")
    
    def print_graph_summary(self):
        """Print a comprehensive summary of the graph"""
        metrics = self.analyze_graph_metrics()
        
        print("\n" + "="*60)
        print("HCL GRAPH SUMMARY")
        print("="*60)
        
        print(f"📊 Basic Statistics:")
        print(f"  • Total nodes: {metrics['num_nodes']}")
        print(f"  • Total edges: {metrics['num_edges']}")
        print(f"  • Graph density: {metrics['density']:.4f}")
        print(f"  • Weakly connected components: {metrics['num_weakly_connected_components']}")
        print(f"  • Average in-degree: {metrics['avg_in_degree']:.2f}")
        print(f"  • Average out-degree: {metrics['avg_out_degree']:.2f}")
        
        print(f"\n🔗 Relationship Types:")
        for rel_type, count in metrics['relationship_type_counts'].most_common():
            print(f"  • {rel_type}: {count} connections")
        
        print(f"\n⭐ Most Referenced HCLs (In-Degree):")
        if 'in_degree_centrality' in metrics:
            top_in = sorted(metrics['in_degree_centrality'].items(), 
                           key=lambda x: x[1], reverse=True)[:5]
            for hcl, centrality in top_in:
                in_degree = self.graph.in_degree(hcl)
                nume = self.graph.nodes[hcl].get('nume', 'N/A')[:40]
                print(f"  • {hcl}: {in_degree} references - {nume}...")
        
        print(f"\n📤 Most Referencing HCLs (Out-Degree):")
        if 'out_degree_centrality' in metrics:
            top_out = sorted(metrics['out_degree_centrality'].items(), 
                            key=lambda x: x[1], reverse=True)[:5]
            for hcl, centrality in top_out:
                out_degree = self.graph.out_degree(hcl)
                nume = self.graph.nodes[hcl].get('nume', 'N/A')[:40]
                print(f"  • {hcl}: references {out_degree} others - {nume}...")

def main():
    """Main function to build and visualize the HCL graph"""
    
    print("HCL GRAPH BUILDER")
    print("="*50)
    print("Building graph from extracted HCL data...")
    
    # Initialize graph builder
    builder = HCLGraphBuilder()
    
    # Load data
    if not builder.load_hcl_data():
        print("Failed to load HCL data!")
        return
    
    # Build graph
    builder.build_graph()
    
    # Print summary
    builder.print_graph_summary()
    
    # Create visualizations
    builder.create_matplotlib_visualization()
    builder.create_interactive_visualization()
    
    # Export data
    builder.export_graph_data()
    
    print(f"\n🎉 GRAPH ANALYSIS COMPLETE!")
    print(f"Generated files:")
    print(f"  • results/visualizations/hcl_graph_analysis.png - Static analysis visualization")
    print(f"  • results/visualizations/hcl_graph_interactive.html - Interactive graph")
    print(f"  • results/data_exports/hcl_graph.gexf - Gephi format")
    print(f"  • results/data_exports/hcl_graph.json - JSON format")
    print(f"  • results/data_exports/hcl_adjacency_matrix.csv - Adjacency matrix")

if __name__ == "__main__":
    main() 