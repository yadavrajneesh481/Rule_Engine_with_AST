from flask import Flask, request, jsonify
import json
import logging
from pymongo import MongoClient
from bson import ObjectId
import random
import string

app = Flask(__name__)

# Set up logging to handle messages above DEBUG level
logging.basicConfig(level=logging.DEBUG)

# Specifically reduce pymongo's logging level
logger = logging.getLogger('pymongo')
logger.setLevel(logging.INFO)

# Setup MongoDB connection
client = MongoClient('mongodb+srv://<USERNAME>:<PASSWORD>@cluster0.vutzzt4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.test  # Replace 'test' with your database name
rules_collection = db.rules

class Node:
    def __init__(self, type, value, left=None, right=None):
        self.type = type
        self.value = value
        self.left = left
        self.right = right

    def to_dict(self):
        return {
            'type': self.type,
            'value': self.value,
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None
        }

    @staticmethod
    def from_dict(data):
        left_node = Node.from_dict(data['left']) if data['left'] else None
        right_node = Node.from_dict(data['right']) if data['right'] else None
        return Node(data['type'], data['value'], left_node, right_node)

def parse_rule_string(rule_string):
    tokens = rule_string.replace('(', ' ( ').replace(')', ' ) ').split()

    def parse_expression():
        stack = [[]]
        for token in tokens:
            if token == '(':
                stack.append([])
            elif token == ')':
                expr = stack.pop()
                stack[-1].append(expr)
            elif token in ['AND', 'OR']:
                stack[-1].append(token)
            else:
                stack[-1].append(token)
        
        def build_tree(expr):
            if isinstance(expr, list):
                if len(expr) == 1:
                    return build_tree(expr[0])
                elif 'OR' in expr:
                    idx = expr.index('OR')
                    return Node('operator', 'OR', build_tree(expr[:idx]), build_tree(expr[idx+1:]))
                elif 'AND' in expr:
                    idx = expr.index('AND')
                    return Node('operator', 'AND', build_tree(expr[:idx]), build_tree(expr[idx+1:]))
            return Node('operand', ' '.join(expr))
        
        return build_tree(stack[0])
    
    return parse_expression()

def evaluate_ast(ast, data):
    if ast.type == 'operator':
        if ast.value == 'AND':
            return evaluate_ast(ast.left, data) and evaluate_ast(ast.right, data)
        elif ast.value == 'OR':
            return evaluate_ast(ast.left, data) or evaluate_ast(ast.right, data)
    elif ast.type == 'operand':
        left, op, right = ast.value.split()
        left_value = data.get(left)
        right_value = int(right) if right.isdigit() else right.strip("'")
        if op == '>':
            return left_value > right_value
        elif op == '<':
            return left_value < right_value
        elif op == '=':
            return left_value == right_value
    return False

def generate_custom_id():
    numbers = ''.join(random.choices(string.digits, k=2))
    letters = ''.join(random.choices(string.ascii_letters, k=2))
    return numbers + letters

@app.route('/create_rule', methods=['POST'])
def create_rule():
    rule_string = request.json['rule_string']
    ast = parse_rule_string(rule_string).to_dict()
    # Insert without specifying an ID to let MongoDB generate an ObjectId automatically
    result = rules_collection.insert_one({'rule_string': rule_string, 'ast': ast})
    rule_id = result.inserted_id  # MongoDB generates an ObjectId
    return jsonify({'id': str(rule_id), 'ast': ast})

@app.route('/combine_rules', methods=['POST'])
def combine_rules():
    rule_ids = request.json['rule_ids']
    rules = rules_collection.find({'_id': {'$in': rule_ids}})
    combined_ast = Node('operator', 'AND', *[Node.from_dict(rule['ast']) for rule in rules])
    combined_rule_string = " AND ".join([rule['rule_string'] for rule in rules])
    combined_rule_id = generate_custom_id()  # Use custom ID instead of MongoDB's ObjectId
    rules_collection.insert_one({'_id': combined_rule_id, 'rule_string': combined_rule_string, 'ast': combined_ast.to_dict()})
    return jsonify({'id': combined_rule_id, 'combined_ast': combined_ast.to_dict()})

@app.route('/evaluate_rule', methods=['POST'])
def evaluate_rule():
    rule_id = request.json['rule_id']
    # Find the rule using the custom string ID directly without converting to ObjectId
    rule = rules_collection.find_one({'_id': rule_id})
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    ast = Node.from_dict(rule['ast'])
    data = request.json['data']
    result = evaluate_ast(ast, data)
    return jsonify({'result': result})


@app.route('/modify_rule', methods=['POST'])
def modify_rule():
    try:
        rule_id = request.json['rule_id']
        new_rule_string = request.json['new_rule_string']
        rule = session.query(Rule).filter_by(id=rule_id).first()
        if rule:
            rule.rule_string = new_rule_string
            rule.ast = json.dumps(parse_rule_string(new_rule_string).to_dict())
            session.commit()
            return jsonify({'message': 'Rule updated successfully'})
        else:
            return jsonify({'message': 'Rule not found'}), 404
    except Exception as e:
        logging.error(f"Error modifying rule: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500



if __name__ == '__main__':
    app.run(debug=True)
