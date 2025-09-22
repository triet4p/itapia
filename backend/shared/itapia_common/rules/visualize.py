import graphviz

from .nodes import _TreeNode
from .rule import Rule


def visualize_rule(rule: Rule, filename: str = "rule_visualization", view: bool = True):
    """
    Generate an image file to visualize the structure of a single Rule.

    Args:
        rule (Rule): The Rule object to be visualized.
        filename (str): Output file name (without extension).
        view (bool): If True, automatically open the image file after creation.
    """
    dot = graphviz.Digraph(
        name=f"Rule_{rule.rule_id}",
        comment=rule.rule_id,
        graph_attr={"splines": "ortho", "ranksep": "0.8", "nodesep": "0.4"},
    )
    dot.attr("graph", label=f"Rule: {rule.name}", labelloc="t", fontsize="20")

    # Start the recursive drawing process from the root
    _recursive_draw_node_simple(dot, rule.root)

    # --- Save the file ---
    try:
        dot.render(filename, format="png", view=view, cleanup=True)
        print(f"Visualization saved to {filename}.png")
    except graphviz.backend.execute.CalledProcessError:
        print("\n--- Graphviz Error ---")
        print(
            "Graphviz executable not found. Please install it and ensure it's in your system's PATH."
        )
        print("Download from: https://graphviz.org/download/")
        print("---------------------\n")


def _recursive_draw_node_simple(graph: graphviz.Digraph, node: _TreeNode):
    """Recursively draw a node and its children."""

    # Use object id as unique node ID
    node_id = str(id(node))

    # --- Node formatting ---
    node_label = f"{node.node_name}\n({node.return_type.value})"
    node_style = {"style": "filled"}

    # Determine color and shape based on node type
    if hasattr(node, "children") and node.children:  # Operator node
        node_style["shape"] = "box"
        node_style["fillcolor"] = "skyblue"
    else:  # Terminal node
        node_style["shape"] = "ellipse"
        node_style["fillcolor"] = "lightgreen"

    # Draw the node
    graph.node(node_id, label=node_label, **node_style)

    # --- Recursively draw children and connecting edges ---
    if hasattr(node, "children") and node.children:
        for i, child in enumerate(node.children):
            child_id = str(id(child))

            # Recursively draw child node
            _recursive_draw_node_simple(graph, child)

            # Draw connecting edge
            graph.edge(node_id, child_id, label=f"arg_{i}")
