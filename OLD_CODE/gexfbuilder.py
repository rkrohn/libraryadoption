#class to create a graph object and export it's gexf representation

from xml.dom import minidom
from cStringIO import StringIO


class Graph():
    """
    Create a Graph object and get its gexf representation.
    Add nodes and edges using add_node() and add_edge() methods.
    Use gexf() to get the file-like object containing the graph. 
    """

    def __init__(self, directed=False):
        self.directed = directed
        self.nodes = {}
        self.edges = {}
        self.attributes = set()

    def __unicode__(self):
        return self.gexf().read()

    def add_node(self, node_id, **kwargs):
        self.nodes.update({node_id: kwargs})
        for attribute in kwargs.keys():
            self.attributes.add(attribute)

    def add_edge(self, from_id, to_id, **kwargs):
		if (from_id, to_id) not in self.edges:
			self.edges.update({(from_id, to_id): kwargs})

    def gexf(self):
        doc = minidom.Document()

        root_node = doc.createElement('gexf')
        root_node.setAttribute('xmlns', 'http://www.gexf.net/1.2draft')
        root_node.setAttribute('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
        root_node.setAttribute('xsi:schemaLocation', 'http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd')
        root_node.setAttribute('version', '1.2')
        doc.appendChild(root_node)

        graph_node = doc.createElement('graph')
        graph_node.setAttribute('mode', 'dynamic')
        graph_node.setAttribute('timeformat', 'date')
        graph_node.setAttribute(
            'defaultedgetype', self.directed and 'directed' or 'undirected'
        )

        attributes_dict = {}
        i = 0
        for attribute in self.attributes:
            if not attribute == 'label':
                attributes_dict[attribute] = str(i)
                i += 1

        # add attributes
        attributes_node = doc.createElement('attributes')
        attributes_node.setAttribute('class', 'node')
        for attribute_name, attribute_id in attributes_dict.items():
            attribute_node = doc.createElement('attribute')
            attribute_node.setAttribute('id', attribute_id)
            attribute_node.setAttribute('title', attribute_name)
            attribute_node.setAttribute('type', 'string')
            attributes_node.appendChild(attribute_node)
        graph_node.appendChild(attributes_node)

        root_node.appendChild(graph_node)

        # Add nodes
        nodes_element = doc.createElement('nodes')
        for node_id, attributes in self.nodes.items():
            node_element = doc.createElement('node')
            node_element.setAttribute('id', node_id)
            if 'label' in attributes:
                node_element.setAttribute('label', attributes['label'])
            if attributes:
                attvalues_element = doc.createElement('attvalues')
                for key, value in attributes.items():
                    if not key == 'label':
                        attvalue_element = doc.createElement('attvalue')
                        attvalue_element.setAttribute('for', attributes_dict[key])
                        attvalue_element.setAttribute('value', value)
                        attvalues_element.appendChild(attvalue_element)
                node_element.appendChild(attvalues_element)
            nodes_element.appendChild(node_element)
        graph_node.appendChild(nodes_element)

        # Add edges
        edges_element = doc.createElement('edges')
        next_id = 0
        for edge, attributes in self.edges.items():
            edge_element = doc.createElement('edge')
            edge_element.setAttribute('id', str(next_id))
            next_id = next_id + 1
            edge_element.setAttribute('source', edge[0])
            edge_element.setAttribute('target', edge[1])
            for key, value in attributes.items():
                edge_element.setAttribute(key, value)
            edges_element.appendChild(edge_element)
        graph_node.appendChild(edges_element)

        f = StringIO()
        f.write(doc.toprettyxml(encoding='UTF-8'))
        f.seek(0)
	return f