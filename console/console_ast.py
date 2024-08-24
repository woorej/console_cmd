from context import Context
from typing import Dict, List

class Node:
    def __init__(self, context: Context):
        self.context = context
        self.children = []
        self.parent = None

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)

class MultiTree:
    def __init__(self, root_node: Node):
        self.root = root_node
    
    def find_context(self, context_name):
        """
        Search for the first node in the tree that matches the context name.
        
        :param context_name: The name of the context to find.
        :return: Node if found, else None.
        """
        return self._find_context_recursive(self.root, context_name.lower())

    def _find_context_recursive(self, current_node, context_name):
        """
        Recursively search for the context name in the tree.
        
        :param current_node: The current node to check.
        :param context_name: The name of the context to find.
        :return: Node if found, else None.
        """
        if self._get_context_name(current_node.context).lower() == context_name:
            return current_node
        for child in current_node.children:
            result = self._find_context_recursive(child, context_name)
            if result is not None:
                return result
        return None
    
    def _get_context_name(self, context: Context) -> str:
        """
        Return the custom name if 'name' attribute exists in the context's class,
        otherwise return the class name in the desired format.
        """
        return getattr(context, 'name', type(context).__name__.lower().replace('context', ''))

    def get_children_contexts(self, node: Node) -> Dict[str, Node]:
        """
        Return a dictionary of the contexts of all child nodes of the given node.
        Uses _get_context_name to determine the name of each context.
    
        :param node: The Node object whose child contexts are to be retrieved
        """
        return {self._get_context_name(child.context): child for child in node.children} if node else {}
    
    def get_parent_contexts(self, node: Node) -> Dict[str, Node]:
        """
        Return a dictionary with the context of the parent node of the given node.
        Uses _get_context_name to determine the name of the parent context.
        
        :param node: The Node object whose parent contexts are to be retrieved
        """
        return {self._get_context_name(node.parent.context): node.parent} if node and node.parent else {}

    def get_contexts_keys(self, node: Node) -> List[str]:
        """
        Return a list of context keys for both children and parent contexts of the given node.
        """
        return list(self.get_children_contexts(node).keys()) + list(self.get_parent_contexts(node).keys())
    
    # def get_children_contexts(self, node: Node) -> Dict[str, Node]:
    #     """
    #     Return a dictionary of the contexts of all child nodes of the given node
    
    #     :param node: The Node object whose child contexts are to be retrieved
    #     """
    #     return {type(child.context).__name__.lower().replace('context', ''): child for child in node.children} if node else {}
    
    # def get_parent_contexts(self, node: Node) -> Dict[str, Node]:
    #     """
    #     Return a dictionary with the context of the parent node of the given node
        
    #     :param node: The Node object whose paraent contexts are to be retrieved
    #     """
    #     return {type(node.parent.context).__name__.lower().replace('context', ''): node.parent} if node and node.parent else {}

    # def get_contexts_keys(self, node: Node) -> List[str]:
    #     return list(self.get_children_contexts(node).keys()) + list(self.get_parent_contexts(node).keys())