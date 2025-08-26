from .rule import Rule
from .nodes import _TreeNode

import graphviz

def visualize_rule(
    rule: Rule,
    filename: str = "rule_visualization",
    view: bool = True
):
    """
    Tạo ra một file hình ảnh để trực quan hóa cấu trúc của một Rule duy nhất.

    Args:
        rule (Rule): Đối tượng Rule cần được vẽ.
        filename (str): Tên file output (không baoiven gồm phần mở rộng).
        highlight_nodes (Optional[...]): Một nút hoặc một danh sách các nút cần được tô đậm.
                                          Rất hữu ích để debug crossover/mutation.
        view (bool): Nếu True, tự động mở file ảnh sau khi tạo.
    """
    dot = graphviz.Digraph(
        name=f'Rule_{rule.rule_id}',
        comment=rule.rule_id,
        graph_attr={'splines': 'ortho', 'ranksep': '0.8', 'nodesep': '0.4'}
    )
    dot.attr('graph', label=f'Rule: {rule.name}', labelloc='t', fontsize='20')

    # Bắt đầu quá trình vẽ đệ quy từ gốc
    _recursive_draw_node_simple(dot, rule.root)

    # --- Lưu file ---
    try:
        dot.render(filename, format='png', view=view, cleanup=True)
        print(f"Visualization saved to {filename}.png")
    except graphviz.backend.execute.CalledProcessError:
        print("\n--- Graphviz Error ---")
        print("Graphviz executable not found. Please install it and ensure it's in your system's PATH.")
        print("Download from: https://graphviz.org/download/")
        print("---------------------\n")


def _recursive_draw_node_simple(
    graph: graphviz.Digraph,
    node: _TreeNode
):
    """Hàm đệ quy để vẽ một nút và các con của nó."""
    
    # Dùng object id làm ID duy nhất cho nút
    node_id = str(id(node))
    
    # --- Định dạng cho nút ---
    node_label = f"{node.node_name}\n({node.return_type.value})"
    node_style = {'style': 'filled'}
    
    # Xác định màu sắc và hình dạng
    if hasattr(node, 'children') and node.children: # Operator
        node_style['shape'] = 'box'
        node_style['fillcolor'] = 'skyblue'
    else: # Terminal
        node_style['shape'] = 'ellipse'
        node_style['fillcolor'] = 'lightgreen'

    # Vẽ nút
    graph.node(node_id, label=node_label, **node_style)

    # --- Đệ quy và vẽ các cạnh nối ---
    if hasattr(node, 'children') and node.children:
        for i, child in enumerate(node.children):
            child_id = str(id(child))
            
            # Đệ quy vẽ nút con
            _recursive_draw_node_simple(graph, child)
            
            # Vẽ cạnh nối
            graph.edge(node_id, child_id, label=f"arg_{i}")