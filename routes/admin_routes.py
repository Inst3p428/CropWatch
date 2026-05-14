from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Admin,Farmer, Officer
from extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    #if current_user.role != 'admin':
        #return "Unauthorized", 403
        
    total_farmers = Farmer.query.count()
    total_officers = Officer.query.count()


    return render_template(
        'admin/dashboard.html',
        total_farmers = total_farmers,
        total_officers = total_officers
    )

@admin_bp.route('/farmer/add', methods=['GET', 'POST'])
@login_required
def add_farmer():
    #if current_user.role != 'admin':
        #return "Unauthorized", 403

    if request.method == 'POST':
        farmer = Farmer(
            full_name=request.form['full_name'],
            email=request.form['email'],
            county=request.form['county'],
            sub_county=request.form['sub_county'],
            farm_size_acres=request.form['farm_size_acres'],
            role=request.form['role'] 
        )
        farmer.set_password(request.form['password'])

        db.session.add(farmer)
        db.session.commit()

        flash('Farmer added successfully')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_farmer.html')

@admin_bp.route('/officer/add', methods=['GET', 'POST'])
@login_required
def add_officer():
    #if current_user.role != 'admin':
        #return "Unauthorized", 403
     

    if request.method == 'POST':
        officer = Officer(
            full_name=request.form['full_name'],
            email=request.form['email'],
            role=request.form['role']
        )
        officer.set_password(request.form['password'])

        db.session.add(officer)
        db.session.commit()

        flash('Officer added successfully')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_officer.html')



# View farmers
@admin_bp.route('/farmers')
@login_required
def view_farmers():

    """if current_user.role != 'admin':
        return "Unauthorized", 403"""

    farmers = Farmer.query.all()

    return render_template(
        'admin/view_farmers.html',
        farmers=farmers
    )


# View officers
@admin_bp.route('/officers')
@login_required
def view_officers():

    """if current_user.role != 'admin':
        return "Unauthorized", 403"""

    officers = Officer.query.all()

    return render_template(
        'admin/view_officers.html',
        officers=officers
    )


# Edit farmer
@admin_bp.route('/farmer/edit/<int:farmer_id>', methods=['GET', 'POST'])
@login_required
def edit_farmer(farmer_id):

    """if current_user.role != 'admin':
        return "Unauthorized", 403"""

    farmer = Farmer.query.get_or_404(farmer_id)

    if request.method == 'POST':
        farmer.full_name = request.form['full_name']
        farmer.email = request.form['email']
        farmer.county = request.form['county']
        farmer.sub_county = request.form['sub_county']
        farmer.farm_size_acres = request.form['farm_size']

        db.session.commit()

        flash("Farmer updated successfully")
        return redirect(url_for('admin.view_farmers'))

    return render_template(
        'admin/edit_farmer.html',
        farmer=farmer
    )


# Delete farmer
@admin_bp.route('/farmer/delete/<int:farmer_id>')
@login_required
def delete_farmer(farmer_id):

    """if current_user.role != 'admin':
        return "Unauthorized", 403"""

    farmer = Farmer.query.get_or_404(farmer_id)
    
    if farmer.id == current_user.id:
        flash("You cannot delete yourself")
        return redirect(url_for('admin.view_farmers'))
    
    db.session.delete(farmer)
    db.session.commit()

    flash("Farmer deleted successfully")
    return redirect(url_for('admin.view_farmers'))

#Edit officer
@admin_bp.route('/officer/edit/<int:officer_id>', methods=['GET', 'POST'])
@login_required
def edit_officer(officer_id):

    """if current_user.role != 'admin':
        return "Unauthorized", 403"""

    officer = Officer.query.get_or_404(officer_id)

    if request.method == 'POST':
        officer.full_name = request.form['full_name']
        officer.email = request.form['email']
        #officer.county = request.form['county']

        db.session.commit()

        flash("Officer updated successfully")
        return redirect(url_for('admin.view_officers'))

    return render_template(
        'admin/edit_officer.html',
        officer=officer
    )

#Delete Officer
@admin_bp.route('/officer/delete/<int:officer_id>')
@login_required
def delete_officer(officer_id):

    """if current_user.role != 'admin':
        return "Unauthorized", 403"""

    officer = Officer.query.get_or_404(officer_id)

    db.session.delete(officer)
    db.session.commit()

    flash("Officer deleted successfully")
    return redirect(url_for('admin.view_officers'))

