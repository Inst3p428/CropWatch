from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from models import RainfallData, SoilHealth, FarmRecord, CountyAverages, CropHealth, Crop,Advisory
from extensions import db
from datetime import datetime, date, timedelta

farmer_bp = Blueprint('farmer', __name__, url_prefix='/farmer')


# ================= DASHBOARD =================
@farmer_bp.route('/dashboard')
@login_required
def dashboard():
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403
    farmer_id = current_user.id

    
    # rainfall = RainfallData.query.order_by(RainfallData.date).all()
    
    soil = SoilHealth.query.filter_by(farmer_id=farmer_id).order_by(SoilHealth.date).all()
    records = FarmRecord.query.filter_by(farmer_id=farmer_id).all()
    all_health = CropHealth.query.filter_by(farmer_id=farmer_id).all()
    county_avg = CountyAverages.query.all()
    
    # Get last 30 days of rainfall for THIS SPECIFIC FARMER only
    thirty_days_ago = date.today() - timedelta(days=30)
    rainfall_data = RainfallData.query.filter_by(
        farmer_id=farmer_id
    ).filter(
        RainfallData.date >= thirty_days_ago
    ).order_by(RainfallData.date).all()
    
    # Calculate total rainfall for THIS FARMER only
    total_rainfall = sum(r.rainfall_mm for r in rainfall_data)
    
    # Calculate peak rainfall for THIS FARMER only
    peak_rainfall = max([r.rainfall_mm for r in rainfall_data]) if rainfall_data else 0
    
    # Prepare data for line graph
    rainfall_dates = [r.date.strftime('%Y-%m-%d') for r in rainfall_data]
    rainfall_values = [r.rainfall_mm for r in rainfall_data]
    
    # Get current day rainfall
    today_rainfall = RainfallData.query.filter_by(
        farmer_id=farmer_id,
        date=date.today()
    ).first()
    
    # Get ONLY the latest record for each crop
    latest_per_crop = {}
    for record in all_health:
        if record.crop_id not in latest_per_crop or record.date > latest_per_crop[record.crop_id].date:
            latest_per_crop[record.crop_id] = record
    
    # Convert to list for template
    latest_health = list(latest_per_crop.values())
    
    # Yield trend data per crop
    yield_trends = (
        db.session.query(
            Crop.crop_name,
            func.sum(FarmRecord.yield_kg).label('total_yield')
        )
        .join(FarmRecord, Crop.id == FarmRecord.crop_id)
        .filter(FarmRecord.farmer_id == farmer_id)
        .group_by(Crop.crop_name)
        .all()
    )

    yield_labels = [y.crop_name for y in yield_trends]
    yield_values = [float(y.total_yield) for y in yield_trends]
    
    yield_data = (
    db.session.query(
        Crop.crop_name,
        func.sum(FarmRecord.yield_kg).label('total_yield')
    )
    .join(FarmRecord, Crop.id == FarmRecord.crop_id)
    .filter(FarmRecord.farmer_id == farmer_id)
    .group_by(Crop.crop_name)
    .all()
)

    crop_names = [row.crop_name for row in yield_data]
    crop_yields = [float(row.total_yield) for row in yield_data]

    # Get alerts with crop information
    alerts_with_crop = db.session.query(
        Advisory,
        CropHealth,
        Crop
    ).join(
        CropHealth, Advisory.crop_health_id == CropHealth.id
    ).join(
        Crop, CropHealth.crop_id == Crop.id
    ).filter(
        Advisory.farmer_id == farmer_id
    ).order_by(
        Advisory.created_at.desc()
    ).all()
    
    # Format alerts to include crop info
    formatted_alerts = []
    for advisory, crop_health_record, crop in alerts_with_crop:
        formatted_alerts.append({
            'id': advisory.id,
            'priority': advisory.priority,
            'recommendation': advisory.recommendation,
            'created_at': advisory.created_at,
            'is_read': advisory.is_read,
            'crop_name': crop.crop_name,
            'health_status': crop_health_record.health_status,
            'crop_date': crop_health_record.date,
            'pest_disease': crop_health_record.pest_or_disease
        })
        
    return render_template(
        'farmer/dashboard.html',
        alerts=formatted_alerts,
        # rainfall=rainfall,  
        rainfall_dates=rainfall_dates,
        rainfall_values=rainfall_values,
        total_rainfall=total_rainfall,
        peak_rainfall=peak_rainfall,
        today_rainfall=today_rainfall.rainfall_mm if today_rainfall else 0,
        soil=soil,
        records=records,
        health=latest_health,
        county_avg=county_avg,
        yield_labels=yield_labels,
        yield_values=yield_values,
        crop_names=crop_names,
        crop_yields=crop_yields
    )



# ================= SOIL HEALTH =================
@farmer_bp.route('/soil-health/add', methods=['GET', 'POST'])
@login_required
def add_soil_health():
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403
    
    if request.method == 'POST':
        # Get form data - match database column names
        date = request.form.get('date')
        moisture_percentage = request.form.get('moisture_percentage')  # Changed to match database
        observation = request.form.get('observation')
        
        # Validation
        if not date or not moisture_percentage:
            flash("❌ Please fill all required fields.")
            return redirect(url_for('farmer.add_soil_health'))

        try:
            moisture_percentage = float(moisture_percentage)
            if moisture_percentage < 0 or moisture_percentage > 100:
                flash("❌ Moisture must be between 0 and 100.")
                return redirect(url_for('farmer.add_soil_health'))
        except ValueError:
            flash("❌ Invalid moisture value.")
            return redirect(url_for('farmer.add_soil_health'))
        
        # Create new record
        new_record = SoilHealth(
            farmer_id=current_user.id,
            date=date,
            moisture_percentage=moisture_percentage,
            observation=observation
        )

        try:
            db.session.add(new_record)
            db.session.commit()
            flash('✅ Soil health record added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('❌ Failed to save record. Please try again.', 'error')
            return redirect(url_for('farmer.add_soil_health'))
        
        return redirect(url_for('farmer.add_soil_health'))
    
    # GET request - show form and existing records
    soil_records = SoilHealth.query.filter_by(farmer_id=current_user.id)\
                               .order_by(SoilHealth.date.desc())\
                               .all()

    return render_template(
        'farmer/soil_moisture.html',
        soil_records=soil_records
    )

# ================= CROP HEALTH =================
@farmer_bp.route('/crop-health/add', methods=['GET', 'POST'])
@login_required
def add_crop_health():
    
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403
    
    crops = Crop.query.order_by(Crop.crop_name).all()
    
    farm_records = FarmRecord.query.filter_by(farmer_id=current_user.id).all()
    
    view_mode = request.args.get('view', 'latest')
    all_records = CropHealth.query.filter_by(farmer_id=current_user.id).order_by(CropHealth.date.desc()).all()
    
    if view_mode == 'latest':
        # Show only latest record per crop
        latest_records = {}
        for record in all_records:
            if record.crop_id not in latest_records or record.date > latest_records[record.crop_id].date:
                latest_records[record.crop_id] = record
        crop_health_records = list(latest_records.values())
        # Sort by date (newest first)
        crop_health_records.sort(key=lambda x: x.date, reverse=True)
    else:
        # Show all records
        crop_health_records = all_records
    
    
    
    if request.method == 'POST':

        crop_id = request.form.get('crop_id')
        date = request.form.get('date')
        health_status=request.form.get('health_status')
        pest_or_disease=request.form.get('pest')
        notes=request.form.get('notes')
        
        
        # Validation
        if not all([crop_id, date, health_status]):
            flash("❌ Please fill all required fields.")
            return redirect(url_for('farmer.add_crop_health'))

        # ✅ CHECK FOR DUPLICATE FIRST
        existing_record = CropHealth.query.filter_by(
            farmer_id=current_user.id,
            crop_id=crop_id,
            date=date
        ).first()

        if existing_record:
            flash("❌ A record for this crop on this date already exists.")
            return redirect(url_for('farmer.add_crop_health'))

        # ✅ If no duplicate, save normally
        record = CropHealth(
            farmer_id=current_user.id,
            crop_id=crop_id,
            date=date,
            health_status=health_status,
            pest_or_disease=pest_or_disease,
            notes=notes
        )

        db.session.add(record)
        db.session.commit()

        flash("✅ Crop health record added successfully.")
        return redirect(url_for('farmer.dashboard'))

   
    return render_template(
        'farmer/add_crop_health.html', 
        crops=crops,
        crop_health_records=crop_health_records,
        view_mode=view_mode,
        total_records=len(all_records),
        latest_count=len(set(r.crop_id for r in all_records)),
        farm_records=farm_records
    )

# ================= FARM RECORD =================
@farmer_bp.route('/farm-record/add', methods=['GET', 'POST'])
@login_required
def add_farm_record():
    
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403

    crops = Crop.query.order_by(Crop.crop_name).all()
    
    records = FarmRecord.query.filter_by(farmer_id=current_user.id).all()

    if request.method == 'POST':

        crop_id = request.form['crop_id']
        season = request.form['season'].strip()
        planting_date = request.form.get('planting_date') or None
        harvest_date = request.form.get('harvest_date') or None
        yield_kg = request.form['yield_kg']
        remarks = request.form.get('remarks')

        # ✅ Season validation
        if not season:
            flash("❌ Season cannot be empty.")
            return redirect(url_for('farmer.add_farm_record'))

        # ✅ Yield validation
        try:
            yield_kg = float(yield_kg)
            if yield_kg <= 0:
                flash("❌ Yield must be greater than 0.")
                return redirect(url_for('farmer.add_farm_record'))
        except ValueError:
            flash("❌ Invalid yield value.")
            return redirect(url_for('farmer.add_farm_record'))

        # ✅ Date validation
        if planting_date and harvest_date:
            if harvest_date < planting_date:
                flash("❌ Harvest date cannot be before planting date.")
                return redirect(url_for('farmer.add_farm_record'))

        # ✅ Prevent duplicate season per crop
        existing = FarmRecord.query.filter_by(
            farmer_id=current_user.id,
            crop_id=crop_id,
            season=season
        ).first()

        if existing:
            flash("❌ A record for this crop in this season already exists.")
            return redirect(url_for('farmer.add_farm_record'))

        # ✅ Save safely
        record = FarmRecord(
            farmer_id=current_user.id,
            crop_id=crop_id,
            season=season,
            planting_date=planting_date,
            harvest_date=harvest_date,
            yield_kg=yield_kg,
            remarks=remarks
        )

        db.session.add(record)
        db.session.commit()

        flash(" Farm record added successfully.")
        return redirect(url_for('farmer.dashboard'))

    return render_template(
        'farmer/add_farm_record.html',
        crops=crops,
        records=records
    )
@farmer_bp.route('/crop-health/<int:record_id>/data')
@login_required
def get_crop_health_data(record_id):
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403
    
    """AJAX endpoint to get crop health record data for editing"""
    record = CropHealth.query.get_or_404(record_id)
    
    # Ensure the farmer owns this record
    if record.farmer_id != current_user.id:
        return {"error": "Unauthorized"}, 403
    
    # Check if this crop has been harvested
    has_harvest = FarmRecord.query.filter_by(
        farmer_id=current_user.id,
        crop_id=record.crop_id
    ).first() is not None
    
    return {
        'crop_id': record.crop_id,
        'date': record.date.strftime('%Y-%m-%d') if record.date else '',
        'health_status': record.health_status,
        'pest_or_disease': record.pest_or_disease,
        'notes': record.notes,
        'has_harvest': has_harvest
    }

@farmer_bp.route('/crop-health/<int:record_id>/edit', methods=['POST'])
@login_required
def edit_crop_health(record_id):
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403
    
    """Edit a crop health record"""
    record = CropHealth.query.get_or_404(record_id)
    
    # Ensure the farmer owns this record
    if record.farmer_id != current_user.id:
        flash('You can only edit your own records.', 'error')
        return redirect(url_for('farmer.dashboard'))
    
    # Check if this crop has been harvested
    has_harvest = FarmRecord.query.filter_by(
        farmer_id=current_user.id,
        crop_id=record.crop_id
    ).first() is not None
    
    if has_harvest:
        flash(' Cannot edit crop health records for harvested crops.', 'error')
        return redirect(url_for('farmer.add_crop_health'))
    
    # Update the record
    record.crop_id = request.form['crop_id']
    record.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    record.health_status = request.form['health_status']
    record.pest_or_disease = request.form.get('pest')
    record.notes = request.form.get('notes')
    
    db.session.commit()
    flash(' Crop health record updated successfully.', 'success')
    
    return redirect(url_for('farmer.add_crop_health'))

@farmer_bp.route('/crop-health/<int:record_id>/delete')
@login_required
def delete_crop_health(record_id):
    
    if current_user.role != 'farmer':
        return "Unauthorized", 403
    
    """Delete a crop health record"""
    record = CropHealth.query.get_or_404(record_id)
    
    # Ensure the farmer owns this record
    if record.farmer_id != current_user.id:
        flash('You can only delete your own records.', 'error')
        return redirect(url_for('farmer.dashboard'))
    
    # Check if this crop has been harvested
    has_harvest = FarmRecord.query.filter_by(
        farmer_id=current_user.id,
        crop_id=record.crop_id
    ).first() is not None
    
    if has_harvest:
        flash(' Cannot delete crop health records for harvested crops.', 'error')
        return redirect(url_for('farmer.add_crop_health'))
    
    db.session.delete(record)
    db.session.commit()
    flash('Crop health record deleted successfully.', 'success')
    
    return redirect(url_for('farmer.add_crop_health'))

