# -*- coding: utf-8 -*-
# https://www.tutorialspoint.com/flask

from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import sqlite3 as sql
import os
os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'
import pydot

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///graph.db'
app.config['SECRET_KEY'] = "random string"
IMAGES_FOLDER = os.path.join('static', 'Images')
GRAPH_PATH = IMAGES_FOLDER+'/graph.png'

db=SQLAlchemy(app)

class Node(db.Model):
    __tablename__ = 'nodes'
    node_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    discriminator = db.Column('type', db.String(50))
    __mapper_args__ = {
        'polymorphic_on': discriminator,
        'polymorphic_identity': 'node'}

    def __init__(self, name="n"):
        self.name = name

    def __repr__(self):
        return "<Node(%s)>" % (self.name)

    def __repr__(self):
        return "<" + self.__class__.__name__ + "({})>".format(self.name)

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def above_neighbors(self):
        return [x.node_above for x in self.previous_edges]

    def below_neighbors(self):
        return [x.node_below for x in self.following_edges]


class NodeColored(Node):

    __mapper_args__ = {'polymorphic_identity': 'nodeColored'}
    color = db.Column(db.String(50))

    def __init__(self, name="n", color='white'):
        Node.__init__(self, name)
        self.color = color

    def getColor(self):
        return self.color


class Edge(db.Model):
    __tablename__ = 'edges'
    discriminator = db.Column('type', db.String(50))
    __mapper_args__ = {
        'polymorphic_on': discriminator,
        'polymorphic_identity': 'edge'}
    edge_id = db.Column(db.Integer, primary_key=True)

    above_id = db.Column(db.Integer, db.ForeignKey('nodes.node_id'))
    node_above = db.relationship(Node,
                                 primaryjoin=above_id == Node.node_id,
                                 backref='following_edges')
    below_id = db.Column(db.Integer, db.ForeignKey('nodes.node_id'))
    node_below = db.relationship(Node,
                                 primaryjoin=below_id == Node.node_id,
                                 backref='previous_edges')

    def __init__(self, n1, n2):
        self.node_above = n1
        self.node_below = n2

    def __repr__(self):
        return "<" + self.__class__.__name__ + "({},{})>".format(self.node_above, self.node_below)

    def get_node_above(self):
        return self.node_above

    def set_node_above(self, node):
        self.node_above = node

    def get_node_below(self):
        return self.node_below

    def set_node_below(self, node):
        self.node_below = node


class EdgeWeighted(Edge):
    __tablename__ = 'edgesweighted'
    __mapper_args__ = {
        'polymorphic_identity': 'edgeweighted'
    }
    edge_id = db.Column(db.Integer,
                        db.ForeignKey('edges.edge_id'),
                        primary_key=True)
    weight = db.Column(db.Integer)

    def __init__(self, n1, n2, weight):
        Edge.__init__(self, n1, n2)
        self.weight = weight

    def __repr__(self):
        return "<" + self.__class__.__name__ + "({},{},{})>".format(self.node_above, self.node_below, self.weight)

    def get_weight(self):
        return self.weight


@app.route('/')
def show_all(): 
    #send the Nodes and Edges to be displayed
    return render_template('show_all.html', Nodes = Node.query.all(),Edges = Edge.query.all() )

@app.route('/newNode', methods = ['GET', 'POST'])
def newNode():
    if request.method == 'POST':
        if not request.form['name'] or not request.form['type'] :
            flash('Please enter all the fields', 'error')
        elif request.form['type'] == 'nodeColored' and not request.form['color']:
            flash('Please enter a Color for the node', 'error')

        else:
            if request.form['type'] == 'nodeColored':
                node = NodeColored(request.form['name'], request.form['color'])
            else:
                node = Node(request.form['name'])  
            db.session.add(node)
            db.session.commit()
            flash("The node has been added ! " )
        return redirect(url_for('show_all'))
    return render_template('newNode.html')


@app.route('/newEdge', methods = ['GET', 'POST'])
def newEdge() :
    if request.method == 'POST':
        if not request.form['type'] or not request.form['from'] or not request.form['to']:
            flash('Please enter all the fields', 'error')
        elif request.form['type'] == 'weighted' and not request.form['weight']:
            flash('Please enter a weight', 'error')

        else :
            fromNode = Node.query.filter_by(node_id=request.form['from']).first()
            toNode = Node.query.filter_by(node_id=request.form['to']).first()

            if  request.form['type'] == "weighted" : # match option value 
                edge = EdgeWeighted(fromNode, toNode, request.form['weight']) 
            else :
                edge = Edge(fromNode, toNode)
            db.session.add(edge)
            db.session.commit()
            flash("The edge has been added ! " )
            return redirect(url_for('show_all'))
    return render_template('newEdge.html', nodes =Node.query.all())

@app.route('/newGraph')
def DrawGraph():
    Nodes = Node.query.all()
    Edges = Edge.query.all() 
    graph = pydot.Dot(graph_type='digraph')

    for node in Nodes:
        if isinstance(node, NodeColored):
            dot_n = pydot.Node(node.get_name(), style="filled",
                               fillcolor=node.getColor())
        else:
            dot_n = pydot.Node(node.get_name())
        graph.add_node(dot_n)
    for edge in Edges:
        if isinstance(edge, EdgeWeighted):
            dot_edge = pydot.Edge(edge.get_node_above().get_name(
            ), edge.get_node_below().get_name(), label=edge.get_weight())
        else:
            dot_edge = pydot.Edge(edge.get_node_above(
            ).get_name(), edge.get_node_below().get_name())
        graph.add_edge(dot_edge)

    graph.write_png(GRAPH_PATH)
    flash("The graph has been generated (static/images/graph) ! " )
    return redirect(url_for('show_all'))



if __name__ == '__main__':
   db.create_all()
   app.run(debug = True)
