from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="Available")
    issuances = db.relationship('Issuance', backref='product', lazy=True)

class Issuance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submission_date = db.Column(db.DateTime, nullable=True)

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/issue/<int:product_id>')
def issue_product(product_id):
    product = Product.query.get_or_404(product_id)
    issuance = Issuance(product_id=product.id)

    db.session.add(issuance)
    product.status = "In Use"
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/submit/<int:issuance_id>')
def submit_product(issuance_id):
    issuance = Issuance.query.get_or_404(issuance_id)
    issuance.submission_date = datetime.utcnow()
    product = Product.query.get_or_404(issuance.product_id)
    product.status = "Available"

    db.session.add(issuance)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/report')
def report():
    issuances = Issuance.query.all()
    return render_template('report.html', issuances=issuances)

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            data = pd.read_excel(file)
            for index, row in data.iterrows():
                product = Product(name=row['name'], description=row['description'])
                db.session.add(product)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('import.html')

@app.route('/clear')
def clear_data():
    db.session.query(Issuance).delete()
    db.session.query(Product).delete()
    db.session.commit()
    return redirect(url_for('index'))
def generate_report_data():
    # Generate dummy report data
    report_data = "Product Name,Status\n"
    products = Product.query.all()
    for product in products:
        report_data += f"{product.name},{product.status}\n"
    return report_data

@app.route('/download_report')
def download_report():
    report_data = generate_report_data()  
    filename = 'report.csv'
    response = make_response(report_data)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/add_sample_data')
def add_sample_data():
    sample_products = [
        Product(name="MOLD 1", description="SHELF ID 1"),
        Product(name="MOLD 2", description="SHELF ID 2"),
        Product(name="MOLD 3", description="SHELF ID 3")
    ]
    db.session.bulk_save_objects(sample_products)
    db.session.commit()
    return redirect(url_for('index'))
@app.route('/scan')
def scan():
    return render_template('qr_scan.html')

@app.route('/process_scan', methods=['POST'])
def process_scan():
    scanned_data = request.form['scanned_data']
    # Process the scanned data here
    return f"Scanned Data: {scanned_data}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)